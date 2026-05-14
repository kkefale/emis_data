# SA EMIS — National Schools Intelligence Dashboard

**v0.1.0** · South African Department of Basic Education · 2025 Data Year

An interactive data exploration dashboard for the South African National Education Management Information System (EMIS). Covers **25,527 schools** across all nine provinces with cross-filtering, a geospatial map, story mode, and full dark/light mode support.

---

## Features

### KPI Banner
Six live metric cards update instantly with every filter change:

| Metric | Description |
|--------|-------------|
| Total Schools | Count of open schools matching active filters |
| Total Learners | Sum of `Learners2025` |
| Total Educators | Sum of `Educators2025` |
| Learner / Educator Ratio | National LER across the filtered selection |
| % No-Fee Schools | Share of schools where fees are waived |
| Critical LER | Schools where LER > 40 (resource-strained) |

### 01 — School Locations
- All schools plotted on a Carto basemap (dark/light tile set matched to theme)
- Marker size scaled to learner enrolment (√ normalised, range 5–22 px)
- Marker colour switchable between Quintile (Q1–Q5) and School Phase
- Hover tooltips: school name, district, province, learners, educators, derived LER

### 02 — Socio-Economic & Resource Analysis

| Chart | What it shows |
|-------|---------------|
| Sunburst (Province → Quintile) | School count hierarchy, sized by school count, coloured by quintile |
| LER by Quintile Bar | Resource gap — stacked LER rates from Q1 (poorest) through Q5 |
| Dual Donut (No-Fee by Sector) | No-Fee vs Fee-Charging split for Public vs Independent sectors |
| LER Scatter | Learners vs Educators with LER = 30 and LER = 40 reference lines, colour-coded by strain level |

### 03 — Province Comparison
Horizontal bar chart switchable between Learners / Educators / Schools per province.

### Cross-Filtering Sidebar
All charts respond simultaneously to:
- Province (cascades to District options)
- District
- Sector (Public / Independent)
- School Phase (Primary, Secondary, Combined, …)
- Quintile (Q1–Q5)
- Urban / Rural

### Story Mode
Toggle **📖 Enable Story Mode** in the sidebar to inject curated narrative blocks above each visualisation, guiding users through spatial inequality, resource strain, and poverty in the SA education system.

### Dark / Light Mode
Sidebar toggle switches the full interface — shell, charts, and map — between a precision dark theme and a high-contrast light theme.

---

## Project Structure

```
sa-emis-dashboard/
├── app.py              # Streamlit entrypoint — layout, KPIs, sidebar, CSS theme engine
├── db.py               # Database access layer — SQL normalisation, @st.cache_data
├── charts.py           # Plotly figure builders (one function per chart)
├── setup.py            # One-time CSV → SQLite conversion script
├── requirements.txt    # Python dependencies
├── emis.csv            # Source dataset (SA DBE EMIS 2025, semicolon-delimited)
├── .streamlit/
│   └── config.toml     # Base Streamlit theme & server settings
└── .gitignore
```

> `emis.db` is generated locally by `setup.py` and excluded from version control via `.gitignore`.

---

## Quick Start

**1 — Clone the repository**

```bash
git clone https://github.com/kkefale/emis_data.git
cd emis_data
```

**2 — Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows PowerShell
```

**3 — Install dependencies**

```bash
pip install -r requirements.txt
```

**4 — Build the SQLite database**

```bash
python setup.py
```

Reads `emis.csv` and writes `emis.db` (~13 MB) with WAL mode and four indexes. Run once; delete `emis.db` and re-run to force a refresh.

**5 — Launch the dashboard**

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**.

---

## Requirements

| Package | Min version | Purpose |
|---------|-------------|---------|
| `streamlit` | 1.35 | Web UI framework |
| `pandas` | 2.2 | DataFrame manipulation |
| `plotly` | 5.20 | Interactive charts & map |

Python **3.10+** required. Developed and tested on macOS Apple Silicon (Python 3.14).

---

## Dataset

**Source:** South African Department of Basic Education (DBE) — EMIS 2025  
**URL:** [https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx](https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx)  
**Rows:** 25,527 schools  
**Key fields:** `NatEmis`, `Province`, `EIDistrict`, `Phase_PED`, `Sector`, `Quintile`, `NoFeeSchool`, `Urban_Rural`, `Learners2025`, `Educators2025`, `GIS_Long`, `GIS_Lat`

Public government dataset — no personally identifiable information.

### Data normalisation applied in `db.py`

| Issue | Fix |
|-------|-----|
| European decimal commas in GIS coordinates (`-31,15778`) | Replaced with `.` before `CAST` |
| Mixed-case Sector values (`PUBLIC`, `Independent`) | `UPPER(TRIM(...))` |
| Varied NoFeeSchool literals (`No Fee`, `YES`, `N`) | Mapped to `No Fee` / `Fee Charging` |
| Quintile sentinels (`99`, `N/A`) | Mapped to `Other` |
| Mixed Status values (`OPEN`, `Open`, `PENDING OPEN`) | Filtered to open schools only |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         app.py                              │
│  Layout · KPI cards · Sidebar filters · CSS theme engine    │
├──────────────────────┬──────────────────────────────────────┤
│       db.py          │            charts.py                 │
│  SQLite queries      │  Plotly figure builders              │
│  @st.cache_data      │  scatter_map()                       │
│  load_filtered_data  │  sunburst_province_quintile()        │
│  get_provinces()     │  donut_no_fee_by_sector()            │
│  get_districts()     │  ler_scatter()                       │
│  get_phases()        │  province_bar()                      │
│                      │  quintile_ler_bar()                  │
└──────────────────────┴──────────────────────────────────────┘
                         ↕
                      emis.db
              (SQLite · ~13 MB · WAL mode · 4 indexes)
```

All data loading is SQL-aggregated before reaching pandas/Plotly. `@st.cache_data(ttl=600)` serves repeated filter interactions from memory.

---

## Design System — Brutalist Data Terminal

Inspired by Bloomberg Terminal and Linear.app: monospace type, tight grids, no decoration.

| Token | Dark | Light |
|-------|------|-------|
| Background | `#0c0c0f` | `#f4f5f7` |
| Surface | `#111116` | `#ffffff` |
| Primary accent | `#4d9fff` | `#1d6ed8` |
| Text | `#f0f0f0` | `#111827` |
| Muted text | `#8a8fa8` | `#6b7280` |
| Red / Critical | `#e05252` | `#dc2626` |
| Green / Healthy | `#4eba7f` | `#16a34a` |
| Typeface | IBM Plex Mono + IBM Plex Sans | |

CSS variables are defined in a single `:root` block and overridden wholesale by the light-mode injection block. All Plotly charts receive explicit `paper_bgcolor` / `plot_bgcolor` / `hoverlabel` values per theme. `.streamlit/config.toml` sets the base Streamlit theme to match the dark defaults.

---

## Changelog

### v0.1.0 — 2026-05-14 · Initial release

- CSV → SQLite pipeline (`setup.py`): WAL mode, 4 indexes, verbose progress output
- Data access layer (`db.py`): parameterised SQL with full field normalisation (sector case, GIS decimal commas, NoFeeSchool variants, quintile sentinels, status filtering); `@st.cache_data` on all query functions
- Plotly chart builders (`charts.py`): `scatter_map`, `sunburst_province_quintile`, `donut_no_fee_by_sector`, `ler_scatter`, `province_bar`, `quintile_ler_bar`; shared `_make_layout()` / `_style_axes()` helpers; explicit dark/light palette for every chart
- Streamlit app (`app.py`): six KPI cards, cross-filtering sidebar (Province → District cascade, Sector, Phase, Quintile, Urban/Rural), map colour toggle, province metric toggle
- Brutalist Data Terminal design system: IBM Plex Mono + IBM Plex Sans, CSS custom-property token system, full dark and light mode
- Story Mode: toggle injects curated narrative blocks above each chart section
- Mobile responsive layout: `@media (max-width: 768px)` — 2-column KPI grid, stacked chart columns, tightened padding
- Source acknowledged: [Dept. of Basic Education — EMIS Downloads](https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx)

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'feat: add my feature'`
4. Push and open a Pull Request

Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## Licence

MIT Licence — see [LICENSE](LICENSE) for details.

The EMIS dataset is published by the South African Department of Basic Education under open government data principles. Dataset available at [education.gov.za/Programmes/EMIS/EMISDownloads.aspx](https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx).


---

## Features

### KPI Banner
Six live metric cards update instantly with every filter change:

| Metric | Description |
|--------|-------------|
| Total Schools | Count of open schools matching active filters |
| Total Learners | Sum of `Learners2025` |
| Total Educators | Sum of `Educators2025` |
| Avg. LER | Learner-to-Educator Ratio |
| % No-Fee Schools | Share of schools where fees are waived |
| Critical LER | Schools where LER > 40 (resource-strained) |

### 01 — School Locations
- All schools plotted on a Carto mapbox basemap (dark/light tile set matched to theme)
- Marker size scaled to learner enrolment (√ normalised)
- Marker colour switchable between Quintile (Q1–Q5) and School Phase
- Hover tooltips: school name, district, learners, educators, derived LER

### 02 — Socio-Economic & Resource Analysis
This section acts as a key narrative piece, highlighting the deep inequalities present in the system, specifically aligned to South Africa's poverty Quintiles.

| Chart | What it shows |
|-------|---------------|
| Sunburst (Province → Quintile) | School count hierarchy; sized by school count, coloured by quintile |
| LER by Quintile Bar | Exposes the resource gap by showing stacked LER rates from Quintile 1 (poorest) through Quintile 5 |
| Dual Donut (No-Fee by Sector) | No-Fee vs Fee-Charging split for Public vs Independent sectors |
| LER Scatter | Learners vs Educators scatter with LER = 30 and LER = 40 reference lines; colour-coded by strain level |

### 03 — Province Comparison
Horizontal bar chart switchable between Learners / Educators / Schools per province.

### Cross-Filtering Sidebar
All charts respond simultaneously to:
- Province (cascades to District options)
- District
- Sector (Public / Independent)
- School Phase (Primary, Secondary, Combined, …)
- Quintile (Q1 – Q5)
- Urban / Rural (Derived location classification)

### Story Mode
Users can toggle **"📖 Enable Story Mode"** from the sidebar to transform the dashboard into a data journalism piece. This injects curated narrative blocks right above visualizations to guide users through the implications of spatial inequality, resource strain, and poverty in the SA education system.

### Dark / Light Mode
Toggle in the sidebar switches the full interface — shell, charts, and map — between a precision dark theme and a high-contrast light theme.

---

## Project Structure

```
sa-emis-dashboard/
├── app.py              # Streamlit entrypoint — layout, KPIs, sidebar, CSS
├── db.py               # Database access layer — SQL queries, @st.cache_data
├── charts.py           # Plotly figure builders (one function per chart)
├── setup.py            # One-time CSV → SQLite conversion script
├── requirements.txt    # Python dependencies
├── emis.csv            # Source dataset (SA DBE EMIS 2025, semicolon-delimited)
├── .streamlit/
│   └── config.toml     # Base theme & server settings
└── .gitignore
```

> `emis.db` is not committed — it is generated locally by `setup.py` (see Quick Start below).

---

## Quick Start

**1 — Clone the repository**

```bash
git clone https://github.com/<your-username>/sa-emis-dashboard.git
cd sa-emis-dashboard
```

**2 — Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows PowerShell
```

**3 — Install dependencies**

```bash
pip install -r requirements.txt
```

**4 — Build the SQLite database**

```bash
python setup.py
```

Reads `emis.csv` and writes `emis.db` (~13 MB) with WAL mode and four indexes. Run once only.

**5 — Launch the dashboard**

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**.

---

## Requirements

| Package | Min version | Purpose |
|---------|-------------|---------|
| `streamlit` | 1.35 | Web UI framework |
| `pandas` | 2.2 | DataFrame manipulation |
| `plotly` | 5.20 | Interactive charts & map |

Python **3.10+** required. Developed and tested on macOS Apple Silicon with Python 3.14.

---

## Dataset

**Source:** South African Department of Basic Education (DBE) — EMIS 2025  
**URL:** [https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx](https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx)  
**Rows:** 25,527 schools  
**Key fields:** `NatEmis`, `Province`, `EIDistrict`, `Phase_PED`, `Sector`, `Quintile`, `NoFeeSchool`, `Urban_Rural`, `Learners2025`, `Educators2025`, `GIS_Long`, `GIS_Lat`

Public government dataset — no personally identifiable information.

### Data normalisation applied in `db.py`

| Issue | Fix |
|-------|-----|
| European decimal commas in GIS coordinates (`-31,15778`) | Replaced with `.` before `CAST` |
| Mixed-case Sector values (`PUBLIC`, `Independent`) | `UPPER(TRIM(...))` |
| Varied NoFeeSchool literals (`No Fee`, `YES`, `N`) | Mapped to `No Fee` / `Fee Charging` |
| Quintile sentinels (`99`, `N/A`) | Mapped to `Other` |
| Mixed Status values (`OPEN`, `Open`, `PENDING OPEN`) | Filtered to open schools only |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         app.py                              │
│  Layout · KPI cards · Sidebar filters · CSS theme engine    │
├──────────────────────┬──────────────────────────────────────┤
│       db.py          │            charts.py                 │
│  SQLite queries      │  Plotly figure builders              │
│  @st.cache_data      │  scatter_map()                       │
│  load_filtered_data  │  sunburst_province_quintile()        │
│  get_provinces()     │  donut_no_fee_by_sector()            │
│  get_districts()     │  ler_scatter()                       │
│  get_phases()        │  province_bar()                      │
└──────────────────────┴──────────────────────────────────────┘
                         ↕
                      emis.db
              (SQLite · ~13 MB · WAL mode · 4 indexes)
```

All data loading is SQL-aggregated before reaching pandas/Plotly. `@st.cache_data(ttl=600)` serves repeated filter interactions from memory.

---

## Design System — Brutalist Data Terminal

Inspired by Bloomberg Terminal and Linear.app: monospace type, tight grids, no decoration.

| Token | Dark | Light |
|-------|------|-------|
| Background | `#0c0c0f` | `#f4f5f7` |
| Surface | `#111116` | `#ffffff` |
| Primary accent | `#4d9fff` | `#1d6ed8` |
| Text | `#f0f0f0` | `#111827` |
| Muted text | `#8a8fa8` | `#6b7280` |
| Red / Critical | `#e05252` | `#e05252` |
| Green / Healthy | `#4eba7f` | `#4eba7f` |
| Typeface | IBM Plex Mono + IBM Plex Sans | |

CSS variables are defined in a single `:root` block and overridden wholesale by the light-mode injection block. All Plotly charts receive explicit `paper_bgcolor` / `plot_bgcolor` / `hoverlabel` values per theme.

---

## Changelog

### v1.4.0 — 2026-05-13
- Mobile responsive layout: `@media (max-width: 768px)` rules added to global CSS
  - Sidebar set to `auto` collapse (hamburger menu on mobile)
  - KPI grid collapses from 6-column single row to 2-column × 3-row grid
  - KPI value font size reduced (`2rem` → `1.45rem`) on narrow screens
  - Header stacks title and subtitle vertically on mobile
  - Section 02 two-column chart row (sunburst + donut) stacks to full-width single column
  - Footer stacks and centres its two spans on mobile
  - Outer padding tightened to `0.75rem` on mobile
- Map chart given explicit `height: 480px`

### v1.3.0 — 2026-05-13
- Section 02 layout changed from 3-column cramped row to 2-row layout (sunburst + donut side-by-side, LER scatter full-width)
- Explicit chart heights added (sunburst/donut 460 px, LER scatter 400 px)
- Light mode: explicit `paper_bgcolor` / `plot_bgcolor` on all charts (eliminates dark-config bleed-through)
- Light mode: `hoverlabel` colours set explicitly on all charts
- Light mode: axis tick/title colours darkened to `#374151`; bar labels and donut annotations to `#374151`
- Light mode: KPI cards, section titles, header, footer — all custom HTML elements receive explicit CSS overrides

### v1.2.0 — 2026-05-13
- Dark / light mode toggle added to sidebar
- Full CSS variable overrides for light mode: sidebar widgets, select boxes, tags, radio buttons, captions
- All `use_container_width=True` replaced with `width="stretch"` (Streamlit 1.40+ API)

### v1.1.0 — 2026-05-13
- Brutalist Data Terminal redesign (replaced initial sci-fi glassmorphism aesthetic)
- IBM Plex Mono + IBM Plex Sans typeface via Google Fonts
- CSS custom-property token system (`--bg`, `--surface`, `--signal`, `--text`, etc.)
- Plotly palette constants: `QUINTILE_COLORS`, `PROVINCE_PALETTE`, `LER_COLORS`, `NO_FEE_COLORS`
- `_make_layout()` / `_style_axes()` helpers centralise chart theme application

### v1.0.0 — 2026-05-13
- Initial release: CSV → SQLite pipeline (`setup.py`), data access layer (`db.py`), Plotly chart builders (`charts.py`), Streamlit app (`app.py`)
- 25,527 schools · 9 provinces · geospatial map, sunburst, dual donut, LER scatter, province bar

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'feat: add my feature'`
4. Push and open a Pull Request

Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## Licence

MIT Licence — see [LICENSE](LICENSE) for details.

The EMIS dataset is published by the South African Department of Basic Education under open government data principles. Dataset available at [education.gov.za/Programmes/EMIS/EMISDownloads.aspx](https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx).

---

## 🙏 Acknowledgements

- [Department of Basic Education, South Africa](https://www.education.gov.za) for publishing the EMIS dataset
- [Streamlit](https://streamlit.io) · [Plotly](https://plotly.com) · [Carto](https://carto.com) for the dark map tiles
