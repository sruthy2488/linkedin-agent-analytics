LinkedIn Agent Analytics Platform
Project Documentation

Candidate: Sruthy Babu
Project: LinkedIn Agent Analytics
Repository: https://github.com/sruthy2488/linkedin-agent-analytics

1. Project Overview

The LinkedIn Agent Analytics Platform is an end-to-end data analytics solution designed to transform LinkedIn outreach data into reliable, validated, and actionable business insights.

The platform covers the complete analytical lifecycle:

Source data ingestion
Data transformation and standardisation
Duplicate detection
Record validation and dead-letter handling
Incremental and idempotent loading
BigQuery data warehousing
Star-schema modelling
Data quality monitoring
Statistical risk analysis
Outreach capacity recommendation
Power BI reporting
Docker containerisation
Automated testing
CI/CD using GitHub Actions
Structured logging
Operational alerting
Failure and recovery validation

The objective is to provide a reliable analytics layer for monitoring LinkedIn lead generation and outreach performance while identifying operational and account-level risks.

2. Business Objectives

The platform is designed to provide visibility into the following business questions:

How many leads are currently available?
How many leads have received invitations?
What percentage of invitations result in connections?
What is the reply performance?
Which lead statuses dominate the pipeline?
What is the current account health and risk level?
How much outreach capacity should be recommended?
Are the underlying data and relationships reliable?
Can the pipeline safely recover from failures?
Can invalid source data be identified before entering the analytical warehouse?

3. Technology Stack

| Area              | Technology                     |
| ----------------- | ------------------------------ |
| Programming       | Python 3.11                    |
| Data Processing   | Pandas, NumPy                  |
| Data Warehouse    | Google BigQuery                |
| BI / Reporting    | Microsoft Power BI             |
| Query / Analytics | SQL, DAX                       |
| Testing           | Pytest                         |
| Containerisation  | Docker                         |
| Version Control   | Git / GitHub                   |
| CI/CD             | GitHub Actions                 |
| Logging           | Structured JSON logging        |
| Alerting          | Discord webhook                |
| Configuration     | Environment variables / `.env` |


4. System Architecture
                LinkedIn / Polluxa Data Export
                           |
                           v
                     Raw CSV Data
                           |
                           v
                  Python Ingestion Layer
                           |
              +------------+------------+
              |            |            |
              v            v            v
        Transformation  Validation  Deduplication
              |            |            |
              +------------+------------+
                           |
                           v
                Incremental Processing
                  + Watermark Logic
                           |
                           v
                     BigQuery
                           |
                    +------+------+
                    |             |
                    v             v
               Staging Layer   Warehouse
                  stg_leads      fct_leads
                                    |
                                    v
                              Star Schema
                                    |
                   +----------------+----------------+
                   |                |                |
                   v                v                v
               dim_agent     dim_lead_status     dim_date
                   |                |                |
                   +----------------+----------------+
                                    |
                                    v
                              fct_leads_star
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
               Risk Model                      DQ Framework
                    |                               |
                    +---------------+---------------+
                                    |
                                    v
                                 Power BI
                                    |
                                    v
                            Business Reporting

5. End-to-End Data Flow

The complete data flow is:
Source Export
     ↓
Raw CSV
     ↓
Read and Transform
     ↓
Stable Lead ID Generation
     ↓
Duplicate Removal
     ↓
Record Validation
     ↓
Dead-Letter Separation
     ↓
Incremental Watermark Filtering
     ↓
BigQuery Staging
     ↓
Warehouse Refresh
     ↓
Star Schema Refresh
     ↓
Referential Integrity Validation
     ↓
Data Quality Checks
     ↓
Risk Model
     ↓
Power BI
Each pipeline execution receives a unique run ID for traceability.

6. Source Dataset

The current analytical source is a LinkedIn lead export containing 468 records.

The dataset contains fields including:
| Source Field   | Description                     |
| -------------- | ------------------------------- |
| Name           | Lead name                       |
| Job Title      | Current job title               |
| Company        | Lead's company                  |
| Industry       | Industry classification         |
| Location       | Lead location                   |
| Agent          | LinkedIn outreach agent         |
| SDR Status     | Current lead status             |
| Comment Status | Comment-related status          |
| Hot Score      | Lead priority / score           |
| Source         | Lead acquisition source         |
| Prioritized    | Lead priority indicator         |
| LinkedIn URL   | LinkedIn profile URL            |
| Added On       | Date/time lead was added        |
| Last Contacted | Last outreach/contact timestamp |
| Invite Sent At | Timestamp of invitation         |
| Connected At   | Timestamp of connection         |


7. Data Ingestion

The primary ingestion module is:
src/ingest.py
The ingestion process performs the following operations:

7.1 Read Source Data

The pipeline reads the raw LinkedIn lead export.

7.2 Transform Source Columns

Source field names are converted into standardised analytical column names.

Example:
Name             → name
Job Title        → job_title
Company          → company
Industry         → industry
Agent            → agent
SDR Status       → sdr_status
LinkedIn URL     → linkedin_url
Added On         → added_on

Operational fields are also generated:
staging_id
record_updated_at
load_timestamp

7.3 Stable Lead ID

A deterministic identifier is created from the LinkedIn URL.

The same LinkedIn URL generates the same identifier across repeated runs.

This supports:

Duplicate detection
Idempotent processing
Stable record identification


8. Data Validation

The ingestion layer validates records before warehouse loading.

Validation rules include checks for:

LinkedIn URL
Staging ID
Added date
Required fields
Basic record consistency

Invalid records are separated into a dead-letter dataset rather than silently entering the warehouse.

9. Duplicate Detection

Duplicate leads are removed before loading.

The latest successful run produced:
Rows read:             468
Duplicates removed:      0
The final warehouse fact table contained:
468 rows
468 unique staging IDs

10. Incremental and Idempotent Loading

The ingestion process uses a watermark to determine which records require processing.

Processing logic
Previous Watermark
        ↓
Read Current Source
        ↓
Identify New / Updated Records
        ↓
Validate
        ↓
Load
        ↓
Update Watermark

A repeated run with no new records does not create additional rows.

The latest repeat run produced:
Starting watermark:        2026-09-03 11:47:00+00:00
Previous watermark:        2026-09-03 11:47:00+00:00
Records newer than watermark: 0

Existing records in staging: 468
Final records in staging:     468
This demonstrates idempotent behaviour.

11. BigQuery Data Warehouse

The project uses Google BigQuery as the analytical warehouse.

11.1 Staging Table
stg_leads

Purpose:

Stores transformed lead records after ingestion and validation.

11.2 Fact Table
fct_leads

Purpose:

Provides the lead-level analytical fact dataset used by downstream analytics.

11.3 Analytical Tables

The pipeline refreshes analytical tables including:

analytics_lead_funnel
analytics_lead_status
analytics_agent_performance
analytics_risk_scores

These tables are designed for Power BI and analytical consumption.

12. Star Schema

The project implements a dimensional star schema.

Fact Table
fct_leads_star

Dimensions
dim_agent
dim_lead_status
dim_date

Fact-to-Dimension Relationships
                  dim_agent
                      |
                      |
                      v
               agent_key
                      |
                      |
dim_lead_status → fct_leads_star ← dim_date
                      |
                      |
                 Lead Facts

The fact table contains surrogate keys:
agent_key
status_key
date_key

13. Star Schema Grain

The grain of the fact table is:

One row per lead record identified by its stable staging_id.

This means each lead represents one analytical fact record at the lead level.

The latest validation produced:
Fact rows:              468
Unique staging IDs:     468
Orphan agents:            0
Orphan statuses:          0
Orphan dates:             0

Result:
Star Schema validation PASSED

14. Dimension Tables
14.1 dim_agent

Stores agent-level dimension information.

Key:
agent_key

Business attribute:
agent_name

14.2 dim_lead_status

Stores standardised lead-status members.

Current dimension values:
captured
connected
contacted
invite_sent
enriched
linkedin_rate_limited
replied

Normalization ensures values such as:
invite sent
and:
invite_sent
are treated consistently.


14.3 dim_date

Stores the date dimension used for time-based analysis.

Key:

date_key

Business attribute:

full_date


15. Data Dictionary
stg_leads / fct_leads / fct_leads_star
| Column            | Description             | Role                 |
| ----------------- | ----------------------- | -------------------- |
| staging_id        | Stable lead identifier  | Primary/business key |
| name              | Lead name               | Attribute            |
| job_title         | Job title               | Attribute            |
| company           | Company                 | Attribute            |
| industry          | Industry                | Attribute            |
| location          | Lead location           | Attribute            |
| agent             | Outreach agent          | Attribute            |
| sdr_status        | Current SDR status      | Attribute            |
| comment_status    | Comment status          | Attribute            |
| hot_score         | Lead priority score     | Measure/input        |
| source            | Lead acquisition source | Attribute            |
| prioritized       | Priority indicator      | Attribute            |
| linkedin_url      | LinkedIn profile URL    | Business identifier  |
| added_on          | Lead creation timestamp | Date/time            |
| last_contacted    | Last contact timestamp  | Date/time            |
| invite_sent_at    | Invitation timestamp    | Date/time            |
| connected_at      | Connection timestamp    | Date/time            |
| record_updated_at | Source/update timestamp | Operational field    |
| load_timestamp    | Pipeline load timestamp | Operational field    |
| agent_key         | Agent surrogate key     | Foreign key          |
| status_key        | Status surrogate key    | Foreign key          |
| date_key          | Date surrogate key      | Foreign key          |


16. Data Quality Framework

The project implements five primary data-quality dimensions.

Completeness

Measures whether required fields are populated.

Uniqueness

Measures duplicate-record violations.

Validity

Measures whether data conforms to expected formats and rules.

Timeliness

Measures whether source data is sufficiently current.

Referential Integrity

Measures whether every fact row can be matched to the corresponding dimension.

17. Composite DQ Score

The individual dimensions are combined into a weighted composite DQ score.

The acceptance threshold is:

95%

Latest result:

Completeness:             100.00%
Uniqueness:               100.00%
Validity:                  93.95%
Timeliness:               100.00%
Referential Integrity:    100.00%

Composite DQ Score:        98.49%
Threshold:                 95.00%

Status: PASS

DQ results are stored historically in:

dq_results

This supports monitoring over multiple pipeline executions.

18. Risk Intelligence

The project includes a statistical risk model designed to identify account-level outreach risk.

The model considers:

Connection rate
Acceptance rate
Reply rate
Ghosting rate
Statistical confidence
Recommended daily outreach capacity

The model also calculates a lower confidence bound for the connection rate.

19. Latest Risk Model Result

Agent: Sruthy Babu

Total leads:                 468
Connection rate:             24.79%
Acceptance rate:             33.14%
Reply rate:                   0.23%
Ghosting rate:               58.00%

95% lower confidence bound:  21.09%

Risk score:                  35.00
Risk level:                  MEDIUM

Recommended daily capacity:  23

Statistical confidence:
Adequate for rate monitoring

Model status:
STATISTICALLY_ACTIONABLE

The result is stored in:

analytics_risk_scores

20. Power BI Dashboard

The Power BI report contains three pages.


20.1 Page 1 — Lead & Outreach Overview

This page provides the overall view of outreach performance.

KPIs
Total Leads
Invites Sent
Acceptance Rate
Reply Rate
Connected Leads
Conversion Rate
Capacity vs Recommended
Risk Score
Risk Level
Ghosting Rate
DQ Score
Visuals
Lead Status Funnel
Status Distribution
Daily Lead Generation
Risk indicators
Data Quality indicator
20.2 Page 2 — Agent Analytics & Risk Intelligence

This page focuses on account health and operational risk.

KPIs
Total Leads
Connected Leads
Ghosting Rate
Risk Score
Recommended Daily Capacity
Visuals
Agent Performance
Account Lead Status
Risk Intelligence
Risk Outcomes
LinkedIn Rate Limited Leads
Capacity analysis
20.3 Page 3 — Campaign & Segment Performance

This page analyses lead performance by available source and segment fields.

KPIs
Total Leads
Invites
Connected Leads
Acceptance Rate
Conversion Rate
Visuals
Source / campaign performance
Industry performance
Segment performance
Campaign performance table

Because the source data does not provide reliable campaign cost and revenue fields, monetary ROI values are not fabricated.

21. Power BI Measures

The Power BI semantic model uses explicit DAX measures.

Examples include:

Total Leads
Invites Sent
Acceptance Rate
Reply Rate
Connected Leads
Conversion Rate
Ghosted Leads
Replied Leads
Rate Limited Leads
Rate Limit Rate
Risk Score
Recommended Daily Capacity
DQ Score

This avoids dependence on implicit aggregations and keeps KPI definitions controlled.

22. Data Reconciliation

The Power BI dashboard uses the validated 468-record export loaded into the analytical warehouse.

The live Polluxa dashboard may display different figures because it represents a different data snapshot.

Therefore:

Dashboard KPIs are calculated from the validated exported dataset used by the analytics pipeline.

The project does not hard-code live dashboard counts into Power BI.

Fields unavailable in the exported dataset are not artificially created.

23. Statistical and Business Assumptions

The risk model assumes that:

Historical outreach behaviour is useful for estimating current operational risk.
Connection and reply rates provide meaningful indicators of account health.
The available sample is sufficiently large for rate monitoring.
Recommended capacity should remain within the defined daily ceiling.
Statistical confidence should be considered when interpreting rate-based risk indicators.

The current model reports:

Statistical confidence:
Adequate for rate monitoring

The recommendations should be treated as analytical guidance rather than guaranteed business outcomes.

24. Testing

Automated tests are implemented using Pytest.

Test coverage includes:

Lead ID
Stable lead ID generation
Case-insensitive URL handling
Missing URL handling
Validation
Valid records
Missing LinkedIn URL
Missing staging ID
Missing added date
Transformation
Normalized output columns
Stable staging IDs
Metadata fields
Duplicate removal

Run the tests with:

python -m pytest -v

The final test suite passes successfully.

25. CI/CD

GitHub Actions is used for continuous integration.

Pipeline:

Git Push / Pull Request
        ↓
Checkout Repository
        ↓
Setup Python 3.11
        ↓
Install Dependencies
        ↓
Run Pytest
        ↓
Build Docker Image

The Docker build is executed only after successful tests.

The final CI workflow completed successfully.

26. Dockerisation

The application is containerised using Docker.

Build:

docker build -t linkedin-agent-analytics .

Run:

docker run --rm linkedin-agent-analytics

The Docker configuration:

Uses Python 3.11
Installs pinned dependencies
Copies application source
Keeps runtime data external
Uses environment-based configuration

The Docker image was successfully created and validated.

27. Dependency Management

Dependencies are pinned in:

requirements.txt

The project uses pinned versions for reproducible installation.

The main dependencies include:

google-cloud-bigquery
pandas
numpy
db-dtypes
pyarrow
python-dotenv
python-json-logger
pytest
28. Structured Logging

The application uses structured JSON logging.

Each pipeline execution is assigned a unique run ID.

Example:

run_id = 12d7547b-e686-4045-8528-eebf255c6fca

The run ID provides correlation across pipeline events.

Structured logging makes logs easier to search and process by monitoring tools.

29. Alerting

Operational alerts are implemented for important pipeline events.

Supported alert scenarios include:

Pipeline failure
Data quality threshold breach
Abnormally long execution duration

Example failure flow:

Pipeline Error
      ↓
Structured Log
      ↓
Failure Alert
      ↓
Pipeline Run Recorded as FAILED
30. Failure Handling and Recovery

A controlled star-schema failure occurred during validation when fact-table status values were not fully represented in the status dimension.

The pipeline correctly detected:

Missing agent keys:   0
Missing status keys:  319
Missing date keys:    0

The pipeline then:

Detected the referential-integrity failure.
Raised an exception.
Sent a pipeline_failure alert.
Recorded the run as FAILED.

The status dimension was corrected and the pipeline was rerun.

The recovered pipeline achieved:

Missing agent keys:   0
Missing status keys:  0
Missing date keys:    0

Star Schema validation PASSED.

The final recovery execution completed successfully:

Composite DQ Score: 98.49%
DQ Status: PASS
Pipeline run: SUCCESS
31. Idempotent Recovery

After recovery, the pipeline was executed again using the existing watermark.

Result:

Records newer than watermark: 0
Existing records in staging:  468
Final records in staging:     468

This confirms that recovery did not create duplicate fact records.

32. Malformed Input / Dead-Letter Testing

A controlled malformed-input test was performed against a temporary copy of the source dataset.

One record was created with a missing LinkedIn URL.

The validation result was:

Valid records:        468
Dead-letter records:    1

The error was identified as:

Missing linkedin_url

The invalid record was isolated and the original source dataset remained unchanged.

This demonstrates that malformed records can be caught before entering the analytical warehouse.

33. Security and Configuration

Environment-specific values are kept outside source control.

A local .env file can contain:

GCP_PROJECT_ID=your_project_id
BQ_DATASET=linkedin_agent_analytics

API_URL=your_api_url
API_TOKEN=your_api_token

ALERT_ENABLED=true
ALERT_WEBHOOK_URL=your_webhook_url

MAX_RUN_DURATION_SECONDS=300
FULL_REFRESH=false

Sensitive values should never be committed to GitHub.

The repository contains .env.example rather than actual credentials.

34. Database Build and Migration Scripts

Database creation and warehouse-building logic is implemented through Python/BigQuery scripts under:

src/

Relevant scripts include:

create_dimensions.py
create_star_analytics.py
refresh_warehouse.py
refresh_star_schema.py
fix_dim_agent.py
fix_status_dimension.py

These scripts support:

Dimension creation
Fact-table construction
Analytical-table refresh
Star-schema creation
Dimension-key validation
Referential-integrity validation
35. Current Final Validation

The final successful pipeline run produced the following state:

Source rows:                     468
Duplicates removed:               0
Valid records:                   468
Dead-letter records:               0
New records on repeat run:         0

Fact rows:                       468
Unique staging IDs:              468

Missing agent keys:                0
Missing status keys:               0
Missing date keys:                 0

Composite DQ score:            98.49%
DQ threshold:                   95.00%
DQ status:                         PASS

Risk score:                      35.00
Risk level:                       MEDIUM
Recommended capacity:               23

Pipeline status:                 SUCCESS
36. Assessment Deliverables

The final submission contains the following:

Source Repository

GitHub repository containing:

Complete Python source code
Tests
Dockerfile
Requirements
CI/CD workflow
README
Database build scripts
Configuration template
Power BI
.pbix Power BI file
PDF export
Screenshots of all three dashboard pages
Documentation
Architecture
Data flow
Database/star schema
Data dictionary
Data quality framework
Risk-model explanation
Operational and CI/CD documentation
Part 1 Evidence
Seven-step integration screenshots
Declared Account Age tier
37. Part 1 Evidence

The Part 1 evidence pack documents the seven-step LinkedIn integration process and supporting screenshots.

Account Age Tier

Declared Account Age Tier: [INSERT YOUR EXACT TIER FROM YOUR PART 1 EVIDENCE]

The declared tier should match the tier used for the capacity/rate-limit assumptions in the assessment.

38. Limitations

The following limitations apply to the current implementation:

The analytical dataset is an exported snapshot and may not exactly match the live application at the same time.
Monetary campaign cost and revenue data is not available, so monetary ROI is not calculated.
Risk recommendations are based on available historical outreach behaviour and should be interpreted as analytical guidance.
LinkedIn operational limits and platform behaviour may change independently of the analytical model.
The current solution is designed around the provided assessment dataset and configuration.
39. Reproduction Instructions

Clone the repository:

git clone https://github.com/sruthy2488/linkedin-agent-analytics.git
cd linkedin-agent-analytics

Install dependencies:

pip install -r requirements.txt

Configure environment variables using:

.env.example

Authenticate to Google Cloud with appropriate BigQuery access.

Run the pipeline:

python src/ingest.py

Run tests:

python -m pytest -v

Build Docker image:

docker build -t linkedin-agent-analytics .
40. Conclusion

The LinkedIn Agent Analytics Platform provides a complete analytical workflow from source ingestion to business intelligence reporting.

The final implementation demonstrates:

Reliable data ingestion
Incremental processing
Idempotent loading
Duplicate prevention
Data validation
Dead-letter handling
BigQuery warehousing
Star-schema modelling
Referential-integrity validation
Data quality monitoring
Statistical risk intelligence
Capacity recommendation
Power BI reporting
Automated testing
Dockerisation
CI/CD
Structured logging
Operational alerting
Failure detection
Recovery without duplication

The final validated pipeline achieved a 98.49% composite data-quality score, passed star-schema integrity checks, completed risk analysis successfully, and demonstrated successful recovery without duplicate records.

Repository

GitHub:
https://github.com/sruthy2488/linkedin-agent-analytics

Candidate

Sruthy Babu

Data Science | Data Analytics