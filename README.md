## Analyzing Industry Carbon Emissions

This mini-project loads an industry-level carbon emissions dataset into SQLite, runs SQL analyses to identify the most recent year and the highest-emitting industries, and visualizes the top 5 as a bar chart.

### Project Structure
- `emissions.csv`: Placeholder dataset with columns `industry, year, emissions_mtco2e`.
- `emissions_analysis.sql`: SQLite script to create schema, import CSV, and run queries.
- `app.py`: Python script to load the CSV into SQLite, run the same queries, and generate a bar chart.
- `emissions.db`: SQLite database file (created on first run).

### Dataset Schema
Table: `emissions`
- `industry` TEXT
- `year` INTEGER
- `emissions_mtco2e` REAL (Megatonnes of CO₂ equivalent)

### Option A: Quickstart with Python (recommended)
Requirements: Python 3.9+ on macOS

1) Install dependencies:
```bash
python3 -m pip install --upgrade pip
python3 -m pip install pandas matplotlib seaborn
```

2) Run the script:
```bash
python3 app.py
```

What it does:
- Creates/overwrites `emissions.db`
- Loads `emissions.csv` into the `emissions` table
- Finds the most recent year
- Calculates and ranks total emissions per industry for that year
- Prints results to the console
- Saves `top5_emissions.png` with a bar chart of the top 5 industries

### Option B: Pure SQLite (CLI)
Ensure `sqlite3` is available (macOS ships with it). From the project directory:

```bash
sqlite3 emissions.db ".read emissions_analysis.sql"
```

The script will:
- Create table `emissions`
- Import `emissions.csv`
- Output:
  - Most recent year
  - Totals by industry (most recent year)
  - Ranked industries
  - Top 5 industries by emissions

### Queries Included
In `emissions_analysis.sql`:
- Find most recent year: `SELECT MAX(year) FROM emissions;`
- Total emissions per industry for that year (uses CTE `latest_year` and `totals`)
- Rank industries with a window function (`RANK() OVER (ORDER BY total_emissions DESC)`) 
- Top 5 industries (`WHERE emissions_rank <= 5`)

### Expected Findings (with placeholder data)
For the included sample dataset (most recent year = 2023), the highest emitting industries are typically:
- Power Generation
- Oil & Gas
- Manufacturing
- Transportation
- Residential / Agriculture (depending on totals)

Run the project to see exact numbers and the chart.

### Notes
- You can replace `emissions.csv` with your own dataset (same columns) and re-run.
- The SQL uses window functions available in modern SQLite versions (3.25+). macOS default SQLite should be sufficient.


