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
# Diverging socioeconomic palette: Q1 (worst) → Q5 (best)
QUINTILE_COLORS: dict[str, str] = {
    "Q1":    "#e05252",   # red   — most disadvantaged
    "Q2":    "#c47a3a",   # amber-brown
    "Q3":    "#8a8fc4",   # muted blue-grey — neutral midpoint
    "Q4":    "#4eba7f",   # muted green
    "Q5":    "#4d9fff",   # signal blue — most advantaged
    "Other": "#2d2d3a",   # near-invisible
}

PROVINCE_PALETTE = [
    "#4d9fff", "#7c6ff5", "#e05252", "#4eba7f",
    "#d4a843", "#5bc4c4", "#b06ec4", "#d47a4a", "#8a8fa8",
]

PROVINCE_NAMES: dict[str, str] = {
    "EC": "Eastern Cape",  "FS": "Free State",   "GT": "Gauteng",
    "KZN": "KwaZulu-Natal","LP": "Limpopo",       "MP": "Mpumalanga",
    "NC": "Northern Cape", "NW": "North West",    "WC": "Western Cape",
}

LER_COLORS: dict[str, str] = {
    "Normal (≤30)":   "#4eba7f",   # green
    "High (30–40)":   "#d4a843",   # amber
    "Critical (>40)": "#e05252",   # red
}

NO_FEE_COLORS: dict[str, str] = {
    "No Fee":       "#4d9fff",
    "Fee Charging": "#e05252",
    "Unknown":      "#2d2d3a",
}

# ─ Plotly dark theme ─────────────────────────────────────────────────────────
_BG    = "rgba(0,0,0,0)"           # fully transparent — surface from CSS
_PAPER = "rgba(17,17,22,0.0)"      # transparent paper
_GRID  = "rgba(255,255,255,0.05)"  # extremely subtle grid
_TEXT  = "#f0f0f0"
_MUTED = "#3d4352"
_FONT  = "IBM Plex Mono, monospace"

def _make_layout(dark: bool = True) -> dict:
    """Return a Plotly layout dict tuned for dark or light mode."""
    if dark:
        text     = "#f0f0f0"
        leg_bg   = "rgba(17,17,22,0.9)"
        leg_bd   = "rgba(255,255,255,0.07)"
        paper_bg = "rgba(0,0,0,0)"
        plot_bg  = "rgba(0,0,0,0)"
        hov_bg   = "rgba(12,12,15,0.97)"
        hov_bd   = "rgba(255,255,255,0.12)"
        hov_txt  = "#f0f0f0"
    else:
        text     = "#111827"
        leg_bg   = "rgba(255,255,255,0.97)"
        leg_bd   = "rgba(0,0,0,0.10)"
        paper_bg = "#ffffff"
        plot_bg  = "#f8fafc"
        hov_bg   = "#ffffff"
        hov_bd   = "rgba(0,0,0,0.12)"
        hov_txt  = "#111827"
    return dict(
        paper_bgcolor = paper_bg,
        plot_bgcolor  = plot_bg,
        font          = dict(family=_FONT, color=text, size=11),
        margin        = dict(t=44, r=16, b=28, l=16),
        legend        = dict(
            bgcolor     = leg_bg,
            bordercolor = leg_bd,
            borderwidth = 1,
            font_size   = 11,
            font_color  = text,
        ),
        hoverlabel = dict(
            bgcolor     = hov_bg,
            bordercolor = hov_bd,
            font        = dict(family=_FONT, color=hov_txt, size=11),
        ),
    )

def _style_axes(fig: go.Figure, dark: bool = True) -> go.Figure:
    if dark:
        grid  = "rgba(255,255,255,0.05)"
        line  = "rgba(255,255,255,0.07)"
        muted = "#3d4352"
    else:
        grid  = "rgba(0,0,0,0.07)"
        line  = "rgba(0,0,0,0.15)"
        muted = "#374151"
    axis_style = dict(
        gridcolor     = grid,
        zerolinecolor = "rgba(0,0,0,0)",
        linecolor     = line,
        tickfont      = dict(color=muted, size=10),
        title_font    = dict(color=muted),
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)
    return fig

# Keep backward-compat alias
def _dark_axes(fig: go.Figure) -> go.Figure:
    return _style_axes(fig, dark=True)


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
def scatter_map(df: pd.DataFrame, color_by: str = "Quintile", dark: bool = True) -> go.Figure:
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

    map_style = "carto-darkmatter" if dark else "carto-positron"
    fig.update_layout(
        **_make_layout(dark),
        mapbox=dict(
            style  = map_style,
            center = dict(lat=-29.0, lon=25.0),
            zoom   = 4.8,
        ),
        uirevision = "map",
        height     = 480,
    )
    return fig


# ── 3. Sunburst: Province → Quintile ─────────────────────────────────────────
def sunburst_province_quintile(df: pd.DataFrame, dark: bool = True) -> go.Figure:
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
        textfont_color         = "#111827" if not dark else "#f0f0f0",
        insidetextorientation  = "radial",
        leaf_opacity           = 0.88,
    )
    title_color = "#f0f0f0" if dark else "#111827"
    fig.update_layout(
        **_make_layout(dark),
        title  = dict(text="Schools by Province & Quintile", font_size=14, x=0.5,
                      font_color=title_color),
        height = 460,
    )
    return fig


# ── 4. Dual donut: No-Fee vs Fee by Sector ───────────────────────────────────
def donut_no_fee_by_sector(df: pd.DataFrame, dark: bool = True) -> go.Figure:
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

    title_color = "#f0f0f0" if dark else "#111827"
    ann_color   = "#3d4352" if dark else "#374151"
    fig.update_layout(
        **_make_layout(dark),
        title  = dict(text="No-Fee vs Fee-Charging by Sector", font_size=14, x=0.5,
                      font_color=title_color),
        height = 460,
    )
    # Style subplot titles
    for ann in fig.layout.annotations:
        ann.font.color = ann_color
        ann.font.size  = 13
    return fig


# ── 5. LER scatter: Learners vs Educators ────────────────────────────────────
def ler_scatter(df: pd.DataFrame, dark: bool = True) -> go.Figure:
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

    title_color = "#f0f0f0" if dark else "#111827"
    fig.update_layout(
        **_make_layout(dark),
        title       = dict(text="Learner-to-Educator Ratio", font_size=14, x=0.5,
                           font_color=title_color),
        xaxis_title = "Educators",
        yaxis_title = "Learners",
        height      = 400,
    )
    _style_axes(fig, dark)
    return fig


# ── 6. Horizontal province bar ────────────────────────────────────────────────
def province_bar(df: pd.DataFrame, metric: str = "Learners2025", dark: bool = True) -> go.Figure:
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
            colorscale = (
                [[0, "#1e1b4b"], [0.45, "#6366f1"], [1, "#c7d2fe"]] if dark
                else [[0, "#dbeafe"], [0.5, "#3b82f6"], [1, "#1d4ed8"]]
            ),
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
        textfont      = dict(color="#3d4352" if dark else "#374151", size=11),
        cliponaxis    = False,
    ))

    title_color = "#f0f0f0" if dark else "#111827"
    fig.update_layout(
        **_make_layout(dark),
        title   = dict(text=f"{y_col} per Province", font_size=14, x=0.5,
                       font_color=title_color),
        xaxis   = dict(range=[0, max_val * 1.18]),
    )
    _style_axes(fig, dark)
    return fig
