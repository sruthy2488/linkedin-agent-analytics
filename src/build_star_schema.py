from google.cloud import bigquery
from datetime import datetime, timezone

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

print("=" * 70)
print("STAR SCHEMA BUILD")
print("=" * 70)


# ============================================================
# 1. CREATE FINAL STAR FACT TABLE
# ============================================================

create_fact_sql = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.fact_leads` AS

SELECT
    f.staging_id,

    -- Dimension keys
    f.agent_key,
    f.status_key,
    f.date_key,

    -- Degenerate / descriptive attributes
    f.name,
    f.job_title,
    f.company,
    f.industry,
    f.location,
    f.comment_status,
    f.hot_score,
    f.source,
    f.prioritized,
    f.linkedin_url,

    -- Dates
    f.added_on,
    f.last_contacted,
    f.invite_sent_at,
    f.connected_at,
    f.record_updated_at,
    f.load_timestamp,

    -- Measures / flags
    f.is_contacted,
    f.is_invite_sent,
    f.is_connected,
    f.is_prioritized,
    f.is_hot_lead,
    f.days_to_connection

FROM `{PROJECT_ID}.{DATASET}.fct_leads_star` f
"""

print("\nCreating fact_leads...")

client.query(create_fact_sql).result()

print("fact_leads created successfully.")


# ============================================================
# 2. CREATE VIEW FOR ANALYTICS
# ============================================================

create_view_sql = f"""
CREATE OR REPLACE VIEW
`{PROJECT_ID}.{DATASET}.vw_leads_analytics`
AS

SELECT

    -- Lead information
    f.staging_id,
    f.name,
    f.job_title,
    f.company,
    f.industry,
    f.location,

    -- Agent dimension
    a.agent_key,
    a.agent_name,

    -- Status dimension
    s.status_key,
    s.lead_status,

    -- Date dimension
    d.date_key,
    d.full_date,
    d.year,
    d.month,
    d.month_name,
    d.quarter,
    d.day_of_month,
    d.day_of_week,

    -- Lead attributes
    f.comment_status,
    f.hot_score,
    f.source,
    f.prioritized,
    f.linkedin_url,

    -- Dates
    f.added_on,
    f.last_contacted,
    f.invite_sent_at,
    f.connected_at,
    f.record_updated_at,

    -- Measures
    f.is_contacted,
    f.is_invite_sent,
    f.is_connected,
    f.is_prioritized,
    f.is_hot_lead,
    f.days_to_connection

FROM `{PROJECT_ID}.{DATASET}.fact_leads` f

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_agent` a
    ON f.agent_key = a.agent_key

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_lead_status` s
    ON f.status_key = s.status_key

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_date` d
    ON f.date_key = d.date_key
"""

print("\nCreating analytics view...")

client.query(create_view_sql).result()

print("vw_leads_analytics created successfully.")


# ============================================================
# 3. VALIDATE ROW COUNT
# ============================================================

count_sql = f"""
SELECT COUNT(*) AS total
FROM `{PROJECT_ID}.{DATASET}.fact_leads`
"""

row_count = list(client.query(count_sql).result())[0].total

print(f"\nFact rows: {row_count}")


# ============================================================
# 4. VALIDATE ORPHAN DIMENSION KEYS
# ============================================================

validation_sql = f"""
SELECT

    COUNTIF(a.agent_key IS NULL) AS orphan_agents,

    COUNTIF(s.status_key IS NULL) AS orphan_statuses,

    COUNTIF(d.date_key IS NULL) AS orphan_dates

FROM `{PROJECT_ID}.{DATASET}.fact_leads` f

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_agent` a
    ON f.agent_key = a.agent_key

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_lead_status` s
    ON f.status_key = s.status_key

LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_date` d
    ON f.date_key = d.date_key
"""

validation = list(client.query(validation_sql).result())[0]

print("\nStar Schema Validation")
print("-" * 40)

print(f"Orphan agents:  {validation.orphan_agents}")
print(f"Orphan statuses: {validation.orphan_statuses}")
print(f"Orphan dates:    {validation.orphan_dates}")



if (
    validation.orphan_agents == 0
    and validation.orphan_statuses == 0
    and validation.orphan_dates == 0
):

    print("\nStar schema validation: PASS")

else:

    print("\nStar schema validation: FAIL")


print("\n" + "=" * 70)
print("STAR SCHEMA BUILD COMPLETE")
print("=" * 70)