"""CAN-REQ-007: match state and priority rubric (pure logic)."""
from datetime import date

from canary.scoring import match_state, score_priority, version_affected

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


def test_baseline_technique_case_scores_65_p2_with_documented_factors():
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


# ------------------------------------------------------------------ PHP2Shell demo scenario (version ranges, P1 gate)
PHP_RANGES = [">=5.4.0,<8.2.0", ">=8.2.0,<8.2.35", ">=8.3.0,<8.3.36", ">=8.4.0,<8.4.27", ">=8.5.0,<8.5.12"]
PORTAL = {"id": 9, "name": "Customer billing portal (PHP-FPM)", "product_key": "php", "version": "8.3.30",
          "capabilities": ["php"], "criticality": "Critical"}
PHP2SHELL = {"affected_products": [{"product_key": "php", "versions": PHP_RANGES}], "technique_tags": [],
             "industries": []}


def test_version_ranges_follow_the_fixed_release_on_each_branch():
    affected = ["8.3.30", "8.3.35", "8.4.26", "8.5.11", "8.2.34", "8.1.31", "7.4.33", "5.4.0"]
    fixed = ["8.3.36", "8.3.40", "8.4.27", "8.5.12", "8.2.35", "5.3.29", "8.6.0"]
    assert all(version_affected(v, PHP_RANGES) for v in affected)
    assert not any(version_affected(v, PHP_RANGES) for v in fixed)


def test_exact_version_lists_still_work():
    assert version_affected("2.4", ["2.4", "2.5"]) and not version_affected("2.6", ["2.4", "2.5"])


def test_known_affected_php_version_is_a_confirmed_match():
    result = match_state(PHP2SHELL, [PORTAL], "Software")
    assert result["state"] == "confirmed" and "8.3.30" in result["evidence"][0]["reason"]


def test_patched_php_version_is_not_a_match():
    assert match_state(PHP2SHELL, [dict(PORTAL, version="8.3.36")], "Software")["state"] == "no_match"


def test_unknown_php_version_is_only_possible():
    assert match_state(PHP2SHELL, [dict(PORTAL, version=None)], "Software")["state"] == "possible"


PHP_INITIAL = dict(
    impact_class="critical_cvss", exploitation_status="claimed_in_wild_unverified", match_state="confirmed",
    criticalities=["Critical"], as_of=date(2026, 11, 14), questionnaire_answer="No", duplicate_without_new_info=False,
    sources=[{"tier": "A", "published_at": "2026-10-21"}, {"tier": "A", "published_at": "2026-10-21"},
             {"tier": "A", "published_at": "2026-10-21"}, {"tier": "B", "published_at": "2026-10-21"}],
)


def test_php2shell_before_confirmed_exploitation_scores_87_but_is_capped_at_p2():
    result = score_priority(**PHP_INITIAL)
    pts = {f["key"]: f["points"] for f in result["factors"]}
    assert (pts["severity"], pts["exploitation"], pts["inventory_match"], pts["asset_criticality"],
            pts["source_reliability"], pts["questionnaire_gap"]) == (25, 12, 20, 15, 10, 5)
    assert result["score"] == 87 and result["priority"] == "P2" and result["p1_gate_met"] is False


def test_php2shell_after_confirmed_exploitation_is_p1():
    result = score_priority(**dict(PHP_INITIAL, exploitation_status="active_in_wild",
                                   sources=PHP_INITIAL["sources"] + [{"tier": "B", "published_at": "2026-11-12"}]))
    assert result["score"] == 95 and result["priority"] == "P1" and result["p1_gate_met"] is True
