-- FinNexus Bot — PostgreSQL / Supabase schema
-- Apply in Supabase SQL editor when SUPABASE_URL is configured.
-- SQLite fallback mirrors this in Bot/db.py (_SQLITE_SCHEMA).

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    name            TEXT DEFAULT '',
    email           TEXT DEFAULT '',
    paper_cash      INTEGER DEFAULT 0,
    current_level   INTEGER DEFAULT 1,
    proficiency     REAL DEFAULT 0.0,
    highest_level_completed INTEGER DEFAULT 0,
    level_20_completed INTEGER DEFAULT 0,
    level_20_completed_at TIMESTAMPTZ,
    total_sessions  INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bot_sessions (
    id              TEXT PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    level           INTEGER NOT NULL,
    current_question INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'active',
    started_at      TIMESTAMPTZ,
    last_activity   TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS bot_answers (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    session_id      TEXT NOT NULL REFERENCES bot_sessions(id),
    question_id     TEXT NOT NULL,
    question_type   TEXT,
    answer          JSONB,
    score           REAL,
    is_level_20     BOOLEAN DEFAULT FALSE,
    feedback        TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_bot_progress (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    level_completed INTEGER NOT NULL,
    score           REAL,
    reward_earned   INTEGER DEFAULT 0,
    total_cash      INTEGER DEFAULT 0,
    next_level_unlocked BOOLEAN DEFAULT FALSE,
    completed_at    TIMESTAMPTZ,
    UNIQUE(user_id, level_completed)
);

CREATE INDEX IF NOT EXISTS idx_bot_sessions_user_status ON bot_sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_bot_answers_user ON bot_answers(user_id, created_at DESC);
