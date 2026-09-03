from google.cloud import bigquery
import pandas as pd


PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"


def get_client():
    """
    Create the BigQuery client only when the function is called.

    This prevents pytest/GitHub Actions from requiring GCP
    credentials just because this module is imported.
    """
    return bigquery.Client(project=PROJECT_ID)


def refresh_star_schema():
    """
    Refresh fct_leads_star by joining the fact table with:
      - dim_agent
      - dim_lead_status
      - dim_date

    Also performs referential-integrity validation before
    replacing the target table.
    """

    client = get_client()

    print("=" * 70)
    print("STAR SCHEMA REFRESH")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Load fact table
    # ---------------------------------------------------------
    print("\nLoading fact table...")

    fact_query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads`
    """

    fact_df = client.query(fact_query).to_dataframe()

    print(f"Fact rows loaded: {len(fact_df)}")

    # ---------------------------------------------------------
    # 2. Load agent dimension
    # ---------------------------------------------------------
    print("\nLoading agent dimension...")

    agent_query = f"""
        SELECT
            agent_key,
            agent_name
        FROM `{PROJECT_ID}.{DATASET_ID}.dim_agent`
        WHERE is_current = TRUE
    """

    agent_df = client.query(agent_query).to_dataframe()

    print(f"Agent dimension rows: {len(agent_df)}")

    # ---------------------------------------------------------
    # 3. Load status dimension
    # ---------------------------------------------------------
    print("\nLoading status dimension...")

    status_query = f"""
        SELECT
            status_key,
            lead_status
        FROM `{PROJECT_ID}.{DATASET_ID}.dim_lead_status`
    """

    status_df = client.query(status_query).to_dataframe()

    print(f"Status dimension rows: {len(status_df)}")

    # ---------------------------------------------------------
    # 4. Load date dimension
    # ---------------------------------------------------------
    print("\nLoading date dimension...")

    date_query = f"""
        SELECT
            date_key,
            full_date
        FROM `{PROJECT_ID}.{DATASET_ID}.dim_date`
    """

    date_df = client.query(date_query).to_dataframe()

    print(f"Date dimension rows: {len(date_df)}")

    # ---------------------------------------------------------
    # 5. Normalize join columns
    # ---------------------------------------------------------
    fact_df["agent"] = (
        fact_df["agent"]
        .astype("string")
        .str.strip()
    )

    agent_df["agent_name"] = (
        agent_df["agent_name"]
        .astype("string")
        .str.strip()
    )

    fact_df["lead_status"] = (
    fact_df["lead_status"]
    .astype("string")
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)

    status_df["lead_status"] = (
    status_df["lead_status"]
    .astype("string")
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)
    
    fact_df["added_date"] = (
        pd.to_datetime(
            fact_df["added_on"],
            errors="coerce"
        )
        .dt.date
    )

    date_df["full_date"] = (
        pd.to_datetime(
            date_df["full_date"],
            errors="coerce"
        )
        .dt.date
    )

    # ---------------------------------------------------------
    # 7. Join agent dimension
    # ---------------------------------------------------------
    fact_df = fact_df.merge(
        agent_df,
        how="left",
        left_on="agent",
        right_on="agent_name"
    )

    fact_df.drop(
        columns=["agent_name"],
        inplace=True
    )

    # ---------------------------------------------------------
    # 8. Join status dimension
    # ---------------------------------------------------------
    fact_df = fact_df.merge(
        status_df,
        how="left",
        on="lead_status"
    )

    # ---------------------------------------------------------
    # 9. Join date dimension
    # ---------------------------------------------------------
    fact_df = fact_df.merge(
        date_df,
        how="left",
        left_on="added_date",
        right_on="full_date"
    )

    fact_df.drop(
        columns=["full_date", "added_date"],
        inplace=True
    )

    # ---------------------------------------------------------
    # 10. Referential integrity validation
    # ---------------------------------------------------------
    missing_agent_keys = (
        fact_df["agent_key"].isna().sum()
    )

    missing_status_keys = (
        fact_df["status_key"].isna().sum()
    )

    missing_date_keys = (
        fact_df["date_key"].isna().sum()
    )

    print()
    print("=" * 70)
    print("REFERENTIAL INTEGRITY CHECK")
    print("=" * 70)

    print(
        f"Missing agent keys:  {missing_agent_keys}"
    )

    print(
        f"Missing status keys: {missing_status_keys}"
    )

    print(
        f"Missing date keys:   {missing_date_keys}"
    )

    if (
        missing_agent_keys > 0
        or missing_status_keys > 0
        or missing_date_keys > 0
    ):
        raise RuntimeError(
            "Dimension key validation failed. "
            "Fact table contains unmatched dimension values."
        )

    print(
        "All dimension relationships validated successfully."
    )

    # ---------------------------------------------------------
    # 11. Convert dimension keys to integer
    # ---------------------------------------------------------
    fact_df["agent_key"] = (
        fact_df["agent_key"]
        .astype("int64")
    )

    fact_df["status_key"] = (
        fact_df["status_key"]
        .astype("int64")
    )

    fact_df["date_key"] = (
        fact_df["date_key"]
        .astype("int64")
    )

    # ---------------------------------------------------------
    # 12. Replace target star fact table
    # ---------------------------------------------------------
    target_table = (
        f"{PROJECT_ID}.{DATASET_ID}.fct_leads_star"
    )

    print("\nWriting star fact table...")

    job_config = bigquery.LoadJobConfig(
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        )
    )

    job = client.load_table_from_dataframe(
        fact_df,
        target_table,
        job_config=job_config
    )

    job.result()

    # ---------------------------------------------------------
    # 13. Success output
    # ---------------------------------------------------------
    print()
    print("=" * 70)
    print("STAR FACT TABLE CREATED")
    print("=" * 70)

    print(f"Table: {target_table}")
    print(f"Rows: {len(fact_df)}")

    print()
    print("Dimension keys added:")
    print("  agent_key")
    print("  status_key")
    print("  date_key")

    print()
    print("=" * 70)
    print("DIMENSION-FACT RELATIONSHIPS COMPLETE")
    print("=" * 70)

    return True


if __name__ == "__main__":
    refresh_star_schema()