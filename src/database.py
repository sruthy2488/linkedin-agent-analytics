import os

from google.cloud import bigquery
from dotenv import load_dotenv


load_dotenv()


PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID",
    "project-6e78a808-2b6c-4a39-a63"
)

DATASET_ID = os.getenv(
    "BQ_DATASET",
    "linkedin_agent_analytics"
)


_client = None


def get_client():
    """
    Create the BigQuery client only when it is actually needed.

    This keeps module imports and unit tests independent
    of Google Cloud credentials.
    """
    global _client

    if _client is None:
        _client = bigquery.Client(
            project=PROJECT_ID
        )

    return _client


def get_table_id(table_name):
    """
    Return a fully-qualified BigQuery table ID.
    """
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"