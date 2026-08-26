# AmbitionBox Analysis

An end-to-end data science project on Indian company data. Company profiles were
scraped from [AmbitionBox](https://www.ambitionbox.com/), cleaned and structured
into a single dataset, analysed, and finally served through an interactive Flask
web app where the whole thing can be filtered and visualised.

The project follows the full data science lifecycle: **data collection ->
data preprocessing -> data analysis -> data visualization.**

- **Companies:** 64,210 (after cleaning)
- **Cities scraped:** 10 major Indian hiring hubs
- **Industries:** 84  ·  **Locations:** 371
- **Interface:** a 5-page Flask app (Home, Explore, Dashboard, Compare, About)


## Table of contents

- [What it does](#what-it-does)
- [The data science pipeline](#the-data-science-pipeline)
- [The dataset](#the-dataset)
- [How the raw data was cleaned](#how-the-raw-data-was-cleaned)
- [The web app](#the-web-app)
- [Key findings](#key-findings)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [API reference](#api-reference)
- [Filters](#filters)
- [Notes and caveats](#notes-and-caveats)
- [Author](#author)
- [Disclaimer](#disclaimer)


## What it does

The app turns a raw pile of scraped listings into something you can actually
explore:

- **Filter** 64,210 companies by name, rating, industry, size, type, age and
  location, with searchable multi-selects and dual range sliders.
- **Browse** matching companies in a sortable, paginated table, and export any
  filtered slice to CSV.
- **Visualise** the same filtered slice through twelve charts that redraw the
  instant you change a filter, including a section that breaks down what
  actually correlates with higher company ratings.
- **Compare** companies head-to-head with an automated scoreboard that crowns a
  winner based on key performance metrics.


## The data science pipeline

### 1. Data collection
Company profiles were web-scraped from AmbitionBox across ten major Indian hiring
hubs: Ahmedabad, Bangalore, Chennai, Gurugram, Hyderabad, Indore, Jaipur, Mumbai,
Noida and Pune. Each city produced its own CSV with the company name, its overall
rating, and a single free-text field holding the rest of the details. That came to
**94,580 rows** in total.

### 2. Data preprocessing
The ten city files were combined, and **30,370 exact duplicate rows** (companies
that appear in more than one city) were removed. The messy free-text details field
was then parsed into five clean columns, ages were converted to numbers, and
missing values were left as blanks rather than guessed. The result is a tidy
dataset of **64,210 unique companies**. See
[How the raw data was cleaned](#how-the-raw-data-was-cleaned) for the details.

### 3. Data analysis
The cleaned data was profiled across 84 industries and 371 locations to look at
rating distributions, company age and size mixes, ownership types, and, most
usefully, which of those factors line up with higher ratings.

### 4. Data visualization
Everything is wrapped in a Flask app with a live dashboard and comparison tool, so the analysis is
interactive rather than a static notebook. Change a filter and every chart and
number updates.


## The dataset

The cleaned dataset lives at `combined_companies_cleaned.csv` (and a copy is
bundled with the app at `ambitionbox_app/data/companies.csv`).

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `company_name` | text | Company name | Zydus Lifesciences |
| `company_rating` | float | Overall AmbitionBox rating, 1.0 - 5.0 | 4.2 |
| `industry` | text | Primary industry | Pharma |
| `size` | text | Employee band | 10k-50k Employees |
| `type` | text | Ownership / classification | Public |
| `years_old` | integer | Company age in years | 72 |
| `location` | text | Head-office location | Ahmedabad |

Coverage and completeness:

- `location` and `company_rating` are present for almost every row (only 82
  companies have no rating).
- `size` is blank for roughly 34% of rows, `industry` for roughly 43%,
  `years_old` for roughly 49%, and `type` for roughly 85%. These gaps come
  straight from the source listings and were deliberately left empty.
- `type` only takes one of nine values: Public, Forbes Global 2000, Startup,
  Fortune India 500, Conglomerate, Indian Unicorn, Central, State and MNC.


## How the raw data was cleaned

The hardest part of preprocessing was the free-text details field. A typical value
looked like this:

```
Pharma , 10k-50k Employees , Public , 72 years old , Ahmedabad +152 more
```

It had to become five separate columns:

```
industry = Pharma
size     = 10k-50k Employees
type     = Public
years_old = 72
location = Ahmedabad
```

The tricky part is that the field is not fixed. Anywhere from one to five of those
pieces can be present, so you cannot rely on position alone. For example, some rows
have no `type` and no `industry`:

```
BPO , 5k-10k Employees , 16 years old , Indore +24 more
```

So each piece is identified by its content rather than its position:

- **size** is the piece that contains the word "Employees".
- **years_old** is the piece that contains "years old" (the number is then
  extracted as an integer).
- **type** is matched against the fixed set of nine known ownership values.
- **location** is always the last piece, with the trailing "+N more" count
  stripped off.
- **industry** is whatever remains at the front.

This approach parses every row with no leftover or misread pieces, and a
row-by-row reconciliation against the raw source confirmed zero mismatches.


## The web app

Five pages, all sharing one filter engine so a selection stays consistent as you
move between them.

| Page | Route | What it does |
|------|-------|--------------|
| Home | `/` | Introduction, high-level metrics and entry point. |
| Explore | `/explore` | Sortable, paginated data table. Allows filtering and exporting to CSV. |
| Dashboard | `/dashboard` | 12 live Chart.js visualizations that react to the active filters. |
| Compare | `/compare` | Head-to-head comparison tool with automated winner scoring and visual progress bars. |
| About | `/about` | Project background, data science pipeline summary, and developer contact details. |


## Key findings

Through interactive exploration on the dashboard, several key insights emerge from the dataset:
- **Age vs Rating**: Older, established companies tend to have more stable but slightly lower average ratings than newer startups which often see high variance.
- **Size vs Rating**: Midsized companies frequently hit the 'sweet spot' for employee satisfaction compared to massive global conglomerates or tiny ventures.
- **Industry Hotspots**: The IT Services and Software industries hold the majority share of the highest-rated companies across the major tech hubs (Bangalore, Pune, Hyderabad).


## Tech stack

- **Data Processing**: Python, Pandas, NumPy
- **Backend**: Flask (Python)
- **Frontend Core**: HTML5, CSS3, Vanilla JavaScript
- **UI & Theming**: Custom Glassmorphism CSS, Dark/Light Mode
- **Charts & Visualization**: Chart.js
- **Controls**: Tom Select (Searchable Dropdowns), noUiSlider (Range sliders)


## Project structure

```text
ambitionbox_app/
├── app.py                 # Core Flask backend and API routing
├── data/
│   └── companies.csv      # The cleaned dataset of 64,210 companies
├── static/
│   ├── css/
│   │   └── style.css      # Custom UI framework (glassmorphism, animations)
│   └── js/
│       ├── dashboard.js   # Chart.js initialization and updates
│       ├── explore.js     # Data table rendering and CSV export logic
│       ├── compare.js     # Head-to-head scoreboard logic
│       ├── filters.js     # Global filter state management
│       ├── search.js      # Global type-ahead search
│       └── theme.js       # Light/Dark mode toggling
└── templates/
    ├── base.html          # Global layout, nav, and modal
    ├── index.html         # Landing page
    ├── explore.html       # Data table view
    ├── dashboard.html     # Charts view
    ├── compare.html       # Compare view
    └── about.html         # About page
```


## Getting started

Ensure you have Python 3.8+ installed.

1. **Install dependencies**:
   ```bash
   pip install flask pandas numpy
   ```

2. **Run the server**:
   ```bash
   python app.py
   ```

3. **View the app**:
   Open `http://127.0.0.1:5000` in your browser.


## API reference

The Flask backend exposes several JSON endpoints used by the frontend:

- `GET /api/meta`: Returns dropdown options (industries, sizes, locations) and total dataset metrics.
- `GET /api/companies`: Accepts query filters and returns paginated, sorted rows for the Explore table.
- `GET /api/analytics`: Accepts query filters and returns pre-aggregated data arrays mapped directly for Chart.js.
- `GET /api/export`: Generates a downloadable `.csv` file matching the current filter state.
- `GET /api/compare`: Accepts `c1` and `c2` (company names) and returns precise exact-match rows for the comparison scoreboard.


## Filters

The filtering engine acts globally across the Explore and Dashboard views. 
- **Text/Select**: Company Name (Global Search), Industry, Size, Type, Location.
- **Range Sliders**: Overall Rating (1.0 to 5.0), Company Age (0 to 100+ years).


## Notes and caveats

- The dataset does not include sub-ratings (e.g., Work-Life Balance, Salary & Benefits).
- The "location" field refers to the location listed in the primary header of the AmbitionBox profile, which is typically the head office or primary Indian hub, not all operational locations.


## Author

**Mayank Kumar**
- Instagram: [@mayank_kumar11](https://instagram.com/mayank_kumar11)
- LinkedIn: [/in/mayank-kumar111](https://www.linkedin.com/in/mayank-kumar111)
- GitHub: [mayank-kumar111](https://github.com/mayank-kumar111)


## Disclaimer

Data is sourced from public AmbitionBox listings strictly for analytical, educational, and portfolio demonstration purposes. The creator is not affiliated with AmbitionBox.
