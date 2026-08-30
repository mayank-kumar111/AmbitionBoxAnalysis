# 📊 AmbitionBox Analysis

> An end-to-end **Data Science + Analytics + Flask dashboard** project built by **Mayank Kumar** to explore Indian company data through interactive search, filtering, visualization, and comparison.

## ⭐ Project Overview

**AmbitionBox Analysis** takes scraped company-profile data through a complete analytics workflow:

**Data Collection → Data Cleaning → Feature Extraction → Analysis → Interactive Visualization → Web Deployment**

The project turns a large company dataset into an interactive web application where users can explore companies, compare organizations, filter results, visualize trends, and export filtered data.

## 🔎 Key Highlights

- **64,210 unique company records** after preprocessing.
- **94,580 raw rows** collected across ten major Indian hiring hubs.
- **30,370 exact duplicate rows** removed during cleaning.
- Analysis covering **84 industries** and **371 locations**.
- Interactive filtering by company, rating, industry, employee size, ownership type, age, and location.
- CSV export for filtered results.
- **12 interactive Chart.js visualizations**.
- Head-to-head company comparison with a quantitative scoreboard.
- Responsive dark/light interface with custom glassmorphism styling.

## 🧠 Data Science Workflow

### 1. Data Collection

Company profile information was collected from AmbitionBox across:

Ahmedabad · Bangalore · Chennai · Gurugram · Hyderabad · Indore · Jaipur · Mumbai · Noida · Pune

Raw information included company name, rating, and additional company details stored in a semi-structured text field.

### 2. Data Preprocessing

The raw city-level datasets were combined and cleaned into a structured analytical dataset.

The preprocessing workflow included:

- Duplicate removal
- Unstructured text parsing
- Industry extraction
- Employee-size extraction
- Ownership/type extraction
- Company-age conversion
- Location extraction
- Missing-value standardization

Example transformation:

```text
Raw:
Pharma, 10k-50k Employees, Public, 72 years old, Ahmedabad +152 more

Structured:
industry     → Pharma
size         → 10k-50k Employees
type         → Public
years_old    → 72
location     → Ahmedabad
```

Content-based parsing was used instead of relying only on fixed field positions so that incomplete or differently formatted records could still be processed.

### 3. Analysis

The cleaned dataset is used to explore:

- Company rating distributions
- Industry-level patterns
- Location-level patterns
- Company age distributions
- Ownership/type distributions
- Relationships between company characteristics and ratings

### 4. Visualization & Web App

The analysis is delivered through an interactive Flask application rather than a static notebook.

## 🖥️ Application

| Route | Purpose |
|---|---|
| `/` | Home page and dataset overview |
| `/explore` | Search, filter, sort, paginate, and export companies |
| `/dashboard` | Interactive charts and analytics |
| `/compare` | Compare two companies |
| `/about` | Project and pipeline information |

### API

| Endpoint | Purpose |
|---|---|
| `/api/meta` | Dataset totals and filter options |
| `/api/companies` | Filtered/paginated company data |
| `/api/analytics` | Analytics payloads for charts |
| `/api/export` | Filtered CSV export |
| `/api/compare` | Exact company comparison data |

## 📁 Dataset

The cleaned dataset is included with the application at:

```text
ambitionbox_app/data/companies.csv
```

| Column | Description |
|---|---|
| `company_name` | Company name |
| `company_rating` | AmbitionBox rating, 1.0–5.0 |
| `industry` | Primary industry |
| `size` | Employee-size band |
| `type` | Ownership classification |
| `years_old` | Company age in years |
| `location` | Head-office location |

## 🛠️ Tech Stack

**Backend**  
Python · Flask

**Data & Analysis**  
Pandas · NumPy

**Frontend**  
HTML5 · CSS3 · Vanilla JavaScript

**Visualization**  
Chart.js

**UI Components**  
Tom Select · noUiSlider

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
git clone https://github.com/mayank-kumar111/AmbitionBoxAnalysis.git
cd AmbitionBoxAnalysis/ambitionbox_app
pip install flask pandas numpy
```

### Run

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## 💼 Why This Project Matters

This project demonstrates practical skills across the full analytics lifecycle:

```text
Raw Data
   ↓
Cleaning & Parsing
   ↓
Structured Dataset
   ↓
Exploratory Analysis
   ↓
Interactive Visualization
   ↓
Flask Web Application
```

It is particularly relevant for demonstrating **Data Science, Data Analytics, Python, Pandas, data cleaning, visualization, and dashboard development**.

## 👨‍💻 Author

**Mayank Kumar**  
GitHub: [@mayank-kumar111](https://github.com/mayank-kumar111)  
LinkedIn: [Mayank Kumar](https://www.linkedin.com/in/mayank-kumar111/)

## 📌 Disclaimer

The project uses AmbitionBox listing data for **educational, analytical, and portfolio demonstration purposes**.
