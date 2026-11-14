"""Notification queue and SMTP delivery — CAN-REQ-009.

Order for every attempt: allowlist (rejected) -> SMTP configured (blocked) ->
demo failure simulation (failed, simulated=1) -> real SMTP send (sent/failed).
Nothing is ever marked sent unless the SMTP server accepted the message.
"""
import json
import smtplib
import uuid
from email.message import EmailMessage

from flask import current_app

from .analysis import apply_corrections, corrections_for
from .db import audit, now_iso
from .notify import SUBJECT_PREFIX, TEST_NOTICE, build_digest, build_message, cadence_for, check_recipient, fingerprint

SIMULATE_KEY = "simulate_delivery_failure"


def get_setting(conn, org_id, key, default="0"):
    row = conn.execute("SELECT value FROM org_settings WHERE org_id=? AND key=?", (org_id, key)).fetchone()
    return row["value"] if row else default


def set_setting(conn, org_id, key, value):
    conn.execute("INSERT INTO org_settings (org_id, key, value) VALUES (?,?,?)"
                 " ON CONFLICT(org_id, key) DO UPDATE SET value=excluded.value", (org_id, key, value))


def smtp_status():
    cfg = current_app.config
    if not cfg.get("SMTP_HOST"):
        return False, "SMTP is not configured (CANARY_SMTP_HOST is missing)."
    if not cfg.get("MAIL_FROM"):
        return False, "SMTP is not configured (CANARY_MAIL_FROM is missing)."
    return True, f"SMTP configured: {cfg['SMTP_HOST']}:{cfg['SMTP_PORT']}"


def alert_context(conn, alert_id):
    a = conn.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()
    f = conn.execute("SELECT * FROM findings WHERE id=?", (a["finding_id"],)).fetchone()
    r = conn.execute("SELECT * FROM relevance WHERE org_id=? AND finding_id=?", (a["org_id"], f["id"])).fetchone()
    org = conn.execute("SELECT name FROM organizations WHERE id=?", (a["org_id"],)).fetchone()
    an_row = conn.execute("SELECT payload FROM analyses WHERE org_id=? AND finding_id=? ORDER BY id DESC LIMIT 1",
                          (a["org_id"], f["id"])).fetchone()
    analysis = {}
    if an_row:  # human corrections (CAN-REQ-006) also apply to email content
        analysis = apply_corrections(json.loads(an_row["payload"]), corrections_for(conn, a["org_id"], f["id"]))
    items = conn.execute("SELECT * FROM source_items WHERE finding_id=? ORDER BY id", (f["id"],)).fetchall()
    n_of = {i["id"]: n for n, i in enumerate(items, start=1)}
    priority = r["override_priority"] or r["priority"]
    match = r["override_match_state"] or r["match_state"]
    return {
        "org_id": a["org_id"], "category": a["category"], "org_name": org["name"], "title": f["title"],
        "priority": priority, "score": r["score"], "match_state": match,
        "what_happened": analysis.get("what_happened", []), "org_context": analysis.get("org_context", []),
        "known": [c["text"] + "".join(f" [{n_of.get(i, '?')}]" for i in c["citations"])
                  for c in analysis.get("source_supported", [])],
        "unknowns": analysis.get("unknowns", []),
        "sources": [{"n": n_of[i["id"]], "title": i["title"], "url": i["url"], "published_at": i["published_at"]}
                    for i in items],
        "link": f"{current_app.config['APP_BASE_URL']}/alerts/{alert_id}",
        "material": {"priority": priority, "match_state": match,
                     "exploitation_status": analysis.get("exploitation_status", "unknown"),
                     "affected_products": json.loads(f["affected_products"]),
                     "source_urls": [i["url"] for i in items]},
    }


def routed_users(conn, org_id, category):
    return [r["user_id"] for r in conn.execute(
        "SELECT nr.user_id FROM notification_rules nr JOIN memberships m ON m.org_id=nr.org_id AND m.user_id=nr.user_id"
        " WHERE nr.org_id=? AND nr.category=? AND m.status='active' ORDER BY nr.user_id", (org_id, category))]


def enqueue_for_alert(conn, alert_id, kind, change=None, actor_label="System notifier"):
    """Queue notifications for routed recipients; suppress unchanged repeats; send P1 immediately."""
    ctx = alert_context(conn, alert_id)
    fp = fingerprint(ctx["material"])
    cadence = cadence_for(ctx["priority"])
    ts = now_iso()
    queued = []
    for uid in routed_users(conn, ctx["org_id"], ctx["category"]):
        last = conn.execute("SELECT fingerprint FROM notifications WHERE alert_id=? AND user_id=? AND status!='suppressed'"
                            " ORDER BY id DESC LIMIT 1", (alert_id, uid)).fetchone()
        if last and last["fingerprint"] == fp:
            conn.execute("INSERT INTO notifications (org_id, alert_id, user_id, kind, cadence, priority, fingerprint,"
                         " change_summary, status, error, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         (ctx["org_id"], alert_id, uid, "update", cadence, ctx["priority"], fp, change, "suppressed",
                          "Unchanged since the last notification (no material change).", ts, ts))
            continue
        msg_kind = "update" if last else kind
        subject, body = build_message(dict(ctx, kind=msg_kind, change=change))
        queued.append(conn.execute(
            "INSERT INTO notifications (org_id, alert_id, user_id, kind, cadence, priority, fingerprint, change_summary,"
            " status, subject, body, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,'pending',?,?,?,?)",
            (ctx["org_id"], alert_id, uid, msg_kind, cadence, ctx["priority"], fp, change, subject, body, ts, ts)
        ).lastrowid)
    if cadence == "immediate":
        for nid in queued:
            dispatch(conn, nid, actor_label)
    return queued


def _send_smtp(to_addr, subject, body):
    cfg = current_app.config
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, cfg["MAIL_FROM"], to_addr
    msg["X-Canary-Mode"] = "demo-test"
    msg.set_content(body)
    smtp_cls = smtplib.SMTP_SSL if cfg.get("SMTP_SSL") else smtplib.SMTP
    with smtp_cls(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15) as smtp:
        if cfg.get("SMTP_STARTTLS") and not cfg.get("SMTP_SSL"):
            smtp.starttls()
        if cfg.get("SMTP_USERNAME"):
            smtp.login(cfg["SMTP_USERNAME"], cfg.get("SMTP_PASSWORD") or "")
        smtp.send_message(msg)


def safe_smtp_error(exc):
    """Record only the error type and numeric SMTP/OS code, never provider-controlled text (CDX-2)."""
    code = getattr(exc, "smtp_code", None)
    if code is None and isinstance(exc, smtplib.SMTPRecipientsRefused):
        codes = {c for c, _msg in exc.recipients.values()}
        code = ",".join(str(c) for c in sorted(codes)) or None
    if code is None:
        code = getattr(exc, "errno", None)
    return f"SMTP error: {type(exc).__name__}" + (f" (code {code})" if code is not None else "")


def _precheck(conn, org_id, email):
    reason = check_recipient(email, current_app.config.get("EMAIL_ALLOWLIST") or set())
    if reason:
        # A missing address is a configuration gap (blocked); any other address off the allowlist is rejected.
        return ("blocked" if not (email or "").strip() else "rejected"), reason, 0
    ok, why = smtp_status()
    if not ok:
        return "blocked", why, 0
    if get_setting(conn, org_id, SIMULATE_KEY) == "1":
        return "failed", "Simulated delivery failure (demo) - no SMTP attempt was made.", 1
    return None, None, 0


def dispatch(conn, notif_id, actor_label="System notifier"):
    n = conn.execute("SELECT * FROM notifications WHERE id=?", (notif_id,)).fetchone()
    if n["kind"] == "test":
        email = n["recipient_email"] or ""
    else:
        rec = conn.execute("SELECT email FROM notification_recipients WHERE org_id=? AND user_id=?",
                           (n["org_id"], n["user_id"])).fetchone()
        email = rec["email"] if rec else ""
    status, error, simulated = _precheck(conn, n["org_id"], email)
    if status is None:
        try:
            _send_smtp(email, n["subject"], n["body"])
            status, error = "sent", None
        except (smtplib.SMTPException, OSError) as exc:
            status, error = "failed", safe_smtp_error(exc)
    ts = now_iso()
    where, key = ("digest_batch=?", n["digest_batch"]) if n["digest_batch"] else ("id=?", notif_id)
    conn.execute(f"UPDATE notifications SET status=?, error=?, simulated=?, recipient_email=?, attempts=attempts+1,"
                 f" updated_at=?, sent_at=? WHERE {where}",
                 (status, error, simulated, email or None, ts, ts if status == "sent" else None, key))
    who = conn.execute("SELECT display_name FROM users WHERE id=?", (n["user_id"],)).fetchone() if n["user_id"] else None
    label = "digest" if n["digest_batch"] else n["kind"]
    audit(conn, org_id=n["org_id"], actor_id=None, actor_label=actor_label, action=f"notification.{status}",
          target_type="notification", target_id=notif_id,
          summary=f"{label.capitalize()} {n['priority'] or ''} email to {who['display_name'] if who else (email or 'no address')}"
                  f": {status}" + (f" ({error})" if error else ""))
    return status


def process_queue(conn, org_id=None, actor_label="System notifier"):
    """Send pending P1/P2 notifications: the 'next local processing cycle'."""
    sql = "SELECT id FROM notifications WHERE status='pending' AND cadence IN ('prompt','immediate')"
    args = ()
    if org_id:
        sql, args = sql + " AND org_id=?", (org_id,)
    return [dispatch(conn, r["id"], actor_label) for r in conn.execute(sql + " ORDER BY id", args).fetchall()]


def process_digest(conn, org_id=None, actor_label="System notifier (daily digest)"):
    sql = "SELECT * FROM notifications WHERE status='pending' AND cadence='digest'"
    args = ()
    if org_id:
        sql, args = sql + " AND org_id=?", (org_id,)
    groups = {}
    for r in conn.execute(sql + " ORDER BY id", args).fetchall():
        groups.setdefault((r["org_id"], r["user_id"]), []).append(r)
    results = []
    for (oid, _uid), group in groups.items():
        entries = []
        for r in group:
            ctx = alert_context(conn, r["alert_id"])
            entries.append({k: ctx[k] for k in ("priority", "match_state", "title", "link")})
        org = conn.execute("SELECT name FROM organizations WHERE id=?", (oid,)).fetchone()
        subject, body = build_digest(org["name"], entries)
        batch = uuid.uuid4().hex[:12]
        conn.executemany("UPDATE notifications SET digest_batch=?, subject=?, body=? WHERE id=?",
                         [(batch, subject, body, r["id"]) for r in group])
        results.append(dispatch(conn, group[0]["id"], actor_label))
    return results


def send_test(conn, org_id, email, actor_label):
    ts = now_iso()
    subject = f"{SUBJECT_PREFIX} Delivery check from Canary"
    body = TEST_NOTICE + "\n\nThis is a delivery check for the Canary demo's test-email path. No alert is attached."
    nid = conn.execute("INSERT INTO notifications (org_id, kind, cadence, status, recipient_email, subject, body,"
                       " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                       (org_id, "test", "manual", "pending", (email or "").strip(), subject, body, ts, ts)).lastrowid
    return dispatch(conn, nid, actor_label)
