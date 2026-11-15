import json
from datetime import datetime, timedelta

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .analysis import apply_corrections, corrections_for
from .auth import ROLE_LABELS, actor_label, login_required, org_required, role_required
from .collector import FIXTURE_ADAPTER, bump_revision, ingest_item, run_collection, snapshot_revision
from .db import audit, get_db, now_iso
from .delivery import (SIMULATE_KEY, allowlist_for, dispatch, env_allowlist, permitted_domains, enqueue_for_alert, get_setting, process_digest, process_queue,
                       send_test, set_setting, smtp_status)
from .fixtures import FOLLOWUP_ITEMS
from .live import LIVE_FEEDS
from .normalize import detect_technique
from .notify import EMAIL_RE, SUBJECT_PREFIX, check_recipient
from .pipeline import assess_backlog, assess_org, process_findings
from .scoring import MATCH_LABELS, PRIORITY_LABELS
from .seed import reset_demo
from .workflow import ALERT_STATUSES, ALERT_TRANSITIONS, NOTE_REQUIRED, TransitionError, check_transition

bp = Blueprint("main", __name__)

CLOSED = ("resolved_verified", "not_applicable", "risk_accepted")
STALE_AFTER = timedelta(hours=2)


PRESENTATION_SCRUB = [
    (" (fictional sample data only)", " (sample data only)"),
    (" (fictional)", ""),
    ("Demo analysis (deterministic) — ", ""),
    (" (demo template; no actions are executed)", " (no actions are executed)"),
    ("Additional evidence (demo follow-up)", "Additional evidence (follow-up report)"),
    ("Offline fixture adapter (demo)", "Catalog feed"),
    ("Seeded fictional demo organization ", "Workspace created: "),
    ("Initial assessment (fictional demo context)", "Initial assessment"),
    ("Signed in (demo authentication)", "Signed in"),
    ("Simulated outage (demo):", "Simulated outage:"),
    ("Simulated delivery failure (demo)", "Simulated delivery failure"),
    ("System (demo seed)", "System"),
    ("Registered a local demo account", "Registered an account"),
    ("Registered local demo user", "Registered user"),
    ("Demo simulation for this organization only:", "Simulation for this organization only:"),
    ("Demo simulation:", "Simulation:"),
    ("Demo step: follow-up report delivered", "Follow-up report delivered"),
    ("Demo reset:", "Workspace reset:"),
]


def register_filters(app):
    app.jinja_env.filters["fromjson"] = json.loads
    app.jinja_env.globals.update(ROLE_LABELS=ROLE_LABELS, MATCH_LABELS=MATCH_LABELS, PRIORITY_LABELS=PRIORITY_LABELS,
                                 ALERT_STATUSES=ALERT_STATUSES, FIXTURE_ADAPTER=FIXTURE_ADAPTER)

    @app.context_processor
    def presentation_flag():
        return {"presentation": bool(current_app.config.get("PRESENTATION_MODE"))}

    # Presentation mode rewrites demo wording stored in the data (seed titles, labels, audit text) at display
    # time only; the database keeps the original labels.
    def finalize(value):
        if isinstance(value, str) and current_app.config.get("PRESENTATION_MODE"):
            for old, new in PRESENTATION_SCRUB:
                if old in value:
                    value = value.replace(old, new)
        return value

    app.jinja_env.finalize = finalize

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def error_page(err):
        return render_template("error.html", error=err), err.code


def commit():
    get_db().commit()


def org_alert_or_404(alert_id):
    row = get_db().execute("SELECT * FROM alerts WHERE id=? AND org_id=?", (alert_id, g.org["id"])).fetchone()
    if row is None:
        abort(404)
    return row


# ---------------------------------------------------------------- auth / org
@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (request.form.get("username", "").strip().lower(),)
                          ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], request.form.get("password", "")):
            error = "Invalid username or password."
        else:
            session.clear()
            session["user_id"] = user["id"]
            orgs = db.execute("SELECT org_id FROM memberships WHERE user_id=? AND status='active'",
                              (user["id"],)).fetchall()
            if len(orgs) == 1:
                session["org_id"] = orgs[0]["org_id"]
            audit(db, org_id=orgs[0]["org_id"] if len(orgs) == 1 else None, actor_id=user["id"],
                  actor_label=user["display_name"], action="session.login", target_type="user",
                  target_id=user["id"], summary="Signed in (demo authentication)")
            commit()
            return redirect(url_for("main.dashboard"))
    accounts = get_db().execute("SELECT username, display_name, title FROM users WHERE is_demo=1 ORDER BY id").fetchall()
    return render_template("login.html", error=error, accounts=accounts)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@bp.route("/orgs")
@login_required
def choose_org():
    orgs = get_db().execute(
        "SELECT o.id, o.name, o.industry, m.role FROM organizations o JOIN memberships m ON m.org_id=o.id"
        " WHERE m.user_id=? AND m.status='active' ORDER BY o.name", (g.user["id"],)).fetchall()
    return render_template("choose_org.html", orgs=orgs)


@bp.post("/orgs/select")
@login_required
def select_org():
    org_id = request.form.get("org_id", type=int)
    ok = get_db().execute("SELECT 1 FROM memberships WHERE org_id=? AND user_id=? AND status='active'",
                          (org_id, g.user["id"])).fetchone()
    if not ok:
        abort(404)
    session["org_id"] = org_id
    return redirect(url_for("main.dashboard"))


# ---------------------------------------------------------------- dashboard
def source_health(db, org_id, now):
    rows = db.execute(
        "SELECT c.*, os.enabled, os.simulate_failure FROM source_catalog c JOIN org_sources os ON os.source_id=c.id"
        " WHERE os.org_id=? ORDER BY c.id", (org_id,)).fetchall()
    out = []
    scope = "(org_id IS NULL OR org_id=?)"  # shared runs plus this org's own simulated outages
    for s in rows:
        last = db.execute(f"SELECT * FROM collection_runs WHERE source_id=? AND {scope} AND outcome!='skipped'"
                          " ORDER BY id DESC LIMIT 1", (s["id"], org_id)).fetchone()
        last_ok = db.execute(f"SELECT finished_at FROM collection_runs WHERE source_id=? AND {scope} AND outcome IN"
                             " ('success','success_no_new') ORDER BY id DESC LIMIT 1", (s["id"], org_id)).fetchone()
        if not s["enabled"]:
            state = "Disabled"
        elif last is None:
            state = "Never checked"
        elif last["outcome"] == "failed":
            state = "Failed"
        elif now - datetime.fromisoformat(last["finished_at"]) > STALE_AFTER:
            state = "Stale"
        else:
            state = "Healthy"
        out.append({"source": s, "last": last, "last_ok": last_ok["finished_at"] if last_ok else None, "state": state})
    return out


def alert_rows(db, org_id, where="", params=()):
    return db.execute(
        "SELECT a.*, f.title, r.score, r.match_state, COALESCE(r.override_priority, r.priority) AS priority,"
        " u.display_name AS assignee FROM alerts a JOIN findings f ON f.id=a.finding_id"
        " JOIN relevance r ON r.org_id=a.org_id AND r.finding_id=a.finding_id"
        " LEFT JOIN users u ON u.id=a.assignee_id WHERE a.org_id=? " + where + " ORDER BY a.created_at DESC, a.id DESC",
        (org_id,) + tuple(params)).fetchall()


@bp.route("/")
@org_required
def dashboard():
    db = get_db()
    oid = g.org["id"]
    alerts = alert_rows(db, oid)
    plans = db.execute("SELECT * FROM plans WHERE org_id=? AND status!='archived' ORDER BY id DESC", (oid,)).fetchall()
    waiting_guides = db.execute(
        "SELECT g.id, f.title FROM guides g JOIN guide_questions q ON q.guide_id=g.id"
        " JOIN alerts a ON a.id=g.alert_id JOIN findings f ON f.id=a.finding_id"
        " WHERE g.org_id=? AND q.answer IS NULL", (oid,)).fetchall()
    in_review = [p for p in plans if p["status"] == "in_review"]
    alert_action = sum(1 for a in alerts if (a["status"] == "new" and a["unread"]) or
                       (a["assignee_id"] and a["status"] in ("under_investigation", "mitigation_in_progress")))
    counts = {
        "new-alerts": sum(1 for a in alerts if a["status"] == "new"),
        "requires-action": alert_action + len(waiting_guides) + len(in_review),
        "high-priority": sum(1 for a in alerts if a["priority"] in ("P1", "P2") and a["status"] not in CLOSED),
        "open-alerts": sum(1 for a in alerts if a["status"] not in CLOSED),
        "open-plans": len(plans),
    }
    events = db.execute("SELECT * FROM audit_events WHERE org_id=? ORDER BY id DESC LIMIT 8", (oid,)).fetchall()
    health = source_health(db, oid, datetime.fromisoformat(now_iso()))
    return render_template("dashboard.html", alerts=alerts[:6], counts=counts, events=events, health=health,
                           plans=plans, in_review=in_review, waiting_guides=waiting_guides)


# ---------------------------------------------------------------- organization
@bp.route("/organization")
@org_required
def organization():
    db = get_db()
    oid = g.org["id"]
    inventory = db.execute("SELECT * FROM inventory_items WHERE org_id=? ORDER BY id", (oid,)).fetchall()
    members = db.execute("SELECT u.id, u.display_name, u.title, m.role, m.status FROM memberships m"
                         " JOIN users u ON u.id=m.user_id WHERE m.org_id=? ORDER BY m.role, u.id", (oid,)).fetchall()
    assessments = db.execute(
        "SELECT s.*, u.display_name AS respondent FROM assessments s LEFT JOIN users u ON u.id=s.respondent_id"
        " WHERE s.org_id=? ORDER BY s.id DESC", (oid,)).fetchall()
    answers = {s["id"]: db.execute("SELECT a.answer, q.text, q.framework_ref, q.framework_url FROM answers a"
                                   " JOIN questions q ON q.key=a.question_key WHERE a.assessment_id=?",
                                   (s["id"],)).fetchall() for s in assessments}
    return render_template("organization.html", inventory=inventory, members=members, assessments=assessments,
                           answers=answers)


@bp.post("/members/<int:user_id>/revoke")
@role_required("admin")
def revoke_member(user_id):
    db = get_db()
    m = db.execute("SELECT * FROM memberships WHERE org_id=? AND user_id=?", (g.org["id"], user_id)).fetchone()
    if m is None:
        abort(404)
    if user_id == g.user["id"]:
        abort(400, description="You cannot revoke your own access.")
    db.execute("UPDATE memberships SET status='revoked' WHERE id=?", (m["id"],))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="membership.revoked",
          target_type="membership", target_id=m["id"], summary="Revoked member access",
          before={"status": m["status"]}, after={"status": "revoked"})
    commit()
    flash("Access revoked. The member can no longer open this organization's records.")
    return redirect(url_for("main.organization"))


# ---------------------------------------------------------------- sources
def followup_ready(db, org_id):
    """The follow-up demo step only makes sense once the finding it follows up on is visible to this org."""
    techniques = {detect_technique(i["title"], i.get("excerpt", "")) for i in FOLLOWUP_ITEMS} - {None}
    return bool(techniques) and db.execute(
        "SELECT 1 FROM relevance r JOIN findings f ON f.id = r.finding_id WHERE r.org_id = ? AND f.technique IN (%s)"
        % ",".join("?" * len(techniques)), (org_id, *techniques)).fetchone() is not None


@bp.route("/sources")
@org_required
def sources():
    db = get_db()
    health = source_health(db, g.org["id"], datetime.fromisoformat(now_iso()))
    runs = db.execute("SELECT r.*, c.name FROM collection_runs r JOIN source_catalog c ON c.id=r.source_id"
                      " JOIN org_sources os ON os.source_id=c.id AND os.org_id=?"
                      " WHERE r.org_id IS NULL OR r.org_id=?"
                      " ORDER BY r.id DESC LIMIT 12", (g.org["id"], g.org["id"])).fetchall()
    items = db.execute("SELECT si.*, r.adapter FROM source_items si LEFT JOIN collection_runs r ON r.id=si.collection_run_id"
                       " WHERE si.source_id IS NULL OR si.source_id IN"
                       " (SELECT source_id FROM org_sources WHERE org_id=? AND enabled=1)"
                       " ORDER BY si.id DESC LIMIT 15", (g.org["id"],)).fetchall()
    return render_template("sources.html", health=health, runs=runs, items=items,
                           live_on=current_app.config.get("LIVE_SOURCES"), live_feeds=LIVE_FEEDS,
                           followup_done=db.execute("SELECT 1 FROM source_items WHERE source_id IS NULL").fetchone(),
                           followup_ready=followup_ready(db, g.org["id"]))


@bp.post("/sources/<int:source_id>/toggle")
@role_required("admin")
def toggle_source(source_id):
    db = get_db()
    row = db.execute("SELECT os.enabled, c.name FROM org_sources os JOIN source_catalog c ON c.id=os.source_id"
                     " WHERE os.org_id=? AND os.source_id=?", (g.org["id"], source_id)).fetchone()
    if row is None:
        abort(404)
    new = 0 if row["enabled"] else 1
    db.execute("UPDATE org_sources SET enabled=? WHERE org_id=? AND source_id=?", (new, g.org["id"], source_id))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="source.toggled",
          target_type="source", target_id=source_id, summary=f"{row['name']} {'enabled' if new else 'disabled'}",
          before={"enabled": bool(row["enabled"])}, after={"enabled": bool(new)})
    if new:
        assess_org(db, g.org["id"], actor_label())
    commit()
    return redirect(url_for("main.sources"))


@bp.post("/sources/<int:source_id>/simulate-failure")
@role_required("admin")
def simulate_failure(source_id):
    db = get_db()
    src = db.execute("SELECT c.name, os.simulate_failure FROM org_sources os JOIN source_catalog c ON c.id=os.source_id"
                     " WHERE os.org_id=? AND os.source_id=?", (g.org["id"], source_id)).fetchone()
    if src is None:
        abort(404)
    new = 0 if src["simulate_failure"] else 1
    db.execute("UPDATE org_sources SET simulate_failure=? WHERE org_id=? AND source_id=?",
               (new, g.org["id"], source_id))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="source.simulation",
          target_type="source", target_id=source_id,
          summary=f"Demo simulation for this organization only: {src['name']} outage {'on' if new else 'off'}")
    commit()
    return redirect(url_for("main.sources"))


@bp.post("/sources/refresh")
@role_required("admin")
def refresh_sources():
    db = get_db()
    touched = run_collection(db, trigger="manual", actor_label=actor_label())
    process_findings(db, touched)
    assess_backlog(db, actor_label())
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="collection.manual_refresh",
          target_type="collection", target_id=None, summary=f"Manual refresh; {len(touched)} finding(s) new or updated")
    commit()
    flash(f"Refresh complete: {len(touched)} finding(s) new or updated. See per-source outcomes below.")
    return redirect(url_for("main.sources"))


# ---------------------------------------------------------------- alerts
@bp.route("/alerts")
@org_required
def alerts():
    clauses, params = [], []
    f = request.args
    if f.get("priority"):
        clauses.append("AND COALESCE(r.override_priority, r.priority)=?")
        params.append(f["priority"])
    if f.get("status"):
        clauses.append("AND a.status=?")
        params.append(f["status"])
    if f.get("category"):
        clauses.append("AND a.category=?")
        params.append(f["category"])
    if f.get("since"):
        clauses.append("AND a.created_at>=?")
        params.append(f["since"])
    if f.get("unread"):
        clauses.append("AND a.unread=1")
    rows = alert_rows(get_db(), g.org["id"], " ".join(clauses), params)
    return render_template("alerts.html", alerts=rows, filters=f)


@bp.route("/alerts/<int:alert_id>")
@org_required
def alert_detail(alert_id):
    db = get_db()
    alert = org_alert_or_404(alert_id)
    if alert["unread"]:
        db.execute("UPDATE alerts SET unread=0 WHERE id=?", (alert_id,))
        commit()
    finding = db.execute("SELECT * FROM findings WHERE id=?", (alert["finding_id"],)).fetchone()
    items = db.execute("SELECT * FROM source_items WHERE finding_id=? ORDER BY id", (finding["id"],)).fetchall()
    rel = db.execute("SELECT * FROM relevance WHERE org_id=? AND finding_id=?", (g.org["id"], finding["id"])).fetchone()
    analysis_row = db.execute("SELECT * FROM analyses WHERE org_id=? AND finding_id=? ORDER BY id DESC LIMIT 1",
                              (g.org["id"], finding["id"])).fetchone()
    corrections = corrections_for(db, g.org["id"], finding["id"])
    analysis = apply_corrections(json.loads(analysis_row["payload"]), corrections) if analysis_row else None
    members = db.execute("SELECT u.id, u.display_name, m.role FROM memberships m JOIN users u ON u.id=m.user_id"
                         " WHERE m.org_id=? AND m.status='active' ORDER BY u.id", (g.org["id"],)).fetchall()
    revisions = db.execute("SELECT * FROM finding_revisions WHERE finding_id=? ORDER BY version DESC",
                           (finding["id"],)).fetchall()
    history = db.execute("SELECT * FROM audit_events WHERE org_id=? AND target_type='alert' AND target_id=?"
                         " ORDER BY id DESC", (g.org["id"], alert_id)).fetchall()
    cite = {i["id"]: n for n, i in enumerate(items, start=1)}
    notes = db.execute("SELECT n.*, u.display_name FROM notifications n LEFT JOIN users u ON u.id=n.user_id"
                       " WHERE n.alert_id=? AND n.org_id=? ORDER BY n.id DESC", (alert_id, g.org["id"])).fetchall()
    overrider = db.execute("SELECT display_name FROM users WHERE id=?", (rel["override_by"],)).fetchone() \
        if rel["override_by"] else None
    guide = db.execute("SELECT id FROM guides WHERE alert_id=?", (alert_id,)).fetchone()
    plan = db.execute("SELECT id, title FROM plans WHERE alert_id=? AND org_id=? ORDER BY id DESC LIMIT 1",
                      (alert_id, g.org["id"])).fetchone()
    return render_template("alert.html", alert=alert, finding=finding, items=items, rel=rel, analysis=analysis,
                           notes=notes, overrider=overrider, guide=guide, plan=plan, corrections=corrections,
                           analysis_row=analysis_row, members=members, revisions=revisions, history=history,
                           cite=cite, next_states=ALERT_TRANSITIONS.get(alert["status"], []),
                           note_required=NOTE_REQUIRED)


@bp.post("/alerts/<int:alert_id>/assign")
@role_required("admin", "lead")
def assign_alert(alert_id):
    db = get_db()
    alert = org_alert_or_404(alert_id)
    assignee = request.form.get("assignee_id", type=int)
    member = db.execute("SELECT u.display_name FROM memberships m JOIN users u ON u.id=m.user_id"
                        " WHERE m.org_id=? AND m.user_id=? AND m.status='active'", (g.org["id"], assignee)).fetchone()
    if member is None:
        abort(400, description="Assignee must be an active member of this organization.")
    db.execute("UPDATE alerts SET assignee_id=?, updated_at=? WHERE id=?", (assignee, now_iso(), alert_id))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="alert.assigned",
          target_type="alert", target_id=alert_id, summary=f"Assigned to {member['display_name']}",
          before={"assignee_id": alert["assignee_id"]}, after={"assignee_id": assignee})
    commit()
    return redirect(url_for("main.alert_detail", alert_id=alert_id))


@bp.post("/alerts/<int:alert_id>/status")
@role_required("admin", "lead")
def change_status(alert_id):
    db = get_db()
    alert = org_alert_or_404(alert_id)
    new, note = request.form.get("status", ""), request.form.get("note", "").strip()
    try:
        check_transition(alert["status"], new, note)
    except TransitionError as exc:
        abort(400, description=str(exc))
    db.execute("UPDATE alerts SET status=?, has_update=0, updated_at=? WHERE id=?", (new, now_iso(), alert_id))
    summary = f"{ALERT_STATUSES[alert['status']]} → {ALERT_STATUSES[new]}" + (f". Note: {note}" if note else "")
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="alert.status_changed",
          target_type="alert", target_id=alert_id, summary=summary,
          before={"status": alert["status"]}, after={"status": new})
    commit()
    return redirect(url_for("main.alert_detail", alert_id=alert_id))


@bp.post("/alerts/<int:alert_id>/grouping/<int:item_id>/<action>")
@role_required("admin", "lead")
def grouping(alert_id, item_id, action):
    db = get_db()
    alert = org_alert_or_404(alert_id)
    item = db.execute("SELECT * FROM source_items WHERE id=? AND finding_id=? AND group_status IN ('proposed','confirmed')",
                      (item_id, alert["finding_id"])).fetchone()
    if item is None or action not in ("confirm", "undo"):
        abort(404)
    if action == "confirm":
        db.execute("UPDATE source_items SET group_status='confirmed', group_basis=? WHERE id=?",
                   (f"{item['group_basis']} — confirmed by {g.user['display_name']}", item_id))
        bump_revision(db, alert["finding_id"], f"Grouping of {item['source_label']} confirmed", actor_label())
        touched = {alert["finding_id"]}
    else:
        ts = now_iso()
        new_fid = db.execute(
            "INSERT INTO findings (title, technique, event_type, affected_products, technique_tags, industries,"
            " identifiers, first_seen_at, updated_at)"
            " SELECT ?, technique, event_type, affected_products, technique_tags, industries, ?, ?, ?"
            " FROM findings WHERE id=?", (item["title"], item["identifiers"], ts, ts, alert["finding_id"])).lastrowid
        db.execute("UPDATE source_items SET finding_id=?, group_status='primary', group_basis=? WHERE id=?",
                   (new_fid, f"Split from finding #{alert['finding_id']} by {g.user['display_name']}", item_id))
        snapshot_revision(db, new_fid, 1, "Finding created by undoing a proposed grouping", actor_label())
        bump_revision(db, alert["finding_id"], f"Grouping of {item['source_label']} undone", actor_label())
        touched = {alert["finding_id"], new_fid}
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(),
          action=f"grouping.{'confirmed' if action == 'confirm' else 'undone'}", target_type="alert",
          target_id=alert_id, summary=f"{item['source_label']} grouping {'confirmed' if action == 'confirm' else 'undone'}")
    process_findings(db, touched, actor_label())
    commit()
    return redirect(url_for("main.alert_detail", alert_id=alert_id))


@bp.post("/alerts/<int:alert_id>/override")
@role_required("admin", "lead")
def override_relevance(alert_id):
    """Reviewer override for this finding only; scoring rules and other findings are untouched."""
    db = get_db()
    alert = org_alert_or_404(alert_id)
    priority = request.form.get("priority") or None
    match = request.form.get("match_state") or None
    reason = request.form.get("reason", "").strip()
    if not reason:
        abort(400, description="A reason is required to override priority or relevance.")
    if priority not in (None, "P1", "P2", "P3", "P4") or (match is not None and match not in MATCH_LABELS):
        abort(400, description="Unknown priority or match state.")
    rel = db.execute("SELECT * FROM relevance WHERE org_id=? AND finding_id=?",
                     (g.org["id"], alert["finding_id"])).fetchone()
    before = {"priority": rel["override_priority"] or rel["priority"],
              "match_state": rel["override_match_state"] or rel["match_state"]}
    db.execute("UPDATE relevance SET override_priority=?, override_match_state=?, override_reason=?, override_by=?,"
               " override_at=? WHERE id=?", (priority, match, reason, g.user["id"], now_iso(), rel["id"]))
    after = {"priority": priority or rel["priority"], "match_state": match or rel["match_state"]}
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="relevance.overridden",
          target_type="alert", target_id=alert_id, summary=f"Reviewer override. Reason: {reason}",
          before=before, after=after)
    change = (f"Reviewer override by {g.user['display_name']} ({before['priority']} -> {after['priority']}): "
              f"{reason}")
    enqueue_for_alert(db, alert_id, "update", change=change, actor_label=actor_label())
    commit()
    return redirect(url_for("main.alert_detail", alert_id=alert_id))


@bp.post("/sources/followup")
@role_required("admin")
def followup_evidence():
    """Demo step: a later report arrives and attaches to the existing finding (CAN-REQ-005 update)."""
    db = get_db()
    if not followup_ready(db, g.org["id"]):
        abort(400, description="Refresh sources first: the follow-up report adds evidence to the PHP2Shell "
                               "finding, which this organization hasn't collected yet.")
    touched = set()
    for raw in FOLLOWUP_ITEMS:
        fid = ingest_item(db, raw, None, None, source_label=raw.get("label", "Additional evidence (demo follow-up)"),
                          tier=raw.get("tier", "C"))
        if fid:
            touched.add(fid)
    process_findings(db, touched, actor_label())
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="evidence.followup",
          target_type="finding", target_id=next(iter(touched), None),
          summary="Demo step: follow-up report delivered" if touched else "Follow-up report was already attached")
    commit()
    flash("Follow-up report attached as additional evidence." if touched
          else "The follow-up report is already attached.")
    return redirect(url_for("main.sources"))


# ---------------------------------------------------------------- notifications
def _active_member(db, uid):
    return db.execute("SELECT 1 FROM memberships WHERE org_id=? AND user_id=? AND status='active'",
                      (g.org["id"], uid)).fetchone() is not None


def _outcomes(results):
    return ", ".join(f"{results.count(s)} {s}" for s in sorted(set(results))) or "nothing to send"


@bp.route("/notifications")
@org_required
def notifications():
    db = get_db()
    oid = g.org["id"]
    members = db.execute(
        "SELECT u.id, u.display_name, m.role, nr.email FROM memberships m JOIN users u ON u.id=m.user_id"
        " LEFT JOIN notification_recipients nr ON nr.org_id=m.org_id AND nr.user_id=m.user_id"
        " WHERE m.org_id=? AND m.status='active' ORDER BY u.id", (oid,)).fetchall()
    rules = db.execute("SELECT nr.*, u.display_name FROM notification_rules nr JOIN users u ON u.id=nr.user_id"
                       " WHERE nr.org_id=? ORDER BY nr.category, u.id", (oid,)).fetchall()
    log = db.execute("SELECT n.*, u.display_name FROM notifications n LEFT JOIN users u ON u.id=n.user_id"
                     " WHERE n.org_id=? ORDER BY n.id DESC LIMIT 50", (oid,)).fetchall()
    smtp_ok, smtp_msg = smtp_status()
    allow = allowlist_for(db, oid)
    added = db.execute("SELECT a.*, u.display_name FROM email_allowlist a LEFT JOIN users u ON u.id=a.added_by"
                       " WHERE a.org_id=? ORDER BY a.email", (oid,)).fetchall()
    return render_template("notifications.html", members=members, rules=rules, log=log, smtp_ok=smtp_ok,
                           smtp_msg=smtp_msg, allowlist=sorted(allow), allow=allow, check_recipient=check_recipient,
                           env_list=sorted(env_allowlist()), added=added, domains=sorted(permitted_domains()),
                           simulate=get_setting(db, oid, SIMULATE_KEY) == "1", SUBJECT_PREFIX=SUBJECT_PREFIX,
                           has_password=bool(current_app.config.get("SMTP_PASSWORD")))


@bp.post("/notifications/recipients")
@role_required("admin")
def set_recipient():
    db = get_db()
    uid = request.form.get("user_id", type=int)
    email = request.form.get("email", "").strip()
    if not _active_member(db, uid):
        abort(400, description="Recipient must be an active member of this organization.")
    if email:
        db.execute("INSERT INTO notification_recipients (org_id, user_id, email, updated_at) VALUES (?,?,?,?)"
                   " ON CONFLICT(org_id, user_id) DO UPDATE SET email=excluded.email, updated_at=excluded.updated_at",
                   (g.org["id"], uid, email, now_iso()))
    else:
        db.execute("DELETE FROM notification_recipients WHERE org_id=? AND user_id=?", (g.org["id"], uid))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(),
          action="notification.recipient_set", target_type="user", target_id=uid,
          summary="Test address " + ("set" if email else "removed"))
    commit()
    problem = check_recipient(email, allowlist_for(db, g.org["id"])) if email else None
    flash("Saved." + (f" Warning: {problem} Sends to this address will be rejected." if problem else ""))
    return redirect(url_for("main.notifications"))


@bp.post("/notifications/allowlist")
@role_required("admin")
def add_allowlist():
    """Option B: an Administrator adds a team-owned address for this organization (explicit, audited)."""
    db = get_db()
    email = (request.form.get("email") or "").strip().lower()
    domains = permitted_domains()
    if not domains:
        abort(400, description="In-app additions are off: no allowlist or permitted domains are configured in .env.")
    if request.form.get("confirm") != "yes":
        abort(400, description="Confirm that this address is owned by your team.")
    if not EMAIL_RE.match(email):
        abort(400, description="Enter a single, valid email address.")
    if email.rsplit("@", 1)[1] not in domains:
        abort(400, description="Only addresses on these domains can be added here: " + ", ".join(sorted(domains)) +
                               ". Other domains must be added to CANARY_EMAIL_ALLOWLIST or CANARY_ALLOWLIST_DOMAINS in .env.")
    if email in allowlist_for(db, g.org["id"]):
        abort(400, description="That address is already allowed.")
    entry = db.execute("INSERT INTO email_allowlist (org_id, email, added_by, added_at) VALUES (?,?,?,?)",
                       (g.org["id"], email, g.user["id"], now_iso())).lastrowid
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(),
          action="notification.allowlist_added", target_type="email_allowlist", target_id=entry,
          summary=f"Allowlisted {email} for this organization (confirmed team-owned)", after={"email": email})
    commit()
    flash(f"{email} can now receive test email for {g.org['name']}. Messages already Rejected stay Rejected; use Retry.")
    return redirect(url_for("main.notifications") + "#allowlist")


@bp.post("/notifications/allowlist/<int:entry_id>/delete")
@role_required("admin")
def remove_allowlist(entry_id):
    db = get_db()
    row = db.execute("SELECT * FROM email_allowlist WHERE id=? AND org_id=?", (entry_id, g.org["id"])).fetchone()
    if row is None:
        abort(404)
    db.execute("DELETE FROM email_allowlist WHERE id=?", (entry_id,))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(),
          action="notification.allowlist_removed", target_type="email_allowlist", target_id=entry_id,
          summary=f"Removed {row['email']} from this organization's allowlist", before={"email": row["email"]})
    commit()
    return redirect(url_for("main.notifications") + "#allowlist")


@bp.post("/notifications/rules")
@role_required("admin")
def add_rule():
    db = get_db()
    uid = request.form.get("user_id", type=int)
    category = request.form.get("category", "cybersecurity")
    if category != "cybersecurity" or not _active_member(db, uid):
        abort(400, description="Unknown category or member.")
    db.execute("INSERT OR IGNORE INTO notification_rules (org_id, category, user_id) VALUES (?,?,?)",
               (g.org["id"], category, uid))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="notification.rule_added",
          target_type="user", target_id=uid, summary=f"Route {category} alerts to member #{uid}")
    commit()
    return redirect(url_for("main.notifications"))


@bp.post("/notifications/rules/<int:rule_id>/delete")
@role_required("admin")
def delete_rule(rule_id):
    db = get_db()
    if not db.execute("DELETE FROM notification_rules WHERE id=? AND org_id=?", (rule_id, g.org["id"])).rowcount:
        abort(404)
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(),
          action="notification.rule_removed", target_type="notification_rule", target_id=rule_id,
          summary="Routing rule removed")
    commit()
    return redirect(url_for("main.notifications"))


@bp.post("/notifications/process")
@role_required("admin")
def process_notifications():
    db = get_db()
    results = process_queue(db, g.org["id"], actor_label())
    commit()
    flash(f"Processing cycle ran for {len(results)} queued P1/P2 message(s): {_outcomes(results)}.")
    return redirect(url_for("main.notifications"))


@bp.post("/notifications/digest")
@role_required("admin")
def run_digest():
    db = get_db()
    results = process_digest(db, g.org["id"], actor_label())
    commit()
    flash(f"Daily digest ran for {len(results)} recipient(s): {_outcomes(results)}.")
    return redirect(url_for("main.notifications"))


@bp.post("/notifications/simulate-failure")
@role_required("admin")
def toggle_delivery_failure():
    db = get_db()
    new = "0" if get_setting(db, g.org["id"], SIMULATE_KEY) == "1" else "1"
    set_setting(db, g.org["id"], SIMULATE_KEY, new)
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="notification.simulation",
          target_type="organization", target_id=g.org["id"],
          summary=f"Demo simulation: delivery failure {'on' if new == '1' else 'off'}")
    commit()
    return redirect(url_for("main.notifications"))


@bp.post("/notifications/<int:notif_id>/retry")
@role_required("admin")
def retry_notification(notif_id):
    db = get_db()
    n = db.execute("SELECT * FROM notifications WHERE id=? AND org_id=?", (notif_id, g.org["id"])).fetchone()
    if n is None:
        abort(404)
    if n["status"] not in ("failed", "blocked", "rejected"):
        abort(400, description="Only failed, blocked, or rejected messages can be retried.")
    if n["attempts"] >= 3:
        abort(400, description="Retry limit reached (3 attempts).")
    status = dispatch(db, notif_id, actor_label())
    commit()
    flash(f"Retry result: {status}.")
    return redirect(url_for("main.notifications"))


@bp.post("/notifications/test")
@role_required("admin")
def test_notification():
    db = get_db()
    status = send_test(db, g.org["id"], request.form.get("email", ""), actor_label())
    commit()
    flash(f"Delivery check: {status}.")
    return redirect(url_for("main.notifications"))


# ---------------------------------------------------------------- audit / demo
@bp.route("/audit")
@org_required
def audit_log():
    events = get_db().execute("SELECT * FROM audit_events WHERE org_id=? ORDER BY id DESC LIMIT 200",
                              (g.org["id"],)).fetchall()
    return render_template("audit.html", events=events)


@bp.post("/demo/reset")
@role_required("admin")
def demo_reset():
    reset_demo(get_db())
    session.clear()
    flash("Demo reset: all seeded and entered records were deleted and the seed state restored. Sign in again.")
    return redirect(url_for("main.login"))
