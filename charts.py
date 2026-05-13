"""
charts.py — All Plotly figure builders for the SA EMIS Dashboard.

Each function accepts a clean DataFrame (as returned by db.load_filtered_data)
and returns a go.Figure ready for st.plotly_chart().
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Palette & theme constants ─────────────────────────────────────────────────
QUINTILE_COLORS: dict[str, str] = {
    "Q1":    "#ef4444",   # red   — most disadvantaged
    "Q2":    "#f97316",   # orange
    "Q3":    "#eab308",   # yellow
    "Q4":    "#84cc16",   # lime
    "Q5":    "#22c55e",   # green — most advantaged
    "Other": "#94a3b8",   # slate
}

PROVINCE_PALETTE = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f43f5e",
    "#f97316", "#eab308", "#22c55e", "#14b8a6", "#3b82f6",
]

PROVINCE_NAMES: dict[str, str] = {
    "EC": "Eastern Cape",  "FS": "Free State",   "GT": "Gauteng",
    "KZN": "KwaZulu-Natal","LP": "Limpopo",       "MP": "Mpumalanga",
    "NC": "Northern Cape", "NW": "North West",    "WC": "Western Cape",
}

LER_COLORS: dict[str, str] = {
    "Normal (≤30)":   "#22c55e",
    "High (30–40)":   "#f97316",
    "Critical (>40)": "#ef4444",
}

NO_FEE_COLORS: dict[str, str] = {
    "No Fee":       "#22c55e",
    "Fee Charging": "#f43f5e",
    "Unknown":      "#475569",
}

# dark theme
_BG       = "#0a0a14"
_PAPER    = "#13131f"
_GRID     = "#1e1e2e"
_TEXT     = "#e2e8f0"
_MUTED    = "#94a3b8"
_FONT     = "Inter, system-ui, sans-serif"

_LAYOUT = dict(
    paper_bgcolor = _PAPER,
    plot_bgcolor  = _BG,
    font          = dict(family=_FONT, color=_TEXT, size=13),
    margin        = dict(t=52, r=16, b=32, l=16),
    legend        = dict(
        bgcolor     = "rgba(255,255,255,0.05)",
        bordercolor = "rgba(255,255,255,0.1)",
        borderwidth = 1,
        font_size   = 12,
    ),
)

def _dark_axes(fig: go.Figure) -> go.Figure:
    axis_style = dict(
        gridcolor     = _GRID,
        zerolinecolor = _GRID,
        linecolor     = _GRID,
        tickfont      = dict(color=_MUTED, size=11),
        title_font    = dict(color=_MUTED),
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)
    return fig


# ── 1. KPI computation ────────────────────────────────────────────────────────
def compute_kpis(df: pd.DataFrame) -> dict:
    total_schools   = len(df)
    total_learners  = int(df["Learners2025"].sum())
    total_educators = int(df["Educators2025"].sum())
    national_ler    = (
        round(total_learners / total_educators, 1) if total_educators > 0 else 0.0
    )
    no_fee_pct = (
        round(100 * (df["NoFeeSchool"] == "No Fee").sum() / total_schools, 1)
        if total_schools > 0 else 0.0
    )
    critical_count = int((df["LER_strain"] == "Critical (>40)").sum())

    return {
        "total_schools":   total_schools,
        "total_learners":  total_learners,
        "total_educators": total_educators,
        "national_ler":    national_ler,
        "no_fee_pct":      no_fee_pct,
        "critical_count":  critical_count,
    }


# ── 2. Geospatial scatter map ─────────────────────────────────────────────────
def scatter_map(df: pd.DataFrame, color_by: str = "Quintile") -> go.Figure:
    """
    Plot all schools on a dark map of South Africa.
    Marker size ∝ sqrt(Learners2025).  Colour by Quintile or Phase_PED.
    """
    mdf = df.dropna(subset=["lat", "lng", "Learners2025"]).copy()
    # Clip to SA bounding box (removes stray/bad coordinates)
    mdf = mdf[mdf["lat"].between(-35.5, -21.5) & mdf["lng"].between(15.5, 33.5)]

    # Normalise marker size to [5, 22] using sqrt scale
    raw  = np.sqrt(mdf["Learners2025"].clip(lower=1))
    rmin, rmax = raw.min(), raw.max()
    mdf["_sz"] = 5 + 17 * (raw - rmin) / max(rmax - rmin, 1)

    mdf["LER_disp"] = (
        mdf["Learners2025"] / mdf["Educators2025"].replace(0, np.nan)
    ).round(1).astype(str)

    mdf["_tip"] = (
        "<b>" + mdf["school_name"] + "</b><br>"
        + "District: "  + mdf["EIDistrict"].fillna("—") + "<br>"
        + "Province: "  + mdf["Province"] + "<br>"
        + "Learners: "  + mdf["Learners2025"].astype(int).astype(str) + "<br>"
        + "Educators: " + mdf["Educators2025"].fillna(0).astype(int).astype(str) + "<br>"
        + "LER: <b>"    + mdf["LER_disp"] + "</b>"
    )

    # Build category → colour map
    if color_by == "Quintile":
        color_map  = QUINTILE_COLORS
        categories = ["Q1", "Q2", "Q3", "Q4", "Q5", "Other"]
    else:
        cats       = sorted(mdf["Phase_PED"].dropna().unique())
        color_map  = dict(zip(cats, PROVINCE_PALETTE))
        categories = cats

    fig = go.Figure()
    for cat in categories:
        sub = mdf[mdf[color_by] == cat]
        if sub.empty:
            continue
        fig.add_trace(go.Scattermapbox(
            lat=sub["lat"],
            lon=sub["lng"],
            mode="markers",
            marker=dict(
                size    = sub["_sz"],
                color   = color_map.get(cat, "#94a3b8"),
                opacity = 0.78,
            ),
            text             = sub["_tip"],
            hovertemplate    = "%{text}<extra></extra>",
            name             = cat,
        ))

    fig.update_layout(
        **_LAYOUT,
        mapbox=dict(
            style  = "carto-darkmatter",
            center = dict(lat=-29.0, lon=25.0),
            zoom   = 4.8,
        ),
        height = 540,
        margin = dict(t=8, r=0, b=0, l=0),
        legend = dict(
            orientation = "v",
            x=0.01, y=0.99,
            bgcolor     = "rgba(10,10,20,0.80)",
            bordercolor = "rgba(255,255,255,0.12)",
            borderwidth = 1,
            font_size   = 12,
        ),
        uirevision="map",
    )
    return fig


# ── 3. Sunburst: Province → Quintile ─────────────────────────────────────────
def sunburst_province_quintile(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby(["Province", "Quintile"], observed=True)
        .agg(Schools=("NatEmis", "count"), Learners=("Learners2025", "sum"))
        .reset_index()
    )
    agg["Province_Label"] = agg["Province"].map(PROVINCE_NAMES).fillna(agg["Province"])

    fig = px.sunburst(
        agg,
        path          = ["Province_Label", "Quintile"],
        values        = "Schools",
        color         = "Quintile",
        color_discrete_map = {**QUINTILE_COLORS, "(?)": "#334155"},
        custom_data   = ["Learners"],
    )
    fig.update_traces(
        hovertemplate = (
            "<b>%{label}</b><br>"
            "Schools: %{value:,}<br>"
            "Learners: %{customdata[0]:,.0f}<br>"
            "<extra></extra>"
        ),
        textfont_size          = 11,
        insidetextorientation  = "radial",
        leaf_opacity           = 0.88,
    )
    fig.update_layout(
        **_LAYOUT,
        title = dict(text="Schools by Province & Quintile", font_size=14, x=0.5,
                     font_color=_TEXT),
        height = 430,
    )
    return fig


# ── 4. Dual donut: No-Fee vs Fee by Sector ───────────────────────────────────
def donut_no_fee_by_sector(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby(["Sector", "NoFeeSchool"], observed=True)
        .size()
        .reset_index(name="count")
    )
    sectors = ["PUBLIC", "INDEPENDENT"]
    agg     = agg[agg["Sector"].isin(sectors)]

    fig = make_subplots(
        rows=1, cols=2,
        specs          = [[{"type": "pie"}, {"type": "pie"}]],
        subplot_titles = ["Public Schools", "Independent Schools"],
    )

    for idx, sector in enumerate(sectors, start=1):
        sub = agg[agg["Sector"] == sector]
        if sub.empty:
            continue
        fig.add_trace(
            go.Pie(
                labels         = sub["NoFeeSchool"],
                values         = sub["count"],
                hole           = 0.58,
                marker_colors  = [NO_FEE_COLORS.get(l, "#94a3b8") for l in sub["NoFeeSchool"]],
                textinfo       = "percent",
                textfont_size  = 12,
                hovertemplate  = (
                    "<b>%{label}</b><br>Schools: %{value:,}<br>Share: %{percent}<extra></extra>"
                ),
                showlegend = (idx == 1),
            ),
            row=1, col=idx,
        )

    fig.update_layout(
        **_LAYOUT,
        title  = dict(text="No-Fee vs Fee-Charging by Sector", font_size=14, x=0.5,
                      font_color=_TEXT),
        height = 430,
        legend = dict(
            orientation = "h",
            x=0.38, y=-0.08,
            bgcolor     = "rgba(255,255,255,0.05)",
            bordercolor = "rgba(255,255,255,0.1)",
            borderwidth = 1,
        ),
    )
    # Style subplot titles
    for ann in fig.layout.annotations:
        ann.font.color = _MUTED
        ann.font.size  = 13
    return fig


# ── 5. LER scatter: Learners vs Educators ────────────────────────────────────
def ler_scatter(df: pd.DataFrame) -> go.Figure:
    sdf = df.dropna(subset=["Learners2025", "Educators2025"]).copy()
    sdf = sdf[(sdf["Educators2025"] > 0) & (sdf["Learners2025"] > 0)]
    sdf["LER"] = (sdf["Learners2025"] / sdf["Educators2025"]).round(1)

    max_edu = float(sdf["Educators2025"].max())
    fig = go.Figure()

    # Threshold reference lines
    for ler_val, col, label in [
        (40, "#ef4444", "LER = 40 (Critical)"),
        (30, "#f97316", "LER = 30 (High)"),
    ]:
        fig.add_trace(go.Scatter(
            x          = [0, max_edu],
            y          = [0, ler_val * max_edu],
            mode       = "lines",
            line       = dict(color=col, dash="dash", width=1.5),
            name       = label,
            hoverinfo  = "skip",
        ))

    # School scatter by strain category
    for strain, color in LER_COLORS.items():
        sub = sdf[sdf["LER_strain"] == strain]
        if sub.empty:
            continue
        cd = sub[["school_name", "Province", "EIDistrict",
                   "Quintile", "LER", "Urban_Rural"]].values
        fig.add_trace(go.Scatter(
            x           = sub["Educators2025"],
            y           = sub["Learners2025"],
            mode        = "markers",
            marker      = dict(color=color, size=5, opacity=0.60,
                               line=dict(width=0)),
            name        = strain,
            customdata  = cd,
            hovertemplate = (
                "<b>%{customdata[0]}</b><br>"
                "Province: %{customdata[1]} · %{customdata[2]}<br>"
                "Quintile: %{customdata[3]} · %{customdata[5]}<br>"
                "Educators: %{x:,}  Learners: %{y:,}<br>"
                "LER: <b>%{customdata[4]}</b>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_LAYOUT,
        title       = dict(text="Learner-to-Educator Ratio", font_size=14, x=0.5,
                           font_color=_TEXT),
        xaxis_title = "Educators",
        yaxis_title = "Learners",
        height      = 430,
    )
    _dark_axes(fig)
    return fig


# ── 6. Horizontal province bar ────────────────────────────────────────────────
def province_bar(df: pd.DataFrame, metric: str = "Learners2025") -> go.Figure:
    agg = (
        df.groupby("Province", observed=True)
        .agg(
            Schools   = ("NatEmis",       "count"),
            Learners  = ("Learners2025",  "sum"),
            Educators = ("Educators2025", "sum"),
        )
        .reset_index()
    )
    agg["LER"]           = (agg["Learners"] / agg["Educators"]).round(1)
    agg["Province_Name"] = agg["Province"].map(PROVINCE_NAMES).fillna(agg["Province"])

    col_map = {"Learners2025": "Learners", "Educators2025": "Educators", "Schools": "Schools"}
    y_col   = col_map.get(metric, "Learners")
    agg     = agg.sort_values(y_col, ascending=True)

    max_val = agg[y_col].max()

    fig = go.Figure(go.Bar(
        x          = agg[y_col],
        y          = agg["Province_Name"],
        orientation = "h",
        marker      = dict(
            color      = agg[y_col],
            colorscale = [[0, "#1e1b4b"], [0.45, "#6366f1"], [1, "#c7d2fe"]],
            showscale  = False,
        ),
        customdata  = agg[["Schools", "Learners", "Educators", "LER"]].values,
        hovertemplate = (
            "<b>%{y}</b><br>"
            "Schools: %{customdata[0]:,}<br>"
            "Learners: %{customdata[1]:,.0f}<br>"
            "Educators: %{customdata[2]:,.0f}<br>"
            "LER: %{customdata[3]}"
            "<extra></extra>"
        ),
        text          = agg[y_col].apply(lambda v: f"{v:,.0f}"),
        textposition  = "outside",
        textfont      = dict(color=_MUTED, size=11),
        cliponaxis    = False,
    ))

    fig.update_layout(
        **_LAYOUT,
        title   = dict(text=f"{y_col} per Province", font_size=14, x=0.5,
                       font_color=_TEXT),
        height  = 420,
        xaxis   = dict(range=[0, max_val * 1.18]),
        margin  = dict(t=52, r=80, b=32, l=16),
    )
    _dark_axes(fig)
    return fig
