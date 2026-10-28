"""Baseer durable store (production, Oct 2026+).

SQLite via stdlib only — no new dependencies. Layout:
  data/baseer.db        inspections, findings(+cases), audit log, users
  data/evidence/<id>/   original uploads + re-inspection media

Design: app.py keeps its REPORTS dict as a write-through cache so every
endpoint behaves exactly as before; the database is the durable truth and
is reloaded on boot. Seeds (analytics.SEED_REPORTS) stay code fixtures.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    inspection_id TEXT NOT NULL,
    site TEXT NOT NULL DEFAULT '',
    finding_index INTEGER NOT NULL DEFAULT 0,
    action TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '',
    finding TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    pw_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

_lock = threading.Lock()
_db: sqlite3.Connection | None = None
_path = ""


def init(db_path: str) -> str:
    """Open (creating) the database. Returns the path used."""
    global _db, _path
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    _db = sqlite3.connect(db_path, check_same_thread=False)
    _db.execute("PRAGMA journal_mode=WAL")
    _db.executescript(SCHEMA)
    _path = db_path
    return db_path


def _conn() -> sqlite3.Connection:
    assert _db is not None, "store.init() was not called"
    return _db


def save_report(data: dict) -> None:
    with _lock:
        _conn().execute(
            "INSERT OR REPLACE INTO inspections (inspection_id, data) VALUES (?, ?)",
            (data["inspection_id"], json.dumps(data, ensure_ascii=False)),
        )
        _conn().commit()


def load_reports() -> dict[str, dict]:
    cur = _conn().execute("SELECT inspection_id, data FROM inspections")
    return {row[0]: json.loads(row[1]) for row in cur.fetchall()}


def log_audit(entry: dict) -> None:
    with _lock:
        _conn().execute(
            "INSERT INTO audit (ts, inspection_id, site, finding_index, action, actor, detail, finding)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (entry.get("ts", ""), entry.get("inspection_id", ""),
             entry.get("site", ""), int(entry.get("finding_index", 0)),
             entry.get("action", ""), entry.get("actor", ""),
             entry.get("detail", ""), entry.get("finding", "")),
        )
        _conn().commit()


def read_audit() -> list[dict]:
    cur = _conn().execute(
        "SELECT ts, inspection_id, site, finding_index, action, actor, detail, finding"
        " FROM audit ORDER BY id DESC")
    return [{"ts": r[0], "inspection_id": r[1], "site": r[2],
             "finding_index": r[3], "action": r[4], "actor": r[5],
             "detail": r[6], "finding": r[7]} for r in cur.fetchall()]


def db_path() -> str:
    return _path
