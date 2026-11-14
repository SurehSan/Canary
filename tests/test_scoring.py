"""CAN-REQ-007: match state and priority rubric (pure logic)."""
from datetime import date

from canary.scoring import match_state, score_priority

CODING_ASSISTANT = {"id": 1, "name": "AI coding assistant", "product_key": "coding-assistant",
                    "version": "2.4", "capabilities": ["ai_coding_agent", "auto_install_packages"],
                    "criticality": "High"}
RUNTIME_AGENT = {"id": 2, "name": "Python runtime agent framework", "product_key": "agentkit",
                 "version": None, "capabilities": ["agent_runtime"], "criticality": "Critical"}
LLM_API = {"id": 3, "name": "LLM API provider", "product_key": "llm-api", "version": None,
           "capabilities": ["llm_api"], "criticality": "Critical"}

HALLUSQUATTING = {"affected_products": [], "technique_tags": ["auto_install_packages", "agent_runtime"],
                  "industries": []}


def test_technique_overlap_without_product_match_is_possible():
    result = match_state(HALLUSQUATTING, [CODING_ASSISTANT, RUNTIME_AGENT, LLM_API], "Software")
    assert result["state"] == "possible"
    assert {e["item_id"] for e in result["evidence"]} == {1, 2}


def test_unknown_version_never_confirmed_even_with_exact_product():
    finding = {"affected_products": [{"product_key": "agentkit", "versions": ["1.0", "1.1"]}],
               "technique_tags": [], "industries": []}
    assert match_state(finding, [RUNTIME_AGENT], "Software")["state"] == "possible"


def test_known_version_in_affected_range_is_confirmed():
    finding = {"affected_products": [{"product_key": "coding-assistant", "versions": ["2.4"]}],
               "technique_tags": [], "industries": []}
    assert match_state(finding, [CODING_ASSISTANT], "Software")["state"] == "confirmed"


def test_known_version_outside_affected_range_is_not_a_match():
    finding = {"affected_products": [{"product_key": "coding-assistant", "versions": ["1.0"]}],
               "technique_tags": [], "industries": []}
    assert match_state(finding, [CODING_ASSISTANT], "Software")["state"] == "no_match"


def test_industry_only_relevance():
    finding = {"affected_products": [], "technique_tags": ["clinical_scribe"], "industries": ["Healthcare"]}
    assert match_state(finding, [LLM_API], "Healthcare")["state"] == "industry_only"


def test_no_supported_relationship_is_no_match():
    finding = {"affected_products": [], "technique_tags": ["clinical_scribe"], "industries": ["Healthcare"]}
    assert match_state(finding, [LLM_API], "Software")["state"] == "no_match"


SEEDED_INPUTS = dict(
    impact_class="code_execution_no_cvss",
    exploitation_status="research_demonstrated",
    match_state="possible",
    criticalities=["High", "Critical"],
    sources=[{"tier": "B", "published_at": "2026-07-08"}, {"tier": "B", "published_at": "2026-04-19"}],
    as_of=date(2026, 11, 14),
    questionnaire_answer="No",
    duplicate_without_new_info=False,
)


def test_seeded_hallusquatting_scores_65_p2_with_documented_factors():
    result = score_priority(**SEEDED_INPUTS)
    pts = {f["key"]: f["points"] for f in result["factors"]}
    assert pts == {"severity": 16, "exploitation": 8, "inventory_match": 12,
                   "asset_criticality": 15, "source_reliability": 9, "questionnaire_gap": 5,
                   "duplicate_penalty": 0}
    assert result["score"] == 65
    assert result["priority"] == "P2"
    assert result["p1_gate_met"] is False


def test_every_factor_carries_an_explanation():
    for factor in score_priority(**SEEDED_INPUTS)["factors"]:
        assert factor["max"] is not None and factor["reason"]


def test_score_bands():
    from canary.scoring import band
    assert [band(s) for s in (100, 80, 79, 60, 59, 35, 34, 0)] == ["P1", "P1", "P2", "P2", "P3", "P3", "P4", "P4"]


def test_high_score_without_p1_gate_caps_at_p2():
    inputs = dict(SEEDED_INPUTS, impact_class="critical_cvss", exploitation_status="active_in_wild",
                  match_state="possible")
    result = score_priority(**inputs)
    assert result["score"] >= 80
    assert result["priority"] == "P2"
    assert "P1 requires" in result["p1_gate_reason"]


def test_p1_requires_active_exploitation_and_confirmed_critical_match():
    inputs = dict(SEEDED_INPUTS, impact_class="critical_cvss", exploitation_status="active_in_wild",
                  match_state="confirmed", criticalities=["Critical"])
    result = score_priority(**inputs)
    assert result["priority"] == "P1"
    assert result["p1_gate_met"] is True


def test_duplicate_without_new_information_subtracts_ten():
    result = score_priority(**dict(SEEDED_INPUTS, duplicate_without_new_info=True))
    assert result["score"] == 55
    assert result["priority"] == "P3"
