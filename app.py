import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


PROJECT_DIR = Path(__file__).parent
CSV_PATH = PROJECT_DIR / "emissions.csv"
DB_PATH = PROJECT_DIR / "emissions.db"
DOCS_DIR = PROJECT_DIR / "docs"


def initialize_database_with_csv(csv_path: Path, db_path: Path) -> None:
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS emissions;")
        cursor.execute(
            """
            CREATE TABLE emissions (
              industry TEXT NOT NULL,
              year INTEGER NOT NULL,
              emissions_mtco2e REAL NOT NULL
            );
            """
        )

        df = pd.read_csv(csv_path)
        df.to_sql("emissions", connection, if_exists="append", index=False)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emissions_year ON emissions(year);")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_emissions_industry_year ON emissions(industry, year);"
        )
        connection.commit()
    finally:
        connection.close()


def fetch_most_recent_year(connection: sqlite3.Connection) -> int:
    cursor = connection.cursor()
    cursor.execute("SELECT MAX(year) FROM emissions;")
    row = cursor.fetchone()
    return int(row[0]) if row and row[0] is not None else None


def fetch_totals_for_latest_year(connection: sqlite3.Connection) -> pd.DataFrame:
    query = (
        """
        WITH latest_year AS (
          SELECT MAX(year) AS year FROM emissions
        ), totals AS (
          SELECT e.industry,
                 SUM(e.emissions_mtco2e) AS total_emissions
          FROM emissions e
          JOIN latest_year ly ON e.year = ly.year
          GROUP BY e.industry
        )
        SELECT industry, total_emissions
        FROM totals
        ORDER BY total_emissions DESC;
        """
    )
    return pd.read_sql_query(query, connection)


def fetch_top5_ranked(connection: sqlite3.Connection) -> pd.DataFrame:
    query = (
        """
        WITH latest_year AS (
          SELECT MAX(year) AS year FROM emissions
        ), totals AS (
          SELECT e.industry,
                 SUM(e.emissions_mtco2e) AS total_emissions
          FROM emissions e
          JOIN latest_year ly ON e.year = ly.year
          GROUP BY e.industry
        ), ranked AS (
          SELECT industry,
                 total_emissions,
                 RANK() OVER (ORDER BY total_emissions DESC) AS emissions_rank
          FROM totals
        )
        SELECT industry, total_emissions, emissions_rank
        FROM ranked
        WHERE emissions_rank <= 5
        ORDER BY emissions_rank, industry;
        """
    )
    return pd.read_sql_query(query, connection)


def plot_top5_bar(top5_df: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(9, 5))
    sns.barplot(
        data=top5_df.sort_values("total_emissions", ascending=False),
        x="total_emissions",
        y="industry",
        palette="Reds_r",
    )
    plt.xlabel("Emissions (MtCO₂e)")
    plt.ylabel("Industry")
    plt.title("Top 5 Highest Emitting Industries (Most Recent Year)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    # Optional: display if running interactively
    # plt.show()


def write_static_report(most_recent_year: int, totals_df: pd.DataFrame, top5_df: pd.DataFrame, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / "top5_emissions.png"
    plot_top5_bar(top5_df, chart_path)

    totals_table_html = totals_df.to_html(index=False, classes="table", border=0)
    top5_table_html = top5_df.to_html(index=False, classes="table", border=0)

    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Analyzing Industry Carbon Emissions</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', Arial, sans-serif; margin: 24px; color: #111; }}
    h1, h2 {{ margin: 0 0 12px; }}
    .muted {{ color: #555; }}
    .container {{ max-width: 960px; margin: 0 auto; }}
    .card {{ background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }}
    .table {{ border-collapse: collapse; width: 100%; }}
    .table th, .table td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #eee; }}
    img {{ max-width: 100%; height: auto; border: 1px solid #eee; border-radius: 8px; }}
    code {{ background: #f6f8fa; padding: 2px 6px; border-radius: 6px; }}
  </style>
  <meta name=\"description\" content=\"SQLite + Python analysis of industry-level carbon emissions.\" />
  <meta name=\"robots\" content=\"index,follow\" />
  <link rel=\"icon\" href=\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌍</text></svg>\" />
  
</head>
<body>
  <div class=\"container\">
    <h1>Analyzing Industry Carbon Emissions</h1>
    <p class=\"muted\">Most recent year: <strong>{most_recent_year}</strong></p>

    <div class=\"card\">
      <h2>Top 5 Highest Emitting Industries</h2>
      <p class=\"muted\">Based on total MtCOe in the most recent year.</p>
      <img src=\"top5_emissions.png\" alt=\"Top 5 emissions chart\" />
      {top5_table_html}
    </div>

    <div class=\"card\">
      <h2>Totals by Industry ({most_recent_year})</h2>
      {totals_table_html}
    </div>

    <div class=\"card\">
      <h2>Reproduce Locally</h2>
      <pre><code>python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py</code></pre>
    </div>
  </div>
</body>
</html>
"""

    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

    initialize_database_with_csv(CSV_PATH, DB_PATH)

    connection = sqlite3.connect(DB_PATH)
    try:
        most_recent_year = fetch_most_recent_year(connection)
        totals_df = fetch_totals_for_latest_year(connection)
        top5_df = fetch_top5_ranked(connection)

        print(f"Most recent year: {most_recent_year}")
        print("\nTotal emissions by industry (most recent year):")
        print(totals_df.to_string(index=False))

        print("\nTop 5 highest emitting industries:")
        print(top5_df.to_string(index=False))

        # Write GitHub Pages-friendly static report under docs/
        report_index = write_static_report(most_recent_year, totals_df, top5_df, DOCS_DIR)
        print(f"\nSaved GitHub Pages report to: {report_index}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()


