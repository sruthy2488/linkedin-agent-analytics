from google.cloud import bigquery


PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)



print("Creating analytics_star_funnel...")

funnel_query = f"""
CREATE OR REPLACE VIEW
`{PROJECT_ID}.{DATASET_ID}.analytics_star_funnel` AS

SELECT

    COUNT(*) AS total_leads,

    COUNTIF(is_contacted = 1)
        AS contacted_leads,

    COUNTIF(is_invite_sent = 1)
        AS invite_sent_leads,

    COUNTIF(is_connected = 1)
        AS connected_leads,

    COUNTIF(is_hot_lead = 1)
        AS hot_leads,

    ROUND(
        SAFE_DIVIDE(
            COUNTIF(is_contacted = 1),
            COUNT(*)
        ) * 100,
        2
    ) AS contact_rate,

    ROUND(
        SAFE_DIVIDE(
            COUNTIF(is_invite_sent = 1),
            COUNT(*)
        ) * 100,
        2
    ) AS invite_rate,

    ROUND(
        SAFE_DIVIDE(
            COUNTIF(is_connected = 1),
            COUNT(*)
        ) * 100,
        2
    ) AS connection_rate

FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads_star`
"""

client.query(funnel_query).result()

print("analytics_star_funnel created.")



print("Creating analytics_star_agent_performance...")

agent_query = f"""
CREATE OR REPLACE VIEW
`{PROJECT_ID}.{DATASET_ID}.analytics_star_agent_performance` AS

SELECT

    a.agent_key,

    a.agent_name,

    COUNT(f.staging_id) AS total_leads,

    COUNTIF(f.is_contacted = 1)
        AS contacted_leads,

    COUNTIF(f.is_invite_sent = 1)
        AS invite_sent_leads,

    COUNTIF(f.is_connected = 1)
        AS connected_leads,

    COUNTIF(f.is_hot_lead = 1)
        AS hot_leads,

    ROUND(
        SAFE_DIVIDE(
            COUNTIF(f.is_connected = 1),
            COUNT(*)
        ) * 100,
        2
    ) AS connection_rate,

    ROUND(
        SAFE_DIVIDE(
            COUNTIF(f.is_hot_lead = 1),
            COUNT(*)
        ) * 100,
        2
    ) AS hot_lead_rate

FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads_star` f

JOIN `{PROJECT_ID}.{DATASET_ID}.dim_agent` a
    ON f.agent_key = a.agent_key

GROUP BY
    a.agent_key,
    a.agent_name

ORDER BY total_leads DESC
"""

client.query(agent_query).result()

print("analytics_star_agent_performance created.")



print("Creating analytics_star_status...")

status_query = f"""
CREATE OR REPLACE VIEW
`{PROJECT_ID}.{DATASET_ID}.analytics_star_status` AS

SELECT

    s.status_key,

    s.lead_status,

    COUNT(f.staging_id) AS lead_count,

    COUNTIF(f.is_contacted = 1)
        AS contacted_count,

    COUNTIF(f.is_invite_sent = 1)
        AS invite_sent_count,

    COUNTIF(f.is_connected = 1)
        AS connected_count,

    COUNTIF(f.is_hot_lead = 1)
        AS hot_lead_count

FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads_star` f

JOIN `{PROJECT_ID}.{DATASET_ID}.dim_lead_status` s
    ON f.status_key = s.status_key

GROUP BY
    s.status_key,
    s.lead_status

ORDER BY lead_count DESC
"""

client.query(status_query).result()

print("analytics_star_status created.")




print("Creating analytics_star_daily_trend...")

daily_query = f"""
CREATE OR REPLACE VIEW
`{PROJECT_ID}.{DATASET_ID}.analytics_star_daily_trend` AS

SELECT

    d.date_key,

    d.full_date,

    d.year,

    d.month,

    d.month_name,

    d.quarter,

    COUNT(f.staging_id) AS total_leads,

    COUNTIF(f.is_contacted = 1)
        AS contacted_leads,

    COUNTIF(f.is_invite_sent = 1)
        AS invite_sent_leads,

    COUNTIF(f.is_connected = 1)
        AS connected_leads,

    COUNTIF(f.is_hot_lead = 1)
        AS hot_leads

FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads_star` f

JOIN `{PROJECT_ID}.{DATASET_ID}.dim_date` d
    ON f.date_key = d.date_key

GROUP BY

    d.date_key,
    d.full_date,
    d.year,
    d.month,
    d.month_name,
    d.quarter

ORDER BY d.full_date
"""

client.query(daily_query).result()

print("analytics_star_daily_trend created.")



print()
print("=" * 60)
print("STAR ANALYTICS VIEWS CREATED SUCCESSFULLY")
print("=" * 60)