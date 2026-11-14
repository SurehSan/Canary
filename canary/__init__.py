"""Canary local demo prototype (Flask + SQLite)."""
import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask


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
    )
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    from . import db, views
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
