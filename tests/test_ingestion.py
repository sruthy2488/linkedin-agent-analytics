import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from ingest import (
    make_lead_id,
    validate_records,
    transform,
)


def test_make_lead_id_is_stable():
    url = "https://www.linkedin.com/in/test-user"

    id1 = make_lead_id(url)
    id2 = make_lead_id(url)

    assert id1 == id2
    assert id1 is not None
    assert len(id1) == 32


def test_make_lead_id_is_case_insensitive():
    url1 = "https://www.linkedin.com/in/Test-User"
    url2 = " HTTPS://www.linkedin.com/in/test-user "

    assert make_lead_id(url1) == make_lead_id(url2)


def test_make_lead_id_returns_none_for_missing_url():
    assert make_lead_id(None) is None
    assert make_lead_id("") is None
    assert make_lead_id("   ") is None


def test_validate_records_accepts_valid_record():
    df = pd.DataFrame(
        {
            "linkedin_url": [
                "https://www.linkedin.com/in/test-user"
            ],
            "staging_id": ["abc123"],
            "added_on": [pd.Timestamp("2026-08-01")],
        }
    )

    valid_df, dead_letter_df = validate_records(df)

    assert len(valid_df) == 1
    assert len(dead_letter_df) == 0


def test_validate_records_rejects_missing_linkedin_url():
    df = pd.DataFrame(
        {
            "linkedin_url": [None],
            "staging_id": ["abc123"],
            "added_on": [pd.Timestamp("2026-08-01")],
        }
    )

    valid_df, dead_letter_df = validate_records(df)

    assert len(valid_df) == 0
    assert len(dead_letter_df) == 1
    assert "Missing linkedin_url" in dead_letter_df.iloc[0]["error_reason"]


def test_validate_records_rejects_missing_staging_id():
    df = pd.DataFrame(
        {
            "linkedin_url": [
                "https://www.linkedin.com/in/test-user"
            ],
            "staging_id": [None],
            "added_on": [pd.Timestamp("2026-08-01")],
        }
    )

    valid_df, dead_letter_df = validate_records(df)

    assert len(valid_df) == 0
    assert len(dead_letter_df) == 1
    assert "Missing staging_id" in dead_letter_df.iloc[0]["error_reason"]


def test_validate_records_rejects_missing_added_on():
    df = pd.DataFrame(
        {
            "linkedin_url": [
                "https://www.linkedin.com/in/test-user"
            ],
            "staging_id": ["abc123"],
            "added_on": [None],
        }
    )

    valid_df, dead_letter_df = validate_records(df)

    assert len(valid_df) == 0
    assert len(dead_letter_df) == 1
    assert "Missing added_on" in dead_letter_df.iloc[0]["error_reason"]


def test_transform_creates_stable_id_and_normalized_columns():
    df = pd.DataFrame(
        {
            "Name": ["Test User"],
            "Job Title": ["Data Analyst"],
            "Company": ["Test Company"],
            "Industry": ["Technology"],
            "Location": ["India"],
            "Agent": ["Sruthy"],
            "SDR Status": ["Connected"],
            "Comment Status": ["Replied"],
            "Hot Score": [80],
            "Source": ["LinkedIn"],
            "Prioritized": ["Yes"],
            "LinkedIn URL": [
                "https://www.linkedin.com/in/test-user"
            ],
            "Added On": ["2026-08-01"],
            "Last Contacted": ["2026-08-02"],
            "Invite Sent At": ["2026-08-01"],
            "Connected At": ["2026-08-03"],
        }
    )

    result = transform(df)

    assert len(result) == 1
    assert "staging_id" in result.columns
    assert "record_updated_at" in result.columns
    assert "load_timestamp" in result.columns

    assert result.iloc[0]["name"] == "Test User"
    assert result.iloc[0]["company"] == "Test Company"


def test_transform_removes_duplicate_leads():
    df = pd.DataFrame(
        {
            "Name": ["User 1", "User 1"],
            "Job Title": ["Analyst", "Analyst"],
            "Company": ["Company A", "Company A"],
            "Industry": ["Technology", "Technology"],
            "Location": ["India", "India"],
            "Agent": ["Agent 1", "Agent 1"],
            "SDR Status": ["New", "New"],
            "Comment Status": ["None", "None"],
            "Hot Score": [50, 50],
            "Source": ["LinkedIn", "LinkedIn"],
            "Prioritized": ["No", "No"],
            "LinkedIn URL": [
                "https://www.linkedin.com/in/duplicate",
                "https://www.linkedin.com/in/duplicate",
            ],
            "Added On": ["2026-08-01", "2026-08-01"],
            "Last Contacted": [None, None],
            "Invite Sent At": [None, None],
            "Connected At": [None, None],
        }
    )

    result = transform(df)

    assert len(result) == 1