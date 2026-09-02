\# LinkedIn Agent Analytics — Data Dictionary



\## 1. Overview



This data dictionary documents the tables used in the LinkedIn Agent

Analytics platform, including staging, warehouse, dimension,

quality-control, pipeline-monitoring, and analytics tables.



\---



\# 2. Staging Layer



\## stg\_leads



\*\*Grain:\*\* One row per ingested LinkedIn lead.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| staging\_id | STRING | Business/record identifier | Unique identifier generated for an ingested lead |

| name | STRING | | Lead name |

| job\_title | STRING | | Lead's job title or professional headline |

| company | STRING | | Company associated with the lead |

| industry | STRING | | Industry associated with the lead |

| location | STRING | | Lead's geographic location |

| agent | STRING | | Agent/account responsible for the lead |

| sdr\_status | STRING | | Current SDR workflow status |

| comment\_status | STRING | | Status of LinkedIn commenting activity |

| hot\_score | FLOAT | | Lead priority/temperature score |

| source | STRING | | Source from which the lead was captured |

| prioritized | STRING | | Indicates whether the lead has been prioritized |

| linkedin\_url | STRING | | LinkedIn profile URL |

| added\_on | DATETIME | | Date/time the lead was added |

| last\_contacted | DATETIME | | Most recent contact timestamp |

| invite\_sent\_at | DATETIME | | Timestamp when connection invite was sent |

| connected\_at | DATETIME | | Timestamp when connection was established |

| record\_updated\_at | DATETIME | | Timestamp of the latest source-record update |

| load\_timestamp | TIMESTAMP | | Timestamp when the record entered the warehouse |



\---



\# 3. Fact Layer



\## fct\_leads\_star



\*\*Grain:\*\* One row per LinkedIn lead.



This table contains the analytical lead record and measures/flags

used for reporting and analysis.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| staging\_id | STRING | Business identifier | Source lead identifier |

| name | STRING | | Lead name |

| job\_title | STRING | | Lead's job title |

| company | STRING | | Lead's company |

| industry | STRING | | Lead's industry |

| location | STRING | | Lead's location |

| agent | STRING | | Agent responsible for the lead |

| sdr\_status | STRING | | SDR workflow status |

| comment\_status | STRING | | Comment activity status |

| hot\_score | FLOAT | | Lead score |

| source | STRING | | Lead source |

| prioritized | STRING | | Priority indicator |

| linkedin\_url | STRING | | LinkedIn profile URL |

| added\_on | DATETIME | | Lead creation/addition timestamp |

| last\_contacted | DATETIME | | Most recent contact timestamp |

| invite\_sent\_at | DATETIME | | Connection invite timestamp |

| connected\_at | DATETIME | | Connection timestamp |

| record\_updated\_at | DATETIME | | Source update timestamp |

| load\_timestamp | TIMESTAMP | | Warehouse ingestion timestamp |

| is\_contacted | INTEGER | Measure/flag | Indicates whether the lead has been contacted |

| is\_invite\_sent | INTEGER | Measure/flag | Indicates whether an invite has been sent |

| is\_connected | INTEGER | Measure/flag | Indicates whether the lead is connected |

| is\_prioritized | INTEGER | Measure/flag | Indicates whether the lead is prioritized |

| is\_hot\_lead | INTEGER | Measure/flag | Indicates whether the lead qualifies as a hot lead |

| days\_to\_connection | INTEGER | Measure | Number of days between lead addition and connection |

| lead\_status | STRING | | Normalized analytical lead status |

| agent\_key | INTEGER | FK | Surrogate key referencing dim\_agent |

| status\_key | INTEGER | FK | Surrogate key referencing dim\_lead\_status |

| date\_key | INTEGER | FK | Surrogate key referencing dim\_date |



\---



\# 4. Dimension Layer



\## dim\_agent



\*\*Grain:\*\* One row per agent version.



This dimension supports agent-level analysis and slowly changing

dimension management.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| agent\_key | INTEGER | PK | Surrogate identifier for an agent version |

| agent\_name | STRING | | Agent name |

| valid\_from | DATETIME | | Start timestamp for this dimension version |

| valid\_to | DATETIME | | End timestamp for this dimension version; NULL for current version |

| is\_current | BOOLEAN | | Indicates whether the dimension record is currently active |



\*\*SCD Strategy:\*\* Type 2 structure.



Historical versions can be retained by creating a new surrogate-key

record when tracked agent attributes change.



\---



\## dim\_lead\_status



\*\*Grain:\*\* One row per distinct lead status.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| status\_key | INTEGER | PK | Surrogate identifier for a lead status |

| lead\_status | STRING | | Normalized lead lifecycle status |



\---



\## dim\_date



\*\*Grain:\*\* One row per calendar date.



| Column | Type | Key | Business Definition |

|---|---|---|---|

| date\_key | INTEGER | PK | Integer representation of calendar date |

| full\_date | DATE | | Calendar date |

| year | INTEGER | | Calendar year |

| month | INTEGER | | Calendar month number |

| month\_name | STRING | | Calendar month name |

| quarter | INTEGER | | Calendar quarter |

| day\_of\_month | INTEGER | | Day number within month |

| day\_of\_week | STRING | | Day of week |



\---



\# 5. Data Quality



\## dq\_results



\*\*Purpose:\*\* Stores historical data-quality assessment results.



The table tracks quality dimensions including:



\- Completeness

\- Uniqueness

\- Validity

\- Timeliness

\- Referential integrity

\- Composite DQ score

\- Pass/fail status



\*\*DQ threshold:\*\* 95%.



\*\*Composite score weighting:\*\*



| Dimension | Weight |

|---|---:|

| Completeness | 25% |

| Uniqueness | 20% |

| Validity | 25% |

| Timeliness | 15% |

| Referential Integrity | 15% |



\---



\# 6. Dead-Letter Layer



\## dead\_letter\_leads



\*\*Purpose:\*\* Stores records that fail validation during ingestion.



Examples of captured validation errors include:



\- Missing LinkedIn URL

\- Missing staging identifier

\- Other record-level validation failures



Dead-letter records are retained separately so that invalid records

do not prevent valid records from entering the warehouse.



\---



\# 7. Pipeline Monitoring



\## pipeline\_runs



\*\*Purpose:\*\* Stores execution metadata for every pipeline run.



The table records pipeline execution information such as:



\- Run ID

\- Start timestamp

\- Completion timestamp

\- Rows read

\- Rows loaded

\- Pipeline status

\- Watermark start

\- Watermark end



This supports operational monitoring and auditability.



\---



\# 8. Presentation / Analytics Tables



\## analytics\_lead\_funnel



\*\*Purpose:\*\* Provides aggregated lead-funnel metrics for reporting.



\## analytics\_lead\_status



\*\*Purpose:\*\* Provides lead counts and metrics grouped by lead status.



\## analytics\_agent\_performance



\*\*Purpose:\*\* Provides agent-level performance metrics.



Important metrics include:



\- Total leads

\- Contacted leads

\- Invite-sent leads

\- Connected leads

\- Hot leads

\- Connection rate



\## analytics\_risk\_scores



\*\*Purpose:\*\* Stores advanced risk-model outputs for each agent.



Important outputs include:



\- Connection rate

\- Acceptance rate

\- Reply rate

\- Ghosting rate

\- 95% lower confidence bound

\- Risk score

\- Risk level

\- Recommended daily capacity

\- Statistical confidence

\- Model status



\---



\# 9. Star Schema Relationships



The primary analytical model follows this structure:



```text

&#x20;                   dim\_agent

&#x20;                      |

&#x20;                      | agent\_key

&#x20;                      |

&#x20;                      v

dim\_date --------> fct\_leads\_star <-------- dim\_lead\_status

&#x20;date\_key             |

&#x20;                     |

&#x20;                  Lead data

&#x20;                  + measures

&#x20;                  + flags

