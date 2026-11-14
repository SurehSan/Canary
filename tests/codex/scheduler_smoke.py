"""Exercise the background notification scheduler alongside active HTTP requests."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, str(Path.cwd()))
import requests

ROOT = Path.cwd()
DB_PATH = ROOT / "instance" / "canary.sqlite"
LOG = ROOT / "tests" / "codex" / "scheduler-app.log"
BASE = "http://127.0.0.1:5000"

env = {k: v for k, v in os.environ.items() if not k.startswith("CANARY_")}
env.update({"CANARY_SMTP_HOST": "", "CANARY_SMTP_PORT": "", "CANARY_SMTP_STARTTLS": "0",
            "CANARY_SMTP_SSL": "0", "CANARY_SMTP_USERNAME": "", "CANARY_SMTP_PASSWORD": "",
            "CANARY_MAIL_FROM": "", "CANARY_EMAIL_ALLOWLIST": "", "CANARY_TEST_RECIPIENTS": "",
            "CANARY_LIVE_SOURCES": "0", "CANARY_SCHEDULER": "1"})
subprocess.run([sys.executable, "run.py", "--reset"], cwd=ROOT, env=env, check=True,
               capture_output=True, text=True)
log = LOG.open("w+", encoding="utf-8")
proc = subprocess.Popen([sys.executable, "run.py"], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
session = requests.Session()
try:
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError(LOG.read_text(encoding="utf-8"))
        try:
            if requests.get(BASE + "/login", timeout=0.5).status_code == 200:
                break
        except requests.RequestException:
            pass
        time.sleep(0.1)
    else:
        raise RuntimeError("server did not start")
    login = session.post(BASE + "/login", data={"username": "wyatt", "password": "demo"},
                         allow_redirects=False, timeout=10)
    assert login.status_code == 302
    org = sqlite3.connect(DB_PATH)
    fern = org.execute("SELECT id FROM organizations WHERE name='Fernwood Labs'").fetchone()[0]
    sureh = org.execute("SELECT id FROM users WHERE username='sureh'").fetchone()[0]
    org.close()
    assert session.post(BASE + "/orgs/select", data={"org_id": fern}, allow_redirects=False).status_code == 302
    assert session.post(BASE + "/notifications/recipients", data={"user_id": sureh, "email": "sureh-test@team.example"},
                        allow_redirects=False).status_code == 302
    assert session.post(BASE + "/sources/refresh", allow_redirects=False).status_code == 302
    started = time.monotonic()
    requests_count = 0
    while time.monotonic() - started < 190:
        assert session.get(BASE + "/", timeout=5).status_code == 200
        assert session.post(BASE + "/sources/refresh", allow_redirects=False, timeout=15).status_code == 302
        requests_count += 2
        time.sleep(5)
    elapsed = round(time.monotonic() - started, 1)
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT status, attempts FROM notifications WHERE kind='new' ORDER BY id DESC LIMIT 1").fetchone()
        outcome = dict(row) if row else None
    log.flush()
    log.seek(0)
    output = log.read()
    problems = [line for line in output.splitlines() if "database is locked" in line.lower()
                or "scheduler cycle failed" in line.lower()]
    assert elapsed >= 180, elapsed
    assert outcome and outcome["status"] == "rejected" and outcome["attempts"] >= 1, outcome
    assert not problems, problems
    print(json.dumps({"elapsed_seconds": elapsed, "active_http_requests": requests_count,
                      "scheduler_processed_notification": outcome, "scheduler_errors": problems}, indent=2))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    log.close()
