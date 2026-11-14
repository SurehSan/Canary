import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_schema(conn):
    conn.executescript((Path(__file__).parent / "schema.sql").read_text(encoding="utf-8"))


def now_iso():
    fixed = current_app.config.get("FIXED_NOW")
    if fixed:
        return fixed
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today():
    return datetime.fromisoformat(now_iso()).date()


def audit(conn, *, org_id, actor_id, actor_label, action, target_type, target_id, summary,
          before=None, after=None):
    """Record an audit event. Callers pass safe summaries only — never secrets."""
    conn.execute(
        "INSERT INTO audit_events (org_id, actor_id, actor_label, action, target_type, target_id, summary,"
        " before_state, after_state, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (org_id, actor_id, actor_label, action, target_type, target_id, summary,
         json.dumps(before) if before is not None else None,
         json.dumps(after) if after is not None else None, now_iso()))
