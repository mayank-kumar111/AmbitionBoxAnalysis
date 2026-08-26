# AmbitionBox Analysis 🚀

An end-to-end data science and web visualization project built by **Mayank Kumar** on Indian company data. 

Company profiles were scraped from [AmbitionBox](https://www.ambitionbox.com/), cleaned and structured into a single dataset, analysed, and finally served through a blazing-fast, interactive Flask web application where the entire dataset can be filtered, visualized, and compared.

The project follows the full data science lifecycle: **Data Collection ➔ Data Preprocessing ➔ Data Analysis ➔ Data Visualization & Deployment.**

---

## 🌟 What It Does

The app turns a raw pile of scraped listings into a beautiful, interactive analytical tool:

- **Filter & Export**: Search 64,210 companies by name, rating, industry, size, type, age, and location using dynamic multi-selects and dual range sliders. Export any filtered slice instantly to a clean CSV.
- **Visualize (Live Dashboard)**: Twelve interactive Chart.js visualizations that redraw in milliseconds the moment you change a filter. Understand what actually correlates with higher company ratings and how industries are distributed.
- **Compare (Head-to-Head)**: Pit two companies against each other in the dedicated Compare Tool. Features a lightning-fast type-ahead search, dynamic visual progress bars, and an automated scoreboard system that crowns an overall winner based on quantitative metrics.
- **Premium UI/UX**: Custom-built CSS framework featuring deep glassmorphism (`backdrop-filter`), an animated Aurora mesh gradient background, smooth micro-interactions, and a seamless Dark/Light mode toggle.

---

## 🧬 The Data Science Pipeline

### 1. Data Collection
Company profiles were web-scraped from AmbitionBox across ten major Indian hiring hubs (Ahmedabad, Bangalore, Chennai, Gurugram, Hyderabad, Indore, Jaipur, Mumbai, Noida, and Pune). Each city produced its own raw CSV containing the company name, overall rating, and a messy free-text string holding the rest of the details. Total raw rows: **94,580**.

### 2. Data Preprocessing
The ten city files were combined, and **30,370 exact duplicate rows** were removed. The messy free-text details field was parsed into five clean columns, ages were converted to integers, and missing values were standardized. Result: a tidy dataset of **64,210 unique companies**.

#### How the raw data was cleaned
The hardest part of preprocessing was parsing the unstructured free-text field. A typical value looked like this:
`Pharma , 10k-50k Employees , Public , 72 years old , Ahmedabad +152 more`

It had to become:
- `industry` = Pharma
- `size`     = 10k-50k Employees
- `type`     = Public
- `years_old` = 72
- `location` = Ahmedabad

Because the fields were variable (some rows lacked `type` or `industry`), position-based splitting failed. Instead, content-based parsing was used:
- **size**: The chunk containing the word "Employees".
- **years_old**: The chunk containing "years old".
- **type**: Matched against a fixed set of nine known ownership values (e.g., Public, Startup, MNC).
- **location**: Always the last piece (stripping trailing "+N more" counts).
- **industry**: Whatever remained at the front.

This guaranteed 100% accurate parsing row-by-row against the source.

### 3. Data Analysis
The cleaned data was profiled across 84 industries and 371 locations to map out rating distributions, age demographics, ownership types, and to surface the factors that actually drive higher ratings.

### 4. Data Visualization
Instead of a static Jupyter notebook, the entire analysis is wrapped in an interactive Flask web application, allowing users to draw their own insights in real-time.

---

## 📂 The Dataset

The cleaned dataset is bundled with the application (`ambitionbox_app/data/companies.csv`).

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `company_name` | text | Company name | Zydus Lifesciences |
| `company_rating` | float | Overall AmbitionBox rating, 1.0 - 5.0 | 4.2 |
| `industry` | text | Primary industry | Pharma |
| `size` | text | Employee band | 10k-50k Employees |
| `type` | text | Ownership classification | Public |
| `years_old` | integer | Company age in years | 72 |
| `location` | text | Head-office location | Ahmedabad |

---

## 🖥️ The Web Application (API & Routes)

The Flask app serves 5 core pages, all sharing a single global filter engine:

| Route | Page | Description |
|-------|------|-------------|
| `/` | **Home** | Landing page with high-level dataset metrics. |
| `/explore` | **Explore** | The main data table. Paginate, sort, filter, and export to CSV. |
| `/dashboard` | **Dashboard** | 12 live charts powered by Chart.js. Reacts to all active filters. |
| `/compare` | **Compare** | The Head-to-Head tool. Pit two companies against each other. |
| `/about` | **About** | Pipeline documentation and contact information. |

### API Endpoints
- `/api/meta`: Returns all unique dropdown options (industries, sizes, locations) and current dataset totals.
- `/api/companies`: Returns paginated, sorted rows based on active query filters.
- `/api/analytics`: Returns pre-aggregated JSON payloads for the Chart.js visualizations.
- `/api/export`: Generates a downloadable CSV slice based on current filters.
- `/api/compare`: Accepts `c1` and `c2` and returns precise exact-match rows for the comparison scoreboard.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask
- **Data Engineering**: Pandas, NumPy
- **Frontend**: HTML5, CSS3 (Custom Glassmorphism Framework), Vanilla JavaScript
- **Visualization**: Chart.js
- **UI Components**: Tom Select (Type-ahead dropdowns), noUiSlider (Range sliders)

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.8+ installed.

### Installation
1. Clone the repository to your local machine.
2. Navigate to the app directory:
   ```bash
   cd ambitionbox_app
   ```
3. Install the required Python dependencies:
   ```bash
   pip install flask pandas numpy
   ```

### Running the App
1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 👨‍💻 Developer

**Built by Mayank Kumar**
- **Instagram**: [@mayank_kumar11](https://instagram.com/mayank_kumar11)
- **LinkedIn**: [/in/mayank-kumar111](https://www.linkedin.com/in/mayank-kumar111)
- **GitHub**: [mayank-kumar111](https://github.com/mayank-kumar111)

---
*Disclaimer: Data is sourced from AmbitionBox listings strictly for analytical, educational, and portfolio demonstration purposes.*
