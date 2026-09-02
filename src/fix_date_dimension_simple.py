from google.cloud import bigquery
from datetime import timedelta

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

print("=" * 60)
print("FIXING DATE DIMENSION")
print("=" * 60)



query = f"""
SELECT
    MIN(DATE(record_updated_at)) AS min_date,
    MAX(DATE(record_updated_at)) AS max_date
FROM `{PROJECT_ID}.{DATASET_ID}.stg_leads`
"""

row = next(client.query(query).result())

min_date = row.min_date
max_date = row.max_date

print(f"Required date range: {min_date} -> {max_date}")




query = f"""
SELECT full_date
FROM `{PROJECT_ID}.{DATASET_ID}.dim_date`
"""

existing_dates = {
    row.full_date
    for row in client.query(query).result()
}

print(f"Existing dates: {len(existing_dates)}")




missing_dates = []

current = min_date

while current <= max_date:

    if current not in existing_dates:
        missing_dates.append(current)

    current += timedelta(days=1)

print(f"Missing dates: {len(missing_dates)}")


# ---------------------------------------------------------
# Insert missing dates
# ---------------------------------------------------------

if not missing_dates:

    print("No missing dates.")

else:

    rows = []

    for d in missing_dates:

        rows.append({
            "date_key": int(d.strftime("%Y%m%d")),
            "full_date": str(d),
            "year": d.year,
            "month": d.month,
            "month_name": d.strftime("%B"),
            "quarter": ((d.month - 1) // 3) + 1
        })

    table_id = f"{PROJECT_ID}.{DATASET_ID}.dim_date"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND"
    )

    job = client.load_table_from_json(
        rows,
        table_id,
        job_config=job_config
    )

    job.result()

    print("Missing dates inserted successfully.")



print("\nFinal date dimension:")

query = f"""
SELECT *
FROM `{PROJECT_ID}.{DATASET_ID}.dim_date`
ORDER BY full_date
"""

for row in client.query(query).result():

    print(
        row.date_key,
        "|",
        row.full_date,
        "|",
        row.year,
        "|",
        row.month,
        "|",
        row.month_name,
        "| Q",
        row.quarter
    )


print("\n" + "=" * 60)
print("DATE DIMENSION FIX COMPLETE")
print("=" * 60)