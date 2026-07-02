"""
FinNexus Bot — Database Adapter
Wraps Supabase (or a local SQLite fallback for development/testing).
All table interactions are centralised here so the rest of the bot
never imports supabase directly.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now().isoformat()


# ---------------------------------------------------------------------------
# Base DB interface
# ---------------------------------------------------------------------------

class BotDB:
    """
    Abstract-ish interface.  Two concrete implementations are provided:
      - SupabaseDB  — real Supabase backend
      - SQLiteDB    — local fallback / unit testing
    """

    # ── Sessions ─────────────────────────────────────────────────────────────

    def create_session(self, session_id: str, user_id: int, level: int) -> None:
        raise NotImplementedError

    def update_session(self, session_id: str, **kwargs) -> None:
        raise NotImplementedError

    def get_active_session(self, user_id: int) -> Optional[Dict]:
        raise NotImplementedError

    def close_session(self, session_id: str, status: str = "completed") -> None:
        raise NotImplementedError

    # ── Answers ──────────────────────────────────────────────────────────────

    def save_answer(
        self,
        user_id: int,
        session_id: str,
        question_id: str,
        question_type: str,
        answer: Any,
        score: float,
        is_level_20: bool = False,
        feedback: str = "",
    ) -> None:
        raise NotImplementedError

    # ── Progress ─────────────────────────────────────────────────────────────

    def save_level_progress(
        self,
        user_id: int,
        level: int,
        score: float,
        reward: int,
        next_level_unlocked: bool,
    ) -> None:
        raise NotImplementedError

    def get_user_history(self, user_id: int, limit: int = 100) -> List[Dict]:
        raise NotImplementedError

    def get_user_progress(self, user_id: int) -> List[Dict]:
        raise NotImplementedError

    # ── Paper cash ───────────────────────────────────────────────────────────

    def add_paper_cash(self, user_id: int, amount: int) -> int:
        """Add paper cash and return new total."""
        raise NotImplementedError

    def get_paper_cash(self, user_id: int) -> int:
        raise NotImplementedError

    # ── User profile ─────────────────────────────────────────────────────────

    def get_user_profile(self, user_id: int) -> Dict:
        raise NotImplementedError

    def save_user_profile(self, user_id: int, **fields: Any) -> Dict:
        raise NotImplementedError

    def increment_session_count(self, user_id: int) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Supabase implementation
# ---------------------------------------------------------------------------

class SupabaseDB(BotDB):
    """Production DB backed by Supabase PostgREST."""

    def __init__(self, url: str, key: str):
        try:
            from supabase import create_client, Client  # type: ignore
            self._client: Client = create_client(url, key)
            logger.info("SupabaseDB connected to %s", url)
        except ImportError as exc:
            raise ImportError(
                "supabase-py not installed. Run: pip install supabase"
            ) from exc

    # ── Internal helper ───────────────────────────────────────────────────────

    def _table(self, name: str):
        return self._client.table(name)

    # ── Sessions ─────────────────────────────────────────────────────────────

    def create_session(self, session_id: str, user_id: int, level: int) -> None:
        self._table("bot_sessions").insert(
            {
                "id": session_id,
                "user_id": user_id,
                "level": level,
                "current_question": 0,
                "status": "active",
                "started_at": _now_iso(),
                "last_activity": _now_iso(),
                "metadata": {},
            }
        ).execute()

    def update_session(self, session_id: str, **kwargs) -> None:
        kwargs["last_activity"] = _now_iso()
        self._table("bot_sessions").update(kwargs).eq("id", session_id).execute()

    def get_active_session(self, user_id: int) -> Optional[Dict]:
        result = (
            self._table("bot_sessions")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "active")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def close_session(self, session_id: str, status: str = "completed") -> None:
        self._table("bot_sessions").update(
            {"status": status, "last_activity": _now_iso()}
        ).eq("id", session_id).execute()

    # ── Answers ──────────────────────────────────────────────────────────────

    def save_answer(
        self,
        user_id: int,
        session_id: str,
        question_id: str,
        question_type: str,
        answer: Any,
        score: float,
        is_level_20: bool = False,
        feedback: str = "",
    ) -> None:
        self._table("bot_answers").insert(
            {
                "user_id": user_id,
                "session_id": session_id,
                "question_id": question_id,
                "question_type": question_type,
                "answer": json.dumps(answer),
                "score": score,
                "is_level_20": is_level_20,
                "feedback": feedback,
                "created_at": _now_iso(),
            }
        ).execute()

    # ── Progress ─────────────────────────────────────────────────────────────

    def save_level_progress(
        self,
        user_id: int,
        level: int,
        score: float,
        reward: int,
        next_level_unlocked: bool,
    ) -> None:
        # Upsert: update existing row for this user+level, or insert
        self._table("user_bot_progress").upsert(
            {
                "user_id": user_id,
                "level_completed": level,
                "score": score,
                "reward_earned": reward,
                "next_level_unlocked": next_level_unlocked,
                "completed_at": _now_iso(),
            },
            on_conflict="user_id,level_completed",
        ).execute()
        # Also update running total
        self._table("user_bot_progress").rpc(
            "increment_total_cash",
            {"p_user_id": user_id, "p_amount": reward},
        ).execute()

    def get_user_history(self, user_id: int, limit: int = 100) -> List[Dict]:
        result = (
            self._table("bot_answers")
            .select("score, question_type, is_level_20, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def get_user_progress(self, user_id: int) -> List[Dict]:
        result = (
            self._table("user_bot_progress")
            .select("*")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .execute()
        )
        return result.data or []

    def add_paper_cash(self, user_id: int, amount: int) -> int:
        result = (
            self._table("users")
            .select("paper_cash")
            .eq("id", user_id)
            .single()
            .execute()
        )
        current = result.data.get("paper_cash", 0) if result.data else 0
        new_total = current + amount
        self._table("users").update({"paper_cash": new_total}).eq("id", user_id).execute()
        return new_total

    def get_paper_cash(self, user_id: int) -> int:
        result = (
            self._table("users")
            .select("paper_cash")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return result.data.get("paper_cash", 0) if result.data else 0

    def get_user_profile(self, user_id: int) -> Dict:
        result = (
            self._table("users")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        return self._default_profile(user_id)

    def save_user_profile(self, user_id: int, **fields: Any) -> Dict:
        fields["updated_at"] = _now_iso()
        self._table("users").upsert({"id": user_id, **fields}, on_conflict="id").execute()
        return self.get_user_profile(user_id)

    def increment_session_count(self, user_id: int) -> None:
        profile = self.get_user_profile(user_id)
        count = int(profile.get("total_sessions", 0)) + 1
        self.save_user_profile(user_id, total_sessions=count)

    @staticmethod
    def _default_profile(user_id: int) -> Dict:
        return {
            "id": user_id,
            "name": "",
            "email": "",
            "paper_cash": 0,
            "current_level": 1,
            "proficiency": 0.0,
            "highest_level_completed": 0,
            "level_20_completed": 0,
            "level_20_completed_at": None,
            "total_sessions": 0,
        }


# ---------------------------------------------------------------------------
# SQLite fallback (dev / unit tests)
# ---------------------------------------------------------------------------

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT DEFAULT '',
    email TEXT DEFAULT '',
    paper_cash INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    proficiency REAL DEFAULT 0.0,
    highest_level_completed INTEGER DEFAULT 0,
    level_20_completed INTEGER DEFAULT 0,
    level_20_completed_at TEXT,
    total_sessions INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS bot_sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    current_question INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    started_at TEXT,
    last_activity TEXT,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS bot_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question_type TEXT,
    answer TEXT,
    score REAL,
    is_level_20 INTEGER DEFAULT 0,
    feedback TEXT DEFAULT '',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS user_bot_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    level_completed INTEGER NOT NULL,
    score REAL,
    reward_earned INTEGER DEFAULT 0,
    total_cash INTEGER DEFAULT 0,
    completed_at TEXT,
    next_level_unlocked INTEGER DEFAULT 0,
    UNIQUE(user_id, level_completed)
);
"""


class SQLiteDB(BotDB):
    """Local SQLite-backed DB — zero external dependencies, great for testing."""

    def __init__(self, db_path: str = ":memory:"):
        self._path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SQLITE_SCHEMA)
        self._migrate_sqlite_schema()
        self._conn.commit()
        logger.info("SQLiteDB initialised at %s", db_path)

    def _migrate_sqlite_schema(self) -> None:
        """Add profile columns to legacy databases."""
        cols = {row[1] for row in self._conn.execute("PRAGMA table_info(users)").fetchall()}
        migrations = [
            ("current_level", "INTEGER DEFAULT 1"),
            ("proficiency", "REAL DEFAULT 0.0"),
            ("highest_level_completed", "INTEGER DEFAULT 0"),
            ("level_20_completed", "INTEGER DEFAULT 0"),
            ("level_20_completed_at", "TEXT"),
            ("total_sessions", "INTEGER DEFAULT 0"),
            ("created_at", "TEXT"),
            ("updated_at", "TEXT"),
        ]
        for col, typedef in migrations:
            if col not in cols:
                self._conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typedef}")

    def _q(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def _commit(self):
        self._conn.commit()

    # ── Sessions ─────────────────────────────────────────────────────────────

    def create_session(self, session_id: str, user_id: int, level: int) -> None:
        now = _now_iso()
        self._q(
            "INSERT INTO bot_sessions(id,user_id,level,status,started_at,last_activity) "
            "VALUES(?,?,?,'active',?,?)",
            (session_id, user_id, level, now, now),
        )
        self._commit()

    def update_session(self, session_id: str, **kwargs) -> None:
        kwargs["last_activity"] = _now_iso()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [session_id]
        self._q(f"UPDATE bot_sessions SET {sets} WHERE id=?", tuple(vals))
        self._commit()

    def get_active_session(self, user_id: int) -> Optional[Dict]:
        row = self._q(
            "SELECT * FROM bot_sessions WHERE user_id=? AND status='active' "
            "ORDER BY started_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

    def close_session(self, session_id: str, status: str = "completed") -> None:
        self._q(
            "UPDATE bot_sessions SET status=?, last_activity=? WHERE id=?",
            (status, _now_iso(), session_id),
        )
        self._commit()

    # ── Answers ──────────────────────────────────────────────────────────────

    def save_answer(
        self,
        user_id: int,
        session_id: str,
        question_id: str,
        question_type: str,
        answer: Any,
        score: float,
        is_level_20: bool = False,
        feedback: str = "",
    ) -> None:
        self._q(
            "INSERT INTO bot_answers(user_id,session_id,question_id,question_type,"
            "answer,score,is_level_20,feedback,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                user_id,
                session_id,
                question_id,
                question_type,
                json.dumps(answer),
                score,
                int(is_level_20),
                feedback,
                _now_iso(),
            ),
        )
        self._commit()

    # ── Progress ─────────────────────────────────────────────────────────────

    def save_level_progress(
        self,
        user_id: int,
        level: int,
        score: float,
        reward: int,
        next_level_unlocked: bool,
    ) -> None:
        existing = self._q(
            "SELECT id, total_cash FROM user_bot_progress WHERE user_id=? AND level_completed=?",
            (user_id, level),
        ).fetchone()

        if existing:
            old_cash = existing["total_cash"] or 0
            self._q(
                "UPDATE user_bot_progress SET score=?,reward_earned=?,total_cash=?,"
                "completed_at=?,next_level_unlocked=? WHERE user_id=? AND level_completed=?",
                (score, reward, old_cash + reward, _now_iso(), int(next_level_unlocked), user_id, level),
            )
        else:
            # Get existing total cash
            prev = self._q(
                "SELECT COALESCE(MAX(total_cash),0) AS tc FROM user_bot_progress WHERE user_id=?",
                (user_id,),
            ).fetchone()
            prev_cash = prev["tc"] if prev else 0
            self._q(
                "INSERT INTO user_bot_progress(user_id,level_completed,score,reward_earned,"
                "total_cash,completed_at,next_level_unlocked) VALUES(?,?,?,?,?,?,?)",
                (user_id, level, score, reward, prev_cash + reward, _now_iso(), int(next_level_unlocked)),
            )
        self._commit()

    def get_user_history(self, user_id: int, limit: int = 100) -> List[Dict]:
        rows = self._q(
            "SELECT score, question_type, is_level_20, created_at FROM bot_answers "
            "WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_user_progress(self, user_id: int) -> List[Dict]:
        rows = self._q(
            "SELECT * FROM user_bot_progress WHERE user_id=? ORDER BY completed_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def add_paper_cash(self, user_id: int, amount: int) -> int:
        # Ensure user exists
        self._q(
            "INSERT OR IGNORE INTO users(id, paper_cash) VALUES(?,0)", (user_id,)
        )
        self._q(
            "UPDATE users SET paper_cash = paper_cash + ? WHERE id=?", (amount, user_id)
        )
        self._commit()
        row = self._q("SELECT paper_cash FROM users WHERE id=?", (user_id,)).fetchone()
        return row["paper_cash"] if row else amount

    def get_paper_cash(self, user_id: int) -> int:
        row = self._q(
            "SELECT paper_cash FROM users WHERE id=?", (user_id,)
        ).fetchone()
        return row["paper_cash"] if row else 0

    def get_user_profile(self, user_id: int) -> Dict:
        row = self._q("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if row:
            return dict(row)
        return SupabaseDB._default_profile(user_id)

    def save_user_profile(self, user_id: int, **fields: Any) -> Dict:
        now = _now_iso()
        self._q(
            "INSERT OR IGNORE INTO users(id, paper_cash, current_level, created_at, updated_at) "
            "VALUES(?, 0, 1, ?, ?)",
            (user_id, now, now),
        )
        if fields:
            fields["updated_at"] = now
            sets = ", ".join(f"{k}=?" for k in fields)
            vals = list(fields.values()) + [user_id]
            self._q(f"UPDATE users SET {sets} WHERE id=?", tuple(vals))
        self._commit()
        return self.get_user_profile(user_id)

    def increment_session_count(self, user_id: int) -> None:
        profile = self.get_user_profile(user_id)
        self.save_user_profile(user_id, total_sessions=int(profile.get("total_sessions", 0)) + 1)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_db(url: str = "", key: str = "", sqlite_path: str = "") -> BotDB:
    """
    Return the appropriate DB backend.
    - If url+key are provided → SupabaseDB
    - Otherwise → SQLiteDB (uses :memory: by default, or sqlite_path if given)
    """
    if url and key:
        return SupabaseDB(url, key)
    path = sqlite_path or ":memory:"
    logger.warning("No Supabase credentials — using SQLiteDB at '%s'", path)
    return SQLiteDB(path)
