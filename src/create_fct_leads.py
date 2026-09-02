from google.cloud import bigquery

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.fct_leads` AS

SELECT
    *,
    
    CASE
        WHEN last_contacted IS NOT NULL THEN 1
        ELSE 0
    END AS is_contacted,

    CASE
        WHEN invite_sent_at IS NOT NULL THEN 1
        ELSE 0
    END AS is_invite_sent,

    CASE
        WHEN connected_at IS NOT NULL THEN 1
        ELSE 0
    END AS is_connected,

    CASE
        WHEN UPPER(TRIM(prioritized)) = 'YES' THEN 1
        ELSE 0
    END AS is_prioritized,

    CASE
        WHEN hot_score IS NOT NULL
             AND hot_score >= 50
        THEN 1
        ELSE 0
    END AS is_hot_lead,

    CASE
        WHEN connected_at IS NOT NULL
             AND added_on IS NOT NULL
        THEN DATETIME_DIFF(connected_at, added_on, DAY)
        ELSE NULL
    END AS days_to_connection,

    CASE
        WHEN sdr_status IS NOT NULL THEN sdr_status
        ELSE 'unknown'
    END AS lead_status

FROM `{PROJECT_ID}.{DATASET}.stg_leads`
"""

job = client.query(query)
job.result()

print("fct_leads created successfully.")