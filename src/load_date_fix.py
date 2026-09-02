from google.cloud import bigquery

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

table_id = f"{PROJECT_ID}.{DATASET_ID}.dim_date"
csv_file = r"..\data\date_fix.csv"

print("=" * 60)
print("LOADING MISSING DATE RECORDS")
print("=" * 60)

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    autodetect=False,
    schema=[
        bigquery.SchemaField("date_key", "INT64"),
        bigquery.SchemaField("full_date", "DATE"),
        bigquery.SchemaField("year", "INT64"),
        bigquery.SchemaField("month", "INT64"),
        bigquery.SchemaField("month_name", "STRING"),
        bigquery.SchemaField("quarter", "INT64"),
    ],
)

with open(csv_file, "rb") as f:
    job = client.load_table_from_file(
        f,
        table_id,
        job_config=job_config
    )

job.result()

print("Missing dates loaded successfully.")
print("=" * 60)