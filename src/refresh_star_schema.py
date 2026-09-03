from google.cloud import bigquery

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

STAGING_TABLE = f"{PROJECT_ID}.{DATASET_ID}.stg_leads"
FACT_TABLE = f"{PROJECT_ID}.{DATASET_ID}.fct_leads_star"

DIM_AGENT = f"{PROJECT_ID}.{DATASET_ID}.dim_agent"
DIM_STATUS = f"{PROJECT_ID}.{DATASET_ID}.dim_lead_status"
DIM_DATE = f"{PROJECT_ID}.{DATASET_ID}.dim_date"


def refresh_star_schema():

    print("=" * 60)
    print("STAR SCHEMA REFRESH")
    print("=" * 60)

    query = f"""
    CREATE OR REPLACE TABLE `{FACT_TABLE}` AS

    SELECT

        s.staging_id,

        s.name,
        s.job_title,
        s.company,
        s.industry,
        s.location,

        s.agent,

        s.sdr_status,
        s.comment_status,
        s.hot_score,
        s.source,
        s.prioritized,
        s.linkedin_url,

        s.added_on,
        s.last_contacted,
        s.invite_sent_at,
        s.connected_at,
        s.record_updated_at,
        s.load_timestamp,

        -- -------------------------------------------------
        -- Fact flags
        -- -------------------------------------------------

        CASE
            WHEN s.last_contacted IS NOT NULL
            THEN 1
            ELSE 0
        END AS is_contacted,

        CASE
            WHEN s.invite_sent_at IS NOT NULL
            THEN 1
            ELSE 0
        END AS is_invite_sent,

        CASE
            WHEN s.connected_at IS NOT NULL
            THEN 1
            ELSE 0
        END AS is_connected,

        CASE
            WHEN LOWER(TRIM(s.prioritized)) = 'yes'
            THEN 1
            ELSE 0
        END AS is_prioritized,

        CASE
            WHEN s.hot_score IS NOT NULL
                 AND s.hot_score >= 70
            THEN 1
            ELSE 0
        END AS is_hot_lead,

        -- -------------------------------------------------
        -- Days to connection
        -- -------------------------------------------------

        CASE
            WHEN s.invite_sent_at IS NOT NULL
                 AND s.connected_at IS NOT NULL
            THEN DATE_DIFF(
                DATE(s.connected_at),
                DATE(s.invite_sent_at),
                DAY
            )
            ELSE NULL
        END AS days_to_connection,

        -- -------------------------------------------------
        -- Lead status
        -- -------------------------------------------------

        CASE
            WHEN s.connected_at IS NOT NULL
                THEN 'connected'

            WHEN s.invite_sent_at IS NOT NULL
                THEN 'invite_sent'

            WHEN s.last_contacted IS NOT NULL
                THEN 'contacted'

            ELSE 'captured'
        END AS lead_status,

        -- -------------------------------------------------
        -- Dimension keys
        -- -------------------------------------------------

        a.agent_key,

        st.status_key,

        d.date_key

    FROM `{STAGING_TABLE}` s

    LEFT JOIN `{DIM_AGENT}` a
        ON s.agent = a.agent_name
        AND a.is_current = TRUE

    LEFT JOIN `{DIM_STATUS}` st
        ON
        (
            CASE
                WHEN s.connected_at IS NOT NULL
                    THEN 'connected'

                WHEN s.invite_sent_at IS NOT NULL
                    THEN 'invite_sent'

                WHEN s.last_contacted IS NOT NULL
                    THEN 'contacted'

                ELSE 'captured'
            END
        ) = st.lead_status

    LEFT JOIN `{DIM_DATE}` d
        ON DATE(s.added_on) = d.full_date
    """
    ensure_dim_date()

    print("\nRefreshing fct_leads_star...")

    job = client.query(query)
    job.result()

    print("fct_leads_star refreshed successfully.")
    validate_star_schema()


def ensure_dim_date():
    """
    Rebuild dim_date from the dates present in staging.
    Uses CREATE OR REPLACE TABLE instead of DML so it works
    without billing-enabled BigQuery.
    """
    query = f"""
    CREATE OR REPLACE TABLE `{DIM_DATE}` AS

    SELECT
        CAST(FORMAT_DATE('%Y%m%d', full_date) AS INT64) AS date_key,
        full_date,
        EXTRACT(YEAR FROM full_date) AS year,
        EXTRACT(MONTH FROM full_date) AS month,
        FORMAT_DATE('%B', full_date) AS month_name,
        EXTRACT(QUARTER FROM full_date) AS quarter,
        EXTRACT(DAY FROM full_date) AS day_of_month,
        FORMAT_DATE('%A', full_date) AS day_of_week
    FROM (
        SELECT DISTINCT
            DATE(added_on) AS full_date
        FROM `{STAGING_TABLE}`
        WHERE added_on IS NOT NULL
    )
    ORDER BY full_date
    """

    print("\nEnsuring dim_date is up to date...")
    job = client.query(query)
    job.result()
    print("dim_date updated successfully.")

def validate_star_schema():

    print("\nValidating Star Schema...")

    validation_query = f"""
    SELECT

        COUNT(*) AS fact_rows,

        COUNT(DISTINCT staging_id) AS unique_staging_ids,

        COUNTIF(agent_key IS NULL) AS orphan_agents,

        COUNTIF(status_key IS NULL) AS orphan_statuses,

        COUNTIF(date_key IS NULL) AS orphan_dates

    FROM `{FACT_TABLE}`
    """

    result = list(client.query(validation_query).result())[0]

    print()
    print(f"Fact rows:              {result.fact_rows}")
    print(f"Unique staging IDs:     {result.unique_staging_ids}")
    print(f"Orphan agents:          {result.orphan_agents}")
    print(f"Orphan statuses:        {result.orphan_statuses}")
    print(f"Orphan dates:           {result.orphan_dates}")

    if result.fact_rows != result.unique_staging_ids:
        raise RuntimeError(
            "Star Schema validation failed: duplicate staging IDs."
        )

    if result.orphan_agents > 0:
        raise RuntimeError(
            "Star Schema validation failed: orphan agent keys."
        )

    if result.orphan_statuses > 0:
        raise RuntimeError(
            "Star Schema validation failed: orphan status keys."
        )

    if result.orphan_dates > 0:
        raise RuntimeError(
            "Star Schema validation failed: orphan date keys."
        )

    print("\nStar Schema validation PASSED.")




if __name__ == "__main__":

    try:

        refresh_star_schema()

        validate_star_schema()

        print()
        print("=" * 60)
        print("STAR SCHEMA REFRESH COMPLETE")
        print("=" * 60)

    except Exception as e:

        print()
        print("=" * 60)
        print("STAR SCHEMA REFRESH FAILED")
        print("=" * 60)

        print(f"\nError: {e}")

        raise