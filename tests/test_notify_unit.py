"""CAN-REQ-009: message content, allowlist, cadence, fingerprint (pure logic)."""
from canary.notify import SUBJECT_PREFIX, build_message, cadence_for, check_recipient, fingerprint, parse_allowlist

CTX = {
    "org_name": "Fernwood Labs", "title": "HalluSquatting: hallucinated package names used to hijack AI coding agents",
    "priority": "P2", "score": 65, "match_state": "possible", "kind": "new",
    "what_happened": ["Researchers showed ..."],
    "org_context": ["AI coding assistant: Technology overlap: auto_install_packages"],
    "known": ["Language models can produce package names that do not exist. [2]"],
    "unknowns": ["No specific malicious package is tied to this organization."],
    "sources": [{"n": 1, "title": "New HalluSquatting Attack", "url": "https://thehackernews.com/x", "published_at": "2026-07-08"}],
    "link": "http://127.0.0.1:5000/alerts/1",
}


def test_subject_is_prefixed_with_test_label():
    subject, _ = build_message(CTX)
    assert subject.startswith("[CANARY DEMO - TEST] ")
    assert SUBJECT_PREFIX == "[CANARY DEMO - TEST]"
    assert "P2" in subject and "Possible match" in subject


def test_body_has_test_notice_why_known_unknown_sources_and_disclaimer():
    _, body = build_message(CTX)
    for text in ("TEST MODE", "not evidence of an actual incident", "Why this may matter to Fernwood Labs",
                 "Known", "Unknown", "https://thehackernews.com/x", "2026-07-08", "P2 High", "65/100",
                 "Possible match", "fictional"):
        assert text in body, text


def test_update_message_is_labeled_as_update():
    subject, body = build_message(dict(CTX, kind="update", change="Source evidence added: 3 sources"))
    assert "Update" in subject and "Source evidence added" in body


def test_allowlist_parsing_is_case_insensitive_and_drops_malformed_entries():
    assert parse_allowlist(" Team@Example.com, bad-address,, other@example.org ") == {"team@example.com", "other@example.org"}


def test_recipient_must_be_on_allowlist():
    allow = {"team@example.com"}
    assert check_recipient("TEAM@example.com", allow) is None
    assert "not on the test allowlist" in check_recipient("someone@else.com", allow)
    assert "allowlist is empty" in check_recipient("team@example.com", set())
    assert "No test address" in check_recipient("", allow)


def test_cadence_by_priority():
    assert [cadence_for(p) for p in ("P1", "P2", "P3", "P4")] == ["immediate", "prompt", "digest", "digest"]


def test_fingerprint_changes_only_on_material_fields():
    base = {"priority": "P2", "match_state": "possible", "exploitation_status": "research_demonstrated",
            "affected_products": [], "source_urls": ["a", "b"]}
    assert fingerprint(base) == fingerprint(dict(base, source_urls=["b", "a"]))
    assert fingerprint(base) != fingerprint(dict(base, source_urls=["a", "b", "c"]))
    assert fingerprint(base) != fingerprint(dict(base, priority="P1"))
