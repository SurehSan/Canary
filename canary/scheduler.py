"""Local hourly collection schedule (demo cadence, not a real-time promise) — CAN-REQ-003/004."""
import threading
import time


def start_scheduler(app):
    def loop():
        while True:
            time.sleep(app.config["SCHEDULE_SECONDS"])
            with app.app_context():
                from .collector import run_collection
                from .db import get_db
                from .pipeline import process_findings
                conn = get_db()
                touched = run_collection(conn, trigger="scheduled", actor_label="System scheduler (hourly)")
                process_findings(conn, touched)
                conn.commit()

    threading.Thread(target=loop, name="canary-scheduler", daemon=True).start()
