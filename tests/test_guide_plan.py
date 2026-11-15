"""CAN-REQ-010, 011, 012, 013, 014: guide, plan approval, questionnaire history, dashboard, audit."""
import pytest

from tests.conftest import login, org_id, refresh

FERNWOOD = "Fernwood Labs"


def uid(db, name):
    return db.execute("SELECT id FROM users WHERE username=?", (name,)).fetchone()["id"]


@pytest.fixture
def fern(client, db):
    """Fernwood with the PHP2Shell alert collected; signed in as Sureh (Cybersecurity Lead)."""
    f = org_id(db, FERNWOOD)
    login(client, "wyatt", org=f)
    refresh(client)
    client.post("/logout")
    login(client, "sureh", org=f)
    return f


def alert_id(db, f):
    return db.execute("SELECT id FROM alerts WHERE org_id=?", (f,)).fetchone()["id"]


def make_guide(client, db, f):
    client.post(f"/alerts/{alert_id(db, f)}/guide")
    return db.execute("SELECT * FROM guides WHERE org_id=?", (f,)).fetchone()


def make_plan(client, db, f):
    g = make_guide(client, db, f)
    client.post(f"/guides/{g['id']}/plan")
    return db.execute("SELECT * FROM plans WHERE org_id=?", (f,)).fetchone()


def audit_actions(db, f):
    return [r["action"] for r in db.execute("SELECT action FROM audit_events WHERE org_id=? ORDER BY id", (f,))]


# ------------------------------------------------------------------ guide (011)
def test_guide_generated_from_alert_without_questionnaire(client, db, fern):
    db.execute("DELETE FROM assessments WHERE org_id=?", (fern,))
    db.commit()
    g = make_guide(client, db, fern)
    assert g is not None
    page = client.get(f"/guides/{g['id']}").data.decode()
    for text in ("AI-generated draft for human review", "Confirm the PHP version", "Why it matters", "Check",
                 "Technique", "reachable from the internet", "Unknown", "CIS Controls v8", "8.3.36"):
        assert text in page, text
    assert db.execute("SELECT COUNT(*) FROM guide_steps WHERE guide_id=?", (g["id"],)).fetchone()[0] == 5


def test_requesting_guide_twice_reuses_it(client, db, fern):
    make_guide(client, db, fern)
    make_guide(client, db, fern)
    assert db.execute("SELECT COUNT(*) FROM guides WHERE org_id=?", (fern,)).fetchone()[0] == 1


def test_unknown_answer_keeps_step_4_conditional(client, db, fern):
    g = make_guide(client, db, fern)
    client.post(f"/guides/{g['id']}/answer", data={"answer": "Unknown"})
    step = db.execute("SELECT * FROM guide_steps WHERE guide_id=? AND position=4", (g["id"],)).fetchone()
    assert step["condition_status"] == "pending" and "Unknown" in step["condition_note"]
    q = db.execute("SELECT * FROM guide_questions WHERE guide_id=?", (g["id"],)).fetchone()
    assert q["answer"] == "Unknown" and q["answered_by"] == uid(db, "sureh")
    assert "guide.answered" in audit_actions(db, fern)


def test_yes_answer_makes_step_4_immediate(client, db, fern):
    g = make_guide(client, db, fern)
    client.post(f"/guides/{g['id']}/answer", data={"answer": "Yes"})
    step = db.execute("SELECT * FROM guide_steps WHERE guide_id=? AND position=4", (g["id"],)).fetchone()
    assert step["condition_status"] == "met"


def test_invalid_answer_rejected(client, db, fern):
    g = make_guide(client, db, fern)
    assert client.post(f"/guides/{g['id']}/answer", data={"answer": "Maybe"}).status_code == 400


def test_step_progress_and_edit_are_audited_with_before_after(client, db, fern):
    g = make_guide(client, db, fern)
    client.post(f"/guides/{g['id']}/steps/1/status", data={"status": "in_progress"})
    client.post(f"/guides/{g['id']}/steps/2/edit", data={"action": "Disable auto-install in the assistant settings.",
                                                         "rationale": "r", "checks": "c", "technique": "t"})
    s1, s2 = db.execute("SELECT * FROM guide_steps WHERE guide_id=? AND position IN (1,2) ORDER BY position",
                        (g["id"],)).fetchall()
    assert s1["status"] == "in_progress"
    assert s2["action"] == "Disable auto-install in the assistant settings." and s2["edited"] == 1
    ev = db.execute("SELECT * FROM audit_events WHERE action='guide.step_edited'").fetchone()
    assert "Upgrade PHP to a fixed release" in ev["before_state"]


def test_other_org_cannot_open_guide(client, db, fern):
    g = make_guide(client, db, fern)
    client.post("/logout")
    login(client, "priya", org=org_id(db, "Prairie Valley Medical Center"))
    assert client.get(f"/guides/{g['id']}").status_code == 404
    assert client.post(f"/guides/{g['id']}/answer", data={"answer": "Yes"}).status_code == 404


# ------------------------------------------------------------------ plan (012)
def test_plan_from_guide_uses_applicable_stages_and_owners(client, db, fern):
    p = make_plan(client, db, fern)
    assert (p["title"], p["status"], p["version"]) == ("Critical PHP remote code execution (PHP2Shell)", "draft", 1)
    stages = [r["stage"] for r in db.execute("SELECT DISTINCT stage FROM plan_actions WHERE plan_id=? ORDER BY position",
                                             (p["id"],))]
    assert stages == ["Detection", "Containment", "Recovery", "Review"]
    owners = {r["owner_id"] for r in db.execute("SELECT owner_id FROM plan_actions WHERE plan_id=?", (p["id"],))}
    assert owners == {uid(db, "sureh"), uid(db, "koewen")}
    assert p["alert_id"] == alert_id(db, fern) and p["guide_id"] is not None


def test_lead_cannot_approve_and_admin_must_confirm(client, db, fern, app):
    p = make_plan(client, db, fern)
    client.post(f"/plans/{p['id']}/submit")
    assert client.post(f"/plans/{p['id']}/approve", data={"confirm": "yes"}).status_code == 403
    client.post("/logout")
    login(client, "wyatt", org=fern)
    assert client.post(f"/plans/{p['id']}/approve").status_code == 400
    client.post(f"/plans/{p['id']}/approve", data={"confirm": "yes"})
    p = db.execute("SELECT * FROM plans WHERE id=?", (p["id"],)).fetchone()
    assert p["status"] == "approved" and p["approved_version"] == p["version"]
    v = db.execute("SELECT * FROM plan_versions WHERE plan_id=? AND status='approved'", (p["id"],)).fetchone()
    assert v["actor_id"] == uid(db, "wyatt")
    assert "plan.approved" in audit_actions(db, fern)
    assert "does not execute" in client.get(f"/plans/{p['id']}").data.decode()


def test_cannot_approve_a_draft(client, db, fern):
    p = make_plan(client, db, fern)
    client.post("/logout")
    login(client, "wyatt", org=fern)
    assert client.post(f"/plans/{p['id']}/approve", data={"confirm": "yes"}).status_code == 400


def test_editing_approved_plan_returns_to_draft_and_keeps_approved_version(client, db, fern):
    p = make_plan(client, db, fern)
    client.post(f"/plans/{p['id']}/submit")
    client.post("/logout")
    login(client, "wyatt", org=fern)
    client.post(f"/plans/{p['id']}/approve", data={"confirm": "yes"})
    approved = db.execute("SELECT approved_version FROM plans WHERE id=?", (p["id"],)).fetchone()[0]
    client.post(f"/plans/{p['id']}/edit", data={"title": "Critical PHP remote code execution (PHP2Shell) (rev)", "review_date": "2027-02-01"})
    p2 = db.execute("SELECT * FROM plans WHERE id=?", (p["id"],)).fetchone()
    assert p2["status"] == "draft" and p2["version"] > approved and p2["approved_version"] == approved
    snap = db.execute("SELECT snapshot FROM plan_versions WHERE plan_id=? AND version=? AND status='approved'",
                      (p["id"], approved)).fetchone()
    assert "(rev)" not in snap["snapshot"]
    page = client.get(f"/plans/{p['id']}").data.decode()
    assert "differs from approved version" in page


def test_plan_in_review_cannot_be_edited(client, db, fern):
    p = make_plan(client, db, fern)
    client.post(f"/plans/{p['id']}/submit")
    assert client.post(f"/plans/{p['id']}/edit", data={"title": "x"}).status_code == 400


def test_plan_action_owner_and_review_date_can_be_set(client, db, fern):
    p = make_plan(client, db, fern)
    action = db.execute("SELECT id FROM plan_actions WHERE plan_id=? ORDER BY position LIMIT 1", (p["id"],)).fetchone()["id"]
    client.post(f"/plans/{p['id']}/edit", data={"review_date": "2027-01-15", f"owner_{action}": uid(db, "koewen"),
                                                 f"status_{action}": "in_progress"})
    p = db.execute("SELECT * FROM plans WHERE id=?", (p["id"],)).fetchone()
    a = db.execute("SELECT * FROM plan_actions WHERE id=?", (action,)).fetchone()
    assert p["review_date"] == "2027-01-15" and a["owner_id"] == uid(db, "koewen") and a["status"] == "in_progress"


def test_dashboard_counts_open_plans_and_plan_awaiting_approval(client, db, fern):
    p = make_plan(client, db, fern)
    client.post(f"/plans/{p['id']}/submit")
    page = client.get("/").data.decode()
    assert 'data-count="open-plans">1<' in page
    assert "Awaiting approval" in page


# ------------------------------------------------------------------ questionnaire (010)
def test_new_assessment_preserves_prior_no_answer(client, db, fern):
    client.post("/questionnaire", data={"q_dep-review": "Yes", "q_agent-permissions": "Partial",
                                        "q_untrusted-content": "Unknown", "q_output-handling": "Not applicable"})
    rows = db.execute("SELECT a.answer FROM answers a JOIN assessments s ON s.id=a.assessment_id"
                      " WHERE s.org_id=? AND a.question_key='dep-review' ORDER BY s.id", (fern,)).fetchall()
    assert [r["answer"] for r in rows] == ["No", "Yes"]
    assert "questionnaire.submitted" in audit_actions(db, fern)


def test_questionnaire_rejects_invalid_answers(client, db, fern):
    assert client.post("/questionnaire", data={"q_dep-review": "Definitely"}).status_code == 400


def test_questionnaire_shows_mapping_and_explains_threat_weighting(client, db, fern):
    page = client.get("/questionnaire").data.decode()
    assert "LLM03:2025 Supply Chain" in page and "https://genai.owasp.org/llmrisk/llm032025-supply-chain/" in page
    assert "Safeguard 7.4" in page and "https://www.cisecurity.org/controls/continuous-vulnerability-management" in page
    assert "Weighted up" in page and "PHP2Shell" in page
    assert "not a compliance score" in page


def test_other_org_cannot_see_fernwood_assessments(client, db, fern):
    client.post("/logout")
    login(client, "priya", org=org_id(db, "Prairie Valley Medical Center"))
    page = client.get("/questionnaire").data.decode()
    assert "No assessments yet" in page and "Initial assessment" not in page
