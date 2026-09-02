from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timezone

PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"

client = bigquery.Client(project=PROJECT_ID)


# ============================================================
# 1. CREATE DIMENSION TABLES
# ============================================================

def create_tables():

    queries = {

        "dim_agent": f"""
        CREATE TABLE IF NOT EXISTS
        `{PROJECT_ID}.{DATASET_ID}.dim_agent`
        (
            agent_key INT64 NOT NULL,
            agent_name STRING NOT NULL,
            valid_from DATETIME NOT NULL,
            valid_to DATETIME,
            is_current BOOL NOT NULL
        )
        """,

        "dim_lead_status": f"""
        CREATE TABLE IF NOT EXISTS
        `{PROJECT_ID}.{DATASET_ID}.dim_lead_status`
        (
            status_key INT64 NOT NULL,
            lead_status STRING NOT NULL
        )
        """,

        "dim_date": f"""
        CREATE TABLE IF NOT EXISTS
        `{PROJECT_ID}.{DATASET_ID}.dim_date`
        (
            date_key INT64 NOT NULL,
            full_date DATE NOT NULL,
            year INT64,
            month INT64,
            month_name STRING,
            quarter INT64,
            day_of_month INT64,
            day_of_week STRING
        )
        """
    }

    for name, query in queries.items():

        client.query(query).result()

        print(f"{name} created/verified.")


# ============================================================
# 2. READ CURRENT FACT DATA
# ============================================================

def read_fact_data():

    query = f"""
    SELECT
        agent,
        lead_status,
        DATE(added_on) AS added_date
    FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads`
    """

    return client.query(query).to_dataframe()


# ============================================================
# 3. BUILD AGENT DIMENSION
# ============================================================

def build_agent_dimension(df):

    agents = (
        df["agent"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    rows = []

    for key, agent in enumerate(agents, start=1):

        rows.append({
            "agent_key": key,
            "agent_name": agent,
            "valid_from": datetime.now(),
            "valid_to": None,
            "is_current": True
        })

    return pd.DataFrame(rows)


# ============================================================
# 4. BUILD STATUS DIMENSION
# ============================================================

def build_status_dimension(df):

    statuses = (
        df["lead_status"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    rows = []

    for key, status in enumerate(statuses, start=1):

        rows.append({
            "status_key": key,
            "lead_status": status
        })

    return pd.DataFrame(rows)


# ============================================================
# 5. BUILD DATE DIMENSION
# ============================================================

def build_date_dimension(df):

    dates = (
        pd.to_datetime(df["added_date"])
        .dropna()
        .dt.date
        .drop_duplicates()
        .sort_values()
    )

    rows = []

    for date_value in dates:

        rows.append({

            "date_key":
                int(date_value.strftime("%Y%m%d")),

            "full_date":
                date_value,

            "year":
                date_value.year,

            "month":
                date_value.month,

            "month_name":
                date_value.strftime("%B"),

            "quarter":
                ((date_value.month - 1) // 3) + 1,

            "day_of_month":
                date_value.day,

            "day_of_week":
                date_value.strftime("%A")
        })

    return pd.DataFrame(rows)



def load_dataframe(df, table_name):

    if df.empty:

        print(f"{table_name}: no records to load.")

        return

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=job_config
    )

    job.result()

    print(
        f"{table_name} loaded successfully: "
        f"{len(df)} rows."
    )




def main():

    print("=" * 60)
    print("DIMENSION TABLE BUILD")
    print("=" * 60)

    # Create tables
    create_tables()

    print()

    # Read fact data
    df = read_fact_data()

    print(
        f"Fact records analysed: {len(df)}"
    )

    # Build dimensions
    agent_df = build_agent_dimension(df)

    status_df = build_status_dimension(df)

    date_df = build_date_dimension(df)

    print()

    print(
        f"Agents found: {len(agent_df)}"
    )

    print(
        f"Statuses found: {len(status_df)}"
    )

    print(
        f"Dates found: {len(date_df)}"
    )

    print()

    # Load dimensions
    load_dataframe(
        agent_df,
        "dim_agent"
    )

    load_dataframe(
        status_df,
        "dim_lead_status"
    )

    load_dataframe(
        date_df,
        "dim_date"
    )

    print()
    print("=" * 60)
    print("DIMENSION BUILD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()