from google.cloud import bigquery

from config import (
    FCT_LEADS_TABLE,
    DIM_DATE_TABLE,
    DIM_AGENT_TABLE,
    DIM_STATUS_TABLE,
)


def get_client():
    return bigquery.Client()


def check_table_exists(client, table_id):
    try:
        client.get_table(table_id)
        return True
    except Exception:
        return False


def check_fact_table(client):
    query = f"""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT staging_id) AS unique_ids
    FROM {FCT_LEADS_TABLE}
    """

    row = next(client.query(query).result())

    return {
        "total_rows": row.total_rows,
        "unique_ids": row.unique_ids,
        "unique_ids_match": row.total_rows == row.unique_ids,
    }


def check_orphan_dates(client):
    query = f"""
    SELECT COUNT(*) AS orphan_count
    FROM {FCT_LEADS_TABLE} f
    LEFT JOIN {DIM_DATE_TABLE} d
        ON f.date_key = d.date_key
    WHERE f.date_key IS NOT NULL
      AND d.date_key IS NULL
    """

    row = next(client.query(query).result())

    return row.orphan_count


def check_orphan_agents(client):
    query = f"""
    SELECT COUNT(*) AS orphan_count
    FROM {FCT_LEADS_TABLE} f
    LEFT JOIN {DIM_AGENT_TABLE} d
        ON f.agent_key = d.agent_key
    WHERE f.agent_key IS NOT NULL
      AND d.agent_key IS NULL
    """

    row = next(client.query(query).result())

    return row.orphan_count


def check_orphan_statuses(client):
    query = f"""
    SELECT COUNT(*) AS orphan_count
    FROM {FCT_LEADS_TABLE} f
    LEFT JOIN {DIM_STATUS_TABLE} d
        ON f.status_key = d.status_key
    WHERE f.status_key IS NOT NULL
      AND d.status_key IS NULL
    """

    row = next(client.query(query).result())

    return row.orphan_count


def validate_warehouse():
    """
    Run structural and referential integrity checks
    against the BigQuery star schema.
    """

    client = get_client()

    tables = {
        "fact": FCT_LEADS_TABLE,
        "date_dimension": DIM_DATE_TABLE,
        "agent_dimension": DIM_AGENT_TABLE,
        "status_dimension": DIM_STATUS_TABLE,
    }

    print("=" * 60)
    print("WAREHOUSE VALIDATION")
    print("=" * 60)

    all_tables_exist = True

    for name, table_id in tables.items():
        exists = check_table_exists(client, table_id)

        status = "PASS" if exists else "FAIL"

        print(f"{name:<20}: {status}")

        if not exists:
            all_tables_exist = False

    if not all_tables_exist:
        raise RuntimeError("Required warehouse tables are missing.")

    fact_result = check_fact_table(client)

    print()
    print(f"Fact rows:             {fact_result['total_rows']}")
    print(f"Unique staging IDs:    {fact_result['unique_ids']}")

    if not fact_result["unique_ids_match"]:
        raise RuntimeError("Duplicate staging IDs detected in fact table.")

    orphan_dates = check_orphan_dates(client)
    orphan_agents = check_orphan_agents(client)
    orphan_statuses = check_orphan_statuses(client)

    print(f"Orphan dates:          {orphan_dates}")
    print(f"Orphan agents:         {orphan_agents}")
    print(f"Orphan statuses:      {orphan_statuses}")

    if orphan_dates > 0:
        raise RuntimeError(
            f"Validation failed: {orphan_dates} orphan date keys."
        )

    if orphan_agents > 0:
        raise RuntimeError(
            f"Validation failed: {orphan_agents} orphan agent keys."
        )

    if orphan_statuses > 0:
        raise RuntimeError(
            f"Validation failed: {orphan_statuses} orphan status keys."
        )

    print()
    print("=" * 60)
    print("WAREHOUSE VALIDATION PASSED")
    print("=" * 60)

    return True


if __name__ == "__main__":
    validate_warehouse()
