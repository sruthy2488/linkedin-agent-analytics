# LinkedIn Agent Analytics â€” Data Dictionary



## 1. Overview



This data dictionary documents the tables used in the LinkedIn Agent

Analytics platform, including staging, warehouse, dimension,

quality-control, pipeline-monitoring, and analytics tables.



---



# 2. Staging Layer



## stg_leads



**Grain:** One row per ingested LinkedIn lead.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| staging_id | STRING | Business/record identifier | Unique identifier generated for an ingested lead |

| name | STRING | | Lead name |

| job_title | STRING | | Lead's job title or professional headline |

| company | STRING | | Company associated with the lead |

| industry | STRING | | Industry associated with the lead |

| location | STRING | | Lead's geographic location |

| agent | STRING | | Agent/account responsible for the lead |

| sdr_status | STRING | | Current SDR workflow status |

| comment_status | STRING | | Status of LinkedIn commenting activity |

| hot_score | FLOAT | | Lead priority/temperature score |

| source | STRING | | Source from which the lead was captured |

| prioritized | STRING | | Indicates whether the lead has been prioritized |

| linkedin_url | STRING | | LinkedIn profile URL |

| added_on | DATETIME | | Date/time the lead was added |

| last_contacted | DATETIME | | Most recent contact timestamp |

| invite_sent_at | DATETIME | | Timestamp when connection invite was sent |

| connected_at | DATETIME | | Timestamp when connection was established |

| record_updated_at | DATETIME | | Timestamp of the latest source-record update |

| load_timestamp | TIMESTAMP | | Timestamp when the record entered the warehouse |



---



# 3. Fact Layer



## fct_leads_star



**Grain:** One row per LinkedIn lead.



This table contains the analytical lead record and measures/flags

used for reporting and analysis.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| staging_id | STRING | Business identifier | Source lead identifier |

| name | STRING | | Lead name |

| job_title | STRING | | Lead's job title |

| company | STRING | | Lead's company |

| industry | STRING | | Lead's industry |

| location | STRING | | Lead's location |

| agent | STRING | | Agent responsible for the lead |

| sdr_status | STRING | | SDR workflow status |

| comment_status | STRING | | Comment activity status |

| hot_score | FLOAT | | Lead score |

| source | STRING | | Lead source |

| prioritized | STRING | | Priority indicator |

| linkedin_url | STRING | | LinkedIn profile URL |

| added_on | DATETIME | | Lead creation/addition timestamp |

| last_contacted | DATETIME | | Most recent contact timestamp |

| invite_sent_at | DATETIME | | Connection invite timestamp |

| connected_at | DATETIME | | Connection timestamp |

| record_updated_at | DATETIME | | Source update timestamp |

| load_timestamp | TIMESTAMP | | Warehouse ingestion timestamp |

| is_contacted | INTEGER | Measure/flag | Indicates whether the lead has been contacted |

| is_invite_sent | INTEGER | Measure/flag | Indicates whether an invite has been sent |

| is_connected | INTEGER | Measure/flag | Indicates whether the lead is connected |

| is_prioritized | INTEGER | Measure/flag | Indicates whether the lead is prioritized |

| is_hot_lead | INTEGER | Measure/flag | Indicates whether the lead qualifies as a hot lead |

| days_to_connection | INTEGER | Measure | Number of days between lead addition and connection |

| lead_status | STRING | | Normalized analytical lead status |

| agent_key | INTEGER | FK | Surrogate key referencing dim_agent |

| status_key | INTEGER | FK | Surrogate key referencing dim_lead_status |

| date_key | INTEGER | FK | Surrogate key referencing dim_date |



---



# 4. Dimension Layer



## dim_agent



**Grain:** One row per agent version.



This dimension supports agent-level analysis and slowly changing

dimension management.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| agent_key | INTEGER | PK | Surrogate identifier for an agent version |

| agent_name | STRING | | Agent name |

| valid_from | DATETIME | | Start timestamp for this dimension version |

| valid_to | DATETIME | | End timestamp for this dimension version; NULL for current version |

| is_current | BOOLEAN | | Indicates whether the dimension record is currently active |



**SCD Strategy:** Type 2 structure.



Historical versions can be retained by creating a new surrogate-key

record when tracked agent attributes change.



---



## dim_lead_status



**Grain:** One row per distinct lead status.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| status_key | INTEGER | PK | Surrogate identifier for a lead status |

| lead_status | STRING | | Normalized lead lifecycle status |



---



## dim_date



**Grain:** One row per calendar date.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| date_key | INTEGER | PK | Integer representation of calendar date |

| full_date | DATE | | Calendar date |

| year | INTEGER | | Calendar year |

| month | INTEGER | | Calendar month number |

| month_name | STRING | | Calendar month name |

| quarter | INTEGER | | Calendar quarter |

| day_of_month | INTEGER | | Day number within month |

| day_of_week | STRING | | Day of week |



---



# 5. Data Quality

## dq_results

**Purpose:** Stores historical data-quality assessment results for each pipeline/DQ execution.

**Grain:** One row per data-quality evaluation run.

**DQ threshold:** 95%.

**Composite score weighting:**

| Dimension | Weight |
|---|---:|
| Completeness | 25% |
| Uniqueness | 20% |
| Validity | 25% |
| Timeliness | 15% |
| Referential Integrity | 15% |

| Column | Type | Key | Business Definition |
|---|---|---|---|
| dq_run_id | STRING | Identifier | Unique identifier for the data-quality evaluation run |
| dq_timestamp | TIMESTAMP | | Timestamp when the DQ evaluation was performed |
| total_rows | INTEGER | | Number of records evaluated by the DQ checks |
| completeness_score | FLOAT | | Score representing completeness of required data |
| uniqueness_score | FLOAT | | Score representing uniqueness of records/identifiers |
| validity_score | FLOAT | | Score representing validity of field values and business rules |
| timeliness_score | FLOAT | | Score representing whether records meet timeliness expectations |
| referential_integrity_score | FLOAT | | Score representing validity of relationships between fact and dimension records |
| composite_dq_score | FLOAT | | Weighted overall data-quality score |
| threshold | FLOAT | | Minimum composite DQ score required for the pipeline to pass |
| dq_status | STRING | | Overall DQ result/status based on the composite score and threshold |




---


# 6. Dead-Letter Layer

## dead_letter_leads

**Purpose:** Stores records that fail validation during ingestion.

**Grain:** One row per rejected lead record for a pipeline run.

| Column | Type | Key | Business Definition |
|---|---|---|---|
| staging_id | STRING | Business identifier | Source lead identifier associated with the rejected record |
| name | STRING | | Lead name |
| job_title | STRING | | Lead's job title |
| company | STRING | | Company associated with the lead |
| industry | STRING | | Industry associated with the lead |
| location | STRING | | Lead's geographic location |
| agent | STRING | | Agent/account responsible for the lead |
| sdr_status | STRING | | SDR workflow status at ingestion |
| comment_status | STRING | | LinkedIn commenting activity status |
| hot_score | FLOAT | | Lead priority/temperature score |
| source | STRING | | Source from which the lead was captured |
| prioritized | STRING | | Indicates whether the lead was prioritized |
| linkedin_url | STRING | | LinkedIn profile URL |
| added_on | DATETIME | | Date/time the lead was added |
| last_contacted | DATETIME | | Most recent contact timestamp |
| invite_sent_at | DATETIME | | Timestamp when a connection invite was sent |
| connected_at | DATETIME | | Timestamp when the connection was established |
| record_updated_at | DATETIME | | Timestamp of the latest source-record update |
| load_timestamp | TIMESTAMP | | Timestamp when the record was processed |
| error_reason | STRING | | Validation or processing reason why the record was rejected |
| dead_letter_run_id | STRING | Run identifier | Pipeline run associated with the rejected record |
| dead_letter_timestamp | TIMESTAMP | | Timestamp when the record was written to the dead-letter table |

Dead-letter records are retained separately so that invalid records do not prevent valid records from entering the warehouse.

---
---



# 7. Pipeline Monitoring

## pipeline_runs

**Purpose:** Stores execution metadata for every pipeline run.

**Grain:** One row per pipeline execution.

| Column | Type | Key | Business Definition |
|---|---|---|---|
| run_id | STRING | PK/Run identifier | Unique identifier for a pipeline execution |
| pipeline_name | STRING | | Name of the pipeline being executed |
| started_at | TIMESTAMP | | Timestamp when the pipeline execution started |
| completed_at | TIMESTAMP | | Timestamp when the pipeline execution completed |
| rows_read | INTEGER | | Number of source records read during the run |
| rows_loaded | INTEGER | | Number of valid records successfully loaded |
| status | STRING | | Final execution status of the pipeline run |
| watermark_start | TIMESTAMP | | Starting watermark used to identify the incremental processing window |
| watermark_end | TIMESTAMP | | Ending watermark recorded after processing |
| error_message | STRING | | Error details when the pipeline execution fails |

This table supports operational monitoring, incremental processing, auditability, and troubleshooting.


---



# 8. Presentation / Analytics Tables

## analytics_lead_funnel

**Purpose:** Provides aggregated lead-funnel metrics for reporting.

**Grain:** One row containing overall lead-funnel metrics.

| Column | Type | Key | Business Definition |
|---|---|---|---|
| total_leads | INTEGER | | Total number of leads |
| contacted_leads | INTEGER | | Number of leads that have been contacted |
| invite_sent_leads | INTEGER | | Number of leads for whom a connection invite was sent |
| connected_leads | INTEGER | | Number of leads that became connected |
| hot_leads | INTEGER | | Number of leads classified as hot |
| connection_rate | FLOAT | | Percentage/rate of leads that became connected |
| invite_rate | FLOAT | | Percentage/rate of leads for whom an invite was sent |

---

## analytics_lead_status

**Purpose:** Provides lead counts and activity metrics grouped by normalized lead status.

**Grain:** One row per lead status.

| Column | Type | Key | Business Definition |
|---|---|---|---|
| lead_status | STRING | Business grouping | Normalized lifecycle status of the lead |
| lead_count | INTEGER | | Number of leads in the status |
| contacted_count | INTEGER | | Number of contacted leads in the status |
| connected_count | INTEGER | | Number of connected leads in the status |
| hot_lead_count | INTEGER | | Number of hot leads in the status |

---

## analytics_agent_performance

**Purpose:** Provides agent-level performance metrics.

**Grain:** One row per agent.

| Column | Type | Key | Business Definition |
|---|---|---|---|
| agent | STRING | Business grouping | Agent/account being evaluated |
| total_leads | INTEGER | | Total leads handled by the agent |
| contacted_leads | INTEGER | | Number of leads contacted by the agent |
| invite_sent_leads | INTEGER | | Number of leads for whom the agent sent an invite |
| connected_leads | INTEGER | | Number of leads connected by the agent |
| hot_leads | INTEGER | | Number of hot leads handled by the agent |
| connection_rate | FLOAT | | Rate at which the agent's leads became connected |

---

## analytics_risk_scores

**Purpose:** Stores advanced risk-model outputs for each agent.

**Grain:** One row per agent evaluated by the risk model.

| Column | Type | Key | Business Definition |
|---|---|---|---|
| agent | STRING | Business grouping | Agent/account evaluated by the risk model |
| total_leads | INTEGER | | Total leads associated with the agent |
| contacted_leads | INTEGER | | Number of leads contacted by the agent |
| invite_sent_leads | INTEGER | | Number of leads for whom an invite was sent |
| connected_leads | INTEGER | | Number of connected leads |
| hot_leads | INTEGER | | Number of leads classified as hot |
| replied_leads | INTEGER | | Number of leads that generated a reply |
| ghosted_leads | INTEGER | | Number of leads classified as ghosted |
| connection_rate | FLOAT | | Rate at which leads became connected |
| acceptance_rate | FLOAT | | Rate at which sent invites were accepted |
| reply_rate | FLOAT | | Rate at which contacted leads generated replies |
| ghosting_rate | FLOAT | | Rate at which leads were classified as ghosted |
| connection_rate_lower_95 | FLOAT | | Lower bound of the 95% confidence interval for connection rate |
| connection_rate_zscore | FLOAT | | Z-score measuring deviation of connection rate from the expected level |
| ghosting_risk_points | INTEGER | | Risk points assigned based on ghosting behavior |
| acceptance_risk_points | INTEGER | | Risk points assigned based on invite acceptance behavior |
| connection_anomaly_points | INTEGER | | Risk points assigned for anomalous connection performance |
| risk_score | INTEGER | | Overall risk score produced by the risk model |
| risk_level | STRING | | Risk classification derived from the risk score |
| recommended_daily_capacity | INTEGER | | Recommended daily operating capacity based on the risk assessment |
| statistical_confidence | STRING | | Confidence classification associated with the model assessment |
| model_status | STRING | | Status of the risk-model evaluation |
| avg_days_to_connection | FLOAT | | Average number of days required for leads to become connected |
---



# 9. Star Schema Relationships



The primary analytical model follows this structure:



```text

                    dim_agent

                       |

                       | agent_key

                       |

                       v

dim_date --------> fct_leads_star <-------- dim_lead_status

 date_key             |

                      |

                   Lead data

                   + measures

                   + flags
