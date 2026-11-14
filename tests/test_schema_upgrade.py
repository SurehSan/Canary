"""A database created by an earlier version must not crash the app (found in local run: Notifications 500)."""
import sqlite3

from canary import create_app
from tests.conftest import login, org_id

BASE = {"TESTING": True, "SECRET_KEY": "t", "START_SCHEDULER": False, "SMTP_HOST": None,
        "EMAIL_ALLOWLIST": set(), "TEST_RECIPIENTS": {}, "LIVE_SOURCES": False, "ALLOWLIST_DOMAINS": None,
        "FIXED_NOW": "2026-11-14T15:00:00+00:00", "RETRY_SLEEP_SECONDS": 0}


def old_database(tmp_path):
    """Seed a current database, then remove a table added later, as an older version would have."""
    path = str(tmp_path / "old.sqlite")
    create_app(dict(BASE, DATABASE=path))
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE email_allowlist")
    conn.execute("INSERT INTO audit_events (actor_label, action, target_type, summary, created_at)"
                 " VALUES ('test', 'marker', 'none', 'keep me', 'now')")
    conn.commit()
    conn.close()
    return path


def test_missing_new_table_is_added_at_startup_without_losing_data(tmp_path):
    path = old_database(tmp_path)
    app = create_app(dict(BASE, DATABASE=path))
    client = app.test_client()
    with app.app_context():
        from canary.db import get_db
        db = get_db()
        login(client, "wyatt", org=org_id(db, "Fernwood Labs"))
        assert client.get("/notifications").status_code == 200
        assert db.execute("SELECT COUNT(*) FROM audit_events WHERE action='marker'").fetchone()[0] == 1


def test_missing_column_is_reported_clearly(tmp_path, caplog):
    path = str(tmp_path / "older.sqlite")
    create_app(dict(BASE, DATABASE=path))
    conn = sqlite3.connect(path)
    conn.execute("ALTER TABLE org_sources DROP COLUMN simulate_failure")
    conn.commit()
    conn.close()
    with caplog.at_level("WARNING"):
        create_app(dict(BASE, DATABASE=path))
    assert "python run.py --reset" in caplog.text and "org_sources.simulate_failure" in caplog.text
