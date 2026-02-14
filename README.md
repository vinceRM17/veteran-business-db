# Veteran Business Database

A Streamlit dashboard and data pipeline for managing a nationwide database of veteran-owned businesses. Built for **Active Heroes** (Shepherdsville, KY) to identify veteran business partners and contractors. Aggregates data from SAM.gov and USAspending.gov, supports CSV imports, and provides interactive maps, search, filtering, and reporting.

## Features

- **Multi-Source Data Aggregation** — Pull businesses from SAM.gov and USAspending.gov APIs
- **CSV Import** — Bulk import businesses from spreadsheets
- **Interactive Map** — Folium-powered map with business markers and distance filtering from HQ
- **Search & Filter** — Filter by data quality grade, trust tier, state, distance, certifications
- **Business Detail Pages** — Individual business profiles with contact info and certifications
- **Data Quality Grading** — A through F grades based on completeness (contact info, certifications, financials)
- **Reporting** — Select businesses and generate comparison reports
- **Export** — Download filtered data as CSV

## Pages

| Page | Description |
|------|-------------|
| Home | Dashboard with KPIs, grade distribution, map overview |
| Search | Browse and filter businesses |
| Import CSV | Bulk import from spreadsheets |
| Fetch Data | Pull from SAM.gov and USAspending.gov APIs |
| Export | Download database as CSV |
| Report | Generate reports from selected businesses |

## Project Structure

```
streamlit_app.py           # Main dashboard
pages/
  1_Search.py              # Search and browse
  2_Import_CSV.py          # CSV import
  3_Fetch_Data.py          # API data fetching
  4_Export.py              # CSV export
  5_Report.py              # Report generation
  _Business_Detail.py      # Individual business view
database.py                # SQLite/Turso database operations
sam_gov.py                 # SAM.gov API integration
usaspending.py             # USAspending.gov API integration
enrich.py                  # Data enrichment pipeline
geo.py                     # Geocoding and distance calculations
branding.py                # UI styling and branding
config.py                  # Configuration and constants
```

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Copy secrets template
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fill in: TURSO_CONNECTION_URL, TURSO_AUTH_TOKEN

# Run the app
streamlit run streamlit_app.py
```

Open http://localhost:8501.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.9+ |
| Dashboard | Streamlit |
| Data | Pandas |
| Database | SQLite (local) / Turso (cloud) |
| Maps | Folium + Streamlit-Folium |
| Geocoding | pgeocode |
| Visualization | Plotly |
| Web Scraping | Requests, BeautifulSoup4, DuckDuckGo Search |
| Hosting | Streamlit Community Cloud |

## Data Sources

| Source | Data | Notes |
|--------|------|-------|
| SAM.gov | Registered businesses, certifications | Requires API key |
| USAspending.gov | Federal contract awards | Public API |
| CSV Import | Manual business entries | Any format with mapping |

## Environment Variables

See `.streamlit/secrets.toml.example`:

- `TURSO_CONNECTION_URL` — Turso cloud database URL
- `TURSO_AUTH_TOKEN` — Turso cloud database token
