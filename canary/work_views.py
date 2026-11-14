"""Guides (CAN-REQ-011), plans (012), and questionnaire (010) routes. All org-scoped; out-of-org ids are 404."""
import json

from flask import abort, flash, g, redirect, render_template, request, url_for

from .auth import actor_label, org_required, role_required
from .db import audit, get_db, now_iso
from .guides import QUESTIONS, build_guide, condition_for_answer
from .pipeline import inventory_for, process_findings
from .plans import ACTION_STATUSES, PLAN_STATUSES, STAGES, record_version, snapshot, template_actions
from .views import CLOSED, bp, commit, org_alert_or_404

STEP_STATUSES = {"draft": "Draft", "in_progress": "In progress", "done": "Done", "deferred": "Deferred"}
ANSWERS = ["Yes", "No", "Partial", "Unknown", "Not applicable"]


def guide_or_404(guide_id):
    row = get_db().execute("SELECT * FROM guides WHERE id=? AND org_id=?", (guide_id, g.org["id"])).fetchone()
    if row is None:
        abort(404)
    return row


def plan_or_404(plan_id):
    row = get_db().execute("SELECT * FROM plans WHERE id=? AND org_id=?", (plan_id, g.org["id"])).fetchone()
    if row is None:
        abort(404)
    return row


def step_or_404(guide_id, position):
    row = get_db().execute("SELECT * FROM guide_steps WHERE guide_id=? AND position=?", (guide_id, position)).fetchone()
    if row is None:
        abort(404)
    return row


# ------------------------------------------------------------------ guides
@bp.post("/alerts/<int:alert_id>/guide")
@role_required("admin", "lead")
def create_guide(alert_id):
    db = get_db()
    alert = org_alert_or_404(alert_id)
    existing = db.execute("SELECT id FROM guides WHERE alert_id=?", (alert_id,)).fetchone()
    if existing:
        return redirect(url_for("main.guide_detail", guide_id=existing["id"]))
    finding = db.execute("SELECT * FROM findings WHERE id=?", (alert["finding_id"],)).fetchone()
    sources = [dict(r) for r in db.execute("SELECT id, url FROM source_items WHERE finding_id=?", (finding["id"],))]
    built = build_guide(finding["technique"], inventory_for(db, g.org["id"]), sources)
    ts = now_iso()
    gid = db.execute("INSERT INTO guides (org_id, alert_id, label, technique, created_by, created_at, updated_at)"
                     " VALUES (?,?,?,?,?,?,?)",
                     (g.org["id"], alert_id, built["label"], finding["technique"], g.user["id"], ts, ts)).lastrowid
    for s in built["steps"]:
        db.execute("INSERT INTO guide_steps (guide_id, position, action, rationale, checks, technique, basis, links,"
                   " condition, condition_status, condition_note, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                   (gid, s["position"], s["action"], s["rationale"], s["checks"], s["technique"], s["basis"],
                    json.dumps(s["links"]), s["condition"], s["condition_status"], s["condition_note"], ts))
    q = built["question"]
    if q:
        db.execute("INSERT INTO guide_questions (guide_id, key, step_position, text, why, options) VALUES (?,?,?,?,?,?)",
                   (gid, q["key"], q["step"], q["text"], q["why"], json.dumps(q["options"])))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="guide.created",
          target_type="guide", target_id=gid, summary=f"Guide drafted from alert #{alert_id} ({len(built['steps'])} steps)")
    commit()
    return redirect(url_for("main.guide_detail", guide_id=gid))


@bp.route("/guides/<int:guide_id>")
@org_required
def guide_detail(guide_id):
    db = get_db()
    guide = guide_or_404(guide_id)
    steps = db.execute("SELECT * FROM guide_steps WHERE guide_id=? ORDER BY position", (guide_id,)).fetchall()
    questions = db.execute("SELECT q.*, u.display_name AS answerer FROM guide_questions q"
                           " LEFT JOIN users u ON u.id=q.answered_by WHERE q.guide_id=?", (guide_id,)).fetchall()
    alert = db.execute("SELECT a.id, f.title FROM alerts a JOIN findings f ON f.id=a.finding_id WHERE a.id=?",
                       (guide["alert_id"],)).fetchone()
    plan = db.execute("SELECT id, title, status FROM plans WHERE guide_id=?", (guide_id,)).fetchone()
    history = db.execute("SELECT * FROM audit_events WHERE org_id=? AND target_type='guide' AND target_id=?"
                         " ORDER BY id DESC", (g.org["id"], guide_id)).fetchall()
    return render_template("guide.html", guide=guide, steps=steps, questions=questions, alert=alert, plan=plan,
                           history=history, STEP_STATUSES=STEP_STATUSES)


@bp.post("/guides/<int:guide_id>/answer")
@role_required("admin", "lead")
def answer_guide_question(guide_id):
    db = get_db()
    guide = guide_or_404(guide_id)
    q = db.execute("SELECT * FROM guide_questions WHERE guide_id=? ORDER BY id LIMIT 1", (guide_id,)).fetchone()
    answer = request.form.get("answer", "")
    if q is None or answer not in json.loads(q["options"]) + ["Not applicable"]:
        abort(400, description="Choose one of the offered answers.")
    status, note = condition_for_answer(answer)
    ts = now_iso()
    db.execute("UPDATE guide_questions SET answer=?, answered_by=?, answered_at=? WHERE id=?",
               (answer, g.user["id"], ts, q["id"]))
    db.execute("UPDATE guide_steps SET condition_status=?, condition_note=?, updated_at=? WHERE guide_id=? AND position=?",
               (status, f"{note} (answered by {g.user['display_name']})", ts, guide_id, q["step_position"]))
    db.execute("UPDATE guides SET updated_at=? WHERE id=?", (ts, guide["id"]))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="guide.answered",
          target_type="guide", target_id=guide_id, summary=f"Answered “{q['text']}” — {answer}",
          before={"answer": q["answer"]}, after={"answer": answer})
    commit()
    return redirect(url_for("main.guide_detail", guide_id=guide_id))


@bp.post("/guides/<int:guide_id>/steps/<int:position>/status")
@role_required("admin", "lead")
def guide_step_status(guide_id, position):
    db = get_db()
    guide_or_404(guide_id)
    step = step_or_404(guide_id, position)
    new = request.form.get("status", "")
    if new not in STEP_STATUSES:
        abort(400, description="Unknown step status.")
    db.execute("UPDATE guide_steps SET status=?, updated_at=? WHERE id=?", (new, now_iso(), step["id"]))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="guide.step_progress",
          target_type="guide", target_id=guide_id,
          summary=f"Step {position}: {STEP_STATUSES[step['status']]} → {STEP_STATUSES[new]}",
          before={"status": step["status"]}, after={"status": new})
    commit()
    return redirect(url_for("main.guide_detail", guide_id=guide_id) + f"#step-{position}")


@bp.post("/guides/<int:guide_id>/steps/<int:position>/edit")
@role_required("admin", "lead")
def guide_step_edit(guide_id, position):
    db = get_db()
    guide_or_404(guide_id)
    step = step_or_404(guide_id, position)
    fields = ("action", "rationale", "checks", "technique")
    new = {f: request.form.get(f, step[f]).strip() or step[f] for f in fields}
    before = {f: step[f] for f in fields if step[f] != new[f]}
    if not before:
        return redirect(url_for("main.guide_detail", guide_id=guide_id))
    db.execute("UPDATE guide_steps SET action=?, rationale=?, checks=?, technique=?, edited=1, updated_at=? WHERE id=?",
               (*(new[f] for f in fields), now_iso(), step["id"]))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="guide.step_edited",
          target_type="guide", target_id=guide_id, summary=f"Step {position} edited ({', '.join(before)})",
          before=before, after={f: new[f] for f in before})
    commit()
    return redirect(url_for("main.guide_detail", guide_id=guide_id) + f"#step-{position}")


# ------------------------------------------------------------------ plans
@bp.post("/guides/<int:guide_id>/plan")
@role_required("admin", "lead")
def create_plan(guide_id):
    db = get_db()
    guide = guide_or_404(guide_id)
    existing = db.execute("SELECT id FROM plans WHERE guide_id=?", (guide_id,)).fetchone()
    if existing:
        return redirect(url_for("main.plan_detail", plan_id=existing["id"]))
    steps = db.execute("SELECT * FROM guide_steps WHERE guide_id=? ORDER BY position", (guide_id,)).fetchall()
    title, actions = template_actions(guide["technique"], steps)
    if title is None:
        title = "Response plan: " + db.execute("SELECT f.title FROM alerts a JOIN findings f ON f.id=a.finding_id"
                                                " WHERE a.id=?", (guide["alert_id"],)).fetchone()["title"]
    other_lead = db.execute("SELECT user_id FROM memberships WHERE org_id=? AND role='lead' AND status='active'"
                            " AND user_id!=? ORDER BY user_id LIMIT 1", (g.org["id"], g.user["id"])).fetchone()
    owners = {"author": g.user["id"], "second_lead": other_lead["user_id"] if other_lead else g.user["id"]}
    ts = now_iso()
    pid = db.execute("INSERT INTO plans (org_id, alert_id, guide_id, title, created_by, created_at, updated_at)"
                     " VALUES (?,?,?,?,?,?,?)",
                     (g.org["id"], guide["alert_id"], guide_id, title, g.user["id"], ts, ts)).lastrowid
    for n, (stage, action, owner) in enumerate(actions, start=1):
        db.execute("INSERT INTO plan_actions (plan_id, stage, position, action, owner_id) VALUES (?,?,?,?,?)",
                   (pid, stage, n, action, owners[owner]))
    record_version(db, pid, g.user["id"], actor_label(), "Draft created from guide")
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="plan.created",
          target_type="plan", target_id=pid, summary=f"Draft plan “{title}” created from guide #{guide_id}")
    commit()
    return redirect(url_for("main.plan_detail", plan_id=pid))


@bp.route("/plans")
@org_required
def plans_list():
    rows = get_db().execute("SELECT p.*, u.display_name AS author FROM plans p LEFT JOIN users u ON u.id=p.created_by"
                            " WHERE p.org_id=? ORDER BY p.id DESC", (g.org["id"],)).fetchall()
    return render_template("plans.html", plans=rows, PLAN_STATUSES=PLAN_STATUSES)


@bp.route("/plans/<int:plan_id>")
@org_required
def plan_detail(plan_id):
    db = get_db()
    plan = plan_or_404(plan_id)
    actions = db.execute("SELECT a.*, u.display_name AS owner FROM plan_actions a LEFT JOIN users u ON u.id=a.owner_id"
                         " WHERE a.plan_id=? ORDER BY a.position", (plan_id,)).fetchall()
    versions = db.execute("SELECT * FROM plan_versions WHERE plan_id=? ORDER BY id DESC", (plan_id,)).fetchall()
    members = db.execute("SELECT u.id, u.display_name FROM memberships m JOIN users u ON u.id=m.user_id"
                         " WHERE m.org_id=? AND m.status='active' ORDER BY u.id", (g.org["id"],)).fetchall()
    approved = None
    if plan["approved_version"]:
        row = db.execute("SELECT * FROM plan_versions WHERE plan_id=? AND version=? AND status='approved'"
                         " ORDER BY id DESC LIMIT 1", (plan_id, plan["approved_version"])).fetchone()
        approved = dict(row, snap=json.loads(row["snapshot"])) if row else None
    return render_template("plan.html", plan=plan, actions=actions, versions=versions, members=members,
                           approved=approved, PLAN_STATUSES=PLAN_STATUSES, ACTION_STATUSES=ACTION_STATUSES,
                           STAGES=STAGES, current=snapshot(db, plan_id))


def _set_plan_status(plan, new, note, action):
    db = get_db()
    db.execute("UPDATE plans SET status=?, updated_at=? WHERE id=?", (new, now_iso(), plan["id"]))
    if new == "approved":
        db.execute("UPDATE plans SET approved_version=version WHERE id=?", (plan["id"],))
    record_version(db, plan["id"], g.user["id"], actor_label(), note)
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action=action,
          target_type="plan", target_id=plan["id"],
          summary=f"{PLAN_STATUSES[plan['status']]} → {PLAN_STATUSES[new]} (v{plan['version']})",
          before={"status": plan["status"]}, after={"status": new})
    commit()
    return redirect(url_for("main.plan_detail", plan_id=plan["id"]))


@bp.post("/plans/<int:plan_id>/submit")
@role_required("admin", "lead")
def submit_plan(plan_id):
    plan = plan_or_404(plan_id)
    if plan["status"] != "draft":
        abort(400, description="Only a draft plan can be submitted for review.")
    return _set_plan_status(plan, "in_review", "Submitted for review (approval recommended)", "plan.submitted")


@bp.post("/plans/<int:plan_id>/return")
@role_required("admin", "lead")
def return_plan(plan_id):
    plan = plan_or_404(plan_id)
    if plan["status"] != "in_review":
        abort(400, description="Only a plan in review can be returned to draft.")
    return _set_plan_status(plan, "draft", "Returned to draft for changes", "plan.returned")


@bp.post("/plans/<int:plan_id>/approve")
@role_required("admin")
def approve_plan(plan_id):
    plan = plan_or_404(plan_id)
    if plan["status"] != "in_review":
        abort(400, description="Only a plan in review can be approved.")
    if request.form.get("confirm") != "yes":
        abort(400, description="Approval requires explicit confirmation.")
    return _set_plan_status(plan, "approved", "Approved by Administrator (human review; nothing executed)",
                            "plan.approved")


@bp.post("/plans/<int:plan_id>/archive")
@role_required("admin")
def archive_plan(plan_id):
    plan = plan_or_404(plan_id)
    if plan["status"] != "approved":
        abort(400, description="Only an approved plan can be archived.")
    return _set_plan_status(plan, "archived", "Archived", "plan.archived")


@bp.post("/plans/<int:plan_id>/edit")
@role_required("admin", "lead")
def edit_plan(plan_id):
    db = get_db()
    plan = plan_or_404(plan_id)
    if plan["status"] not in ("draft", "approved"):
        abort(400, description="Plans in review or archived cannot be edited; return the plan to draft first.")
    before = snapshot(db, plan_id)
    f = request.form
    db.execute("UPDATE plans SET title=?, review_date=? WHERE id=?",
               ((f.get("title") or plan["title"]).strip(), f.get("review_date", plan["review_date"]) or None, plan_id))
    member_ids = {r["user_id"] for r in db.execute("SELECT user_id FROM memberships WHERE org_id=? AND status='active'",
                                                   (g.org["id"],))}
    for a in db.execute("SELECT * FROM plan_actions WHERE plan_id=?", (plan_id,)).fetchall():
        owner = f.get(f"owner_{a['id']}", type=int) or a["owner_id"]
        status = f.get(f"status_{a['id']}", a["status"])
        if owner not in member_ids or status not in ACTION_STATUSES:
            abort(400, description="Owners must be active members; statuses must be valid.")
        db.execute("UPDATE plan_actions SET action=?, owner_id=?, status=?, due_date=? WHERE id=?",
                   ((f.get(f"action_{a['id']}") or a["action"]).strip(), owner, status,
                    f.get(f"due_{a['id']}", a["due_date"]) or None, a["id"]))
    after = snapshot(db, plan_id)
    if {k: v for k, v in after.items() if k not in ("version", "status")} == \
            {k: v for k, v in before.items() if k not in ("version", "status")}:
        return redirect(url_for("main.plan_detail", plan_id=plan_id))
    new_status = "draft"  # an approved plan that is materially edited returns to draft
    db.execute("UPDATE plans SET version=version+1, status=?, updated_at=? WHERE id=?", (new_status, now_iso(), plan_id))
    note = "Edited after approval; returned to draft (approved version preserved)" if plan["status"] == "approved" \
        else "Draft edited"
    record_version(db, plan_id, g.user["id"], actor_label(), note)
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="plan.edited",
          target_type="plan", target_id=plan_id, summary=f"{note} (v{plan['version']} → v{plan['version'] + 1})",
          before={"title": before["title"], "review_date": before["review_date"], "status": plan["status"]},
          after={"title": after["title"], "review_date": after["review_date"], "status": new_status})
    commit()
    return redirect(url_for("main.plan_detail", plan_id=plan_id))


# ------------------------------------------------------------------ questionnaire
@bp.route("/questionnaire", methods=["GET", "POST"])
@org_required
def questionnaire():
    db = get_db()
    oid = g.org["id"]
    questions = db.execute("SELECT * FROM questions ORDER BY rowid").fetchall()
    if request.method == "POST":
        if g.role not in ("admin", "lead"):
            abort(403)
        answers = {q["key"]: request.form.get(f"q_{q['key']}", "") for q in questions}
        answers = {k: v for k, v in answers.items() if v}
        if not answers or any(v not in ANSWERS for v in answers.values()):
            abort(400, description="Answer at least one question using Yes, No, Partial, Unknown, or Not applicable.")
        aid = db.execute("INSERT INTO assessments (org_id, respondent_id, created_at, note) VALUES (?,?,?,?)",
                         (oid, g.user["id"], now_iso(), request.form.get("note", "").strip() or None)).lastrowid
        db.executemany("INSERT INTO answers (assessment_id, question_key, answer) VALUES (?,?,?)",
                       [(aid, k, v) for k, v in answers.items()])
        audit(db, org_id=oid, actor_id=g.user["id"], actor_label=actor_label(), action="questionnaire.submitted",
              target_type="assessment", target_id=aid,
              summary=f"New assessment with {len(answers)} answer(s); earlier assessments unchanged")
        # Re-assess this org's findings so the questionnaire-gap factor reflects the latest answers.
        fids = {r["finding_id"] for r in db.execute("SELECT finding_id FROM relevance WHERE org_id=?", (oid,))}
        process_findings(db, fids, actor_label())
        commit()
        flash("Assessment saved. Earlier assessments are kept unchanged in history.")
        return redirect(url_for("main.questionnaire"))
    assessments = db.execute("SELECT s.*, u.display_name AS respondent FROM assessments s"
                             " LEFT JOIN users u ON u.id=s.respondent_id WHERE s.org_id=? ORDER BY s.id DESC",
                             (oid,)).fetchall()
    answers = {s["id"]: {r["question_key"]: r["answer"] for r in db.execute(
        "SELECT question_key, answer FROM answers WHERE assessment_id=?", (s["id"],))} for s in assessments}
    latest = answers[assessments[0]["id"]] if assessments else {}
    # Threat weighting: open alerts whose technique maps to a question raise its recommendation weight.
    open_alerts = db.execute(
        "SELECT a.id, f.title, f.technique FROM alerts a JOIN findings f ON f.id=a.finding_id"
        " WHERE a.org_id=? AND a.status NOT IN (%s)" % ",".join("?" * len(CLOSED)), (oid, *CLOSED)).fetchall()
    weights = {}
    for q in questions:
        related = [a for a in open_alerts if q["technique"] and a["technique"] == q["technique"]]
        weights[q["key"]] = {"weight": 1 + len(related), "alerts": related}
    gaps = sorted([q for q in questions if latest.get(q["key"]) in ("No", "Partial", "Unknown")],
                  key=lambda q: -weights[q["key"]]["weight"])
    return render_template("questionnaire.html", questions=questions, assessments=assessments, answers=answers,
                           latest=latest, weights=weights, gaps=gaps, ANSWERS=ANSWERS)
