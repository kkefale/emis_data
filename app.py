"""
app.py — SA EMIS National Dashboard
Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from db import (
    load_filtered_data,
    get_provinces,
    get_districts,
    get_phases,
)
from charts import (
    compute_kpis,
    scatter_map,
    sunburst_province_quintile,
    donut_no_fee_by_sector,
    ler_scatter,
    province_bar,
)

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title = "SA EMIS Explorer",
    page_icon  = "🎓",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ─── Layout ─────────────────────────────────────────────────────────────── */
.block-container {
    padding-top: 0.75rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}

/* ─── Header ─────────────────────────────────────────────────────────────── */
.emis-header {
    text-align: center;
    padding: 1.2rem 0 0.6rem;
}
.emis-header h1 {
    font-size: 2.25rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #a5b4fc 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem;
}
.emis-header p {
    color: #64748b;
    font-size: 0.9rem;
    margin: 0;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ─── KPI grid ───────────────────────────────────────────────────────────── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0.85rem;
    margin: 1rem 0 1.4rem;
}
.kpi-card {
    background: linear-gradient(
        135deg,
        rgba(99, 102, 241, 0.13) 0%,
        rgba(139, 92, 246, 0.07) 100%
    );
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(99, 102, 241, 0.22);
    border-radius: 16px;
    padding: 1.15rem 0.75rem;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 36px rgba(99, 102, 241, 0.22);
}
.kpi-card.accent {
    background: linear-gradient(
        135deg,
        rgba(236, 72, 153, 0.16) 0%,
        rgba(244, 63, 94, 0.09) 100%
    );
    border-color: rgba(236, 72, 153, 0.28);
}
.kpi-card.accent:hover { box-shadow: 0 18px 36px rgba(236, 72, 153, 0.22); }
.kpi-card.green {
    background: linear-gradient(
        135deg,
        rgba(34, 197, 94, 0.16) 0%,
        rgba(20, 184, 166, 0.08) 100%
    );
    border-color: rgba(34, 197, 94, 0.28);
}
.kpi-card.green:hover { box-shadow: 0 18px 36px rgba(34, 197, 94, 0.22); }
.kpi-card.red {
    background: linear-gradient(
        135deg,
        rgba(239, 68, 68, 0.16) 0%,
        rgba(220, 38, 38, 0.08) 100%
    );
    border-color: rgba(239, 68, 68, 0.28);
}
.kpi-card.red:hover { box-shadow: 0 18px 36px rgba(239, 68, 68, 0.22); }
.kpi-icon  { font-size: 1.65rem; margin-bottom: 0.4rem; line-height: 1; }
.kpi-value {
    font-size: 1.75rem;
    font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -0.03em;
    line-height: 1;
    margin-bottom: 0.35rem;
}
.kpi-label {
    font-size: 0.72rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    font-weight: 600;
}

/* ─── Section title ──────────────────────────────────────────────────────── */
.sec-title {
    font-size: 1rem;
    font-weight: 700;
    color: #a5b4fc;
    margin: 1rem 0 0.4rem;
    padding-left: 0.1rem;
    letter-spacing: 0.02em;
}

/* ─── Chart cards (wraps plotly iframes) ────────────────────────────────── */
[data-testid="stPlotlyChart"] {
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    overflow: hidden;
    background: rgba(19, 19, 31, 0.55);
    backdrop-filter: blur(8px);
}

/* ─── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c0c1a 0%, #13131f 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
    color: #818cf8;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.25);
    padding-bottom: 0.6rem;
}
[data-testid="stSidebar"] label {
    color: #64748b !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.07);
    margin: 0.9rem 0;
}

/* ─── Divider ─────────────────────────────────────────────────────────────── */
.emis-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.3), transparent);
    margin: 1.2rem 0;
}

/* ─── Footer ─────────────────────────────────────────────────────────────── */
.emis-footer {
    text-align: center;
    color: #334155;
    font-size: 0.76rem;
    padding: 2rem 0 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    margin-top: 2rem;
    letter-spacing: 0.04em;
}

/* ─── Empty state ────────────────────────────────────────────────────────── */
.emis-empty {
    text-align: center;
    padding: 3rem;
    color: #475569;
    font-size: 0.9rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Filters")

    all_provinces = get_provinces()
    sel_provinces = st.multiselect(
        "Province",
        options     = all_provinces,
        placeholder = "All provinces",
        key         = "f_province",
    )

    all_districts = get_districts(tuple(sel_provinces) if sel_provinces else None)
    sel_districts = st.multiselect(
        "District",
        options     = all_districts,
        placeholder = "All districts",
        key         = "f_district",
    )

    sel_sectors = st.multiselect(
        "Sector",
        options     = ["PUBLIC", "INDEPENDENT"],
        placeholder = "All sectors",
        key         = "f_sector",
    )

    all_phases = get_phases()
    sel_phases = st.multiselect(
        "School Phase",
        options     = all_phases,
        placeholder = "All phases",
        key         = "f_phase",
    )

    sel_quintiles = st.multiselect(
        "Quintile",
        options     = ["Q1", "Q2", "Q3", "Q4", "Q5"],
        placeholder = "All quintiles",
        key         = "f_quintile",
    )

    st.markdown("---")
    st.markdown("**Map options**")
    color_by = st.radio(
        "Colour nodes by",
        options    = ["Quintile", "Phase_PED"],
        format_func = lambda x: "Quintile" if x == "Quintile" else "School Phase",
        horizontal = True,
        key        = "map_color",
    )

    st.markdown("---")
    st.markdown("**Province chart**")
    prov_metric = st.radio(
        "Metric",
        options    = ["Learners2025", "Educators2025", "Schools"],
        format_func = lambda x: {"Learners2025": "Learners", "Educators2025": "Educators",
                                  "Schools": "Schools"}[x],
        key        = "prov_metric",
    )

    st.markdown("---")
    st.caption("Data: SA EMIS 2025 · Schools with OPEN status only")


# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading data…"):
    df = load_filtered_data(
        provinces = tuple(sel_provinces) if sel_provinces else None,
        districts = tuple(sel_districts) if sel_districts else None,
        sectors   = tuple(sel_sectors)   if sel_sectors   else None,
        phases    = tuple(sel_phases)    if sel_phases     else None,
        quintiles = tuple(sel_quintiles) if sel_quintiles  else None,
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="emis-header">
      <h1>🎓 SA EMIS National Dashboard</h1>
      <p>South African Education Management Information System &nbsp;·&nbsp; 2025 Data Year</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPI cards ─────────────────────────────────────────────────────────────────
if df.empty:
    st.markdown('<div class="emis-empty">No schools match the selected filters.</div>',
                unsafe_allow_html=True)
    st.stop()

kpis = compute_kpis(df)

st.markdown(
    f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-icon">🏫</div>
        <div class="kpi-value">{kpis["total_schools"]:,}</div>
        <div class="kpi-label">Total Schools</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon">👨‍🎓</div>
        <div class="kpi-value">{kpis["total_learners"]:,}</div>
        <div class="kpi-label">Total Learners</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon">👩‍🏫</div>
        <div class="kpi-value">{kpis["total_educators"]:,}</div>
        <div class="kpi-label">Total Educators</div>
      </div>
      <div class="kpi-card accent">
        <div class="kpi-icon">📊</div>
        <div class="kpi-value">{kpis["national_ler"]}</div>
        <div class="kpi-label">Avg. LER (national)</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-icon">🆓</div>
        <div class="kpi-value">{kpis["no_fee_pct"]}%</div>
        <div class="kpi-label">No-Fee Schools</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-icon">⚠️</div>
        <div class="kpi-value">{kpis["critical_count"]:,}</div>
        <div class="kpi-label">Critical LER (&gt;40)</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Map ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">📍 School Locations</div>', unsafe_allow_html=True)
st.plotly_chart(
    scatter_map(df, color_by=color_by),
    use_container_width = True,
    config = {"displayModeBar": True, "scrollZoom": True,
              "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
)

st.markdown('<div class="emis-divider"></div>', unsafe_allow_html=True)

# ── Analysis row (3 columns) ──────────────────────────────────────────────────
st.markdown('<div class="sec-title">🔬 Socio-Economic & Resource Analysis</div>',
            unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.plotly_chart(
        sunburst_province_quintile(df),
        use_container_width = True,
        config = {"displayModeBar": False},
    )

with col2:
    st.plotly_chart(
        donut_no_fee_by_sector(df),
        use_container_width = True,
        config = {"displayModeBar": False},
    )

with col3:
    st.plotly_chart(
        ler_scatter(df),
        use_container_width = True,
        config = {"displayModeBar": False},
    )

st.markdown('<div class="emis-divider"></div>', unsafe_allow_html=True)

# ── Province comparison bar ───────────────────────────────────────────────────
st.markdown('<div class="sec-title">🗺️ Province Comparison</div>', unsafe_allow_html=True)
st.plotly_chart(
    province_bar(df, metric=prov_metric),
    use_container_width = True,
    config = {"displayModeBar": False},
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='emis-footer'>"
    "South African EMIS · 2025 Data Year · "
    "Dashboard built with Streamlit &amp; Plotly · "
    "Source: Department of Basic Education"
    "</div>",
    unsafe_allow_html=True,
)
