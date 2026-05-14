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
    quintile_ler_bar,
)

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title = "SA EMIS Explorer",
    page_icon  = "🎓",
    layout     = "wide",
    initial_sidebar_state = "auto",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0c0c0f;
    --surface:   #111116;
    --surface2:  #17171e;
    --signal:    #4d9fff;
    --signal-d:  rgba(77, 159, 255, 0.12);
    --border:    rgba(255, 255, 255, 0.07);
    --text:      #f0f0f0;
    --text-2:    #8a8fa8;
    --text-3:    #6b7280;
    --red:       #e05252;
    --amber:     #d4a843;
    --green:     #4eba7f;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
}

/* ─── Base ───────────────────────────────────────────────────────────────── */
.stApp {
    background-color: var(--bg);
}

/* ─── Layout ─────────────────────────────────────────────────────────────── */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}

/* ─── Header ─────────────────────────────────────────────────────────────── */
.emis-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 2rem 0 1.75rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.emis-header h1 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--text);
    margin: 0;
}
.emis-header h1 span {
    color: var(--signal);
}
.emis-header p {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-3);
    margin: 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ─── KPI grid ───────────────────────────────────────────────────────────── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 1px;
    background: var(--border);
    margin-bottom: 2.5rem;
    border: 1px solid var(--border);
}
.kpi-card {
    background: var(--surface);
    border-left: 3px solid var(--signal);
    padding: 1.4rem 1.2rem 1.2rem;
    transition: background 0.2s ease;
}
.kpi-card:hover { background: var(--surface2); }
.kpi-card.accent { border-left-color: var(--amber); }
.kpi-card.green  { border-left-color: var(--green); }
.kpi-card.red    { border-left-color: var(--red); }

.kpi-value {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 0.5rem;
    display: block;
}
.kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: var(--text-2);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 400;
}

/* ─── Section title ──────────────────────────────────────────────────────── */
.sec-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--text-2);
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin: 2.5rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.sec-title::before {
    content: '';
    display: inline-block;
    width: 24px;
    height: 1px;
    background: var(--signal);
}
.sec-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ─── Chart wrappers ─────────────────────────────────────────────────────── */
[data-testid="stPlotlyChart"] {
    border: 1px solid var(--border);
    background: var(--surface);
}

/* ─── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 2rem;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--text-2);
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
    padding-bottom: 0;
    border-bottom: none;
}
[data-testid="stSidebar"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--text-3) !important;
    font-size: 0.68rem !important;
    font-weight: 400 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
[data-testid="stSidebar"] hr {
    border-color: var(--border);
    margin: 1.5rem 0;
}

/* ─── Footer ─────────────────────────────────────────────────────────────── */
.emis-footer {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-3);
    padding: 2rem 0 2rem;
    border-top: 1px solid var(--border);
    margin-top: 4rem;
    letter-spacing: 0.06em;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* ─── Empty state ────────────────────────────────────────────────────────── */
.emis-empty {
    font-family: 'IBM Plex Mono', monospace;
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-3);
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border: 1px solid var(--border);
}

/* ─── Story block ────────────────────────────────────────────────────────── */
.story-block {
    background: var(--surface);
    border-left: 4px solid var(--signal);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    font-family: 'IBM Plex Sans', sans-serif;
    color: var(--text);
    font-size: 0.95rem;
    line-height: 1.5;
    border-radius: 0 4px 4px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.story-block strong {
    color: var(--signal);
    font-weight: 600;
}

/* ─── Filter tags (active-filter summary in header) ─────────────────────── */
.filter-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: 0.5rem;
}
.filter-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    color: var(--signal);
    background: var(--signal-d);
    border: 1px solid rgba(77, 159, 255, 0.25);
    padding: 0.15rem 0.55rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-radius: 2px;
}

/* ─── KPI delta ──────────────────────────────────────────────────────────── */
.kpi-delta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.04em;
    margin-top: 0.35rem;
    display: block;
}
.kpi-delta.worse   { color: var(--red); }
.kpi-delta.better  { color: var(--green); }
.kpi-delta.neutral { color: var(--text-2); }

/* ─── Mobile ─────────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
    /* Tighter outer padding */
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-top: 0.75rem !important;
    }

    /* Header: stack label under title */
    .emis-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.35rem;
        padding: 1.1rem 0 1.1rem;
        margin-bottom: 1.25rem;
    }
    .emis-header h1 { font-size: 1.1rem; }

    /* KPI grid: 2 columns × 3 rows */
    .kpi-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .kpi-card {
        padding: 1rem 0.85rem 0.85rem;
    }
    .kpi-value {
        font-size: 1.45rem;
    }

    /* Section title: reduce letter-spacing so it doesn't overflow */
    .sec-title {
        font-size: 0.65rem;
        letter-spacing: 0.12em;
        margin: 1.75rem 0 0.75rem;
    }

    /* Stack all Streamlit 2-col rows into a single column */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0 !important;
    }
    [data-testid="stColumn"],
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }

    /* Reduce chart border weight */
    [data-testid="stPlotlyChart"] {
        border-width: 1px;
    }

    /* Footer: stack vertically and centre */
    .emis-footer {
        flex-direction: column;
        gap: 0.4rem;
        text-align: center;
        margin-top: 2.5rem;
        padding: 1.5rem 0;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Filters")

    # ── Display toggles visible at the very top ───────────────────────────────
    _tc1, _tc2 = st.columns(2)
    with _tc1:
        story_mode = st.toggle("📖 Story", value=False, key="story_mode_toggle")
    with _tc2:
        light_mode = st.toggle("☀️ Light", value=False, key="theme_toggle")

    # ── Reset all filters ─────────────────────────────────────────────────────
    if st.button("↺  Reset all filters", use_container_width=True):
        for _k in ["f_province", "f_district", "f_sector",
                   "f_phase", "f_quintile", "f_urban_rural"]:
            st.session_state[_k] = []
        st.rerun()

    st.markdown("---")

    all_provinces = get_provinces()
    sel_provinces = st.multiselect(
        "Province",
        options     = all_provinces,
        placeholder = "All provinces",
        key         = "f_province",
    )

    all_districts = get_districts(tuple(sel_provinces) if sel_provinces else None)
    sel_districts = st.multiselect(
        f"District  ({len(all_districts)} available)",
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

    sel_urban_rural = st.multiselect(
        "Urban / Rural",
        options     = ["Urban", "Rural"],
        placeholder = "All locations",
        key         = "f_urban_rural",
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
    st.caption("Data: [SA EMIS 2025](https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx) · Schools with OPEN status only")


# ── Active-filter summary tokens (used in header and export) ─────────────────
_active: list[str] = []
if sel_provinces:
    _active += sel_provinces
if sel_districts:
    _active.append(f"{len(sel_districts)} district{'s' if len(sel_districts) > 1 else ''}")
if sel_sectors:
    _active += [s.title() for s in sel_sectors]
if sel_phases:
    _active += sel_phases
if sel_quintiles:
    _active += sel_quintiles
if sel_urban_rural:
    _active += sel_urban_rural


# ── Theme override (injected after sidebar so light_mode is available) ────────
if light_mode:
    st.markdown(
        """
<style>
:root {
    --bg:        #f4f5f7;
    --surface:   #ffffff;
    --surface2:  #eaecef;
    --signal:    #1d6ed8;
    --signal-d:  rgba(29, 110, 216, 0.10);
    --border:    rgba(0, 0, 0, 0.09);
    --text:      #111827;
    --text-2:    #4b5563;
    --text-3:    #9ca3af;
    --red:       #dc2626;
    --amber:     #b45309;
    --green:     #16a34a;
}

/* ── App shell ── */
.stApp { background-color: #f4f5f7 !important; }
[data-testid="stMain"],
[data-testid="stAppViewContainer"] { background-color: #f4f5f7 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
    background: #f4f5f7 !important;
    border-right: 1px solid rgba(0,0,0,0.09) !important;
}

/* ── All text in sidebar & main ── */
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #111827 !important;
}

/* ── Widget labels ── */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
[data-testid="stWidgetLabel"] p { color: #4b5563 !important; }

/* ── Multiselect & select boxes ── */
[data-baseweb="select"] > div { background-color: #ffffff !important; border-color: rgba(0,0,0,0.15) !important; }
[data-baseweb="select"] span,
[data-baseweb="select"] input,
[data-baseweb="select"] [data-testid="stMultiSelectOption"],
[data-baseweb="select"] div { color: #111827 !important; }

/* Selected tags */
[data-baseweb="tag"] { background-color: #dbeafe !important; }
[data-baseweb="tag"] span { color: #1d4ed8 !important; }

/* Placeholder */
[data-baseweb="select"] input::placeholder { color: #9ca3af !important; }

/* Dropdown menu */
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"] { background-color: #ffffff !important; border-color: rgba(0,0,0,0.12) !important; }
[data-baseweb="menu"] li,
[data-baseweb="menu"] li span,
[data-baseweb="menu"] [role="option"] { color: #111827 !important; background-color: #ffffff !important; }
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [role="option"]:hover { background-color: #eff6ff !important; }

/* ── Radio buttons ── */
[data-testid="stRadio"] label,
[data-testid="stRadio"] label span,
[data-testid="stRadio"] [data-testid="stWidgetLabel"] p { color: #111827 !important; }

/* ── Toggle ── */
[data-testid="stToggle"] label,
[data-testid="stToggle"] label span,
[data-testid="stToggle"] p { color: #111827 !important; }

/* ── Horizontal rules ── */
[data-testid="stSidebar"] hr { border-color: rgba(0,0,0,0.1) !important; }

/* ── Main content text (outside custom HTML) ── */
[data-testid="stMain"] p,
[data-testid="stMain"] span,
[data-testid="stMain"] label,
[data-testid="stMain"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] span { color: #111827 !important; }

/* ── KPI card values & labels ── */
.kpi-value { color: #111827 !important; }
.kpi-label { color: #4b5563 !important; }

/* ── Section titles ── */
.sec-title { color: #4b5563 !important; }
.sec-title::before { background: #1d6ed8 !important; }
.sec-title::after  { background: rgba(0,0,0,0.10) !important; }

/* ── Header ── */
.emis-header { border-bottom-color: rgba(0,0,0,0.09) !important; }
.emis-header h1 { color: #111827 !important; }
.emis-header h1 span { color: #1d6ed8 !important; }
.emis-header p  { color: #9ca3af !important; }

/* ── KPI card borders ── */
.kpi-grid { background: rgba(0,0,0,0.06) !important; border-color: rgba(0,0,0,0.06) !important; }
.kpi-card { background: #ffffff !important; }
.kpi-card:hover { background: #f0f5ff !important; }
.kpi-card { border-left-color: #1d6ed8 !important; }
.kpi-card.accent { border-left-color: #b45309 !important; }
.kpi-card.green  { border-left-color: #16a34a !important; }
.kpi-card.red    { border-left-color: #dc2626 !important; }

/* ── Footer ── */
.emis-footer { color: #9ca3af !important; border-top-color: rgba(0,0,0,0.09) !important; }

/* ── Empty state ── */
.emis-empty { color: #6b7280 !important; border-color: rgba(0,0,0,0.09) !important; }

/* ── Story Block ── */
.story-block { background: #ffffff !important; border-left-color: #1d6ed8 !important; color: #111827 !important; }
.story-block strong { color: #1d6ed8 !important; }

/* ── Chart wrapper ── */
[data-testid="stPlotlyChart"] {
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.09) !important;
}

/* ── Spinner text ── */
[data-testid="stSpinner"] p { color: #4b5563 !important; }

/* ── Filter tags ── */
.filter-tag { color: #1d6ed8 !important; background: rgba(29,110,216,0.10) !important; border-color: rgba(29,110,216,0.25) !important; }

/* ── KPI delta ── */
.kpi-delta.worse   { color: #dc2626 !important; }
.kpi-delta.better  { color: #16a34a !important; }
.kpi-delta.neutral { color: #4b5563 !important; }

/* ── Sidebar buttons ── */
[data-testid="stSidebar"] button {
    background-color: #ffffff !important;
    color: #111827 !important;
    border: 1px solid rgba(0,0,0,0.15) !important;
}
[data-testid="stSidebar"] button:hover {
    background-color: #eff6ff !important;
    border-color: rgba(29,110,216,0.4) !important;
}
[data-testid="stDownloadButton"] button {
    background-color: #dbeafe !important;
    color: #1d4ed8 !important;
    border: 1px solid rgba(29,110,216,0.25) !important;
}
[data-testid="stDownloadButton"] button:hover {
    background-color: #bfdbfe !important;
}
</style>
""",
        unsafe_allow_html=True,
    )

# ── Chart config constants ────────────────────────────────────────────────────
_MAP_CFG = {
    "displayModeBar":          "hover",
    "scrollZoom":              True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
}
_CHART_CFG = {
    "displayModeBar":          "hover",
    "scrollZoom":              False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
}

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading data…"):
    df = load_filtered_data(
        provinces   = tuple(sel_provinces)   if sel_provinces   else None,
        districts   = tuple(sel_districts)   if sel_districts   else None,
        sectors     = tuple(sel_sectors)     if sel_sectors     else None,
        phases      = tuple(sel_phases)      if sel_phases      else None,
        quintiles   = tuple(sel_quintiles)   if sel_quintiles   else None,
        urban_rural = tuple(sel_urban_rural) if sel_urban_rural else None,
    )

# ── National baseline KPIs (for deltas — cached, no extra DB hit) ─────────────
_any_filter = bool(
    sel_provinces or sel_districts or sel_sectors
    or sel_phases or sel_quintiles or sel_urban_rural
)
if _any_filter:
    _nat_df   = load_filtered_data()   # no-arg call is independently cached
    nat_kpis  = compute_kpis(_nat_df)
else:
    nat_kpis  = None

# ── Sidebar: CSV export (placed here because it needs df) ─────────────────────
with st.sidebar:
    st.markdown("---")
    st.download_button(
        label               = "⬇  Export filtered data (CSV)",
        data                = df.to_csv(index=False).encode("utf-8"),
        file_name           = "emis_filtered.csv",
        mime                = "text/csv",
        use_container_width = True,
    )

# ── Header ────────────────────────────────────────────────────────────────────
_filter_tags_html = ""
if _active:
    _tags = "".join(f'<span class="filter-tag">{t}</span>' for t in _active)
    _filter_tags_html = f'<div class="filter-tags">{_tags}</div>'

st.markdown(
    f"""
    <div class="emis-header">
      <div>
        <h1>SA EMIS &mdash; <span>National Schools Intelligence</span></h1>
        {_filter_tags_html}
      </div>
      <p>Dept. of Basic Education &middot; 2025 Data Year</p>
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

# ── KPI delta strings (shown when filters are active) ────────────────────────
if nat_kpis:
    _ler_diff = round(kpis["national_ler"] - nat_kpis["national_ler"], 1)
    if abs(_ler_diff) < 0.1:
        _ler_delta = '<span class="kpi-delta neutral">≈ national avg</span>'
    elif _ler_diff > 0:
        _ler_delta = f'<span class="kpi-delta worse">▲ +{_ler_diff} vs national</span>'
    else:
        _ler_delta = f'<span class="kpi-delta better">▼ {_ler_diff} vs national</span>'

    _nf_diff = round(kpis["no_fee_pct"] - nat_kpis["no_fee_pct"], 1)
    if abs(_nf_diff) < 0.1:
        _nf_delta = '<span class="kpi-delta neutral">≈ national avg</span>'
    elif _nf_diff > 0:
        _nf_delta = f'<span class="kpi-delta better">▲ +{_nf_diff}% vs national</span>'
    else:
        _nf_delta = f'<span class="kpi-delta worse">▼ {_nf_diff}% vs national</span>'
else:
    _ler_delta = ""
    _nf_delta  = ""

st.markdown(
    f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-value">{kpis["total_schools"]:,}</span>
        <span class="kpi-label">Schools</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-value">{kpis["total_learners"]:,}</span>
        <span class="kpi-label">Learners</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-value">{kpis["total_educators"]:,}</span>
        <span class="kpi-label">Educators</span>
      </div>
      <div class="kpi-card accent">
        <span class="kpi-value">{kpis["national_ler"]}</span>
        <span class="kpi-label">Learner / Educator Ratio</span>
        {_ler_delta}
      </div>
      <div class="kpi-card green">
        <span class="kpi-value">{kpis["no_fee_pct"]}%</span>
        <span class="kpi-label">No-Fee Schools</span>
        {_nf_delta}
      </div>
      <div class="kpi-card red">
        <span class="kpi-value">{kpis["critical_count"]:,}</span>
        <span class="kpi-label">Critical LER &gt; 40</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Critical schools drilldown ────────────────────────────────────────────────
_critical = df[df["LER_strain"] == "Critical (>40)"].copy()
if not _critical.empty:
    with st.expander(
        f"🔴 {len(_critical):,} Critical Schools (LER > 40) — click to view",
        expanded=False,
    ):
        _disp = (
            _critical[["school_name", "Province", "EIDistrict", "Quintile",
                        "Urban_Rural", "Learners2025", "Educators2025", "LER"]]
            .sort_values("LER", ascending=False)
            .rename(columns={
                "school_name":   "School",
                "EIDistrict":    "District",
                "Urban_Rural":   "Urban/Rural",
                "Learners2025":  "Learners",
                "Educators2025": "Educators",
            })
            .reset_index(drop=True)
        )
        st.dataframe(_disp, use_container_width=True, height=400)

# ── Map ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">01 &mdash; School Locations</div>', unsafe_allow_html=True)

if story_mode:
    st.markdown(
        '<div class="story-block">'
        '<strong>The Geographic Divide:</strong> Spatial inequality remains a defining feature of South Africa’s education landscape. '
        'Notice the dense clustering of well-resourced schools (Quintile 4 & 5) in urban hubs like Gauteng and the Western Cape, '
        'contrasting starkly with the vast expanse of poorer, No-Fee schools in rural areas like the Eastern Cape and KwaZulu-Natal. '
        '<em>Try filtering by "Rural" in the sidebar to visualize this intersection of poverty and geography.</em>'
        '</div>',
        unsafe_allow_html=True
    )

st.plotly_chart(
    scatter_map(df, color_by=color_by, dark=not light_mode),
    width="stretch",
    config=_MAP_CFG,
)

# ── Analysis row (3 columns) ──────────────────────────────────────────────────
st.markdown('<div class="sec-title">02 &mdash; Socio-Economic &amp; Resource Analysis</div>',
            unsafe_allow_html=True)

if story_mode:
    st.markdown(
        '<div class="story-block">'
        '<strong>The Legacy of Inequality:</strong> South Africa categorises public schools into poverty "Quintiles" to determine funding allocations. '
        'Yet, structural disparities persist. In the charts below, observe how <strong>Quintile 1-3 schools (the poorest) overwhelmingly bear the brunt of overcrowding</strong>. '
        'They systematically display higher Learner-to-Educator Ratios than the wealthiest schools in Quintile 5. '
        'This deep resource gap remains a primary driver of disparate educational outcomes.'
        '</div>',
        unsafe_allow_html=True
    )

col1, col2 = st.columns(2, gap="large")

with col1:
    st.plotly_chart(
        sunburst_province_quintile(df, dark=not light_mode),
        width="stretch",
        config=_CHART_CFG,
    )
    if df["Quintile"].isin(["Q1", "Q2", "Q3", "Q4", "Q5"]).any():
        st.plotly_chart(
            quintile_ler_bar(df, dark=not light_mode),
            width="stretch",
            config=_CHART_CFG,
        )
    else:
        st.caption("No quintile data for the current selection.")

with col2:
    if df["Sector"].isin(["PUBLIC", "INDEPENDENT"]).any():
        st.plotly_chart(
            donut_no_fee_by_sector(df, dark=not light_mode),
            width="stretch",
            config=_CHART_CFG,
        )
    else:
        st.caption("No sector data for the current selection.")

    _has_ler = (
        df["Learners2025"].notna()
        & df["Educators2025"].notna()
        & (df["Educators2025"] > 0)
    ).any()
    if _has_ler:
        st.plotly_chart(
            ler_scatter(df, dark=not light_mode),
            width="stretch",
            config=_CHART_CFG,
        )
    else:
        st.caption("Insufficient educator/learner data for LER scatter.")

# ── Province comparison bar ───────────────────────────────────────────────────
st.markdown('<div class="sec-title">03 &mdash; Province Comparison</div>', unsafe_allow_html=True)

if story_mode:
    st.markdown(
        '<div class="story-block">'
        '<strong>Provincial Strain:</strong> Demographics and resources are deeply uneven across provincial lines. '
        'Populous or heavily rural provinces frequently manage massive learner populations with constrained educator numbers, '
        'pushing their limits far beyond wealthier, urbanized jurisdictions.'
        '</div>',
        unsafe_allow_html=True
    )

st.plotly_chart(
    province_bar(df, metric=prov_metric, dark=not light_mode),
    width="stretch",
    config=_CHART_CFG,
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='emis-footer'>"
    "<span>SA EMIS &mdash; 2025 Data Year</span>"
    "<span>Source: <a href='https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx' "
    "target='_blank' rel='noopener noreferrer' "
    "style='color:inherit;text-decoration:underline;text-underline-offset:3px;'>Dept. of Basic Education &mdash; EMIS Downloads</a></span>"
    "</div>",
    unsafe_allow_html=True,
)
