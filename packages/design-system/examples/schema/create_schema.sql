-- ============================================
-- JHG Application Schema Template
-- ============================================
-- This template creates a standard schema for JHG Flask applications
-- using Databricks Unity Catalog.
--
-- Usage:
--   1. Replace {catalog} with your Unity Catalog name
--   2. Replace {schema} with your application schema name
--   3. Execute in Databricks SQL warehouse
-- ============================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}
COMMENT 'Application schema for JHG Flask app';

USE {catalog}.{schema};

-- ============================================
-- AUDIT LOG TABLE
-- ============================================
-- Tracks all user actions and system events
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    timestamp TIMESTAMP NOT NULL,
    app_name STRING NOT NULL,
    action STRING NOT NULL,
    user_id STRING,
    session_id STRING,
    ip_address STRING,
    metadata STRING,  -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
COMMENT 'Application audit log'
TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true,
    delta.autoOptimize.autoCompact = true,
    delta.logRetentionDuration = 'interval 30 days',
    delta.deletedFileRetentionDuration = 'interval 7 days'
);

-- Optimize audit log for time-based queries
ALTER TABLE audit_log SET TBLPROPERTIES (
    delta.tuneFileSizesForRewrites = true
);


-- ============================================
-- CACHE METADATA TABLE (Optional)
-- ============================================
-- For distributed caching across multiple instances
CREATE TABLE IF NOT EXISTS cache_metadata (
    cache_key STRING NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ttl_seconds INT NOT NULL,
    data_hash STRING,  -- For invalidation detection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP,
    CONSTRAINT pk_cache PRIMARY KEY (cache_key)
)
USING DELTA
COMMENT 'Cache metadata for distributed caching'
TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true,
    delta.autoOptimize.autoCompact = true
);


-- ============================================
-- USER PREFERENCES TABLE (Optional)
-- ============================================
-- Store user-specific settings
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id STRING NOT NULL,
    preference_key STRING NOT NULL,
    preference_value STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP,
    CONSTRAINT pk_user_pref PRIMARY KEY (user_id, preference_key)
)
USING DELTA
COMMENT 'User preferences and settings'
TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true,
    delta.autoOptimize.autoCompact = true
);


-- ============================================
-- APPLICATION CONFIGURATION TABLE
-- ============================================
-- Runtime configuration stored in database
CREATE TABLE IF NOT EXISTS app_config (
    config_key STRING NOT NULL,
    config_value STRING,
    description STRING,
    is_secret BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP,
    CONSTRAINT pk_app_config PRIMARY KEY (config_key)
)
USING DELTA
COMMENT 'Application configuration'
TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true
);


-- ============================================
-- FEATURE FLAGS TABLE
-- ============================================
-- Control feature rollouts
CREATE TABLE IF NOT EXISTS feature_flags (
    flag_name STRING NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INT DEFAULT 0,  -- 0-100 for gradual rollout
    description STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP,
    CONSTRAINT pk_feature_flags PRIMARY KEY (flag_name)
)
USING DELTA
COMMENT 'Feature flags for gradual rollout'
TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true
);


-- ============================================
-- SESSION TABLE (For custom session storage)
-- ============================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id STRING NOT NULL,
    user_id STRING,
    data STRING,  -- JSON blob
    ip_address STRING,
    user_agent STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    expires_at TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP,
    CONSTRAINT pk_sessions PRIMARY KEY (session_id)
)
USING DELTA
COMMENT 'User sessions'
TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true,
    delta.autoOptimize.autoCompact = true
);


-- ============================================
-- GRANTS (Adjust principals as needed)
-- ============================================
-- Grant usage on schema
-- GRANT USAGE ON SCHEMA {catalog}.{schema} TO `app-service-principal`;

-- Grant read/write on tables
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {catalog}.{schema}.audit_log TO `app-service-principal`;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {catalog}.{schema}.cache_metadata TO `app-service-principal`;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {catalog}.{schema}.user_preferences TO `app-service-principal`;
-- GRANT SELECT ON TABLE {catalog}.{schema}.app_config TO `app-service-principal`;
-- GRANT SELECT ON TABLE {catalog}.{schema}.feature_flags TO `app-service-principal`;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {catalog}.{schema}.sessions TO `app-service-principal`;


-- ============================================
-- VIEWS
-- ============================================

-- Recent audit events (last 7 days)
CREATE OR REPLACE VIEW v_recent_audit AS
SELECT *
FROM audit_log
WHERE timestamp >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY timestamp DESC;

-- Active sessions
CREATE OR REPLACE VIEW v_active_sessions AS
SELECT *
FROM sessions
WHERE expires_at > CURRENT_TIMESTAMP()
ORDER BY last_accessed_at DESC;

-- Enabled feature flags
CREATE OR REPLACE VIEW v_enabled_features AS
SELECT flag_name, rollout_percentage, description
FROM feature_flags
WHERE is_enabled = TRUE;


-- ============================================
-- SAMPLE DATA (Optional - for development)
-- ============================================

-- Insert sample feature flags
-- INSERT INTO feature_flags (flag_name, is_enabled, rollout_percentage, description)
-- VALUES
--     ('dark_mode', TRUE, 100, 'Enable dark mode theme'),
--     ('new_dashboard', TRUE, 50, 'New dashboard design (50% rollout)'),
--     ('export_pdf', FALSE, 0, 'PDF export feature');

-- Insert sample config
-- INSERT INTO app_config (config_key, config_value, description, is_secret)
-- VALUES
--     ('cache_ttl_default', '600', 'Default cache TTL in seconds', FALSE),
--     ('max_upload_size', '10485760', 'Max file upload size in bytes', FALSE),
--     ('maintenance_mode', 'false', 'Enable maintenance mode', FALSE);
