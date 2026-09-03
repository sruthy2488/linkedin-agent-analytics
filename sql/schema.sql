-- ============================================================
-- LinkedIn Agent Analytics
-- BigQuery Warehouse Schema
-- ============================================================

-- Dataset:
-- linkedin_agent_analytics


-- ============================================================
-- STAGING TABLE
-- ============================================================

-- stg_leads
--
-- Grain:
-- One row per validated lead record.
--
-- Main business identifier:
-- staging_id

-- Columns:
-- staging_id
-- name
-- job_title
-- company
-- industry
-- location
-- agent
-- sdr_status
-- comment_status
-- hot_score
-- source
-- prioritized
-- linkedin_url
-- added_on
-- last_contacted
-- invite_sent_at
-- connected_at
-- record_updated_at
-- load_timestamp


-- ============================================================
-- FACT TABLE
-- ============================================================

-- fct_leads
--
-- Grain:
-- One row per lead.
--
-- Business key:
-- staging_id


-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- dim_agent
--
-- Primary key:
-- agent_key
--
-- Attribute:
-- agent_name


-- dim_lead_status
--
-- Primary key:
-- status_key
--
-- Attribute:
-- lead_status


-- dim_date
--
-- Primary key:
-- date_key
--
-- Attribute:
-- full_date


-- ============================================================
-- STAR FACT TABLE
-- ============================================================

-- fct_leads_star
--
-- Grain:
-- One row per lead.
--
-- Foreign keys:
-- agent_key  -> dim_agent.agent_key
-- status_key -> dim_lead_status.status_key
-- date_key   -> dim_date.date_key


-- ============================================================
-- ANALYTICS TABLES
-- ============================================================

-- analytics_lead_funnel
-- analytics_lead_status
-- analytics_agent_performance
-- analytics_risk_scores
-- dq_results
