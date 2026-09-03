from google.cloud import bigquery
from datetime import datetime, timezone


PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET_ID = "linkedin_agent_analytics"


# ---------------------------------------------------------
# BigQuery client
# ---------------------------------------------------------

def get_client():
    return bigquery.Client(project=PROJECT_ID)


# ---------------------------------------------------------
# Run Data Quality checks
# ---------------------------------------------------------

def run_dq_checks():
    client = get_client()

    table = f"`{PROJECT_ID}.{DATASET_ID}.fct_leads`"

    # -----------------------------------------------------
    # 1. Completeness
    # -----------------------------------------------------

    completeness_query = f"""
    SELECT
        COUNT(*) AS total_rows,

        COUNTIF(name IS NOT NULL AND TRIM(name) != '')
            AS valid_name,

        COUNTIF(linkedin_url IS NOT NULL AND TRIM(linkedin_url) != '')
            AS valid_linkedin_url,

        COUNTIF(added_on IS NOT NULL)
            AS valid_added_on,

        COUNTIF(agent IS NOT NULL AND TRIM(agent) != '')
            AS valid_agent

    FROM {table}
    """

    row = list(client.query(completeness_query).result())[0]

    total_rows = row.total_rows

    if total_rows == 0:
        completeness_score = 0
    else:
        completeness_score = (
            (
                row.valid_name
                + row.valid_linkedin_url
                + row.valid_added_on
                + row.valid_agent
            )
            / (total_rows * 4)
        ) * 100

    # -----------------------------------------------------
    # 2. Uniqueness
    # -----------------------------------------------------

    uniqueness_query = f"""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT staging_id) AS unique_staging_ids,
        COUNT(DISTINCT linkedin_url) AS unique_linkedin_urls
    FROM {table}
    """

    row = list(client.query(uniqueness_query).result())[0]

    if row.total_rows == 0:
        uniqueness_score = 0
    else:
        staging_score = (
            row.unique_staging_ids / row.total_rows
        ) * 100

        linkedin_score = (
            row.unique_linkedin_urls / row.total_rows
        ) * 100

        uniqueness_score = (
            staging_score + linkedin_score
        ) / 2

    # -----------------------------------------------------
    # 3. Validity
    # -----------------------------------------------------

    validity_query = f"""
    SELECT
        COUNT(*) AS total_rows,

        COUNTIF(
            hot_score IS NULL
            OR (hot_score >= 0 AND hot_score <= 100)
        ) AS valid_hot_scores,

        COUNTIF(
            prioritized IS NULL
            OR UPPER(TRIM(prioritized)) IN ('YES', 'NO')
        ) AS valid_prioritized,

        COUNTIF(
            sdr_status IS NULL
            OR LOWER(TRIM(sdr_status))
                IN (
                    'captured',
                    'invite sent',
                    'connected',
                    'replied',
                    'rejected',
                    'unknown'
                )
        ) AS valid_statuses

    FROM {table}
    """

    row = list(client.query(validity_query).result())[0]

    if row.total_rows == 0:
        validity_score = 0
    else:
        validity_score = (
            (
                row.valid_hot_scores
                + row.valid_prioritized
                + row.valid_statuses
            )
            / (row.total_rows * 3)
        ) * 100

    # -----------------------------------------------------
    # 4. Timeliness
    # -----------------------------------------------------

   
    timeliness_query = f"""
            SELECT
        COUNT(*) AS total_rows,

        COUNTIF(
            record_updated_at IS NOT NULL
            AND record_updated_at <= CURRENT_TIMESTAMP()
        ) AS timely_records

    FROM `{PROJECT_ID}.{DATASET_ID}.stg_leads`
    WHERE record_updated_at IS NOT NULL
    """

    row = list(
        client.query(timeliness_query).result()
    )[0]

    row = list(
            client.query(timeliness_query).result()
        )[0]


    if row.total_rows == 0:
        timeliness_score = 0
    else:
        timeliness_score = (
            row.timely_records / row.total_rows
        ) * 100

    

    referential_query = f"""
    SELECT
        COUNT(*) AS total_rows,

        COUNTIF(
            agent IS NOT NULL
            AND TRIM(agent) != ''
        ) AS valid_agents

    FROM {table}
    """

    row = list(client.query(referential_query).result())[0]

    if row.total_rows == 0:
        referential_integrity_score = 0
    else:
        referential_integrity_score = (
            row.valid_agents / row.total_rows
        ) * 100

    # -----------------------------------------------------
    # Composite DQ score
    #
    # Weighting:
    # Completeness             25%
    # Uniqueness               20%
    # Validity                 25%
    # Timeliness               15%
    # Referential Integrity    15%
    # -----------------------------------------------------

    dq_score = (
        completeness_score * 0.25
        + uniqueness_score * 0.20
        + validity_score * 0.25
        + timeliness_score * 0.15
        + referential_integrity_score * 0.15
    )

    # -----------------------------------------------------
    # Pass / Fail
    # -----------------------------------------------------

    threshold = 95.0

    dq_status = (
        "PASS"
        if dq_score >= threshold
        else "FAIL"
    )

    # -----------------------------------------------------
    # Print results
    # -----------------------------------------------------

    print("\n==============================")
    print("DATA QUALITY RESULTS")
    print("==============================")

    print(
        f"Completeness:              "
        f"{completeness_score:.2f}%"
    )

    print(
        f"Uniqueness:                "
        f"{uniqueness_score:.2f}%"
    )

    print(
        f"Validity:                  "
        f"{validity_score:.2f}%"
    )

    print(
        f"Timeliness:                "
        f"{timeliness_score:.2f}%"
    )

    print(
        f"Referential Integrity:     "
        f"{referential_integrity_score:.2f}%"
    )

    print("------------------------------")

    print(
        f"Composite DQ Score:        "
        f"{dq_score:.2f}%"
    )

    print(
        f"Threshold:                 "
        f"{threshold:.2f}%"
    )

    print(
        f"Status:                    "
        f"{dq_status}"
    )

    print("==============================")

    return {
        "completeness_score": completeness_score,
        "uniqueness_score": uniqueness_score,
        "validity_score": validity_score,
        "timeliness_score": timeliness_score,
        "referential_integrity_score": referential_integrity_score,
        "dq_score": dq_score,
        "dq_status": dq_status,
    }


# ---------------------------------------------------------
# Create DQ history table
# ---------------------------------------------------------

def create_dq_history_table():
    client = get_client()

    query = f"""
    CREATE TABLE IF NOT EXISTS
    `{PROJECT_ID}.{DATASET_ID}.dq_results`
    (
        dq_run_id STRING,
        dq_timestamp TIMESTAMP,

        total_rows INT64,

        completeness_score FLOAT64,
        uniqueness_score FLOAT64,
        validity_score FLOAT64,
        timeliness_score FLOAT64,
        referential_integrity_score FLOAT64,

        composite_dq_score FLOAT64,
        threshold FLOAT64,

        dq_status STRING
    )
    """

    client.query(query).result()

    print(
        "DQ history table ready: "
        f"{DATASET_ID}.dq_results"
    )


# ---------------------------------------------------------
# Save DQ result
# ---------------------------------------------------------


def save_dq_result(result):
    """
    Save the DQ result to BigQuery using a load job
    instead of DML.

    This works without requiring BigQuery DML/billing.
    """

    client = get_client()

    run_id = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d%H%M%S%f"
    )

    # Get total rows
    count_query = f"""
    SELECT COUNT(*) AS total_rows
    FROM `{PROJECT_ID}.{DATASET_ID}.fct_leads`
    """

    count_row = list(
        client.query(count_query).result()
    )[0]

    total_rows = count_row.total_rows

    # Create one-row DataFrame
    import pandas as pd

    dq_record = pd.DataFrame([
        {
            "dq_run_id": run_id,
            "dq_timestamp": datetime.now(timezone.utc),

            "total_rows": int(total_rows),

            "completeness_score":
                float(result["completeness_score"]),

            "uniqueness_score":
                float(result["uniqueness_score"]),

            "validity_score":
                float(result["validity_score"]),

            "timeliness_score":
                float(result["timeliness_score"]),

            "referential_integrity_score":
                float(
                    result[
                        "referential_integrity_score"
                    ]
                ),

            "composite_dq_score":
                float(result["dq_score"]),

            "threshold": 95.0,

            "dq_status":
                result["dq_status"],
        }
    ])

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"dq_results"
    )

    job_config = bigquery.LoadJobConfig(
        write_disposition=(
            bigquery.WriteDisposition.WRITE_APPEND
        )
    )

    job = client.load_table_from_dataframe(
        dq_record,
        table_id,
        job_config=job_config
    )

    job.result()

    print(
        "DQ result saved successfully."
    )

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    create_dq_history_table()

    result = run_dq_checks()

    save_dq_result(result)