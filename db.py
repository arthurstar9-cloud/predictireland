"""SQLite database for post logging, market deduplication, and run history."""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "predictireland.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS markets (
            id TEXT PRIMARY KEY,
            slug TEXT,
            title TEXT,
            first_seen TEXT NOT NULL,
            last_used TEXT,
            times_used INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            pillar INTEGER NOT NULL,
            market_ids TEXT,
            caption TEXT,
            image_paths TEXT,
            tiktok_post_id TEXT,
            status TEXT DEFAULT 'created'
        );

        CREATE TABLE IF NOT EXISTS run_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            pillar INTEGER,
            status TEXT DEFAULT 'running',
            error TEXT
        );
    """)
    conn.commit()
    conn.close()


def mark_market_used(market_id: str, slug: str, title: str):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO markets (id, slug, title, first_seen, last_used, times_used)
        VALUES (?, ?, ?, ?, ?, 1)
        ON CONFLICT(id) DO UPDATE SET
            last_used = ?,
            times_used = times_used + 1
    """, (market_id, slug, title, now, now, now))
    conn.commit()
    conn.close()


def was_market_used(market_id: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT id FROM markets WHERE id = ?", (market_id,)).fetchone()
    conn.close()
    return row is not None


def get_used_market_ids() -> set:
    conn = get_conn()
    rows = conn.execute("SELECT id FROM markets").fetchall()
    conn.close()
    return {r["id"] for r in rows}


def log_post(pillar: int, market_ids: list, caption: str, image_paths: list,
             tiktok_post_id: str = None, status: str = "created") -> int:
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    cur = conn.execute("""
        INSERT INTO posts (created_at, pillar, market_ids, caption, image_paths, tiktok_post_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now, pillar, ",".join(market_ids), caption, ",".join(image_paths), tiktok_post_id, status))
    conn.commit()
    post_id = cur.lastrowid
    conn.close()
    return post_id


def update_post_status(post_id: int, status: str, tiktok_post_id: str = None):
    conn = get_conn()
    if tiktok_post_id:
        conn.execute("UPDATE posts SET status = ?, tiktok_post_id = ? WHERE id = ?",
                      (status, tiktok_post_id, post_id))
    else:
        conn.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))
    conn.commit()
    conn.close()


def log_run_start(pillar: int) -> int:
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    cur = conn.execute("INSERT INTO run_history (started_at, pillar) VALUES (?, ?)", (now, pillar))
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def log_run_end(run_id: int, status: str, error: str = None):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    conn.execute("UPDATE run_history SET finished_at = ?, status = ?, error = ? WHERE id = ?",
                  (now, status, error, run_id))
    conn.commit()
    conn.close()


# Auto-init on import
init_db()
