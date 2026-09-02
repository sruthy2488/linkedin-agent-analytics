from google.cloud import bigquery

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

print("=" * 60)
print("FIXING DIM_DATE")
print("=" * 60)

query = f"""
CREATE OR REPLACE TABLE
`{PROJECT_ID}.{DATASET_ID}.dim_date` AS

WITH date_range AS (
    SELECT
        MIN(DATE(record_updated_at)) AS min_date,
        MAX(DATE(record_updated_at)) AS max_date
    FROM `{PROJECT_ID}.{DATASET_ID}.stg_leads`
),

dates AS (
    SELECT date_value
    FROM date_range,
    UNNEST(
        GENERATE_DATE_ARRAY(min_date, max_date)
    ) AS date_value
)

SELECT
    CAST(FORMAT_DATE('%Y%m%d', date_value) AS INT64) AS date_key,
    date_value AS full_date,
    EXTRACT(YEAR FROM date_value) AS year,
    EXTRACT(MONTH FROM date_value) AS month,
    FORMAT_DATE('%B', date_value) AS month_name,
    EXTRACT(QUARTER FROM date_value) AS quarter,
    EXTRACT(DAY FROM date_value) AS day,
    FORMAT_DATE('%A', date_value) AS day_name,
    EXTRACT(WEEK FROM date_value) AS week

FROM dates

ORDER BY date_value
"""

client.query(query).result()

print("dim_date rebuilt successfully.")

verify_query = f"""
SELECT
    MIN(full_date) AS min_date,
    MAX(full_date) AS max_date,
    COUNT(*) AS dates
FROM `{PROJECT_ID}.{DATASET_ID}.dim_date`
"""

row = next(client.query(verify_query).result())

print()
print("Final date dimension:")
print(f"Min date:   {row.min_date}")
print(f"Max date:   {row.max_date}")
print(f"Total dates: {row.dates}")

print()
print("=" * 60)
print("DATE DIMENSION FIX COMPLETE")
print("=" * 60)