import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

DB_DIR = Path.home() / ".oracle"
DB_PATH = DB_DIR / "db.sqlite3"


def _connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT    NOT NULL UNIQUE,
                original_url TEXT   NOT NULL UNIQUE,
                created_at  TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT    NOT NULL,
                clicked_at  TEXT    NOT NULL,
                referrer    TEXT,
                user_agent  TEXT,
                FOREIGN KEY (code) REFERENCES links(code)
            )
        """)


def get_by_url(url: str) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM links WHERE original_url = ?", (url,)
        ).fetchone()


def get_by_code(code: str) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM links WHERE code = ?", (code,)
        ).fetchone()


def code_exists(code: str) -> bool:
    return get_by_code(code) is not None


def insert(code: str, url: str) -> sqlite3.Row:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO links (code, original_url, created_at) VALUES (?, ?, ?)",
            (code, url, created_at),
        )
    return get_by_code(code)


def list_all() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM links ORDER BY created_at ASC"
        ).fetchall()


def delete(code: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM links WHERE code = ?", (code,))
        return cursor.rowcount > 0


def insert_click(
    code: str,
    clicked_at: str,
    referrer: Optional[str],
    user_agent: Optional[str],
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO clicks (code, clicked_at, referrer, user_agent) VALUES (?, ?, ?, ?)",
            (code, clicked_at, referrer, user_agent),
        )


def get_clicks_by_code(code: str) -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM clicks WHERE code = ? ORDER BY clicked_at DESC",
            (code,),
        ).fetchall()


def get_click_count_by_code(code: str) -> int:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM clicks WHERE code = ?", (code,)
        ).fetchone()
        return row["cnt"]


def get_all_click_counts() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute("""
            SELECT l.code, l.original_url AS url, COUNT(c.id) AS click_count
            FROM links l
            LEFT JOIN clicks c ON c.code = l.code
            GROUP BY l.code
            ORDER BY click_count DESC
        """).fetchall()


def get_recent_clicks(limit: int = 50) -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM clicks ORDER BY clicked_at DESC LIMIT ?", (limit,)
        ).fetchall()
