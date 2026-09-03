# LinkedIn Agent Analytics Platform

A production-oriented analytics platform for monitoring, validating, and analyzing automated LinkedIn outreach activity.

The project implements an end-to-end data analytics pipeline covering data ingestion, validation, incremental and idempotent processing, BigQuery warehousing, star-schema modelling, data quality monitoring, statistical risk intelligence, Power BI reporting, Docker containerisation, CI/CD, structured logging, alerting, and failure/recovery validation.

---

## Candidate

**Sruthy Babu**

Data Science / Data Analytics

---

# Project Overview

The LinkedIn Agent Analytics Platform converts LinkedIn outreach data into reliable analytical datasets and actionable performance insights.

The platform is designed to answer questions such as:

- How many leads are being processed?
- How effective are the outreach and connection stages?
- What is the acceptance and reply performance?
- Which lead statuses dominate the pipeline?
- What is the current account risk level?
- What outreach capacity is recommended?
- Are data quality and referential integrity within acceptable limits?
- Can the pipeline recover from failures without creating duplicate records?
- Can malformed records be detected before reaching the analytical warehouse?

The solution follows an ETL/ELT-oriented architecture with a BigQuery analytical warehouse and Power BI reporting layer.

---

# Architecture

```text
                 LinkedIn / Polluxa Export
                           |
                           v
                    Raw CSV Dataset
                           |
                           v
                  Python Ingestion Layer
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
        Transformation  Validation   Deduplication
             |             |             |
             +-------------+-------------+
                           |
                           v
                Incremental Processing
                   + Watermarking
                           |
                           v
                    BigQuery Staging
                       stg_leads
                           |
                           v
                    Warehouse Layer
                       fct_leads
                           |
             +-------------+-------------+
             |                           |
             v                           v
      Analytics Tables              Star Schema
                                     Dimensions
                                         |
                  +----------------------+----------------+
                  |                      |                |
                  v                      v                v
              dim_agent          dim_lead_status      dim_date
                                         |
                                         v
                                  fct_leads_star
                                         |
                       +-----------------+----------------+
                       |                                  |
                       v                                  v
                Risk Intelligence                   Data Quality
                       |                                  |
                       +-----------------+----------------+
                                         |
                                         v
                                      Power BI
                                         |
                                         v
                              Business Analytics
