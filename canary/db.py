import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        # Busy timeout + WAL: the background scheduler and web requests share this file.
        conn = sqlite3.connect(current_app.config["DATABASE"], timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_schema(conn):
    conn.executescript((Path(__file__).parent / "schema.sql").read_text(encoding="utf-8"))


def upgrade_schema(conn, logger):
    """Bring a database from an earlier version up to date where that is safe.

    Tables added in later versions are created (nothing existing is touched). Missing columns
    cannot be added safely, so they are reported with the reset command instead of failing later.
    Returns the list of missing "table.column" names.
    """
    reference = sqlite3.connect(":memory:")
    reference.executescript((Path(__file__).parent / "schema.sql").read_text(encoding="utf-8"))
    present = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing_columns = []
    for name, create_sql in reference.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
        if name not in present:
            conn.execute(create_sql)
            logger.warning("Database upgrade: added missing table %s.", name)
            continue
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({name})")}
        missing_columns += [f"{name}.{r[1]}" for r in reference.execute(f"PRAGMA table_info({name})") if r[1] not in have]
    conn.commit()
    reference.close()
    if missing_columns:
        logger.warning("This database was created by an older version of Canary and is missing: %s. "
                       "Run `python run.py --reset` to rebuild the demo data.", ", ".join(missing_columns))
    return missing_columns


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
