-- =====================================================================
-- MELOOHA AUSPICIOUS MUHURTA PLANNER: POSTGRESQL SCHEMA MIGRATION
-- =====================================================================

-- 1. Muhurta Plans Table
CREATE TABLE IF NOT EXISTS muhurta_plans (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    birth_profile_id VARCHAR(36) REFERENCES birth_profiles(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    category VARCHAR(64) NOT NULL,
    override VARCHAR(64),
    location_name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timezone_str VARCHAR(64) NOT NULL,
    target_start_date DATE NOT NULL,
    target_end_date DATE NOT NULL,
    time_preference VARCHAR(32) DEFAULT 'any' NOT NULL,
    slots_json JSONB NOT NULL,
    advisory_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexing for high-frequency user lookup and date querying
CREATE INDEX IF NOT EXISTS idx_muhurta_plans_user_id ON muhurta_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_muhurta_plans_profile_id ON muhurta_plans(birth_profile_id);
CREATE INDEX IF NOT EXISTS idx_muhurta_plans_created_at ON muhurta_plans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_muhurta_plans_category ON muhurta_plans(category);

-- 2. Proactive Webhook & Notification Dispatcher Queue
CREATE TABLE IF NOT EXISTS muhurta_notifications (
    id VARCHAR(36) PRIMARY KEY,
    muhurta_plan_id VARCHAR(36) NOT NULL REFERENCES muhurta_plans(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(32) DEFAULT 'push' NOT NULL, -- 'push', 'whatsapp', 'telegram'
    trigger_time TIMESTAMP WITH TIME ZONE NOT NULL,
    reminder_type VARCHAR(16) NOT NULL, -- '24h', '1h'
    status VARCHAR(32) DEFAULT 'pending' NOT NULL, -- 'pending', 'sent', 'failed'
    payload JSONB,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexing for background cron / worker dispatching
CREATE INDEX IF NOT EXISTS idx_muhurta_notif_pending ON muhurta_notifications(status, trigger_time)
WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_muhurta_notif_user ON muhurta_notifications(user_id);
