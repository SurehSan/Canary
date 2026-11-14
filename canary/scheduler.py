"""Local background schedule (demo cadence, not a real-time promise) — CAN-REQ-003/004/009.

Every NOTIFY_CYCLE_SECONDS: process the P1/P2 queue ("next local processing cycle").
Every SCHEDULE_SECONDS (hourly): collect from enabled sources.
Every DIGEST_SECONDS (daily): send the P3/P4 digest.
"""
import threading
import time


def run_cycle(conn, collect, digest, actor_label="System scheduler"):
    from .collector import run_collection
    from .delivery import process_digest, process_queue
    from .pipeline import assess_backlog, process_findings
    touched = set()
    if collect:
        touched = run_collection(conn, trigger="scheduled", actor_label=f"{actor_label} (hourly)")
        process_findings(conn, touched)
        assess_backlog(conn, f"{actor_label} (hourly)")
    sent = process_queue(conn, actor_label=f"{actor_label} (processing cycle)")
    digests = process_digest(conn) if digest else []
    conn.commit()
    return {"touched": len(touched), "queue": sent, "digests": digests}


def start_scheduler(app):
    def loop():
        last_collect = last_digest = time.monotonic()
        while True:
            time.sleep(app.config["NOTIFY_CYCLE_SECONDS"])
            now = time.monotonic()
            collect = now - last_collect >= app.config["SCHEDULE_SECONDS"]
            digest = now - last_digest >= app.config["DIGEST_SECONDS"]
            try:
                with app.app_context():
                    from .db import get_db
                    run_cycle(get_db(), collect, digest)
            except Exception as exc:  # keep the demo scheduler alive; never log secrets
                app.logger.error("Scheduler cycle failed: %s", type(exc).__name__)
            if collect:
                last_collect = now
            if digest:
                last_digest = now

    threading.Thread(target=loop, name="canary-scheduler", daemon=True).start()
