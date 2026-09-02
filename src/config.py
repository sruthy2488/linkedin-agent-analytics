import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
LOG_DIR = PROJECT_ROOT / "logs"

CSV_PATH = RAW_DATA_DIR / "polluxa_leads.csv"


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")


GCP_PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID",
    "project-6e78a808-2b6c-4a39-a63"
)

BQ_DATASET = os.getenv(
    "BQ_DATASET",
    "linkedin_agent_analytics"
)

API_URL = os.getenv(
    "API_URL",
    ""
)

API_TOKEN = os.getenv(
    "API_TOKEN",
    ""
)


# ============================================================
# BIGQUERY TABLES
# ============================================================

STG_LEADS_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.stg_leads"
FCT_LEADS_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.fct_leads"

DIM_DATE_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.dim_date"
DIM_AGENT_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.dim_agent"
DIM_STATUS_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.dim_status"


# ============================================================
# PIPELINE CONFIGURATION
# ============================================================

PIPELINE_NAME = "polluxa_leads_ingestion"

DQ_THRESHOLD = 95.0

WATERMARK_COLUMN = "record_updated_at"


# ============================================================
# LOGGING
# ============================================================

LOG_FILE = LOG_DIR / "pipeline.log"


# ============================================================
# VALIDATION
# ============================================================

def validate_config():
    """
    Validate the minimum configuration required by the pipeline.
    """

    if not GCP_PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID is not configured.")

    if not BQ_DATASET:
        raise ValueError("BQ_DATASET is not configured.")

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {CSV_PATH}"
        )

    return True


if __name__ == "__main__":
    validate_config()

    print("Configuration loaded successfully.")
    print(f"Project: {GCP_PROJECT_ID}")
    print(f"Dataset: {BQ_DATASET}")
    print(f"CSV: {CSV_PATH}")
    print(f"DQ threshold: {DQ_THRESHOLD}%")
