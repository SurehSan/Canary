"""Contingency plan templates, lifecycle, and versions — CAN-REQ-012.

Draft -> In review -> Approved -> Archived. Only an Administrator approves, with
explicit confirmation. Editing an approved plan returns it to Draft; the
approved version stays preserved in plan_versions. Approval records human
review only; Canary never executes plan actions.
"""
import json

from .db import now_iso

PLAN_STATUSES = {"draft": "Draft", "in_review": "In review", "approved": "Approved", "archived": "Archived"}
STAGES = ["Preparation", "Detection", "Containment", "Recovery", "Review"]
ACTION_STATUSES = {"open": "Open", "in_progress": "In progress", "done": "Done"}

TEMPLATES = {
    "php2shell": {
        "title": "Critical PHP remote code execution (PHP2Shell)",
        "actions": [
            ("Detection", "Confirm the PHP version on every internet-facing service and review web and PHP-FPM logs "
                          "since October 21 for unusual requests or crashes.", "author"),
            ("Containment", "Upgrade the billing portal to PHP 8.3.36 or later and restart every PHP-FPM worker.",
             "author"),
            ("Containment", "Until the upgrade is verified, set session.upload_progress.enabled = 0 in the PHP-FPM pool "
                            "configuration and confirm the portal's internet exposure.", "second_lead"),
            ("Recovery", "If indicators of compromise are found, rebuild the host from a clean image and rotate the "
                         "secrets the portal can read.", "author"),
            ("Review", "Adopt a 72-hour patch target for critical advisories on internet-facing systems "
                       "(CIS Controls v8, Safeguard 7.4).", "author"),
        ],
    },
}


def template_actions(technique, guide_steps):
    tpl = TEMPLATES.get(technique)
    if tpl:
        return tpl["title"], tpl["actions"]
    actions = [("Detection" if s["position"] == 1 else "Containment", s["action"], "author") for s in guide_steps]
    return None, actions


def snapshot(conn, plan_id):
    p = conn.execute("SELECT title, status, version, review_date FROM plans WHERE id=?", (plan_id,)).fetchone()
    actions = conn.execute(
        "SELECT a.stage, a.action, a.status, a.due_date, u.display_name AS owner FROM plan_actions a"
        " LEFT JOIN users u ON u.id=a.owner_id WHERE a.plan_id=? ORDER BY a.position", (plan_id,)).fetchall()
    return {**dict(p), "actions": [dict(a) for a in actions]}


def record_version(conn, plan_id, actor_id, actor_label, note=None):
    snap = snapshot(conn, plan_id)
    conn.execute("INSERT INTO plan_versions (plan_id, version, status, snapshot, actor_id, actor_label, note, created_at)"
                 " VALUES (?,?,?,?,?,?,?,?)",
                 (plan_id, snap["version"], snap["status"], json.dumps(snap), actor_id, actor_label, note, now_iso()))
    return snap
