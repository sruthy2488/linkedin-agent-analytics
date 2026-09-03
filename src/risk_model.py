from google.cloud import bigquery
import pandas as pd
import numpy as np
from math import sqrt, floor



PROJECT_ID = "project-6e78a808-2b6c-4a39-a63"
DATASET = "linkedin_agent_analytics"

SOURCE_TABLE = f"{PROJECT_ID}.{DATASET}.fct_leads"
TARGET_TABLE = f"{PROJECT_ID}.{DATASET}.analytics_risk_scores"

TIER_DAILY_CEILING = 100


TARGET_CONNECTIONS_PER_DAY = 5

Z_95 = 1.96

MIN_SAMPLE_SIZE = 30


def run_risk_model():
    client = bigquery.Client(project=PROJECT_ID)

    
    def wilson_lower_bound(successes, trials, z=Z_95):
        """
        Wilson score lower confidence bound for a binomial proportion.

        More reliable than a normal approximation when sample sizes
        are small or the observed proportion is close to 0 or 1.
        """

        if trials == 0:
            return 0.0

        p = successes / trials

        denominator = 1 + (z ** 2 / trials)

        centre = (
            p + (z ** 2 / (2 * trials))
        ) / denominator

        margin = (
            z
            * sqrt(
                (p * (1 - p) / trials)
                + (z ** 2 / (4 * trials ** 2))
            )
            / denominator
        )

        return max(0.0, centre - margin)

   
    query = f"""
    SELECT
        agent,
        COUNT(*) AS total_leads,
        COUNTIF(is_contacted = 1) AS contacted_leads,
        COUNTIF(is_invite_sent = 1) AS invite_sent_leads,
        COUNTIF(is_connected = 1) AS connected_leads,
        COUNTIF(is_hot_lead = 1) AS hot_leads,
        COUNTIF(
            is_invite_sent = 1
            AND is_connected = 0
            AND invite_sent_at IS NOT NULL
            AND DATE_DIFF(
                CURRENT_DATE(),
                DATE(invite_sent_at),
                DAY
            ) >= 7
        ) AS ghosted_leads,
        COUNTIF(
    LOWER(TRIM(COALESCE(sdr_status, ''))) = 'replied'
) AS replied_leads,        AVG(
            CASE
                WHEN days_to_connection IS NOT NULL
                THEN days_to_connection
            END
        ) AS avg_days_to_connection
    FROM `{SOURCE_TABLE}`
    WHERE agent IS NOT NULL
    GROUP BY agent
    """

    df = client.query(query).to_dataframe()

    if df.empty:
        raise RuntimeError("No agent data found in fct_leads.")

   
    df["connection_rate"] = np.where(
        df["total_leads"] > 0,
        df["connected_leads"] / df["total_leads"],
        0
    )

    df["acceptance_rate"] = np.where(
        df["invite_sent_leads"] > 0,
        df["connected_leads"] / df["invite_sent_leads"],
        0
    )

    df["reply_rate"] = np.where(
        df["contacted_leads"] > 0,
        df["replied_leads"] / df["contacted_leads"],
        0
    )

    df["ghosting_rate"] = np.where(
        df["invite_sent_leads"] > 0,
        df["ghosted_leads"] / df["invite_sent_leads"],
        0
    )

    
    df["connection_rate_lower_95"] = df.apply(
        lambda row: wilson_lower_bound(
            int(row["connected_leads"]),
            int(row["total_leads"])
        ),
        axis=1
    )

    
    total_connections = df["connected_leads"].sum()
    total_leads = df["total_leads"].sum()

    if total_leads > 0:
        pooled_connection_rate = (
            total_connections / total_leads
        )
    else:
        pooled_connection_rate = 0.0

    
    def calculate_z_score(row):
        """
        One-proportion z-score against the pooled baseline.

        When the dataset contains only one agent, a peer comparison
        is not statistically meaningful. In that case we return 0
        and mark the model as having insufficient peer data.
        """

        if len(df) < 2:
            return 0.0

        n = row["total_leads"]

        if n < MIN_SAMPLE_SIZE:
            return 0.0

        p0 = pooled_connection_rate

        if p0 <= 0 or p0 >= 1:
            return 0.0

        p = row["connection_rate"]

        standard_error = sqrt(
            p0 * (1 - p0) / n
        )

        if standard_error == 0:
            return 0.0

        return (p - p0) / standard_error

    df["connection_rate_zscore"] = df.apply(
        calculate_z_score,
        axis=1
    )

    
    def ghosting_risk(row):
        if row["invite_sent_leads"] < 5:
            return 0
        if row["ghosting_rate"] >= 0.50:
            return 35
        if row["ghosting_rate"] >= 0.30:
            return 20
        if row["ghosting_rate"] >= 0.15:
            return 10
        return 0

    def acceptance_risk(row):
        if row["invite_sent_leads"] < 5:
            return 0
        if row["acceptance_rate"] < 0.05:
            return 30
        if row["acceptance_rate"] < 0.10:
            return 20
        if row["acceptance_rate"] < 0.15:
            return 10
        return 0

    def connection_anomaly_risk(row):
        z = row["connection_rate_zscore"]
        if z <= -3:
            return 35
        if z <= -2:
            return 25
        if z <= -1:
            return 10
        return 0

    df["ghosting_risk_points"] = df.apply(
        ghosting_risk,
        axis=1
    )

    df["acceptance_risk_points"] = df.apply(
        acceptance_risk,
        axis=1
    )

    df["connection_anomaly_points"] = df.apply(
        connection_anomaly_risk,
        axis=1
    )

    
    df["statistical_confidence"] = np.where(
        df["total_leads"] >= MIN_SAMPLE_SIZE,
        "Adequate for rate monitoring",
        "Insufficient sample"
    )

    df["risk_score"] = (
        df["ghosting_risk_points"]
        + df["acceptance_risk_points"]
        + df["connection_anomaly_points"]
    )

    df["risk_score"] = df["risk_score"].clip(0, 100)

    def risk_level(score):
        if score >= 60:
            return "HIGH"
        if score >= 30:
            return "MEDIUM"
        return "LOW"

    df["risk_level"] = df["risk_score"].apply(
        risk_level
    )

    
    def recommend_capacity(row):
        # Small sample:
        # do not aggressively reduce capacity based on unstable rates.
        if row["total_leads"] < MIN_SAMPLE_SIZE:
            return TIER_DAILY_CEILING

        lower_bound = row["connection_rate_lower_95"]
        if lower_bound <= 0:
            return 50

        estimated_capacity = (
            TARGET_CONNECTIONS_PER_DAY / lower_bound
        )

        capacity = min(
            TIER_DAILY_CEILING,
            max(10, floor(estimated_capacity))
        )

        if row["risk_level"] == "HIGH":
            capacity = min(capacity, 50)
        elif row["risk_level"] == "MEDIUM":
            capacity = min(capacity, 75)

        return capacity

    df["recommended_daily_capacity"] = df.apply(
        recommend_capacity,
        axis=1
    )

    
    df["model_status"] = np.where(
        df["total_leads"] >= MIN_SAMPLE_SIZE,
        "STATISTICALLY_ACTIONABLE",
        "MONITOR_ONLY"
    )

    
    final_df = df[
        [
            "agent",
            "total_leads",
            "contacted_leads",
            "invite_sent_leads",
            "connected_leads",
            "hot_leads",
            "replied_leads",
            "ghosted_leads",
            "connection_rate",
            "acceptance_rate",
            "reply_rate",
            "ghosting_rate",
            "connection_rate_lower_95",
            "connection_rate_zscore",
            "ghosting_risk_points",
            "acceptance_risk_points",
            "connection_anomaly_points",
            "risk_score",
            "risk_level",
            "recommended_daily_capacity",
            "statistical_confidence",
            "model_status",
            "avg_days_to_connection"
        ]
    ]

   
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    )

    job = client.load_table_from_dataframe(
        final_df,
        TARGET_TABLE,
        job_config=job_config
    )

    job.result()

    # ============================================================
    # DISPLAY RESULTS
    # ============================================================
    print()
    print("=" * 70)
    print("ADVANCED RISK MODEL")
    print("=" * 70)
    print()

    for _, row in final_df.iterrows():
        print(f"Agent: {row['agent']}")
        print(f"Total leads: {row['total_leads']}")
        print(
            f"Connection rate: "
            f"{row['connection_rate'] * 100:.2f}%"
        )
        print(
            f"Acceptance rate: "
            f"{row['acceptance_rate'] * 100:.2f}%"
        )
        print(
            f"Reply rate: "
            f"{row['reply_rate'] * 100:.2f}%"
        )
        print(
            f"Ghosting rate: "
            f"{row['ghosting_rate'] * 100:.2f}%"
        )
        print(
            f"95% lower confidence bound: "
            f"{row['connection_rate_lower_95'] * 100:.2f}%"
        )
        print(
            f"Risk score: "
            f"{row['risk_score']:.2f}"
        )
        print(
            f"Risk level: "
            f"{row['risk_level']}"
        )
        print(
            f"Recommended daily capacity: "
            f"{row['recommended_daily_capacity']}"
        )
        print(
            f"Statistical confidence: "
            f"{row['statistical_confidence']}"
        )
        print(
            f"Model status: "
            f"{row['model_status']}"
        )
        print()
    print("=" * 70)
    print(
        f"Risk table created: {TARGET_TABLE}"
    )
    print("=" * 70)

if __name__ == "__main__":
    run_risk_model()