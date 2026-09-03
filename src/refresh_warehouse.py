from google.cloud import bigquery


PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"


def get_client():
    return bigquery.Client(project=PROJECT_ID)




def refresh_fct_leads(client):

    query = f"""
    CREATE OR REPLACE TABLE
    `{PROJECT_ID}.{DATASET_ID}.fct_leads` AS

    SELECT
        *,

        -- Contacted flag
        CASE
            WHEN last_contacted IS NOT NULL THEN 1
            ELSE 0
        END AS is_contacted,

        -- Invite sent flag
        CASE
            WHEN invite_sent_at IS NOT NULL THEN 1
            ELSE 0
        END AS is_invite_sent,

        -- Connected flag
        CASE
            WHEN connected_at IS NOT NULL THEN 1
            ELSE 0
        END AS is_connected,

        -- Prioritized flag
        CASE
            WHEN UPPER(TRIM(prioritized)) = 'YES' THEN 1
            ELSE 0
        END AS is_prioritized,

        -- Hot lead flag
        CASE
            WHEN hot_score IS NOT NULL
                 AND hot_score >= 50
            THEN 1
            ELSE 0
        END AS is_hot_lead,

        -- Days taken to connect
        CASE
            WHEN connected_at IS NOT NULL
                 AND added_on IS NOT NULL
            THEN DATETIME_DIFF(
                connected_at,
                added_on,
                DAY
            )
            ELSE NULL
        END AS days_to_connection,

        -- Lead status
        CASE
            WHEN sdr_status IS NOT NULL
            THEN sdr_status
            ELSE 'unknown'
        END AS lead_status

    FROM `{PROJECT_ID}.{DATASET_ID}.stg_leads`
    """

    job = client.query(query)
    job.result()

    print("fct_leads refreshed successfully.")



def refresh_analytics(client):

    

    funnel_query = f"""
    CREATE OR REPLACE VIEW
    `{PROJECT_ID}.{DATASET_ID}.analytics_lead_funnel` AS

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

        SAFE_DIVIDE(
            COUNTIF(is_connected = 1),
            COUNT(*)
        ) * 100 AS connection_rate,

        SAFE_DIVIDE(
            COUNTIF(is_invite_sent = 1),
            COUNT(*)
        ) * 100 AS invite_rate

    FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads`
    """



    print("Refreshing analytics_lead_funnel...")

    job = client.query(funnel_query)

    try:
        job.result(timeout=30)
        print("analytics_lead_funnel refreshed successfully.")

    except Exception as e:
        print(f"analytics_lead_funnel refresh failed: {e}")
        raise


    
    status_query = f"""
    CREATE OR REPLACE VIEW
    `{PROJECT_ID}.{DATASET_ID}.analytics_lead_status` AS

    SELECT

        lead_status,

        COUNT(*) AS lead_count,

        COUNTIF(is_contacted = 1)
            AS contacted_count,

        COUNTIF(is_connected = 1)
            AS connected_count,

        COUNTIF(is_hot_lead = 1)
            AS hot_lead_count

    FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads`

    GROUP BY lead_status

    ORDER BY lead_count DESC
    """

    print("Refreshing analytics_lead_status...")

    job = client.query(status_query)

    try:
        job.result(timeout=30)
        print("analytics_lead_status refreshed successfully.")
    except Exception as e:
        print(f"analytics_lead_status refresh failed: {e}")
        raise


    

    agent_query = f"""
    CREATE OR REPLACE VIEW
    `{PROJECT_ID}.{DATASET_ID}.analytics_agent_performance` AS

    SELECT

        agent,

        COUNT(*) AS total_leads,

        COUNTIF(is_contacted = 1)
            AS contacted_leads,

        COUNTIF(is_invite_sent = 1)
            AS invite_sent_leads,

        COUNTIF(is_connected = 1)
            AS connected_leads,

        COUNTIF(is_hot_lead = 1)
            AS hot_leads,

        SAFE_DIVIDE(
            COUNTIF(is_connected = 1),
            COUNT(*)
        ) * 100 AS connection_rate

    FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads`

    GROUP BY agent

    ORDER BY total_leads DESC
    """

    print("Refreshing analytics_agent_performance...")

    job = client.query(agent_query)

    try:
        job.result(timeout=30)
        print("analytics_agent_performance refreshed successfully.")
    except Exception as e:
        print(f"analytics_agent_performance refresh failed: {e}")
        raise




def refresh_warehouse():

    client = get_client()

    print("\nRefreshing warehouse...")

    refresh_fct_leads(client)

    refresh_analytics(client)

    print("\nWarehouse refresh completed successfully.")




if __name__ == "__main__":

    refresh_warehouse()