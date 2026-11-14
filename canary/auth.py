"""Demo authentication, organization selection, and server-side role checks — CAN-REQ-001/015.

Every org-scoped view runs through org_required, which re-checks ACTIVE
membership on each request (so revocation takes effect immediately) and
exposes g.org / g.role. Records outside the selected org return 404 so
failures do not disclose that another organization's record exists.
"""
from functools import wraps

from flask import abort, g, redirect, session, url_for

from .db import get_db

ROLE_LABELS = {"admin": "Administrator", "lead": "Cybersecurity Lead"}


def load_user():
    g.user, g.org, g.role = None, None, None
    uid = session.get("user_id")
    if uid is None:
        return
    db = get_db()
    g.user = db.execute("SELECT id, username, display_name, title FROM users WHERE id=?", (uid,)).fetchone()
    if g.user is None:
        session.clear()
        return
    org_id = session.get("org_id")
    if org_id is not None:
        row = db.execute(
            "SELECT o.*, m.role FROM organizations o JOIN memberships m ON m.org_id = o.id"
            " WHERE o.id=? AND m.user_id=? AND m.status='active'", (org_id, uid)).fetchone()
        if row is None:
            session.pop("org_id", None)
        else:
            g.org, g.role = row, row["role"]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)
    return wrapped


def org_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("main.login"))
        if g.org is None:
            return redirect(url_for("main.choose_org"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.role not in roles:
                abort(403, description="Your role does not allow this action.")
            return view(*args, **kwargs)
        return org_required(wrapped)
    return decorator


def actor_label():
    return f"{g.user['display_name']} ({ROLE_LABELS.get(g.role, 'no role')})"
