-- ============================================================================
-- Melooha AI Vedic Astrology - PostgreSQL / Supabase Database Schema
-- Run this script in the Supabase SQL Editor to initialize all tables
-- ============================================================================

-- 1. Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Users Table (Google OAuth & User Credentials)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    google_id VARCHAR(100) UNIQUE,
    avatar_url VARCHAR(500),
    auth_provider VARCHAR(50) DEFAULT 'google',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- 3. Birth Profiles Table (Vedic horary inputs)
CREATE TABLE IF NOT EXISTS birth_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    birth_time VARCHAR(10),
    time_known BOOLEAN DEFAULT TRUE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timezone_str VARCHAR(64) NOT NULL,
    place_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_birth_profiles_user_id ON birth_profiles(user_id);

-- 4. Computed Astrological Charts (Lahiri Sidereal Swiss Ephemeris Facts)
CREATE TABLE IF NOT EXISTS charts (
    id VARCHAR(36) PRIMARY KEY,
    birth_profile_id VARCHAR(36) UNIQUE NOT NULL REFERENCES birth_profiles(id) ON DELETE CASCADE,
    ayanamsa VARCHAR(32) DEFAULT 'Lahiri' NOT NULL,
    facts_json JSONB NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_charts_birth_profile_id ON charts(birth_profile_id);

-- 5. User Questions History
CREATE TABLE IF NOT EXISTS questions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_questions_user_id ON questions(user_id);

-- 6. Generated Astrological Answers with Grounded Citations
CREATE TABLE IF NOT EXISTS answers (
    id VARCHAR(36) PRIMARY KEY,
    question_id VARCHAR(36) UNIQUE NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    cited_facts_json JSONB,
    grounding_status VARCHAR(32) DEFAULT 'grounded' NOT NULL,
    replaced_reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_answers_question_id ON answers(question_id);

-- 7. Question Credits Append-Only Ledger
CREATE TABLE IF NOT EXISTS balance_ledger (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delta INTEGER NOT NULL,
    reason VARCHAR(100) NOT NULL,
    idempotency_key VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_balance_ledger_user_id ON balance_ledger(user_id);

-- 8. Analytics & Telemetry Events
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    event_name VARCHAR(64) NOT NULL,
    payload_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_event_name ON events(event_name);

-- 9. A/B Testing Experiments Table (Part A3: Arm assignment)
CREATE TABLE IF NOT EXISTS experiments (
    user_id VARCHAR(36) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    arm VARCHAR(32) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 10. Past Check Sets (Trust verification before paywall)
CREATE TABLE IF NOT EXISTS past_check_sets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chart_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_past_check_user_chart UNIQUE (user_id, chart_hash)
);

CREATE INDEX IF NOT EXISTS idx_past_check_sets_user_id ON past_check_sets(user_id);

-- 11. Past Check Items (3 candidate statements per set, with server-only decoy flag)
CREATE TABLE IF NOT EXISTS past_check_items (
    id VARCHAR(36) PRIMARY KEY,
    set_id VARCHAR(36) NOT NULL REFERENCES past_check_sets(id) ON DELETE CASCADE,
    fact_id VARCHAR(32) NOT NULL,
    event_date VARCHAR(16) NOT NULL,
    theme VARCHAR(32) NOT NULL,
    text_en TEXT NOT NULL,
    text_hi TEXT NOT NULL,
    is_decoy BOOLEAN DEFAULT FALSE NOT NULL,
    answer VARCHAR(16),
    answered_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_past_check_items_set_id ON past_check_items(set_id);
