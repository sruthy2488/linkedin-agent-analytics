from google.cloud import bigquery



PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

TABLE = f"{PROJECT_ID}.{DATASET_ID}.dim_lead_status"



print("=" * 60)
print("FIXING DIM_LEAD_STATUS")
print("=" * 60)


query = f"""
CREATE OR REPLACE TABLE `{TABLE}` AS

SELECT
    CAST(
        ROW_NUMBER() OVER (ORDER BY lead_status)
        AS INT64
    ) AS status_key,

    lead_status

FROM UNNEST([
    'captured',
    'contacted',
    'invite_sent',
    'connected'
]) AS lead_status
"""


client.query(query).result()


print("\ndim_lead_status rebuilt successfully.")



print("\nFinal status dimension:")

verify_query = f"""
SELECT
    status_key,
    lead_status
FROM `{TABLE}`
ORDER BY status_key
"""


for row in client.query(verify_query).result():

    print(
        f"{row.status_key} | "
        f"{row.lead_status}"
    )


print("\n" + "=" * 60)
print("STATUS DIMENSION FIX COMPLETE")
print("=" * 60)