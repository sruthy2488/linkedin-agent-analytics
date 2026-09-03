from google.cloud import bigquery


PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

FACT_TABLE = f"{PROJECT_ID}.{DATASET_ID}.fct_leads"
DIM_TABLE = f"{PROJECT_ID}.{DATASET_ID}.dim_lead_status"


def get_client():
    return bigquery.Client(project=PROJECT_ID)


def normalize_status(status):
    """
    Normalize status values so that equivalent values such as
    'invite sent' and 'invite_sent' are treated consistently.
    """
    if status is None:
        return None

    status = str(status).strip().lower()

    replacements = {
        "invite sent": "invite_sent",
        "linkedin rate limited": "linkedin_rate_limited",
    }

    return replacements.get(status, status)


def refresh_status_dimension():
    client = get_client()

    print("=" * 70)
    print("REFRESHING LEAD STATUS DIMENSION")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Read existing dimension
    # ---------------------------------------------------------
    existing_query = f"""
        SELECT
            status_key,
            lead_status
        FROM `{DIM_TABLE}`
        ORDER BY status_key
    """

    existing_rows = list(client.query(existing_query).result())

    existing = {}

    for row in existing_rows:
        normalized = normalize_status(row.lead_status)

        if normalized:
            existing[normalized] = int(row.status_key)

    print(f"Existing dimension statuses: {len(existing)}")

    # ---------------------------------------------------------
    # 2. Read every status currently used by the fact table
    # ---------------------------------------------------------
    fact_query = f"""
        SELECT DISTINCT
            LOWER(TRIM(lead_status)) AS lead_status
        FROM `{FACT_TABLE}`
        WHERE lead_status IS NOT NULL
    """

    fact_rows = list(client.query(fact_query).result())

    fact_statuses = set()

    for row in fact_rows:
        normalized = normalize_status(row.lead_status)

        if normalized:
            fact_statuses.add(normalized)

    print(f"Fact table statuses: {len(fact_statuses)}")

    # ---------------------------------------------------------
    # 3. Add missing statuses
    # ---------------------------------------------------------
    next_key = max(existing.values(), default=0) + 1

    for status in sorted(fact_statuses):
        if status not in existing:
            existing[status] = next_key
            next_key += 1

    # ---------------------------------------------------------
    # 4. Build dimension rows
    # ---------------------------------------------------------
    dimension_rows = [
        {
            "status_key": key,
            "lead_status": status,
        }
        for status, key in existing.items()
    ]

    dimension_rows.sort(key=lambda x: x["status_key"])

    print("\nFinal dimension:")
    for row in dimension_rows:
        print(
            f"  {row['status_key']:>3}  {row['lead_status']}"
        )

    # ---------------------------------------------------------
    # 5. Replace dimension table
    # ---------------------------------------------------------
    schema = [
        bigquery.SchemaField(
            "status_key",
            "INT64",
            mode="REQUIRED",
        ),
        bigquery.SchemaField(
            "lead_status",
            "STRING",
            mode="REQUIRED",
        ),
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_json(
        dimension_rows,
        DIM_TABLE,
        job_config=job_config,
    )

    job.result()

    print("\nStatus dimension refreshed successfully.")
    print(f"Rows: {len(dimension_rows)}")

    # ---------------------------------------------------------
    # 6. Validate all fact statuses have a dimension key
    # ---------------------------------------------------------
    validation_query = f"""
    SELECT COUNT(*) AS unmatched_rows
    FROM `{FACT_TABLE}` f
    LEFT JOIN `{DIM_TABLE}` d
        ON REPLACE(
            LOWER(TRIM(f.lead_status)),
            ' ',
            '_'
        ) =
        LOWER(TRIM(d.lead_status))
    WHERE d.status_key IS NULL
"""

    validation_result = list(
        client.query(validation_query).result()
    )[0]

    unmatched = int(validation_result.unmatched_rows)

    print(f"\nUnmatched fact rows: {unmatched}")

    if unmatched > 0:
        raise RuntimeError(
            f"Status dimension validation failed: "
            f"{unmatched} fact rows remain unmatched."
        )

    print("Status dimension validation PASSED.")

    return True


if __name__ == "__main__":
    refresh_status_dimension()