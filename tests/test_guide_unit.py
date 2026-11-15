"""CAN-REQ-011: guide generation and targeted clarification (pure logic). Demo scenario: PHP2Shell."""
from canary.fixtures import CHECK_POINT_URL, GHSA_OOM_URL, GHSA_STATE_URL, PHP_NET_URL, THN_URL
from canary.guides import build_guide, condition_for_answer

PORTAL = {"id": 9, "name": "Customer billing portal (PHP-FPM)", "capabilities": ["php"]}
SOURCES = [{"id": 1, "url": PHP_NET_URL, "source_label": "PHP security announcements"},
           {"id": 2, "url": THN_URL, "source_label": "The Hacker News"},
           {"id": 3, "url": GHSA_OOM_URL, "source_label": "GitHub Security Advisories"},
           {"id": 4, "url": GHSA_STATE_URL, "source_label": "GitHub Security Advisories"}]
CIS = "https://www.cisecurity.org/controls/continuous-vulnerability-management"


def test_php2shell_guide_has_five_ordered_steps_with_required_fields():
    g = build_guide("php2shell", [PORTAL], SOURCES)
    assert [s["position"] for s in g["steps"]] == [1, 2, 3, 4, 5]
    assert g["steps"][0]["action"].startswith("Confirm the PHP version")
    assert "8.3.36" in g["steps"][1]["action"]
    assert "session.upload_progress.enabled" in g["steps"][2]["action"]
    for s in g["steps"]:
        for field in ("action", "rationale", "checks", "technique", "links", "basis"):
            assert s[field], (s["position"], field)
    assert "AI-generated draft for human review" in g["label"]


def test_source_links_are_labeled_with_the_source_name():
    g = build_guide("php2shell", [PORTAL], SOURCES)
    titles = [l["title"] for l in g["steps"][1]["links"]]
    assert titles[0] == "PHP security announcements" and "GitHub Security Advisories" in titles
    assert all(l["title"] != "Cited source" for s in g["steps"] for l in s["links"])


def test_steps_link_only_to_supplied_sources_plus_framework():
    g = build_guide("php2shell", [PORTAL], SOURCES)
    urls = {l["url"] for s in g["steps"] for l in s["links"]}
    assert CHECK_POINT_URL not in urls  # not collected yet
    assert PHP_NET_URL in urls and CIS in urls
    g2 = build_guide("php2shell", [PORTAL], SOURCES + [{"id": 5, "url": CHECK_POINT_URL, "source_label": "Follow-up"}])
    assert CHECK_POINT_URL in {l["url"] for s in g2["steps"] for l in s["links"]}


def test_asks_one_targeted_question_when_internet_exposure_is_unknown():
    g = build_guide("php2shell", [PORTAL], SOURCES)
    q = g["question"]
    assert q["text"] == "Is the Customer billing portal (PHP-FPM) reachable from the internet?"
    assert q["options"] == ["Yes", "No", "Unknown"] and "step 4" in q["why"].lower()
    assert g["steps"][3]["condition"] and g["steps"][3]["condition_status"] == "pending"


def test_no_question_when_inventory_already_answers_it():
    known = dict(PORTAL, capabilities=["php", "internet_exposed_yes"])
    g = build_guide("php2shell", [known], SOURCES)
    assert g["question"] is None and g["steps"][3]["condition_status"] == "met"


def test_answers_change_step_4_condition_without_inventing_facts():
    assert condition_for_answer("internet_exposure", "Yes")[0] == "met"
    assert condition_for_answer("internet_exposure", "No")[0] == "not_met"
    status, note = condition_for_answer("internet_exposure", "Unknown")
    assert status == "pending" and "verify" in note.lower()


def test_unrecognized_threat_gets_limited_guide_that_states_its_limits():
    g = build_guide(None, [PORTAL], SOURCES[:1])
    assert g["question"] is None and len(g["steps"]) >= 2
    assert any("vendor" in s["action"].lower() or "authoritative" in s["technique"].lower() for s in g["steps"])
    assert "limited" in g["label"].lower()
