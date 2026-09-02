from google.cloud import bigquery

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

query = f"""
SELECT
    name,
    sdr_status,
    hot_score,
    prioritized,
    last_contacted,
    invite_sent_at,
    connected_at
FROM `{PROJECT_ID}.{DATASET_ID}.stg_leads`
WHERE name = 'Incremental Test Lead'
"""

rows = client.query(query).result()

for row in rows:
    print(dict(row))