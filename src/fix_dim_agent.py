from google.cloud import bigquery

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)

source = f"{PROJECT_ID}.{DATASET}.dim_agent"
temp = f"{PROJECT_ID}.{DATASET}.dim_agent_fixed"


print("=" * 60)
print("FIXING DIM_AGENT SCD TIMESTAMP TYPES")
print("=" * 60)




query = f"""
CREATE OR REPLACE TABLE `{temp}` AS

SELECT
    CAST(agent_key AS INT64) AS agent_key,
    agent_name,

    CAST(valid_from AS DATETIME) AS valid_from,

    CASE
        WHEN valid_to IS NULL
             OR TRIM(valid_to) = ''
        THEN NULL
        ELSE SAFE_CAST(valid_to AS DATETIME)
    END AS valid_to,

    CAST(is_current AS BOOL) AS is_current

FROM `{source}`
"""

client.query(query).result()

print("Temporary corrected table created.")




query = f"""
CREATE OR REPLACE TABLE `{source}` AS

SELECT
    agent_key,
    agent_name,
    valid_from,
    valid_to,
    is_current

FROM `{temp}`
"""

client.query(query).result()

print("dim_agent replaced successfully.")



table = client.get_table(source)

print()
print("Final schema:")

for field in table.schema:
    print(
        f"{field.name} | "
        f"{field.field_type} | "
        f"{field.mode}"
    )


query = f"""
SELECT *
FROM `{source}`
ORDER BY agent_key
"""

rows = list(client.query(query).result())

print()
print(f"Records preserved: {len(rows)}")

for row in rows:
    print(dict(row))


print()
print("=" * 60)
print("DIM_AGENT SCD FIX COMPLETE")
print("=" * 60)