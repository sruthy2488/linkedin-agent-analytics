from google.cloud import bigquery


PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"
TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.dead_letter_leads"


client = bigquery.Client(project=PROJECT_ID)


schema = [
    bigquery.SchemaField("staging_id", "STRING"),
    bigquery.SchemaField("name", "STRING"),
    bigquery.SchemaField("job_title", "STRING"),
    bigquery.SchemaField("company", "STRING"),
    bigquery.SchemaField("industry", "STRING"),
    bigquery.SchemaField("location", "STRING"),
    bigquery.SchemaField("agent", "STRING"),
    bigquery.SchemaField("sdr_status", "STRING"),
    bigquery.SchemaField("comment_status", "STRING"),
    bigquery.SchemaField("hot_score", "FLOAT"),
    bigquery.SchemaField("source", "STRING"),
    bigquery.SchemaField("prioritized", "STRING"),
    bigquery.SchemaField("linkedin_url", "STRING"),
    bigquery.SchemaField("added_on", "DATETIME"),
    bigquery.SchemaField("last_contacted", "DATETIME"),
    bigquery.SchemaField("invite_sent_at", "DATETIME"),
    bigquery.SchemaField("connected_at", "DATETIME"),
    bigquery.SchemaField("record_updated_at", "DATETIME"),
    bigquery.SchemaField("load_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("error_reason", "STRING"),
    bigquery.SchemaField("dead_letter_run_id", "STRING"),
    bigquery.SchemaField("dead_letter_timestamp", "TIMESTAMP"),
]


table = bigquery.Table(
    TABLE_ID,
    schema=schema
)

table = client.create_table(table)

print(
    f"Created table: {table.full_table_id}"
)