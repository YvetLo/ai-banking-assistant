"""
SQLite database — tickets and unresolved_queries tables.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "banking.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS tickets (
            id          TEXT PRIMARY KEY,
            created_at  TEXT NOT NULL,
            user_id     TEXT,
            type        TEXT NOT NULL,
            description TEXT,
            card_id     TEXT,
            status      TEXT DEFAULT 'open',
            priority    TEXT DEFAULT 'normal'
        );

        CREATE TABLE IF NOT EXISTS unresolved_queries (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at     TEXT NOT NULL,
            session_id     TEXT,
            user_query     TEXT NOT NULL,
            language       TEXT,
            intent         TEXT,
            trigger_reason TEXT NOT NULL,
            similarity_score REAL
        );
    """)
    c.commit()
    c.close()


def create_ticket(
    type: str,
    user_id: str = None,
    card_id: str = None,
    description: str = "",
    priority: str = "normal",
) -> dict:
    today = datetime.now().strftime("%Y%m%d")
    c = _conn()
    count = c.execute(
        "SELECT COUNT(*) FROM tickets WHERE id LIKE ?", (f"T-{today}-%",)
    ).fetchone()[0]
    ticket_id = f"T-{today}-{count + 1:03d}"
    created_at = datetime.now().isoformat()

    c.execute(
        "INSERT INTO tickets VALUES (?,?,?,?,?,?,'open',?)",
        (ticket_id, created_at, user_id, type, description, card_id, priority),
    )
    c.commit()
    c.close()

    return {"ticket_id": ticket_id, "created_at": created_at, "status": "open"}


def get_tickets(user_id: str = None, limit: int = 20) -> list[dict]:
    c = _conn()
    if user_id:
        rows = c.execute(
            "SELECT * FROM tickets WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    c.close()
    return [dict(r) for r in rows]
