-- Analyzing Industry Carbon Emissions (SQLite)
-- This script creates the schema, imports the CSV, and runs analysis queries.
-- Usage (from project directory):
--   sqlite3 emissions.db ".read emissions_analysis.sql"
-- Make sure `emissions.csv` is present in the same directory.

-- 0) Clean slate and create table
DROP TABLE IF EXISTS emissions;
CREATE TABLE emissions (
  industry TEXT NOT NULL,
  year INTEGER NOT NULL,
  emissions_mtco2e REAL NOT NULL
);

-- 1) Import CSV into the `emissions` table (SQLite CLI dot-commands)
.mode csv
.import --skip 1 'emissions.csv' emissions

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_emissions_year ON emissions(year);
CREATE INDEX IF NOT EXISTS idx_emissions_industry_year ON emissions(industry, year);

-- 2) Find the most recent year in the dataset
SELECT MAX(year) AS most_recent_year FROM emissions;

-- 3) Calculate total emissions per industry for the most recent year
WITH latest_year AS (
  SELECT MAX(year) AS year FROM emissions
), totals AS (
  SELECT e.industry,
         SUM(e.emissions_mtco2e) AS total_emissions
  FROM emissions e
  JOIN latest_year ly ON e.year = ly.year
  GROUP BY e.industry
)
SELECT *
FROM totals
ORDER BY total_emissions DESC;

-- 4) Rank industries by emissions (most recent year)
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
SELECT *
FROM ranked
ORDER BY emissions_rank, industry;

-- 5) Show the top 5 highest emitting industries (most recent year)
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


