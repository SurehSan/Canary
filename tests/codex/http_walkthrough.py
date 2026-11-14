"""Drive the two W1-W17 verification runs over HTTP, with SQLite evidence."""
import html
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, str(Path.cwd()))

import requests
from tests.smtp_capture import CaptureServer


ROOT = Path.cwd()
DB_PATH = ROOT / "instance" / "canary.sqlite"
BASE = "http://127.0.0.1:5000"
LOG = ROOT / "tests" / "codex" / "http-app.log"
SUREH_ADDR = "sureh-test@team.example"
ORIGINAL = "Researchers showed AI coding assistants can be led to fetch and run attacker-registered code under names that models commonly hallucinate."
CORRECTED = "Researchers demonstrated package-name confusion; no evidence links an installation to this organization."
observations = []


def note(run, step, status, evidence):
    observations.append({"run": run, "step": step, "status": status, "evidence": evidence})


def dbconn():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, args=()):
    with dbconn() as db:
        return db.execute(sql, args).fetchall()


def scalar(sql, args=()):
    return query(sql, args)[0][0]


def reset_and_start(extra_env):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CANARY_")}
    # run.py loads the repository .env with setdefault; blank values here are
    # deliberate and prevent any personal SMTP credentials from reaching this app.
    env.update({"CANARY_SMTP_HOST": "", "CANARY_SMTP_PORT": "", "CANARY_SMTP_STARTTLS": "0",
                "CANARY_SMTP_SSL": "0", "CANARY_SMTP_USERNAME": "", "CANARY_SMTP_PASSWORD": "",
                "CANARY_MAIL_FROM": "", "CANARY_EMAIL_ALLOWLIST": "", "CANARY_TEST_RECIPIENTS": "",
                "CANARY_LIVE_SOURCES": "0"})
    env.update(extra_env)
    env["CANARY_SCHEDULER"] = "0"
    subprocess.run([sys.executable, "run.py", "--reset"], cwd=ROOT, env=env, check=True,
                   capture_output=True, text=True)
    log_handle = LOG.open("w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "run.py"], cwd=ROOT, env=env, stdout=log_handle,
                            stderr=subprocess.STDOUT)
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError("app exited during startup: " + LOG.read_text(encoding="utf-8"))
        try:
            r = requests.get(BASE + "/login", timeout=0.5)
            if r.status_code == 200:
                return env, proc, log_handle
        except requests.RequestException:
            pass
        time.sleep(0.1)
    proc.terminate()
    raise RuntimeError("app did not start in time: " + LOG.read_text(encoding="utf-8"))


def stop(proc, log_handle):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    log_handle.close()


def actor(session, user, org):
    session.post(BASE + "/logout", timeout=5)
    r = session.post(BASE + "/login", data={"username": user, "password": "demo"},
                     allow_redirects=False, timeout=10)
    assert r.status_code == 302, (user, r.status_code, r.text[:300])
    r = session.post(BASE + "/orgs/select", data={"org_id": org}, allow_redirects=False, timeout=10)
    assert r.status_code == 302, (user, org, r.status_code, r.text[:300])


def post(session, path, data=None, expected=302):
    r = session.post(BASE + path, data=data or {}, allow_redirects=False, timeout=20)
    assert r.status_code == expected, (path, r.status_code, html.unescape(r.text[:500]))
    return r


def page(session, path, expected=200):
    r = session.get(BASE + path, timeout=10)
    assert r.status_code == expected, (path, r.status_code, html.unescape(r.text[:500]))
    return html.unescape(r.text)


def ids():
    return {
        "fern": scalar("SELECT id FROM organizations WHERE name='Fernwood Labs'"),
        "prairie": scalar("SELECT id FROM organizations WHERE name='Prairie Valley Medical Center'"),
        "wyatt": scalar("SELECT id FROM users WHERE username='wyatt'"),
        "sureh": scalar("SELECT id FROM users WHERE username='sureh'"),
        "koewen": scalar("SELECT id FROM users WHERE username='koewen'"),
    }


def do_walkthrough(run_name, smtp=None):
    extra = {}
    if smtp:
        extra.update({"CANARY_SMTP_HOST": "127.0.0.1", "CANARY_SMTP_PORT": str(smtp.port),
                      "CANARY_SMTP_STARTTLS": "0", "CANARY_SMTP_SSL": "0",
                      "CANARY_SMTP_USERNAME": "", "CANARY_SMTP_PASSWORD": "",
                      "CANARY_MAIL_FROM": "canary-demo@team.example",
                      "CANARY_EMAIL_ALLOWLIST": SUREH_ADDR,
                      "CANARY_TEST_RECIPIENTS": f"sureh={SUREH_ADDR}"})
    env, proc, log_handle = reset_and_start(extra)
    s = requests.Session()
    try:
        x = ids()
        actor(s, "wyatt", x["fern"])

        org_page = page(s, "/organization")
        assert all(v in org_page for v in ("Demo data", "Python runtime agent framework", "Unknown", "Sureh", "Koewen", "No"))
        note(run_name, "W1", "Pass", "Organization page showed demo banner, Unknown runtime version, seeded leads and No questionnaire assessment.")

        source_page = page(s, "/sources")
        assert all(name in source_page for name in ("The Hacker News", "CSA", "GitHub Security Advisories", "OWASP"))
        assert "Notification cadence" in source_page and "Collection cadence" in source_page
        if smtp:
            post(s, "/notifications/recipients", {"user_id": x["sureh"], "email": SUREH_ADDR})
        post(s, "/sources/refresh")
        thn_id = scalar("SELECT id FROM source_catalog WHERE key='thehackernews'")
        csa_id = scalar("SELECT id FROM source_catalog WHERE key='csa'")
        ghsa_id = scalar("SELECT id FROM source_catalog WHERE key='ghsa'")
        alert = scalar("SELECT id FROM alerts WHERE org_id=?", (x["fern"],))
        assert scalar("SELECT COUNT(*) FROM source_items") == 2
        assert scalar("SELECT outcome FROM collection_runs WHERE source_id=? AND (org_id=? OR org_id IS NULL) ORDER BY id DESC LIMIT 1",
                      (thn_id, x["fern"])) == "success"
        assert scalar("SELECT outcome FROM collection_runs WHERE source_id=? AND (org_id=? OR org_id IS NULL) ORDER BY id DESC LIMIT 1",
                      (csa_id, x["fern"])) == "success"
        assert scalar("SELECT new_items FROM collection_runs WHERE source_id=? AND (org_id=? OR org_id IS NULL) ORDER BY id DESC LIMIT 1",
                      (thn_id, x["fern"])) == 1
        owasp_id = scalar("SELECT id FROM source_catalog WHERE key='owasp-genai'")
        assert scalar("SELECT outcome FROM collection_runs WHERE source_id=? AND (org_id=? OR org_id IS NULL) ORDER BY id DESC LIMIT 1",
                      (ghsa_id, x["fern"])) == "success_no_new"
        assert scalar("SELECT outcome FROM collection_runs WHERE source_id=? AND (org_id=? OR org_id IS NULL) ORDER BY id DESC LIMIT 1",
                      (owasp_id, x["fern"])) == "success_no_new"
        note(run_name, "W2", "Pass", "Four catalog sources displayed; refresh recorded THN/CSA success and two source items.")

        post(s, f"/sources/{ghsa_id}/simulate-failure")
        post(s, "/sources/refresh")
        failed = scalar("SELECT outcome FROM collection_runs WHERE org_id=? AND source_id=? ORDER BY id DESC LIMIT 1",
                        (x["fern"], ghsa_id))
        attempts = scalar("SELECT attempts FROM collection_runs WHERE org_id=? AND source_id=? ORDER BY id DESC LIMIT 1",
                          (x["fern"], ghsa_id))
        src = page(s, "/sources")
        assert failed == "failed" and attempts == 3 and "this organization only" in src
        actor(s, "priya", x["prairie"])
        prairie_src = page(s, "/sources")
        assert "GitHub Security Advisories" in prairie_src and "Failed" not in prairie_src
        prairie_run = query("SELECT outcome FROM collection_runs WHERE org_id=? AND source_id=? ORDER BY id DESC LIMIT 1",
                            (x["prairie"], ghsa_id))
        assert not prairie_run or prairie_run[0]["outcome"] != "failed"
        actor(s, "wyatt", x["fern"])
        post(s, f"/sources/{ghsa_id}/simulate-failure")
        note(run_name, "W3", "Pass", "Fernwood's GHSA run failed after 3 attempts; Prairie Valley's GHSA page did not show Failed.")

        alert_page = page(s, f"/alerts/{alert}")
        assert "Proposed" in alert_page and "affects every organization" in alert_page
        assert "2026-07-08" in alert_page and "2026-04-19" in alert_page
        note(run_name, "W4", "Pass", "One alert preserved THN/CSA evidence dates, proposed grouping and shared-evidence notice.")

        assert all(term in alert_page for term in ("Source-supported", "Organization context", "Unknown",
                                                    "Canary interpretation", "Conflicting", "Demo analysis"))
        assert "Fernwood is exposed" not in alert_page
        assert "Fernwood is compromised" not in alert_page
        note(run_name, "W5", "Pass", "Analysis sections, conflict and demo label were present; no exposure claim.")

        assert "Possible match" in alert_page and "65/100" in alert_page and "P2 High" in alert_page
        relevance = query("SELECT * FROM relevance WHERE org_id=?", (x["fern"],))[0]
        points = {factor["key"]: factor["points"] for factor in json.loads(relevance["factors"])}
        assert [points[k] for k in ("severity", "exploitation", "inventory_match", "asset_criticality",
                                     "source_reliability", "questionnaire_gap")] == [16, 8, 12, 15, 9, 5]
        assert relevance["score"] == 65 and relevance["priority"] == "P2"
        assert relevance["p1_gate_reason"] and "not evidence of exposure" in alert_page
        note(run_name, "W6", "Pass", "Alert page showed Possible, 65/100, P2 High, the expected factor values and P1 rationale.")

        post(s, "/notifications/process")
        status = scalar("SELECT status FROM notifications WHERE kind='new' ORDER BY id DESC LIMIT 1")
        if smtp:
            assert status == "sent"
            msg = smtp.messages[-1]
            body = msg["msg"].get_content()
            assert msg["rcpts"] == [SUREH_ADDR]
            assert msg["msg"]["Subject"].startswith("[CANARY DEMO - TEST] P2")
            assert "TEST MODE" in body and "https://thehackernews.com" in body
        else:
            assert status == "blocked"
            blocked_row = query("SELECT error FROM notifications WHERE kind='new' ORDER BY id DESC LIMIT 1")[0]
            notifications = page(s, "/notifications")
            assert "No test address" in blocked_row["error"] and "Blocked" in notifications
            sureh_addr_id = x["sureh"]
            post(s, "/notifications/recipients", {"user_id": sureh_addr_id, "email": SUREH_ADDR})
            notif = scalar("SELECT id FROM notifications WHERE kind='new' ORDER BY id DESC LIMIT 1")
            post(s, f"/notifications/{notif}/retry")
            status = scalar("SELECT status FROM notifications WHERE id=?", (notif,))
            assert status == "rejected"
        # Always test the delivery-check rejection, with zero SMTP connection for a forbidden recipient.
        before_messages = len(smtp.messages) if smtp else 0
        before_connections = smtp.connections if smtp else 0
        post(s, "/notifications/test", {"email": "not-allowlisted@else.example"})
        assert scalar("SELECT status FROM notifications WHERE kind='test' ORDER BY id DESC LIMIT 1") == "rejected"
        if smtp:
            assert len(smtp.messages) == before_messages and smtp.connections == before_connections
            evidence = "Initial notification was Sent to the allowlisted address; off-list delivery check was Rejected with no SMTP connection."
        else:
            evidence = "P2 was Blocked with no address, then Rejected after adding an address and retrying; off-list delivery check was Rejected."
        note(run_name, "W7", "Pass", evidence)

        if smtp:
            post(s, "/notifications/simulate-failure")
            post(s, "/notifications/test", {"email": SUREH_ADDR})
            sim = scalar("SELECT id FROM notifications WHERE kind='test' ORDER BY id DESC LIMIT 1")
            assert scalar("SELECT status FROM notifications WHERE id=?", (sim,)) == "failed"
            assert scalar("SELECT simulated FROM notifications WHERE id=?", (sim,)) == 1
            post(s, "/notifications/simulate-failure")
            post(s, f"/notifications/{sim}/retry")
            assert scalar("SELECT status FROM notifications WHERE id=?", (sim,)) == "sent"
            assert scalar("SELECT attempts FROM notifications WHERE id=?", (sim,)) == 2
            note(run_name, "W8", "Pass", "Simulated delivery failure became Failed (simulated), then Retry became Sent at attempt 2.")
        else:
            note(run_name, "W8", "Blocked", "The run requires configured SMTP; only the capture-server run exercises failure and retry.")

        post(s, "/sources/followup")
        assert scalar("SELECT COUNT(*) FROM source_items WHERE finding_id=(SELECT finding_id FROM alerts WHERE id=?)", (alert,)) == 3
        if smtp:
            post(s, "/notifications/process")
            update = smtp.messages[-1]
            assert update["msg"]["Subject"].startswith("[CANARY DEMO - TEST] Update:")
        else:
            post(s, "/notifications/process")
            assert scalar("SELECT status FROM notifications WHERE kind='update' ORDER BY id DESC LIMIT 1") in ("blocked", "rejected")
        note(run_name, "W9", "Pass", "Xygeni follow-up produced the third source and a material alert update.")

        actor(s, "sureh", x["fern"])
        post(s, f"/alerts/{alert}/assign", {"assignee_id": x["sureh"]})
        post(s, f"/alerts/{alert}/status", {"status": "under_investigation"})
        post(s, f"/alerts/{alert}/guide")
        guide = scalar("SELECT id FROM guides WHERE alert_id=?", (alert,))
        guide_page = page(s, f"/guides/{guide}")
        post(s, f"/guides/{guide}/answer", {"answer": "Unknown"})
        post(s, f"/guides/{guide}/steps/1/status", {"status": "in_progress"})
        assert scalar("SELECT condition_status FROM guide_steps WHERE guide_id=? AND position=4", (guide,)) == "pending"
        assert "AI-generated draft for human review" in guide_page and "Step 5" in guide_page
        note(run_name, "W10", "Pass", "Sureh assigned/investigated; guide had five steps; Unknown kept step 4 conditional.")

        post(s, f"/guides/{guide}/plan")
        plan = scalar("SELECT id FROM plans WHERE guide_id=?", (guide,))
        post(s, f"/plans/{plan}/submit")
        assert post(s, f"/plans/{plan}/approve", {"confirm": "yes"}, expected=403).status_code == 403
        actor(s, "wyatt", x["fern"])
        post(s, f"/plans/{plan}/approve", {"confirm": "yes"})
        plan_page = page(s, f"/plans/{plan}")
        stages = {r[0] for r in query("SELECT DISTINCT stage FROM plan_actions WHERE plan_id=?", (plan,))}
        assert stages == {"Detection", "Containment", "Recovery", "Review"}
        assert scalar("SELECT COUNT(*) FROM plan_actions WHERE plan_id=? AND owner_id=?", (plan, x["koewen"])) >= 1
        assert "Approved" in plan_page and "does not execute" in plan_page
        assert scalar("SELECT COUNT(*) FROM audit_events WHERE org_id=? AND action='plan.approved'", (x["fern"],)) == 1
        note(run_name, "W11", "Pass", "Lead approval was denied; Wyatt approved; plan stages, Koewen owner and no-execution notice verified.")

        analysis = json.loads(scalar("SELECT payload FROM analyses WHERE org_id=? ORDER BY id DESC LIMIT 1", (x["fern"],)))
        original = analysis["what_happened"][0]
        actor(s, "sureh", x["fern"])
        post(s, f"/alerts/{alert}/analysis/correct", {"section": "what_happened", "original": original,
             "corrected": CORRECTED, "reason": "Clarify that this is a technique-level finding."})
        corrected_page = page(s, f"/alerts/{alert}")
        assert CORRECTED in corrected_page and "Correction history" in corrected_page
        assert scalar("SELECT COUNT(*) FROM analysis_corrections WHERE org_id=?", (x["fern"],)) == 1
        assert scalar("SELECT COUNT(*) FROM audit_events WHERE org_id=? AND action='analysis.corrected'", (x["fern"],)) == 1
        note(run_name, "W12", "Pass", "Correction rendered in place with provenance/history and an analysis correction row.")

        actor(s, "wyatt", x["fern"])
        post(s, "/organization/profile", {"name": "Fernwood Labs", "industry": "Software / FinTech",
             "size": "", "location": "Remote", "monitoring_interests": ""})
        post(s, "/organization/inventory", {"name": "Runtime check model", "category": "LLM API",
             "product_key": "runtime-check-model", "version": "", "criticality": "Medium", "capabilities": "llm_api"})
        new_item = scalar("SELECT id FROM inventory_items WHERE org_id=? AND name='Runtime check model'", (x["fern"],))
        assert scalar("SELECT version_status FROM inventory_items WHERE id=?", (new_item,)) == "unknown"
        assert "Runtime check model" in page(s, "/organization")
        post(s, f"/organization/inventory/{new_item}", {"name": "Runtime check model v2", "category": "LLM API",
             "product_key": "runtime-check-model", "version": "2.0", "version_status": "known",
             "criticality": "High", "capabilities": "llm_api"})
        org_page = page(s, "/organization")
        assert "Unknown" in org_page and "Runtime check model v2" in org_page
        assert scalar("SELECT size FROM organizations WHERE id=?", (x["fern"],)) is None
        assert scalar("SELECT COUNT(*) FROM audit_events WHERE org_id=? AND action IN ('organization.profile_updated','inventory.created','inventory.updated')",
                      (x["fern"],)) >= 3
        note(run_name, "W13", "Pass", "Profile size cleared to Unknown; blank-version inventory item saved as Unknown, edited, and changes audited.")

        post(s, "/register", {"username": "runtime_dana", "display_name": "Dana", "password": "pass1234"})
        post(s, "/orgs/create", {"name": "Runtime Check Co", "industry": "Software"})
        new_org = scalar("SELECT id FROM organizations WHERE name='Runtime Check Co'")
        dana = scalar("SELECT id FROM users WHERE username='runtime_dana'")
        post(s, "/organization/inventory", {"name": "AI coding agent", "category": "Coding assistant",
             "product_key": "coding-assistant", "version": "", "criticality": "High",
             "capabilities": "ai_coding_agent, auto_install_packages"})
        post(s, "/sources/refresh")
        new_org_alerts = scalar("SELECT COUNT(*) FROM alerts WHERE org_id=?", (new_org,))
        note(run_name, "REQ-016-new-org-workflow", "Pass" if new_org_alerts else "Fail",
             f"After creating org, adding relevant inventory and refreshing previously collected sources, alert count was {new_org_alerts}.")
        demote = post(s, f"/members/{dana}/role", {"role": "lead"}, expected=400)
        post(s, "/members/invite", {"username": "koewen", "role": "lead"})
        post(s, f"/members/{x['koewen']}/role", {"role": "admin"})
        assert scalar("SELECT role FROM memberships WHERE org_id=? AND user_id=?", (new_org, dana)) == "admin"
        assert scalar("SELECT role FROM memberships WHERE org_id=? AND user_id=?", (new_org, x["koewen"])) == "admin"
        actor(s, "koewen", new_org)
        assert page(s, "/").find("Runtime Check Co") >= 0
        assert scalar("SELECT COUNT(*) FROM audit_events WHERE org_id=? AND action IN ('membership.invited','membership.role_changed')",
                      (new_org,)) >= 2
        note(run_name, "W14", "Pass", "Local account created organization as Admin; last-admin demotion returned 400; invite/role change audited; Koewen opened org.")

        privacy = page(s, "/privacy")
        assert all(term in privacy for term in ("Data flows", "SMTP", "No model provider", "Retention", "until you reset", "HIPAA"))
        assert "Live RSS is off" in privacy
        assert ("SMTP configured" if smtp else "SMTP not configured") in privacy
        note(run_name, "W15", "Pass", "Privacy page described local data flows, retention and no-compliance boundary.")

        actor(s, "priya", x["prairie"])
        routes = [f"/alerts/{alert}", f"/guides/{guide}", f"/plans/{plan}"]
        status_before_probe = scalar("SELECT status FROM alerts WHERE id=?", (alert,))
        assert all(s.get(BASE + route, timeout=10).status_code == 404 for route in routes)
        post(s, f"/alerts/{alert}/status", {"status": "under_investigation"}, expected=404)
        assert scalar("SELECT status FROM alerts WHERE id=?", (alert,)) == status_before_probe
        note(run_name, "W16", "Pass", "Prairie Valley received 404 for Fernwood alert, guide, plan and POST; Fernwood alert remained unchanged.")

        actor(s, "sureh", x["fern"])
        post(s, f"/alerts/{alert}/status", {"status": "mitigation_in_progress"})
        post(s, f"/alerts/{alert}/status", {"status": "resolved_verified", "note": "Runtime permission verified; demo review completed."})
        post(s, "/questionnaire", {"q_dep-review": "Yes"})
        answers = [r[0] for r in query("SELECT a.answer FROM answers a JOIN assessments s ON s.id=a.assessment_id WHERE s.org_id=? AND a.question_key='dep-review' ORDER BY s.id", (x["fern"],))]
        assert answers == ["No", "Yes"]
        audit_actions = {r[0] for r in query("SELECT action FROM audit_events WHERE org_id=?", (x["fern"],))}
        assert {"alert.assigned", "alert.status_changed", "guide.answered", "plan.approved",
                "analysis.corrected", "organization.profile_updated", "questionnaire.submitted"} <= audit_actions
        actor(s, "wyatt", x["fern"])
        post(s, "/demo/reset")
        assert scalar("SELECT COUNT(*) FROM alerts") == 0
        assert scalar("SELECT COUNT(*) FROM plans") == 0
        assert scalar("SELECT COUNT(*) FROM organizations") == 2
        assert scalar("SELECT COUNT(*) FROM users WHERE username='runtime_dana'") == 0
        note(run_name, "W17", "Pass", "Alert resolved with note; No/Yes assessments both retained; reset removed entered account/plans/alerts and restored two seed orgs.")
        if smtp:
            note(run_name, "Email", "Pass", f"Local SMTP capture, not a real inbox: captured {len(smtp.messages)} messages; initial/update/retry outcomes verified.")
        else:
            note(run_name, "Email", "Blocked", "Real inbox delivery blocked: no SMTP configuration or team-owned inbox; blocked and rejected UI states observed.")
        return LOG.read_text(encoding="utf-8", errors="replace")
    finally:
        stop(proc, log_handle)


if __name__ == "__main__":
    smtp = None
    try:
        do_walkthrough("No SMTP", None)
        smtp = CaptureServer()
        do_walkthrough("Local SMTP capture", smtp)
    finally:
        if smtp:
            smtp.close()
    print(json.dumps(observations, indent=2))
