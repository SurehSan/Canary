"""CAN-REQ-011: guide generation and targeted clarification (pure logic)."""
from canary.guides import build_guide, condition_for_answer

RUNTIME = {"id": 2, "name": "Python runtime agent framework", "capabilities": ["agent_runtime", "python_packages"]}
SOURCES = [{"id": 11, "url": "https://thehackernews.com/2026/07/new-hallusquatting-attack-could-trick.html"},
           {"id": 12, "url": "https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/04/"
                             "CSA_research_note_slopsquatting-ai-supply-chain_20260419-csa-styled-1.pdf"}]


def test_hallusquatting_guide_has_five_ordered_steps_with_required_fields():
    g = build_guide("package-hallucination-squatting", [RUNTIME], SOURCES)
    assert [s["position"] for s in g["steps"]] == [1, 2, 3, 4, 5]
    assert g["steps"][0]["action"].startswith("Review recent lockfile")
    for s in g["steps"]:
        for field in ("action", "rationale", "checks", "technique", "links", "basis"):
            assert s[field], (s["position"], field)
    assert "AI-generated draft for human review" in g["label"]


def test_steps_link_only_to_supplied_sources_plus_framework():
    g = build_guide("package-hallucination-squatting", [RUNTIME], SOURCES[:1])
    urls = {l["url"] for s in g["steps"] for l in s["links"]}
    assert SOURCES[1]["url"] not in urls
    assert "https://genai.owasp.org/llmrisk/llm032025-supply-chain/" in urls


def test_asks_one_targeted_question_when_install_permission_is_unknown():
    g = build_guide("package-hallucination-squatting", [RUNTIME], SOURCES)
    q = g["question"]
    assert q["text"].startswith("Does Ledgerly's runtime agent") is False  # org-neutral wording
    assert "install packages in production" in q["text"]
    assert q["options"] == ["Yes", "No", "Unknown"]
    assert "step 4" in q["why"].lower()
    assert g["steps"][3]["condition"] and g["steps"][3]["condition_status"] == "pending"


def test_no_question_when_inventory_already_answers_it():
    known = dict(RUNTIME, capabilities=["agent_runtime", "install_permission_no"])
    g = build_guide("package-hallucination-squatting", [known], SOURCES)
    assert g["question"] is None
    assert g["steps"][3]["condition_status"] == "not_met"


def test_answers_change_step_4_condition_without_inventing_facts():
    assert condition_for_answer("Yes") == ("met", "Immediate action: the runtime agent can install packages in production.")
    assert condition_for_answer("No")[0] == "not_met"
    status, note = condition_for_answer("Unknown")
    assert status == "pending" and "verify" in note.lower()


def test_unrecognized_threat_gets_limited_guide_that_states_its_limits():
    g = build_guide(None, [RUNTIME], SOURCES[:1])
    assert g["question"] is None and len(g["steps"]) >= 2
    assert any("vendor" in s["action"].lower() or "authoritative" in s["technique"].lower() for s in g["steps"])
    assert "limited" in g["label"].lower()
