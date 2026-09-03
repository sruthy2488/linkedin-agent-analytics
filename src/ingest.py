import os
from alerts import send_alert
from risk_model import run_risk_model
from logging_utils import get_pipeline_logger
from dq_checks import (
    create_dq_history_table,
    run_dq_checks,
    save_dq_result
)

from refresh_warehouse import refresh_warehouse
from refresh_star_schema import refresh_star_schema
from reliability import run_with_retry
import hashlib
from pathlib import Path
import uuid
from datetime import datetime, timezone

import pandas as pd
from google.cloud import bigquery

from database import get_client, get_table_id


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "polluxa_leads.csv"


def make_lead_id(linkedin_url):
    """Create a stable ID from the LinkedIn URL."""

    if pd.isna(linkedin_url) or not str(linkedin_url).strip():
        return None

    value = str(linkedin_url).strip().lower()

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:32]


def load_csv():

    print(f"Reading: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    print(f"Rows read: {len(df)}")

    return df
def validate_records(df):
    """
    Validate records before loading them into staging.

    Returns:
        valid_df
        dead_letter_df
    """

    df = df.copy()

    errors = pd.Series(
        "",
        index=df.index,
        dtype="object"
    )

    missing_url = (
        df["linkedin_url"].isna()
        |
        df["linkedin_url"].astype(str).str.strip().eq("")
    )

    errors.loc[missing_url] = (
        errors.loc[missing_url]
        + "Missing linkedin_url; "
    )

    missing_id = df["staging_id"].isna()

    errors.loc[missing_id] = (
        errors.loc[missing_id]
        + "Missing staging_id; "
    )

    missing_added_on = df["added_on"].isna()

    errors.loc[missing_added_on] = (
        errors.loc[missing_added_on]
        + "Missing added_on; "
    )

    dead_letter_mask = errors.str.strip().ne("")

    dead_letter_df = df.loc[
        dead_letter_mask
    ].copy()

    valid_df = df.loc[
        ~dead_letter_mask
    ].copy()

    if not dead_letter_df.empty:

        dead_letter_df["error_reason"] = (
            errors.loc[dead_letter_mask]
            .str.strip()
        )

    return valid_df, dead_letter_df
def load_dead_letters(df, run_id):
    """
    Store invalid records in a BigQuery dead-letter table.
    """

    if df.empty:
        print("No dead-letter records.")
        return

    client = get_client()

    table_id = get_table_id("dead_letter_leads")

    df = df.copy()

    df["dead_letter_run_id"] = run_id
    df["dead_letter_timestamp"] = pd.Timestamp.now(tz="UTC")

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )

    job_id = (
        f"dead_letter_"
        f"{run_id.replace('-', '')}_"
        f"{uuid.uuid4().hex[:8]}"
    )

    job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=job_config,
        job_id=job_id
    )

    job.result()

    print(
        f"Loaded {len(df)} dead-letter records "
        f"into {table_id}"
    )

    print(f"Dead-letter job ID: {job.job_id}")

def transform(df):

    df = df.rename(columns={
        "Name": "name",
        "Job Title": "job_title",
        "Company": "company",
        "Industry": "industry",
        "Location": "location",
        "Agent": "agent",
        "SDR Status": "sdr_status",
        "Comment Status": "comment_status",
        "Hot Score": "hot_score",
        "Source": "source",
        "Prioritized": "prioritized",
        "LinkedIn URL": "linkedin_url",
        "Added On": "added_on",
        "Last Contacted": "last_contacted",
        "Invite Sent At": "invite_sent_at",
        "Connected At": "connected_at"
    })

    df["staging_id"] = df["linkedin_url"].apply(make_lead_id)

    before = len(df)

    df = df.drop_duplicates(
        subset=["staging_id"],
        keep="last"
    )

    after = len(df)

    print(f"Duplicates removed: {before - after}")

    date_columns = [
        "added_on",
        "last_contacted",
        "invite_sent_at",
        "connected_at"
    ]

    for column in date_columns:
        df[column] = pd.to_datetime(
        df[column],
        errors="coerce",
        utc=True,
        format="mixed"
    )

    df["record_updated_at"] = df[date_columns].max(axis=1)

    df["load_timestamp"] = pd.Timestamp.now(tz="UTC")

    columns = [
        "staging_id",
        "name",
        "job_title",
        "company",
        "industry",
        "location",
        "agent",
        "sdr_status",
        "comment_status",
        "hot_score",
        "source",
        "prioritized",
        "linkedin_url",
        "added_on",
        "last_contacted",
        "invite_sent_at",
        "connected_at",
        "record_updated_at",
        "load_timestamp"
    ]

    return df[columns]


def get_current_watermark():

    client = get_client()

    table_id = get_table_id("pipeline_runs")

    query = f"""
        SELECT MAX(watermark_end) AS watermark
        FROM `{table_id}`
        WHERE pipeline_name = 'polluxa_leads_ingestion'
          AND status = 'SUCCESS'
          AND watermark_end IS NOT NULL
    """

    result = list(client.query(query).result())

    if not result:
        return None

    return result[0].watermark


def get_existing_staging():

    client = get_client()

    table_id = get_table_id("stg_leads")

    query = f"""
        SELECT *
        FROM `{table_id}`
    """

    result = client.query(query).result()

    
    return result.to_dataframe()


def prepare_incremental_data(df):

    df["record_updated_at"] = pd.to_datetime(
        df["record_updated_at"],
        utc=True,
        errors="coerce"
    )

    # ---------------------------------------------------------
    # FULL REFRESH MODE
    # ---------------------------------------------------------

    full_refresh = (
        os.getenv("FULL_REFRESH", "false")
        .strip()
        .lower() == "true"
    )

    if full_refresh:

        print(
            "\nFULL_REFRESH=true"
        )

        print(
            "Loading the complete current source dataset."
        )

        final_df = df.copy()

        new_watermark = (
            final_df["record_updated_at"].max()
        )

        print(
            f"Full-refresh records: {len(final_df)}"
        )

        return final_df, new_watermark

    

    current_watermark = get_current_watermark()

    if current_watermark is None:
        print(
            "No previous successful "
            "watermark found."
        )

        final_df = df.copy()

        new_watermark = (
            final_df["record_updated_at"].max()
        )

        return final_df, new_watermark

    current_watermark = pd.to_datetime(
        current_watermark,
        utc=True
    )

    print(
        f"Previous watermark: "
        f"{current_watermark}"
    )

    incremental_df = df[
        df["record_updated_at"] > current_watermark
    ].copy()

    print(
        f"Records newer than watermark: "
        f"{len(incremental_df)}"
    )

    existing_df = get_existing_staging()

    print(
        f"Existing records in staging: "
        f"{len(existing_df)}"
    )

    if existing_df.empty:

        final_df = incremental_df

    elif incremental_df.empty:

        final_df = existing_df

    else:

        final_df = pd.concat(
            [
                existing_df,
                incremental_df
            ],
            ignore_index=True
        )

        final_df = final_df.drop_duplicates(
            subset=["staging_id"],
            keep="last"
        )

    if incremental_df.empty:

        new_watermark = current_watermark

    else:

        new_watermark = (
            incremental_df[
                "record_updated_at"
            ].max()
        )

    return final_df, new_watermark


def load_to_bigquery(df, run_id):
    """
    Load staging data into BigQuery using a deterministic
    job ID so retries do not duplicate the same load.
    """

    if df.empty:
        print("No records to load into BigQuery.")
        return

    client = get_client()
    table_id = get_table_id("stg_leads")

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    job_id = f"stg_leads_{run_id.replace('-', '')}"

    def start_load():
        job = client.load_table_from_dataframe(
            df,
            table_id,
            job_config=job_config,
            job_id=job_id,
            num_retries=6
        )

        job.result()

        return job

    job = run_with_retry(
        start_load,
        "BigQuery staging load"
    )

    print(
        f"Loaded {len(df)} rows into {table_id}"
    )

    print(
        f"BigQuery job ID: {job.job_id}"
    )


def record_pipeline_run(
    run_id,
    started_at,
    completed_at,
    rows_read,
    rows_loaded,
    status,
    watermark_start=None,
    watermark_end=None,
    error_message=None
):

    client = get_client()

    table_id = get_table_id("pipeline_runs")

    run_data = pd.DataFrame([{

        "run_id": run_id,

        "pipeline_name":
            "polluxa_leads_ingestion",

        "started_at": started_at,

        "completed_at": completed_at,

        "rows_read": rows_read,

        "rows_loaded": rows_loaded,

        "status": status,

        "watermark_start":
            watermark_start,

        "watermark_end":
            watermark_end,

        "error_message":
            error_message

    }])

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )

    job = client.load_table_from_dataframe(
        run_data,
        table_id,
        job_config=job_config
    )

    job.result()

    print(
        f"Pipeline run recorded: {status}"
    )


def main():
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    logger = get_pipeline_logger(run_id)

    logger.info(
        "Pipeline started",
        extra={
            "event": "pipeline_started"
        }
    )

    print(f"Starting pipeline: {run_id}")

    rows_read = 0
    rows_loaded = 0
    watermark_start = None
    watermark_end = None

    try:


        df = load_csv()
        rows_read = len(df)

        logger.info(
            "Input data loaded",
            extra={
                "event": "input_loaded",
                "rows_read": rows_read
            }
        )


        df = transform(df)

        print("\nTransformed columns:")
        print(df.columns.tolist())

        print(
            f"\nRows ready for processing: "
            f"{len(df)}"
        )

        

        valid_df, dead_letter_df = validate_records(df)

        logger.info(
            "Input validation completed",
            extra={
                "event": "validation_completed",
                "valid_records": len(valid_df),
                "dead_letter_records": len(dead_letter_df)
            }
        )

        print(
            f"Valid records: {len(valid_df)}"
        )

        print(
            f"Dead-letter records: "
            f"{len(dead_letter_df)}"
        )

        
        if not dead_letter_df.empty:

            load_dead_letters(
                dead_letter_df,
                run_id
            )

        df = valid_df

        

        watermark_start = get_current_watermark()

        if watermark_start is None:

            print(
                "\nNo previous successful "
                "watermark found."
            )

        else:

            print(
                f"\nStarting watermark: "
                f"{watermark_start}"
            )

        final_df, watermark_end = (
            prepare_incremental_data(df)
        )

        logger.info(
            "Incremental processing completed",
            extra={
                "event": "incremental_processing_completed",
                "final_records": len(final_df),
                "watermark_end": (
                    str(watermark_end)
                    if watermark_end is not None
                    else None
                )
            }
        )

        print(
            f"Final records in staging: "
            f"{len(final_df)}"
        )

        print(
            f"New watermark: "
            f"{watermark_end}"
        )

       

        load_to_bigquery(
            final_df,
            run_id
        )

        rows_loaded = len(final_df)

        logger.info(
            "Staging load completed",
            extra={
                "event": "staging_load_completed",
                "rows_loaded": rows_loaded
            }
        )

       

        print("\nRefreshing warehouse...")

        refresh_warehouse()

        logger.info(
            "Warehouse refresh completed",
            extra={
                "event": "warehouse_refresh_completed"
            }
        )

        print("Warehouse refresh completed.")

       

        print("\nRefreshing star schema...")

        refresh_star_schema()

        logger.info(
            "Star schema refresh completed",
            extra={
                "event": "star_schema_refresh_completed"
            }
        )

        print("Star schema refresh completed.")

        

        print("\nRunning data quality checks...")

        create_dq_history_table()

        dq_result = run_dq_checks()

        save_dq_result(dq_result)

        logger.info(
            "Data quality check completed",
            extra={
                "event": "dq_check_completed",
                "dq_score": dq_result["dq_score"],
                "dq_status": dq_result["dq_status"]
            }
        )

        

        if dq_result["dq_status"] != "PASS":

            send_alert(
                event="dq_threshold_breach",
                message=(
                    "Data quality score fell below "
                    "the configured threshold."
                ),
                run_id=run_id,
                severity="CRITICAL",
                dq_score=dq_result["dq_score"],
                dq_status=dq_result["dq_status"]
            )

            raise RuntimeError(
                f"Data Quality check failed. "
                f"Score: {dq_result['dq_score']:.2f}%"
            )

        print(
            f"Data Quality check passed: "
            f"{dq_result['dq_score']:.2f}%"
        )

        

        print("\nRunning advanced risk model...")

        run_risk_model()

        logger.info(
            "Risk model completed",
            extra={
                "event": "risk_model_completed"
            }
        )

        print("Advanced risk model completed.")

        
        completed_at = datetime.now(timezone.utc)

        duration_seconds = (
            completed_at - started_at
        ).total_seconds()

        logger.info(
            "Pipeline completed successfully",
            extra={
                "event": "pipeline_completed",
                "status": "SUCCESS",
                "rows_read": rows_read,
                "rows_loaded": rows_loaded,
                "duration_seconds": duration_seconds
            }
        )

        

        max_duration = float(
            os.getenv(
                "MAX_RUN_DURATION_SECONDS",
                "300"
            )
        )

        if duration_seconds > max_duration:

            send_alert(
                event="anomalous_run_duration",
                message=(
                    "Pipeline runtime exceeded "
                    "the configured maximum duration."
                ),
                run_id=run_id,
                severity="WARNING",
                duration_seconds=duration_seconds,
                max_duration_seconds=max_duration
            )

        

        record_pipeline_run(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            rows_read=rows_read,
            rows_loaded=rows_loaded,
            status="SUCCESS",
            watermark_start=watermark_start,
            watermark_end=watermark_end
        )

        print(
            "\nIngestion completed successfully."
        )

    

    except Exception as e:

        completed_at = datetime.now(timezone.utc)

        duration_seconds = (
            completed_at - started_at
        ).total_seconds()

       

        logger.error(
            "Pipeline failed",
            extra={
                "event": "pipeline_failed",
                "status": "FAILED",
                "error": str(e),
                "duration_seconds": duration_seconds,
                "rows_read": rows_read,
                "rows_loaded": rows_loaded
            }
        )

       
        send_alert(
            event="pipeline_failure",
            message=(
                "LinkedIn Agent Analytics "
                "pipeline failed."
            ),
            run_id=run_id,
            severity="CRITICAL",
            error=str(e),
            rows_read=rows_read,
            rows_loaded=rows_loaded,
            duration_seconds=duration_seconds
        )

        print(
            f"\nPipeline failed: {e}"
        )

        

        try:

            record_pipeline_run(
                run_id=run_id,
                started_at=started_at,
                completed_at=completed_at,
                rows_read=rows_read,
                rows_loaded=rows_loaded,
                status="FAILED",
                watermark_start=watermark_start,
                watermark_end=watermark_end,
                error_message=str(e)
            )

        except Exception as logging_error:

            print(
                "Could not record "
                f"pipeline failure: "
                f"{logging_error}"
            )

        raise


if __name__ == "__main__":
    main()