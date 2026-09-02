from google.cloud import bigquery


PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)


def run_query(query):
    return list(client.query(query).result())


print("=" * 70)
print("STAR SCHEMA VERIFICATION")
print("=" * 70)




print("\n1. Checking required tables...")

required_tables = [
    "fct_leads_star",
    "dim_agent",
    "dim_lead_status",
    "dim_date"
]

tables = list(
    client.query(
        f"""
        SELECT table_name
        FROM `{PROJECT_ID}.{DATASET}.INFORMATION_SCHEMA.TABLES`
        """
    ).result()
)

existing_tables = {row.table_name for row in tables}

for table in required_tables:
    if table in existing_tables:
        print(f"  [PASS] {table}")
    else:
        print(f"  [FAIL] {table}")




print("\n2. Fact table checks...")

fact_rows = run_query(
    f"""
    SELECT COUNT(*) AS total
    FROM `{PROJECT_ID}.{DATASET}.fct_leads_star`
    """
)[0].total

print(f"  Fact rows: {fact_rows}")

if fact_rows > 0:
    print("  [PASS] Fact table contains records")
else:
    print("  [FAIL] Fact table is empty")



duplicate_rows = run_query(
    f"""
    SELECT COUNT(*) AS duplicates
    FROM (
        SELECT staging_id
        FROM `{PROJECT_ID}.{DATASET}.fct_leads_star`
        GROUP BY staging_id
        HAVING COUNT(*) > 1
    )
    """
)[0].duplicates

print(f"  Duplicate staging IDs: {duplicate_rows}")

if duplicate_rows == 0:
    print("  [PASS] No duplicate fact records")
else:
    print("  [FAIL] Duplicate fact records found")




orphan_agents = run_query(
    f"""
    SELECT COUNT(*) AS total
    FROM `{PROJECT_ID}.{DATASET}.fct_leads_star` f
    LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_agent` d
        ON f.agent_key = d.agent_key
    WHERE d.agent_key IS NULL
    """
)[0].total

print(f"  Orphan agent keys: {orphan_agents}")

if orphan_agents == 0:
    print("  [PASS] Agent relationships valid")
else:
    print("  [FAIL] Orphan agent keys found")




orphan_statuses = run_query(
    f"""
    SELECT COUNT(*) AS total
    FROM `{PROJECT_ID}.{DATASET}.fct_leads_star` f
    LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_lead_status` d
        ON f.status_key = d.status_key
    WHERE d.status_key IS NULL
    """
)[0].total

print(f"  Orphan status keys: {orphan_statuses}")

if orphan_statuses == 0:
    print("  [PASS] Status relationships valid")
else:
    print("  [FAIL] Orphan status keys found")



orphan_dates = run_query(
    f"""
    SELECT COUNT(*) AS total
    FROM `{PROJECT_ID}.{DATASET}.fct_leads_star` f
    LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_date` d
        ON f.date_key = d.date_key
    WHERE d.date_key IS NULL
    """
)[0].total

print(f"  Orphan date keys: {orphan_dates}")

if orphan_dates == 0:
    print("  [PASS] Date relationships valid")
else:
    print("  [FAIL] Orphan date keys found")



print("\n3. Checking SCD Type 2 structure...")

scd_rows = run_query(
    f"""
    SELECT
        COUNT(*) AS total,
        COUNTIF(is_current = TRUE) AS current_rows,
        COUNTIF(valid_from IS NOT NULL) AS valid_from_rows
    FROM `{PROJECT_ID}.{DATASET}.dim_agent`
    """
)[0]

print(f"  Agent dimension rows: {scd_rows.total}")
print(f"  Current records: {scd_rows.current_rows}")
print(f"  Records with valid_from: {scd_rows.valid_from_rows}")

if (
    scd_rows.total > 0
    and scd_rows.current_rows > 0
    and scd_rows.valid_from_rows == scd_rows.total
):
    print("  [PASS] SCD structure valid")
else:
    print("  [FAIL] SCD structure needs review")




print("\n4. Dimension table counts...")

agent_count = run_query(
    f"""
    SELECT COUNT(*) AS total
    FROM `{PROJECT_ID}.{DATASET}.dim_agent`
    """
)[0].total

status_count = run_query(
    f"""
    SELECT COUNT(*) AS total
    FROM `{PROJECT_ID}.{DATASET}.dim_lead_status`
    """
)[0].total

date_count = run_query(
    f"""
    SELECT COUNT(*) AS total
    FROM `{PROJECT_ID}.{DATASET}.dim_date`
    """
)[0].total

print(f"  dim_agent:       {agent_count}")
print(f"  dim_lead_status: {status_count}")
print(f"  dim_date:        {date_count}")




print("\n" + "=" * 70)

failed = (
    duplicate_rows > 0
    or orphan_agents > 0
    or orphan_statuses > 0
    or orphan_dates > 0
    or fact_rows == 0
)

if failed:
    print("STAR SCHEMA VERIFICATION: FAILED")
    print("Review the failed checks above.")
else:
    print("STAR SCHEMA VERIFICATION: PASSED")
    print("Fact and dimension relationships are valid.")

print("=" * 70)