import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


PROJECT_DIR = Path(__file__).parent
CSV_PATH = PROJECT_DIR / "emissions.csv"
DB_PATH = PROJECT_DIR / "emissions.db"


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

        output_chart = PROJECT_DIR / "top5_emissions.png"
        plot_top5_bar(top5_df, output_chart)
        print(f"\nSaved bar chart to: {output_chart}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()


