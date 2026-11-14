"""Slice 4 routes: analysis correction (CAN-REQ-006), profile/inventory editing (002),
registration, organization creation, simulated invites, role changes (001), privacy page (015)."""
import json
import re

from flask import abort, current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from .analysis import CORRECTABLE_SECTIONS, apply_corrections, corrections_for, section_texts
from .auth import actor_label, login_required, org_required, role_required
from .db import audit, get_db, now_iso
from .delivery import allowlist_for, env_allowlist, smtp_status
from .pipeline import assess_org
from .views import bp, commit, org_alert_or_404

CRITICALITIES = ("Low", "Medium", "High", "Critical", "Unknown")
VERSION_STATUSES = ("known", "unconfirmed")
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")
TAG_RE = re.compile(r"[^a-z0-9_]+")


def _required(value, label):
    value = (value or "").strip()
    if not value:
        abort(400, description=f"{label} is required.")
    return value


def _optional(value):
    value = (value or "").strip()
    return value or None


def _reassess_org(db, org_id, label):
    assess_org(db, org_id, label)


# ------------------------------------------------------------------ CAN-REQ-006 analysis correction
@bp.post("/alerts/<int:alert_id>/analysis/correct")
@role_required("admin", "lead")
def correct_analysis(alert_id):
    db = get_db()
    alert = org_alert_or_404(alert_id)
    f = request.form
    section = f.get("section", "")
    if section not in CORRECTABLE_SECTIONS:
        abort(400, description="That part of the analysis cannot be corrected here.")
    original, corrected = f.get("original", ""), _required(f.get("corrected"), "Corrected text")
    reason = _required(f.get("reason"), "A reason")
    row = db.execute("SELECT payload FROM analyses WHERE org_id=? AND finding_id=? ORDER BY id DESC LIMIT 1",
                     (g.org["id"], alert["finding_id"])).fetchone()
    current = apply_corrections(json.loads(row["payload"]), corrections_for(db, g.org["id"], alert["finding_id"]))
    raw_texts = section_texts(json.loads(row["payload"]), section)
    if original not in section_texts(current, section):
        abort(400, description="The text to correct is not in the current analysis.")
    # Store the correction against the generated text so it keeps applying after re-analysis.
    prior = original
    for c in corrections_for(db, g.org["id"], alert["finding_id"]):
        if c["section"] == section and c["new_value"] == original and c["prior_value"] in raw_texts:
            prior = c["prior_value"]
    db.execute("INSERT INTO analysis_corrections (org_id, finding_id, section, prior_value, new_value, reason,"
               " editor_id, created_at) VALUES (?,?,?,?,?,?,?,?)",
               (g.org["id"], alert["finding_id"], section, prior, corrected, reason, g.user["id"], now_iso()))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="analysis.corrected",
          target_type="alert", target_id=alert_id,
          summary=f"Corrected {CORRECTABLE_SECTIONS[section]}. Reason: {reason}",
          before={"section": section, "text": original}, after={"section": section, "text": corrected})
    commit()
    return redirect(url_for("main.alert_detail", alert_id=alert_id) + "#analysis")


# ------------------------------------------------------------------ CAN-REQ-002 profile + inventory
@bp.post("/organization/profile")
@role_required("admin")
def edit_profile():
    db = get_db()
    f = request.form
    before = {k: g.org[k] for k in ("name", "industry", "size", "location", "monitoring_interests")}
    after = {"name": _required(f.get("name"), "Organization name"), "industry": _required(f.get("industry"), "Industry"),
             "size": _optional(f.get("size")), "location": _optional(f.get("location")),
             "monitoring_interests": _optional(f.get("monitoring_interests"))}
    db.execute("UPDATE organizations SET name=?, industry=?, size=?, location=?, monitoring_interests=?, updated_at=?"
               " WHERE id=?", (*after.values(), now_iso(), g.org["id"]))
    changed = {k: v for k, v in before.items() if v != after[k]}
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(),
          action="organization.profile_updated", target_type="organization", target_id=g.org["id"],
          summary="Profile updated: " + (", ".join(changed) or "no changes"),
          before=changed, after={k: after[k] for k in changed})
    if "industry" in changed:
        _reassess_org(db, g.org["id"], actor_label())
    commit()
    return redirect(url_for("main.organization"))


def _inventory_values(f):
    version = _optional(f.get("version"))
    criticality = f.get("criticality") or "Unknown"
    status = f.get("version_status") or "known"
    if criticality not in CRITICALITIES or (version and status not in VERSION_STATUSES):
        abort(400, description="Unknown criticality or version status.")
    tags = sorted({TAG_RE.sub("_", t.strip().lower()).strip("_") for t in (f.get("capabilities") or "").split(",")} - {""})
    return {"name": _required(f.get("name"), "Item name"), "category": _optional(f.get("category")),
            "product_key": _optional(f.get("product_key")), "version": version,
            "version_status": status if version else "unknown", "owner_team": _optional(f.get("owner_team")),
            "criticality": criticality, "capabilities": json.dumps(tags),
            "capability_notes": _optional(f.get("capability_notes")),
            "data_access_notes": _optional(f.get("data_access_notes"))}


def _inventory_item_or_404(db, item_id):
    row = db.execute("SELECT * FROM inventory_items WHERE id=? AND org_id=?", (item_id, g.org["id"])).fetchone()
    if row is None:
        abort(404)
    return row


def _touch_org(db):
    db.execute("UPDATE organizations SET updated_at=? WHERE id=?", (now_iso(), g.org["id"]))


@bp.post("/organization/inventory")
@role_required("admin", "lead")
def add_inventory():
    db = get_db()
    v = _inventory_values(request.form)
    iid = db.execute("INSERT INTO inventory_items (org_id, name, category, product_key, version, version_status,"
                     " owner_team, criticality, capabilities, capability_notes, data_access_notes, updated_at)"
                     " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (g.org["id"], *v.values(), now_iso())).lastrowid
    _touch_org(db)
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="inventory.created",
          target_type="inventory_item", target_id=iid, summary=f"Inventory item added: {v['name']}",
          after={k: v[k] for k in ("name", "version", "criticality")})
    _reassess_org(db, g.org["id"], actor_label())
    commit()
    return redirect(url_for("main.organization") + "#inventory")


@bp.post("/organization/inventory/<int:item_id>")
@role_required("admin", "lead")
def edit_inventory(item_id):
    db = get_db()
    item = _inventory_item_or_404(db, item_id)
    v = _inventory_values(request.form)
    db.execute("UPDATE inventory_items SET name=?, category=?, product_key=?, version=?, version_status=?, owner_team=?,"
               " criticality=?, capabilities=?, capability_notes=?, data_access_notes=?, updated_at=? WHERE id=?",
               (*v.values(), now_iso(), item_id))
    _touch_org(db)
    changed = [k for k in v if (item[k] or None) != (v[k] or None)]
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="inventory.updated",
          target_type="inventory_item", target_id=item_id,
          summary=f"Inventory item updated: {v['name']} ({', '.join(changed) or 'no changes'})",
          before={k: item[k] for k in changed}, after={k: v[k] for k in changed})
    _reassess_org(db, g.org["id"], actor_label())
    commit()
    return redirect(url_for("main.organization") + "#inventory")


@bp.post("/organization/inventory/<int:item_id>/delete")
@role_required("admin", "lead")
def delete_inventory(item_id):
    db = get_db()
    item = _inventory_item_or_404(db, item_id)
    db.execute("DELETE FROM inventory_items WHERE id=?", (item_id,))
    _touch_org(db)
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="inventory.deleted",
          target_type="inventory_item", target_id=item_id, summary=f"Inventory item removed: {item['name']}",
          before={"name": item["name"], "version": item["version"], "criticality": item["criticality"]})
    _reassess_org(db, g.org["id"], actor_label())
    commit()
    return redirect(url_for("main.organization") + "#inventory")


# ------------------------------------------------------------------ CAN-REQ-001 accounts and membership
@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = get_db()
        username = (request.form.get("username") or "").strip().lower()
        name = _required(request.form.get("display_name"), "Display name")
        password = request.form.get("password") or ""
        if not USERNAME_RE.match(username) or len(password) < 8:
            abort(400, description="Username must be 3-20 lowercase letters, digits, or _; password at least 8 characters.")
        if db.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
            abort(400, description="That username is unavailable.")
        user_id = db.execute("INSERT INTO users (username, display_name, title, password_hash, is_demo)"
                             " VALUES (?,?,?,?,0)", (username, name, "Registered local demo user",
                                                     generate_password_hash(password))).lastrowid
        audit(db, org_id=None, actor_id=user_id, actor_label=name, action="user.registered", target_type="user",
              target_id=user_id, summary="Registered a local demo account")
        commit()
        session.clear()
        session["user_id"] = user_id
        return redirect(url_for("main.choose_org"))
    return render_template("register.html")


@bp.post("/orgs/create")
@login_required
def create_org():
    db = get_db()
    name = _required(request.form.get("name"), "Organization name")
    industry = _required(request.form.get("industry"), "Industry")
    ts = now_iso()
    oid = db.execute("INSERT INTO organizations (name, industry, is_demo, created_at, updated_at) VALUES (?,?,0,?,?)",
                     (name, industry, ts, ts)).lastrowid
    db.execute("INSERT INTO memberships (org_id, user_id, role, created_at) VALUES (?,?,'admin',?)",
               (oid, g.user["id"], ts))
    db.execute("INSERT INTO org_sources (org_id, source_id, enabled) SELECT ?, id, 1 FROM source_catalog", (oid,))
    db.execute("INSERT INTO notification_rules (org_id, category, user_id) VALUES (?, 'cybersecurity', ?)",
               (oid, g.user["id"]))
    audit(db, org_id=oid, actor_id=g.user["id"], actor_label=f"{g.user['display_name']} (Administrator)",
          action="organization.created", target_type="organization", target_id=oid,
          summary=f"Created organization {name}; creator is its first Administrator")
    assess_org(db, oid, f"{g.user['display_name']} (Administrator)")
    commit()
    session["org_id"] = oid
    flash(f"{name} created. Add your AI inventory on the Organization page, then refresh sources.")
    return redirect(url_for("main.dashboard"))


def _member_or_404(db, user_id):
    row = db.execute("SELECT m.*, u.display_name FROM memberships m JOIN users u ON u.id=m.user_id"
                     " WHERE m.org_id=? AND m.user_id=?", (g.org["id"], user_id)).fetchone()
    if row is None:
        abort(404)
    return row


@bp.post("/members/invite")
@role_required("admin")
def invite_member():
    db = get_db()
    role = request.form.get("role", "")
    user = db.execute("SELECT id, display_name FROM users WHERE username=?",
                      ((request.form.get("username") or "").strip().lower(),)).fetchone()
    if role not in ("admin", "lead") or user is None:
        abort(400, description="Choose an existing local account and a role.")
    existing = db.execute("SELECT * FROM memberships WHERE org_id=? AND user_id=?", (g.org["id"], user["id"])).fetchone()
    if existing and existing["status"] == "active":
        abort(400, description="That person is already an active member.")
    if existing:
        db.execute("UPDATE memberships SET status='active', role=? WHERE id=?", (role, existing["id"]))
    else:
        db.execute("INSERT INTO memberships (org_id, user_id, role, created_at) VALUES (?,?,?,?)",
                   (g.org["id"], user["id"], role, now_iso()))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="membership.invited",
          target_type="user", target_id=user["id"],
          summary=f"Simulated invite: {user['display_name']} added as {role} (no email sent)",
          before={"status": existing["status"]} if existing else None, after={"status": "active", "role": role})
    commit()
    flash(f"{user['display_name']} now has access (simulated invite; no email was sent).")
    return redirect(url_for("main.organization") + "#members")


@bp.post("/members/<int:user_id>/role")
@role_required("admin")
def change_role(user_id):
    db = get_db()
    member = _member_or_404(db, user_id)
    role = request.form.get("role", "")
    if role not in ("admin", "lead"):
        abort(400, description="Unknown role.")
    admins = db.execute("SELECT COUNT(*) FROM memberships WHERE org_id=? AND role='admin' AND status='active'",
                        (g.org["id"],)).fetchone()[0]
    if member["role"] == "admin" and role != "admin" and admins <= 1:
        abort(400, description="An organization needs at least one active Administrator.")
    db.execute("UPDATE memberships SET role=? WHERE id=?", (role, member["id"]))
    audit(db, org_id=g.org["id"], actor_id=g.user["id"], actor_label=actor_label(), action="membership.role_changed",
          target_type="user", target_id=user_id, summary=f"{member['display_name']}: {member['role']} → {role}",
          before={"role": member["role"]}, after={"role": role})
    commit()
    return redirect(url_for("main.organization") + "#members")


# ------------------------------------------------------------------ CAN-REQ-015 privacy / data flows
@bp.route("/privacy")
@login_required
def privacy():
    smtp_ok, smtp_msg = smtp_status()
    return render_template("privacy.html", smtp_ok=smtp_ok, smtp_msg=smtp_msg,
                           live_on=current_app.config.get("LIVE_SOURCES"),
                           allowlist_size=len(allowlist_for(get_db(), g.org["id"]) if g.org else env_allowlist()))


@bp.app_context_processor
def _org_page_helpers():
    return {"CRITICALITIES": CRITICALITIES, "CORRECTABLE_SECTIONS": CORRECTABLE_SECTIONS}
