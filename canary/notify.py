"""Test-email notifications — CAN-REQ-009.

Safety order for every send: recipient on the env allowlist (checked BEFORE
anything else) -> SMTP configured -> send. Every message is a labeled test
message. There is no production mode and no mock-inbox fallback: a send that
cannot happen is recorded as rejected, blocked, or failed.
"""
import hashlib
import json
import re

from .scoring import MATCH_LABELS, PRIORITY_LABELS

SUBJECT_PREFIX = "[CANARY DEMO - TEST]"
EMAIL_RE = re.compile(r"^[^@\s,]+@[^@\s,]+\.[^@\s,]+$")
TEST_NOTICE = ("*** TEST MODE - CANARY DEMO NOTIFICATION ***\n"
               "This message comes from a local Canary demo prototype. It is a demo notification and is "
               "not evidence of an actual incident. The organization and people named are fictional.")


def parse_allowlist(raw):
    out = set()
    for part in (raw or "").split(","):
        addr = part.strip().lower()
        if addr and EMAIL_RE.match(addr):
            out.add(addr)
    return out


def check_recipient(email, allowlist):
    """Return None if sending is allowed, else the rejection reason."""
    if not (email or "").strip():
        return "No test address is configured for this recipient."
    if not allowlist:
        return "Rejected: the test allowlist is empty or malformed, so no recipient is allowed."
    if email.strip().lower() not in allowlist:
        return "Rejected before sending: address is not on the test allowlist."
    return None


def cadence_for(priority):
    return {"P1": "immediate", "P2": "prompt"}.get(priority, "digest")


def fingerprint(material):
    """Hash of the fields whose change counts as a meaningful update."""
    norm = {"priority": material["priority"], "match_state": material["match_state"],
            "exploitation_status": material["exploitation_status"],
            "affected_products": sorted(json.dumps(p, sort_keys=True) for p in material["affected_products"]),
            "source_urls": sorted(material["source_urls"])}
    return hashlib.sha256(json.dumps(norm, sort_keys=True).encode()).hexdigest()[:16]


def build_message(ctx):
    label = PRIORITY_LABELS[ctx["priority"]]
    match = MATCH_LABELS[ctx["match_state"]]
    kind = "Update: " if ctx["kind"] == "update" else ""
    subject = f"{SUBJECT_PREFIX} {kind}{ctx['priority']} · {match} · {ctx['title']}"
    lines = [TEST_NOTICE, ""]
    if ctx["kind"] == "update":
        lines += [f"UPDATE: {ctx.get('change', 'Meaningful change to this alert')}", ""]
    lines += [ctx["title"], "",
              f"Priority: {label} ({ctx['score']}/100) - a triage recommendation, not proof of exposure",
              f"Relevance: {match}", "",
              "Summary:", *[f"  {w}" for w in ctx["what_happened"]], "",
              f"Why this may matter to {ctx['org_name']}:", *[f"  - {c}" for c in ctx["org_context"]], "",
              "Known (source-supported):", *[f"  - {k}" for k in ctx["known"]], "",
              "Unknown:", *[f"  - {u}" for u in ctx["unknowns"]], "",
              "Sources:", *[f"  [{s['n']}] {s['title']} - {s['url']} (published {s['published_at'] or 'not supplied'})"
                            for s in ctx["sources"]], "",
              f"Open in Canary (local): {ctx['link']}", "",
              "Reminder: demo notification, not evidence of an actual incident."]
    return subject, "\n".join(lines)


def parse_recipients(raw):
    """CANARY_TEST_RECIPIENTS="sureh=a@team.example,wyatt=b@team.example" -> {username: email}."""
    out = {}
    for part in (raw or "").split(","):
        if "=" in part:
            user, addr = (x.strip() for x in part.split("=", 1))
            if user and addr:
                out[user.lower()] = addr
    return out


def build_digest(org_name, entries):
    subject = f"{SUBJECT_PREFIX} Daily digest · {org_name} · {len(entries)} item(s)"
    lines = [TEST_NOTICE, "", f"Daily digest for {org_name} (P3/P4 alerts):", ""]
    for e in entries:
        lines.append(f"  - {e['priority']} · {MATCH_LABELS[e['match_state']]} · {e['title']} - {e['link']}")
    lines += ["", "Reminder: demo notification, not evidence of an actual incident."]
    return subject, "\n".join(lines)
