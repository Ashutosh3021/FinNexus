-- FinNexus Bot — PostgreSQL / Supabase schema
-- Apply in Supabase SQL editor when SUPABASE_URL is configured.
-- SQLite fallback mirrors this in Bot/db.py (_SQLITE_SCHEMA).

-- ─── Tables ───────────────────────────────────────────────────────────────────

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

-- ─── Indexes ──────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_bot_sessions_user_status ON bot_sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_bot_sessions_last_activity ON bot_sessions(last_activity DESC);
CREATE INDEX IF NOT EXISTS idx_bot_answers_user ON bot_answers(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_bot_progress(user_id, completed_at DESC);

-- ─── RPC: increment_total_cash ────────────────────────────────────────────────
-- Called by SupabaseDB.save_level_progress() after each level completion.
-- Atomically adds p_amount to user_bot_progress.total_cash for the latest row
-- and also updates users.paper_cash for the given user.
--
-- Parameters:
--   p_user_id  INTEGER  — the user whose cash balance to update
--   p_amount   INTEGER  — amount to add (may be 0 or negative for corrections)
--
-- Usage (from Python):
--   self._table("user_bot_progress").rpc(
--       "increment_total_cash",
--       {"p_user_id": user_id, "p_amount": reward},
--   ).execute()

CREATE OR REPLACE FUNCTION increment_total_cash(p_user_id INTEGER, p_amount INTEGER)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Update the cumulative total_cash on the most-recently-completed level row
    UPDATE user_bot_progress
    SET    total_cash = total_cash + p_amount
    WHERE  user_id    = p_user_id
      AND  id = (
          SELECT id FROM user_bot_progress
          WHERE  user_id = p_user_id
          ORDER BY completed_at DESC
          LIMIT 1
      );

    -- Also keep users.paper_cash in sync
    UPDATE users
    SET    paper_cash = paper_cash + p_amount,
           updated_at = NOW()
    WHERE  id = p_user_id;

    -- Auto-create user row if not present (handles first-time reward)
    IF NOT FOUND THEN
        INSERT INTO users (id, paper_cash, created_at, updated_at)
        VALUES (p_user_id, GREATEST(p_amount, 0), NOW(), NOW())
        ON CONFLICT (id) DO UPDATE
            SET paper_cash = users.paper_cash + p_amount,
                updated_at = NOW();
    END IF;
END;
$$;

-- Grant execute to the authenticated and service_role roles used by Supabase
GRANT EXECUTE ON FUNCTION increment_total_cash(INTEGER, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION increment_total_cash(INTEGER, INTEGER) TO service_role;

-- ─── Row Level Security (recommended for production) ─────────────────────────
-- Enable RLS on sensitive tables. Service-role bypasses RLS automatically.

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_bot_progress ENABLE ROW LEVEL SECURITY;

-- Users can only read/update their own row
CREATE POLICY IF NOT EXISTS "users_self_access"
    ON users FOR ALL
    USING (id = (current_setting('request.jwt.claims', true)::jsonb->>'sub')::integer);

-- Sessions: users can access only their own sessions
CREATE POLICY IF NOT EXISTS "sessions_owner_access"
    ON bot_sessions FOR ALL
    USING (user_id = (current_setting('request.jwt.claims', true)::jsonb->>'sub')::integer);

-- Answers: users can access only their own answers
CREATE POLICY IF NOT EXISTS "answers_owner_access"
    ON bot_answers FOR ALL
    USING (user_id = (current_setting('request.jwt.claims', true)::jsonb->>'sub')::integer);

-- Progress: users can access only their own progress
CREATE POLICY IF NOT EXISTS "progress_owner_access"
    ON user_bot_progress FOR ALL
    USING (user_id = (current_setting('request.jwt.claims', true)::jsonb->>'sub')::integer);
