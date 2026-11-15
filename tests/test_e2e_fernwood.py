"""End-to-end Fernwood PHP2Shell walkthrough (documents/php2shell-demo-flow.md, steps 1-11)."""
from canary.db import get_db
from tests.conftest import login, org_id
from tests.smtp_capture import CaptureServer
from tests.test_notifications import KOEWEN_ADDR, make_app


def test_full_fernwood_walkthrough(tmp_path):
    smtp = CaptureServer()
    try:
        app = make_app(tmp_path, smtp)
        c = app.test_client()
        with app.app_context():
            db = get_db()
            fern = org_id(db, "Fernwood Labs")
            uid = {u: db.execute("SELECT id FROM users WHERE username=?", (u,)).fetchone()["id"]
                   for u in ("wyatt", "sureh", "koewen")}

            # 1. Organization and roles
            login(c, "wyatt", org=fern)
            org = c.get("/organization").data.decode()
            assert "Demo data" in org and "8.3.30" in org and "Cybersecurity Lead" in org

            # 2. Sources + refresh; 3. normalize/dedup
            c.post("/notifications/recipients", data={"user_id": uid["koewen"], "email": KOEWEN_ADDR})
            c.post("/sources/refresh")
            alert = db.execute("SELECT id FROM alerts WHERE org_id=?", (fern,)).fetchone()["id"]
            assert db.execute("SELECT COUNT(*) FROM source_items").fetchone()[0] == 4
            assert db.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 1

            # 4-5. Evidence-backed analysis: Confirmed / 87 / held at P2 (exploitation not yet confirmed)
            page = c.get(f"/alerts/{alert}").data.decode()
            assert "Confirmed match · Score 87/100" in page and "P2 High" in page and "gate not met" in page

            # 6. Real test email path (local capture server stands in for the SMTP provider)
            c.post("/notifications/process")
            assert smtp.messages and smtp.messages[0]["msg"]["Subject"].startswith("[CANARY DEMO - TEST] P2")
            c.post("/notifications/test", data={"email": "not-on-list@else.example"})
            assert db.execute("SELECT status FROM notifications WHERE kind='test'").fetchone()[0] == "rejected"

            # 3 (later). Check Point confirms exploitation -> escalates to P1 with an immediate update email
            c.post("/sources/followup")
            assert db.execute("SELECT COUNT(*) FROM source_items").fetchone()[0] == 5
            page = c.get(f"/alerts/{alert}").data.decode()
            assert "Confirmed match · Score 95/100" in page and "P1 Critical" in page
            assert smtp.messages[-1]["msg"]["Subject"].startswith("[CANARY DEMO - TEST] Update: P1")
            c.post("/logout")

            # 7. Sureh investigates
            login(c, "sureh", org=fern)
            c.post(f"/alerts/{alert}/assign", data={"assignee_id": uid["sureh"]})
            c.post(f"/alerts/{alert}/status", data={"status": "under_investigation"})

            # 8. Targeted guide, Unknown answer keeps step 4 conditional
            c.post(f"/alerts/{alert}/guide")
            guide = db.execute("SELECT id FROM guides WHERE alert_id=?", (alert,)).fetchone()["id"]
            c.post(f"/guides/{guide}/answer", data={"answer": "Unknown"})
            c.post(f"/guides/{guide}/steps/1/status", data={"status": "in_progress"})
            assert db.execute("SELECT condition_status FROM guide_steps WHERE guide_id=? AND position=4",
                              (guide,)).fetchone()[0] == "pending"

            # 9. Plan: draft -> in review -> Administrator approval
            c.post(f"/guides/{guide}/plan")
            plan = db.execute("SELECT id FROM plans WHERE guide_id=?", (guide,)).fetchone()["id"]
            koewen_action = db.execute("SELECT 1 FROM plan_actions WHERE plan_id=? AND owner_id=?",
                                       (plan, uid["koewen"])).fetchone()
            assert koewen_action, "Koewen owns the interim mitigation and exposure check"
            c.post(f"/plans/{plan}/submit")
            assert c.post(f"/plans/{plan}/approve", data={"confirm": "yes"}).status_code == 403
            c.post("/logout")
            login(c, "wyatt", org=fern)
            c.post(f"/plans/{plan}/approve", data={"confirm": "yes"})
            assert db.execute("SELECT status FROM plans WHERE id=?", (plan,)).fetchone()[0] == "approved"
            c.post("/logout")

            # 10. Close-out: mitigation -> resolved with verification note; new Yes assessment
            login(c, "sureh", org=fern)
            c.post(f"/alerts/{alert}/status", data={"status": "mitigation_in_progress"})
            c.post(f"/alerts/{alert}/status", data={"status": "resolved_verified",
                                                    "note": "Portal upgraded to PHP 8.3.36; workers restarted; no indicators found"})
            c.post("/questionnaire", data={"q_patch-sla": "Yes"})
            answers = [r[0] for r in db.execute(
                "SELECT a.answer FROM answers a JOIN assessments s ON s.id=a.assessment_id"
                " WHERE s.org_id=? AND a.question_key='patch-sla' ORDER BY s.id", (fern,))]
            assert answers == ["No", "Yes"]
            actions = {r[0] for r in db.execute("SELECT action FROM audit_events WHERE org_id=?", (fern,))}
            assert {"alert.assigned", "alert.status_changed", "guide.answered", "plan.approved",
                    "questionnaire.submitted", "notification.sent"} <= actions
            assert db.execute("SELECT status FROM alerts WHERE id=?", (alert,)).fetchone()[0] == "resolved_verified"
            c.post("/logout")

            # 11. Reset restores the seed state
            login(c, "wyatt", org=fern)
            c.post("/demo/reset")
            db = get_db()
            assert db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0] == 0
            assert db.execute("SELECT COUNT(*) FROM plans").fetchone()[0] == 0
            assert db.execute("SELECT COUNT(*) FROM organizations").fetchone()[0] == 2
    finally:
        smtp.close()
