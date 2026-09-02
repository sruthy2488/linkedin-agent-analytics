from google.cloud import bigquery

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"

client = bigquery.Client(project=PROJECT_ID)

queries = {

    "lead_funnel": """
    CREATE OR REPLACE VIEW
    linkedin_agent_analytics.analytics_lead_funnel AS

    SELECT
        COUNT(*) AS total_leads,

        COUNTIF(is_contacted = 1) AS contacted_leads,

        COUNTIF(is_invite_sent = 1) AS invite_sent_leads,

        COUNTIF(is_connected = 1) AS connected_leads,

        COUNTIF(is_prioritized = 1) AS prioritized_leads,

        COUNTIF(is_hot_lead = 1) AS hot_leads

    FROM linkedin_agent_analytics.fct_leads
    """,

    "lead_status": """
    CREATE OR REPLACE VIEW
    linkedin_agent_analytics.analytics_lead_status AS

    SELECT
        lead_status,
        COUNT(*) AS lead_count

    FROM linkedin_agent_analytics.fct_leads

    GROUP BY lead_status

    ORDER BY lead_count DESC
    """,

    "agent_performance": """
    CREATE OR REPLACE VIEW
    linkedin_agent_analytics.analytics_agent_performance AS

    SELECT
        agent,

        COUNT(*) AS total_leads,

        COUNTIF(is_contacted = 1) AS contacted,

        COUNTIF(is_invite_sent = 1) AS invites_sent,

        COUNTIF(is_connected = 1) AS connected,

        COUNTIF(is_hot_lead = 1) AS hot_leads,

        COUNTIF(is_prioritized = 1) AS prioritized

    FROM linkedin_agent_analytics.fct_leads

    GROUP BY agent

    ORDER BY total_leads DESC
    """
}


for name, query in queries.items():

    print(f"Creating {name}...")

    client.query(query).result()

    print(f"{name} created successfully.")


print("\nAnalytics layer created successfully.")