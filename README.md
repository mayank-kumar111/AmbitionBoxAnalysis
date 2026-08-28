# AmbitionBox Analysis 🚀

An end-to-end **data engineering + data science + web analytics** project built on Indian company data collected from AmbitionBox. The project demonstrates the complete lifecycle:

**Scraping → Cleaning → Validation → Incremental Ingestion → Quality Monitoring → SQLite History → Analytics → Flask Dashboard → CI/CD**

The application exposes company exploration, interactive analytics, head-to-head comparison, refresh history, and data-quality/health signals.

> **Data note:** AmbitionBox is the source of the collected company-listing data. Use the project only in accordance with the source website's terms, robots.txt, applicable law, and responsible scraping practices.

---

## ✨ Current capabilities

- Explore and filter the cleaned company dataset.
- Interactive dashboard with Chart.js visualizations.
- Compare two companies using quantitative metrics.
- Incrementally merge new snapshots without duplicating companies.
- Track company snapshots and field-level changes in SQLite.
- Detect suspicious refreshes such as large growth/drop, duplicate spikes, invalid-record spikes, rating-change spikes, and empty outputs.
- Convert refresh anomalies into a health score and status.
- Generate actionable refresh alerts and GitHub Actions summaries.
- Run automated tests locally and in GitHub Actions.
- Schedule or manually trigger data refreshes through GitHub Actions.

The canonical company schema is:

| Column | Type | Example |
|---|---|---|
| `company_name` | text | Zydus Lifesciences |
| `company_rating` | float | 4.2 |
| `industry` | text | Pharma |
| `size` | text | 10k-50k Employees |
| `type` | text | Public |
| `years_old` | integer | 72 |
| `location` | text | Ahmedabad |

---

## 🏗️ Architecture

```text
                    AmbitionBox
                         │
                         ▼
                ┌─────────────────┐
                │     Scraper     │
                │ requests + BS4  │
                └────────┬────────┘
                         │ raw CSV snapshots
                         ▼
                ┌─────────────────┐
                │   Preprocessing  │
                │ parse + normalize│
                └────────┬────────┘
                         │ cleaned rows
                         ▼
                ┌─────────────────┐
                │    Validation   │
                │ schema + values │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Incremental     │
                │ Ingestion/Merge │
                └────────┬────────┘
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       ┌────────────┐        ┌────────────────┐
       │ SQLite DB  │        │ Quality Layer  │
       │ snapshots  │        │ anomalies +    │
       │ changes    │        │ health + alerts│
       └─────┬──────┘        └───────┬────────┘
             │                       │
             └───────────┬───────────┘
                         ▼
                ┌─────────────────┐
                │  Flask / APIs   │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │ Dashboard / UI  │
                └─────────────────┘

                 GitHub Actions CI/CD
              ┌─────────────────────────┐
              │ pytest → E2E → refresh  │
              │ → history → artifacts   │
              └─────────────────────────┘
```

---

## 📁 Repository structure

```text
AmbitionBoxAnalysis/
├── ambitionbox_app/
│   ├── app.py
│   ├── data/
│   │   └── companies.csv
│   ├── templates/
│   └── static/
├── src/
│   ├── analytics/
│   │   └── history.py
│   ├── database/
│   │   └── sqlite_store.py
│   ├── ingestion/
│   │   └── incremental.py
│   ├── pipeline/
│   │   └── runner.py
│   ├── preprocessing/
│   │   ├── cleaner.py
│   │   ├── quality.py
│   │   └── validator.py
│   ├── quality/
│   │   ├── alerts.py
│   │   ├── anomaly_detector.py
│   │   ├── health.py
│   │   └── monitor.py
│   └── scraper/
│       ├── ambitionbox_scraper.py
│       └── config.py
├── scripts/
│   ├── auto_refresh.py
│   ├── build_database.py
│   ├── collect_and_update.py
│   ├── github_summary.py
│   ├── notify_refresh.py
│   └── refresh_history.py
├── tests/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── data-refresh.yml
├── requirements.txt
└── README.md
```

---

## 🔄 Data pipeline

### 1. Collection
The scraper collects company cards for configured hiring hubs and saves one CSV per location. It uses `requests`, retry/backoff handling, and BeautifulSoup parsing. The parser extracts company name, rating, and the semi-structured details field.

The scraper is intentionally isolated from preprocessing and analytics so collection can be re-run independently.

### 2. Preprocessing
The raw `other_data` field is parsed by content rather than assuming fixed positions. Employee size, company age, company type, and location are detected separately; trailing `+N more` / `+N other locations` suffixes are normalized.

The result is standardized to the seven-column canonical schema.

### 3. Validation
Validation checks required columns, missing company names, ratings outside the 1–5 range, negative ages, and duplicate rows. The pipeline can validate incoming snapshots without rejecting them merely because duplicate keys need to be collapsed by incremental ingestion.

### 4. Incremental ingestion
Company identity is normalized using:

```text
company_name + location
```

The merger distinguishes:

```text
NEW        → company not previously present
UPDATED    → same company/location, one or more fields changed
UNCHANGED  → same company/location, no data change
DUPLICATE  → repeated identity key in the incoming snapshot
```

A partial scrape is treated conservatively: missing rows are **not** interpreted as removals unless `--full-snapshot` is explicitly used.

### 5. Historical storage
SQLite stores:

- Current company records.
- Every observed snapshot.
- Field-level change history.
- Refresh-run summary metrics.

This enables queries such as rating movement, newly observed companies, company history, and most-improved companies.

### 6. Quality monitoring
Refreshes are checked for suspicious conditions. Current anomaly categories include:

| Code | Meaning | Severity |
|---|---|---|
| `LARGE_DATASET_GROWTH` | Dataset grew above configured threshold | warning |
| `LARGE_DATASET_DROP` | Large full-snapshot removal | critical |
| `DUPLICATE_SPIKE` | Incoming duplicate ratio is high | warning |
| `INVALID_RECORD_SPIKE` | Invalid-record ratio is high | critical |
| `RATING_CHANGE_SPIKE` | Unusually many ratings changed | warning |
| `EMPTY_FINAL_DATASET` | Refresh produced no rows | critical |

Health scoring starts at 100. Warnings reduce the score by 20 and critical anomalies reduce it by 60, with the score clamped at zero. The resulting status is `Healthy`, `Warning`, or `Blocked`.

### 7. Dashboard/API
The Flask application provides the main pages and APIs for exploration, analytics, export, comparison, refresh history, and data-quality reporting.

---

## 🚀 Local setup

### Requirements

- Python 3.8+ for compatibility with the project documentation; the CI workflow currently runs Python 3.12.
- Git.

### 1. Clone

```bash
git clone https://github.com/mayank-kumar111/AmbitionBoxAnalysis.git
cd AmbitionBoxAnalysis
git checkout develop
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run tests

```bash
pytest -q
```

### 5. Start the Flask application

```bash
python ambitionbox_app/app.py
```

Then open:

```text
http://127.0.0.1:5000
```

The principal application pages are:

| Route | Purpose |
|---|---|
| `/` | Home / overview |
| `/explore` | Filter, sort, paginate, export |
| `/dashboard` | Interactive analytics |
| `/compare` | Company comparison |
| `/about` | Project documentation |

---

## 🔧 Refresh commands

### Dry-run refresh

A dry run is the safer default because it does not modify the master dataset.

```bash
python scripts/auto_refresh.py --pages 1
```

### Apply a refresh

```bash
python scripts/auto_refresh.py --pages 1 --apply
```

### Extended refresh

```bash
python scripts/auto_refresh.py --extended --pages 2 --apply
```

### Full-snapshot mode

Use this only when the collection covers the complete source scope and absent companies should be considered removals.

```bash
python scripts/auto_refresh.py --pages 1 --apply --full-snapshot
```

### Build/update SQLite from a cleaned CSV

```bash
python scripts/build_database.py ambitionbox_app/data/companies.csv
```

### Refresh historical database from a collected snapshot

```bash
python scripts/refresh_history.py \
  --master ambitionbox_app/data/companies.csv \
  --incoming data/incoming \
  --database data/ambitionbox.db \
  --report reports/history_refresh.json
```

---

## 🧪 Testing strategy

The test suite covers the important layers independently and together:

```text
Scraper parsing
   ↓
Preprocessing/parser tests
   ↓
Validation + quality profiling
   ↓
Incremental ingestion
   ↓
SQLite persistence
   ↓
Historical analytics
   ↓
Anomaly / health / alerts
   ↓
Flask API smoke tests
   ↓
End-to-end pipeline
```

Run all tests with:

```bash
pytest -q
```

Run a focused layer:

```bash
pytest -q tests/test_preprocessing.py
a
pytest -q tests/test_ingestion.py
pytest -q tests/test_database.py
pytest -q tests/test_history.py
pytest -q tests/test_anomaly_detector.py
pytest -q tests/test_e2e_pipeline.py
```

> Remove the accidental standalone `a` line above when copying focused commands; it is intentionally harmless in this documentation source.

---

## ⚙️ GitHub Actions

### CI workflow

`.github/workflows/ci.yml` runs the automated test gates on pushes and pull requests targeting the main development branches.

The quality sequence is:

```text
Install dependencies
       ↓
Full pytest suite
       ↓
Deterministic E2E pipeline test
```

### Scheduled data refresh

`.github/workflows/data-refresh.yml` supports manual execution and a weekly scheduled run. The workflow:

```text
Checkout develop
    ↓
Install dependencies
    ↓
Run tests
    ↓
Restore latest history artifact
    ↓
Collect snapshot
    ↓
Generate GitHub summary
    ↓
Send optional Slack alert
    ↓
Persist SQLite history
    ↓
Upload history + reports
```

The manual workflow supports `extended` and `pages` inputs.

---

## 🔐 Configuration / secrets

The refresh workflow can send Slack notifications using:

```text
SLACK_WEBHOOK_URL
```

Store that value as a GitHub Actions repository secret. The repository does **not** commit `.env` files or generated refresh reports/database files; those paths are ignored by `.gitignore`.

---

## 📊 Example refresh health logic

A refresh with no anomalies receives:

```text
Health score: 100
Status: Healthy
```

A warning anomaly lowers the score; a critical anomaly can push the refresh into `Blocked` state. Alerts contain severity, anomaly code, message, metric, value, threshold, snapshot timestamp, and whether the refreshed dataset was applied.

This makes refresh failures explainable rather than silently changing the analytical dataset.

---

## 🛠️ Troubleshooting

### `ModuleNotFoundError`

Activate the virtual environment and reinstall dependencies:

```bash
python -m pip install -r requirements.txt
```

### Tests fail because data is missing

Confirm that the cleaned dataset exists at:

```text
ambitionbox_app/data/companies.csv
```

### Refresh returns no companies

Check the scraper logs and source availability. Do not enable full-snapshot mode when the scrape scope is incomplete.

### Refresh is `Warning` or `Blocked`

Inspect:

```text
reports/update_report.json
```

and the anomaly codes. A blocked or suspicious refresh should be investigated before applying the data.

### SQLite history is stale

Run the history refresh command again against the intended incoming snapshot directory, or restore the latest GitHub Actions history artifact.

---

## 🎯 Why this project is portfolio-ready

This project demonstrates more than a static visualization notebook. It shows practical engineering patterns that are valuable in Data Science / Data Engineering / ML-oriented roles:

- Reproducible ingestion.
- Defensive preprocessing.
- Schema and value validation.
- Incremental data updates.
- Historical data modeling.
- Data-quality monitoring.
- Automated anomaly detection.
- CI/CD quality gates.
- Flask APIs and interactive analytics.
- Operational reporting and notifications.

---

## 👨‍💻 Developer

**Mayank Kumar**

- GitHub: `mayank-kumar111`
- Repository: `AmbitionBoxAnalysis`

---

## 📜 Disclaimer

This project is intended for analytical, educational, and portfolio demonstration purposes. Verify that your collection and use of source data comply with AmbitionBox's current terms, robots.txt, rate limits, and applicable policies/laws before running or distributing a scraper.