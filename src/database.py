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

client = bigquery.Client(project=PROJECT_ID)


def get_client():
    return client


def get_table_id(table_name):
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"