"""Canary local demo prototype (Flask + SQLite)."""
import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask

from .notify import parse_allowlist, parse_recipients


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    root = Path(__file__).resolve().parent.parent
    app.config.update(
        SECRET_KEY=os.environ.get("CANARY_SECRET_KEY") or secrets.token_hex(32),
        DATABASE=os.environ.get("CANARY_DATABASE") or str(root / "instance" / "canary.sqlite"),
        FIXED_NOW=os.environ.get("CANARY_FIXED_NOW"),
        RETRY_SLEEP_SECONDS=0.2,
        START_SCHEDULER=os.environ.get("CANARY_SCHEDULER", "1") == "1",
        SCHEDULE_SECONDS=3600,
        NOTIFY_CYCLE_SECONDS=60,
        DIGEST_SECONDS=86400,
        # CAN-REQ-009 test email. Credentials come only from the environment / local .env.
        SMTP_HOST=os.environ.get("CANARY_SMTP_HOST") or None,
        SMTP_PORT=int(os.environ.get("CANARY_SMTP_PORT") or 587),
        SMTP_USERNAME=os.environ.get("CANARY_SMTP_USERNAME") or None,
        SMTP_PASSWORD=os.environ.get("CANARY_SMTP_PASSWORD") or None,
        SMTP_STARTTLS=os.environ.get("CANARY_SMTP_STARTTLS", "1") == "1",
        SMTP_SSL=os.environ.get("CANARY_SMTP_SSL", "0") == "1",
        MAIL_FROM=os.environ.get("CANARY_MAIL_FROM") or None,
        EMAIL_ALLOWLIST=parse_allowlist(os.environ.get("CANARY_EMAIL_ALLOWLIST")),
        TEST_RECIPIENTS=parse_recipients(os.environ.get("CANARY_TEST_RECIPIENTS")),
        APP_BASE_URL=os.environ.get("CANARY_BASE_URL") or "http://127.0.0.1:5000",
        LIVE_SOURCES=os.environ.get("CANARY_LIVE_SOURCES", "0") == "1",
        LIVE_MIN_INTERVAL_SECONDS=900,
        HTTP_GET=None,
    )
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    from . import db, views, work_views  # noqa: F401  (work_views registers routes on views.bp)
    from .auth import load_user
    app.teardown_appcontext(db.close_db)
    app.before_request(load_user)
    app.register_blueprint(views.bp)
    views.register_filters(app)

    _ensure_seeded(app)
    if app.config["START_SCHEDULER"]:
        from .scheduler import start_scheduler
        start_scheduler(app)
    return app


def _ensure_seeded(app):
    with app.app_context():
        from .db import get_db
        from .seed import reset_demo
        conn = get_db()
        try:
            conn.execute("SELECT 1 FROM organizations LIMIT 1")
        except sqlite3.OperationalError:
            reset_demo(conn)
