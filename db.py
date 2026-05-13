"""
db.py — Database access layer for the SA EMIS Dashboard.

All SQL-level normalisation happens here so that charts.py and app.py
only deal with clean, analysis-ready DataFrames.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Path ──────────────────────────────────────────────────────────────────────
DB_PATH = str(Path(__file__).parent / "emis.db")

# ── Base normalisation query (CTE style) ─────────────────────────────────────
_NORM_SQL = """
    SELECT
        NatEmis,
        Official_Institution_Name                                        AS school_name,
        Province,
        EIDistrict,
        DMunName,
        UPPER(TRIM(Sector))                                              AS Sector,
        Phase_PED,
        CASE UPPER(TRIM(Quintile))
            WHEN 'Q1' THEN 'Q1'  WHEN 'Q2' THEN 'Q2'  WHEN 'Q3' THEN 'Q3'
            WHEN 'Q4' THEN 'Q4'  WHEN 'Q5' THEN 'Q5'
            ELSE 'Other'
        END                                                              AS Quintile,
        CASE
            WHEN UPPER(TRIM(NoFeeSchool)) IN ('NO FEE', 'YES')         THEN 'No Fee'
            WHEN UPPER(TRIM(NoFeeSchool)) IN ('FEE CHARGING',
                                              'FREE CHARGING',
                                              'NO', 'N')               THEN 'Fee Charging'
            ELSE 'Unknown'
        END                                                              AS NoFeeSchool,
        CASE
            WHEN UPPER(TRIM(Urban_Rural)) LIKE '%RURAL%'               THEN 'Rural'
            WHEN UPPER(TRIM(Urban_Rural)) LIKE '%URBAN%'               THEN 'Urban'
            ELSE 'Unknown'
        END                                                              AS Urban_Rural,
        CAST(NULLIF(TRIM(Learners2025),  '') AS REAL)                    AS Learners2025,
        CAST(NULLIF(TRIM(Educators2025), '') AS REAL)                    AS Educators2025,
        CAST(NULLIF(REPLACE(TRIM(GIS_Long), ',', '.'), '') AS REAL)      AS lng,
        CAST(NULLIF(REPLACE(TRIM(GIS_Lat),  ',', '.'), '') AS REAL)      AS lat
    FROM emis
    WHERE UPPER(TRIM(Status)) IN ('OPEN', 'PENDING OPEN')
"""


def _build_where(
    provinces: tuple,
    districts: tuple,
    sectors: tuple,
    phases: tuple,
    quintiles: tuple,
) -> tuple[str, list]:
    """Return (WHERE clause string, params list) for the normalised sub-query."""
    conditions: list[str] = []
    params: list = []

    def _add(col: str, values: tuple) -> None:
        if values:
            ph = ",".join("?" * len(values))
            conditions.append(f"{col} IN ({ph})")
            params.extend(values)

    _add("Province",  provinces)
    _add("EIDistrict", districts)
    _add("Sector",    sectors)
    _add("Phase_PED", phases)
    _add("Quintile",  quintiles)

    return (" AND ".join(conditions), params)


# ── Main data loader ──────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def load_filtered_data(
    provinces: tuple | None = None,
    districts: tuple | None = None,
    sectors:   tuple | None = None,
    phases:    tuple | None = None,
    quintiles: tuple | None = None,
) -> pd.DataFrame:
    """
    Load schools from the DB with optional filters applied.
    All parameters should be tuples (hashable) or None.
    Returns a clean DataFrame with derived LER columns appended.
    """
    where_clause, params = _build_where(
        provinces  or (),
        districts  or (),
        sectors    or (),
        phases     or (),
        quintiles  or (),
    )
    sql = f"SELECT * FROM ({_NORM_SQL})"
    if where_clause:
        sql += f" WHERE {where_clause}"

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(sql, conn, params=params)

    # Derived columns
    df["LER"] = (
        df["Learners2025"] / df["Educators2025"].replace(0, float("nan"))
    ).round(1)

    df["LER_strain"] = df["LER"].apply(
        lambda x: (
            "Critical (>40)"  if pd.notna(x) and x > 40 else
            "High (30–40)"    if pd.notna(x) and x > 30 else
            "Normal (≤30)"
        )
    )
    return df


# ── Filter option loaders (cached independently) ─────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def get_provinces() -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT DISTINCT Province FROM emis "
            "WHERE Province != '' ORDER BY Province",
            conn,
        )["Province"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_districts(provinces: tuple | None = None) -> list[str]:
    """Return districts, optionally scoped to selected provinces."""
    if provinces:
        ph = ",".join("?" * len(provinces))
        sql = (
            f"SELECT DISTINCT EIDistrict FROM emis "
            f"WHERE Province IN ({ph}) AND EIDistrict != '' "
            f"ORDER BY EIDistrict"
        )
        params: list = list(provinces)
    else:
        sql = (
            "SELECT DISTINCT EIDistrict FROM emis "
            "WHERE EIDistrict != '' ORDER BY EIDistrict"
        )
        params = []

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)["EIDistrict"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_phases() -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT DISTINCT Phase_PED FROM emis "
            "WHERE Phase_PED != '' ORDER BY Phase_PED",
            conn,
        )["Phase_PED"].tolist()
