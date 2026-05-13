# 🎓 SA EMIS National Schools Dashboard

A **next-generation, fully interactive data exploration dashboard** for the South African National Education Management Information System (EMIS) dataset. Built with Streamlit and Plotly, it lets analysts, researchers, and policymakers explore over **25,000 schools** across all nine provinces through a high-performance dark-mode interface.

![Dashboard preview — dark glassmorphism UI with map, KPI banner, sunburst, scatter and donut charts](https://placehold.co/1200x600/0a0a14/6366f1?text=SA+EMIS+Dashboard+Preview)

---

## ✨ Features

### KPI Banner
Six live metric cards update instantly with every filter change:

| Metric | Description |
|--------|-------------|
| Total Schools | Count of open schools matching active filters |
| Total Learners | Sum of `Learners2025` |
| Total Educators | Sum of `Educators2025` |
| Avg. LER | National Learner-to-Educator Ratio |
| % No-Fee Schools | Share of schools where fees are waived |
| Critical LER | Schools where LER > 40 (resource-strained) |

### 📍 Geospatial Map
- All schools plotted on a dark **Carto mapbox** basemap
- Marker **size** scaled to learner enrolment (√ normalised)
- Marker **colour** switchable between Quintile (Q1–Q5) and School Phase
- Rich hover tooltips: school name, district, learners, educators, derived LER

### 🔬 Socio-Economic Analysis
| Chart | What it shows |
|-------|---------------|
| **Sunburst** | Province → Quintile hierarchy, sized by school count |
| **Dual Donut** | No-Fee vs Fee-Charging for Public vs Independent sectors |
| **LER Scatter** | Learners vs Educators with LER = 30 and LER = 40 reference lines; colour-coded by strain level |
| **Province Bar** | Horizontal bar switchable between Learners / Educators / Schools |

### 🔍 Cross-Filtering Sidebar
All charts respond simultaneously to:
- Province (cascades to District options)
- District
- Sector (Public / Independent)
- School Phase (Primary, Secondary, Combined, …)
- Quintile (Q1 – Q5)

---

## 🗂️ Project Structure

```
sa-emis-dashboard/
├── app.py              # Streamlit entrypoint — layout, KPIs, sidebar
├── db.py               # Database access layer — SQL queries, @st.cache_data
├── charts.py           # Plotly figure builders (one function per chart)
├── setup.py            # One-time CSV → SQLite conversion script
├── requirements.txt    # Python dependencies
├── emis.csv            # Source dataset (SA DBE EMIS 2025, semicolon-delimited)
├── .streamlit/
│   └── config.toml     # Dark theme & server settings
└── .gitignore
```

> `emis.db` is not committed — it is **generated locally** by `setup.py` (see Quick Start below).

---

## ⚡ Quick Start

### 1 — Clone the repository

```bash
git clone https://github.com/<your-username>/sa-emis-dashboard.git
cd sa-emis-dashboard
```

### 2 — Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows PowerShell
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Build the SQLite database

```bash
python setup.py
```

This reads `emis.csv` and creates `emis.db` (~13 MB) with optimised indexes. It only needs to be run once.

### 5 — Launch the dashboard

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**.

---

## 🛠️ Requirements

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥ 1.35 | Web UI framework |
| `pandas` | ≥ 2.2 | DataFrame manipulation |
| `plotly` | ≥ 5.20 | Interactive charts & map |

Python **3.10+** required. Tested on macOS (Apple Silicon) with Python 3.14.

---

## 📊 Dataset

**Source:** South African Department of Basic Education (DBE) — EMIS 2025  
**URL:** https://www.education.gov.za/Informationfor/EducationManagementInformationSystem.aspx  
**Rows:** 25,527 schools  
**Key fields:** NatEmis, Province, EIDistrict, Phase_PED, Sector, Quintile, NoFeeSchool, Urban_Rural, Learners2025, Educators2025, GIS_Long, GIS_Lat

The dataset is a **public government dataset** published by the South African DBE. It does not contain personally identifiable information.

### Data normalisation applied
The raw CSV has several inconsistencies handled transparently in `db.py`:

| Issue | Fix |
|-------|-----|
| European decimal commas in GIS coordinates (`-31,15778`) | Replaced with `.` before `CAST` |
| Mixed-case Sector values (`PUBLIC`, `Independent`) | `UPPER(TRIM(...))` |
| Varied NoFeeSchool literals (`No Fee`, `YES`, `N`) | Mapped to `No Fee` / `Fee Charging` |
| Quintile sentinels (`99`, `N/A`) | Mapped to `Other` |
| Mixed Status values (`OPEN`, `Open`, `PENDING OPEN`) | Filtered to open schools only |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         app.py                              │
│  (Layout · KPI cards · Sidebar filters · Chart placement)   │
├──────────────────────┬──────────────────────────────────────┤
│       db.py          │            charts.py                  │
│  SQLite queries      │  Plotly figure builders               │
│  @st.cache_data      │  scatter_map()                        │
│  load_filtered_data  │  sunburst_province_quintile()         │
│  get_provinces()     │  donut_no_fee_by_sector()             │
│  get_districts()     │  ler_scatter()                        │
│  get_phases()        │  province_bar()                       │
└──────────────────────┴──────────────────────────────────────┘
                         ↕
                      emis.db
              (SQLite · ~13 MB · WAL mode)
```

All data loading is **SQL-aggregated first**, minimising the volume of data transferred to pandas/Plotly. `@st.cache_data(ttl=600)` ensures repeated filter interactions are served from memory.

---

## 🎨 Design System

| Token | Value |
|-------|-------|
| Background | `#0a0a14` |
| Surface | `#13131f` |
| Grid lines | `#1e1e2e` |
| Primary accent | `#6366f1` (Indigo) |
| Text | `#e2e8f0` |
| Muted text | `#94a3b8` |
| Critical (LER > 40) | `#ef4444` |
| Q1 (most disadvantaged) | `#ef4444` → Q5 `#22c55e` |

Cards use **glassmorphism** (`backdrop-filter: blur`), subtle gradient borders, and lift-on-hover transitions injected via Streamlit's `st.markdown` unsafe HTML escape hatch.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push and open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 Licence

This project is licensed under the **MIT Licence** — see [LICENSE](LICENSE) for details.

The EMIS dataset is published by the South African Department of Basic Education under open government data principles.

---

## 🙏 Acknowledgements

- [Department of Basic Education, South Africa](https://www.education.gov.za) for publishing the EMIS dataset
- [Streamlit](https://streamlit.io) · [Plotly](https://plotly.com) · [Carto](https://carto.com) for the dark map tiles
