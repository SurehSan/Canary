"""CAN-REQ-005: source normalization and duplicate detection (pure logic)."""
from canary.normalize import canonical_url, classify_duplicate, detect_technique, extract_identifiers


def test_canonical_url_strips_tracking_fragment_and_trailing_slash():
    assert canonical_url("HTTPS://TheHackerNews.com/2026/07/x.html/?utm_source=rss&id=3#top") == \
        "https://thehackernews.com/2026/07/x.html?id=3"


def test_extract_identifiers_finds_cve_and_ghsa():
    ids = extract_identifiers("Fix for CVE-2026-1234 and GHSA-abcd-1234-wxyz in pkg")
    assert ids == ["CVE-2026-1234", "GHSA-ABCD-1234-WXYZ"]


def test_detect_technique_from_alias():
    assert detect_technique("Slopsquatting: AI Code Hallucinations Fuel Supply Chain Attacks", "") == "package-hallucination-squatting"
    assert detect_technique("New HalluSquatting Attack Could Trick AI Coding Assistants", "") == "package-hallucination-squatting"
    assert detect_technique("Quarterly cloud pricing update", "") is None


EXISTING = [{"finding_id": 7, "identifiers": ["CVE-2026-1234"],
             "canonical_urls": ["https://thehackernews.com/a.html"],
             "technique": "package-hallucination-squatting"}]


def test_same_advisory_identifier_is_exact_duplicate():
    item = {"identifiers": ["CVE-2026-1234"], "canonical_url": "https://other.example/x", "technique": None}
    assert classify_duplicate(item, EXISTING) == {"finding_id": 7, "status": "exact",
                                                  "basis": "Same advisory identifier CVE-2026-1234"}


def test_same_canonical_url_is_exact_duplicate():
    item = {"identifiers": [], "canonical_url": "https://thehackernews.com/a.html", "technique": None}
    assert classify_duplicate(item, EXISTING)["status"] == "exact"


def test_shared_technique_alias_is_only_a_proposal_for_human_review():
    item = {"identifiers": [], "canonical_url": "https://labs.example/csa.pdf",
            "technique": "package-hallucination-squatting"}
    result = classify_duplicate(item, EXISTING)
    assert result["status"] == "proposed"
    assert result["finding_id"] == 7
    assert "review" in result["basis"].lower()


def test_unrelated_item_is_not_grouped():
    item = {"identifiers": [], "canonical_url": "https://x.example/y", "technique": None}
    assert classify_duplicate(item, EXISTING) is None
