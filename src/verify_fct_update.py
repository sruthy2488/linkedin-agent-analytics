from google.cloud import bigquery

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

query = f"""
SELECT
    name,
    lead_status,
    is_contacted,
    is_invite_sent,
    is_connected,
    is_prioritized,
    is_hot_lead,
    days_to_connection
FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads`
WHERE name = 'Incremental Test Lead'
"""

rows = client.query(query).result()

for row in rows:
    print(dict(row))