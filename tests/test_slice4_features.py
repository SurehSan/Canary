"""Slice 4: analysis correction (006), profile/inventory editing (002), org creation, invites, roles (001),
privacy/data-flow page (015)."""
import json

import pytest

from canary.analysis import apply_corrections
from tests.conftest import login, org_id, refresh

FERNWOOD, PRAIRIE = "Fernwood Labs", "Prairie Valley Medical Center"


def uid(db, name):
    return db.execute("SELECT id FROM users WHERE username=?", (name,)).fetchone()["id"]


def fern_alert(client, db, user="sureh"):
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    refresh(client)
    if user != "wyatt":
        client.post("/logout")
        login(client, user, org=fern)
    return fern, db.execute("SELECT id FROM alerts WHERE org_id=?", (fern,)).fetchone()["id"]


# ------------------------------------------------------------------ CAN-REQ-006 correction
ORIGINAL = ("An internet-facing service on a PHP version inside the affected range should be treated as urgent "
            "patch work.")
CORRECTED = "The billing portal is internet-facing and on an affected PHP version; patching it is the top priority."


def test_apply_corrections_overlays_matching_text_only():
    analysis = {"interpretation": [ORIGINAL, "Other"], "source_supported": [{"text": "Claim", "citations": [1]}]}
    corrections = [{"section": "interpretation", "prior_value": ORIGINAL, "new_value": CORRECTED, "editor": "Sureh",
                    "reason": "r", "created_at": "t"},
                   {"section": "source_supported", "prior_value": "Claim", "new_value": "Claim (verified)",
                    "editor": "Sureh", "reason": "r", "created_at": "t"},
                   {"section": "unknowns", "prior_value": "gone", "new_value": "x", "editor": "S", "reason": "r",
                    "created_at": "t"}]
    out = apply_corrections(analysis, corrections)
    assert out["interpretation"][0] == CORRECTED and out["interpretation"][1] == "Other"
    assert out["source_supported"][0]["text"] == "Claim (verified)" and out["source_supported"][0]["citations"] == [1]
    assert out["corrected"][("interpretation", CORRECTED)]["editor"] == "Sureh"
    assert analysis["interpretation"][0] == ORIGINAL, "input not mutated"


def test_correction_is_recorded_with_provenance_and_shown(client, db):
    fern, alert = fern_alert(client, db)
    client.post(f"/alerts/{alert}/analysis/correct", data={"section": "interpretation", "original": ORIGINAL,
                                                           "corrected": CORRECTED, "reason": "More precise"})
    row = db.execute("SELECT * FROM analysis_corrections WHERE org_id=?", (fern,)).fetchone()
    assert (row["prior_value"], row["new_value"], row["reason"], row["editor_id"]) == \
        (ORIGINAL, CORRECTED, "More precise", uid(db, "sureh"))
    assert row["created_at"]
    page = client.get(f"/alerts/{alert}").data.decode()
    assert CORRECTED in page and "Corrected by Sureh" in page and "More precise" in page
    ev = db.execute("SELECT * FROM audit_events WHERE action='analysis.corrected'").fetchone()
    assert ORIGINAL in ev["before_state"] and CORRECTED in ev["after_state"]


def test_correction_survives_reassessment(client, db):
    fern, alert = fern_alert(client, db, user="wyatt")
    client.post(f"/alerts/{alert}/analysis/correct", data={"section": "interpretation", "original": ORIGINAL,
                                                           "corrected": CORRECTED, "reason": "r"})
    client.post("/sources/followup")
    assert CORRECTED in client.get(f"/alerts/{alert}").data.decode()


@pytest.mark.parametrize("data", [
    {"section": "interpretation", "original": ORIGINAL, "corrected": CORRECTED, "reason": " "},
    {"section": "exploitation_status", "original": "x", "corrected": "y", "reason": "r"},
    {"section": "interpretation", "original": "text that is not in the analysis", "corrected": "y", "reason": "r"},
])
def test_invalid_corrections_are_rejected(client, db, data):
    _, alert = fern_alert(client, db)
    assert client.post(f"/alerts/{alert}/analysis/correct", data=data).status_code == 400


def test_other_org_cannot_correct_analysis(client, db):
    _, alert = fern_alert(client, db, user="wyatt")
    client.post("/logout")
    login(client, "priya", org=org_id(db, PRAIRIE))
    resp = client.post(f"/alerts/{alert}/analysis/correct", data={"section": "interpretation", "original": ORIGINAL,
                                                                   "corrected": "x", "reason": "r"})
    assert resp.status_code == 404


# ------------------------------------------------------------------ CAN-REQ-002 profile + inventory
def test_admin_edits_profile_with_unknowns_and_audit(client, db):
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    client.post("/organization/profile", data={"name": "Fernwood Labs", "industry": "Software / FinTech",
                                               "size": "", "location": "Remote", "monitoring_interests": ""})
    org = db.execute("SELECT * FROM organizations WHERE id=?", (fern,)).fetchone()
    assert (org["industry"], org["size"], org["location"]) == ("Software / FinTech", None, "Remote")
    assert db.execute("SELECT 1 FROM audit_events WHERE action='organization.profile_updated'").fetchone()
    assert "Unknown" in client.get("/organization").data.decode()


def test_profile_requires_name_and_industry(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert client.post("/organization/profile", data={"name": "Fernwood Labs", "industry": " "}).status_code == 400


def test_lead_cannot_edit_profile_but_can_maintain_inventory(client, db):
    fern = org_id(db, FERNWOOD)
    login(client, "sureh", org=fern)
    assert client.post("/organization/profile", data={"name": "x", "industry": "y"}).status_code == 403
    client.post("/organization/inventory", data={"name": "Embedding model API", "category": "LLM API",
                                                 "version": "", "criticality": "Medium", "capabilities": "llm_api"})
    item = db.execute("SELECT * FROM inventory_items WHERE name='Embedding model API'").fetchone()
    assert item["org_id"] == fern and item["version"] is None and item["version_status"] == "unknown"
    assert json.loads(item["capabilities"]) == ["llm_api"]


def test_inventory_edit_and_delete_are_audited_and_rescore(client, db):
    fern, alert = fern_alert(client, db, user="wyatt")
    portal = db.execute("SELECT id FROM inventory_items WHERE org_id=? AND product_key='php'", (fern,)).fetchone()["id"]
    client.post(f"/organization/inventory/{portal}", data={"name": "Customer billing portal (PHP-FPM)",
                                                           "product_key": "php", "version": "8.3.36",
                                                           "version_status": "known", "criticality": "Critical",
                                                           "capabilities": "php"})
    rel = db.execute("SELECT match_state FROM relevance WHERE org_id=?", (fern,)).fetchone()
    assert rel["match_state"] == "no_match"  # patched to a fixed release: no longer affected
    edited = db.execute("SELECT * FROM inventory_items WHERE id=?", (portal,)).fetchone()
    assert (edited["version"], edited["version_status"], edited["criticality"]) == ("8.3.36", "known", "Critical")
    client.post(f"/organization/inventory/{portal}/delete")
    assert db.execute("SELECT 1 FROM inventory_items WHERE id=?", (portal,)).fetchone() is None
    actions = {r[0] for r in db.execute("SELECT action FROM audit_events WHERE org_id=?", (fern,))}
    assert {"inventory.updated", "inventory.deleted"} <= actions


def test_inventory_rejects_invalid_values(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert client.post("/organization/inventory", data={"name": " "}).status_code == 400
    assert client.post("/organization/inventory", data={"name": "x", "criticality": "Extreme"}).status_code == 400


def test_other_org_cannot_edit_or_delete_inventory(client, db):
    item = db.execute("SELECT i.id FROM inventory_items i JOIN organizations o ON o.id=i.org_id"
                      " WHERE o.name=?", (FERNWOOD,)).fetchone()["id"]
    login(client, "priya", org=org_id(db, PRAIRIE))
    assert client.post(f"/organization/inventory/{item}", data={"name": "hijack"}).status_code == 404
    assert client.post(f"/organization/inventory/{item}/delete").status_code == 404


# ------------------------------------------------------------------ CAN-REQ-001 register, create org, invite, roles
def register(client, username="dana"):
    return client.post("/register", data={"username": username, "display_name": "Dana", "password": "pass1234"})


def test_new_user_registers_and_creates_org_as_admin(client, db):
    register(client)
    client.post("/orgs/create", data={"name": "Juniper Robotics", "industry": "Manufacturing"})
    org = db.execute("SELECT * FROM organizations WHERE name='Juniper Robotics'").fetchone()
    m = db.execute("SELECT role, status FROM memberships WHERE org_id=? AND user_id=?",
                   (org["id"], uid(db, "dana"))).fetchone()
    assert tuple(m) == ("admin", "active")
    page = client.get("/").data.decode()
    assert "Juniper Robotics" in page
    assert client.post("/orgs/select", data={"org_id": org_id(db, FERNWOOD)}).status_code == 404
    assert db.execute("SELECT COUNT(*) FROM org_sources WHERE org_id=? AND enabled=1", (org["id"],)).fetchone()[0] == 5


def test_duplicate_username_is_rejected(client, db):
    assert register(client, "wyatt").status_code == 400


def test_create_org_requires_name_and_industry(client, db):
    register(client)
    assert client.post("/orgs/create", data={"name": "X", "industry": ""}).status_code == 400


def test_admin_invites_existing_user_and_changes_role(client, db):
    register(client)
    client.post("/orgs/create", data={"name": "Juniper Robotics", "industry": "Manufacturing"})
    jun = org_id(db, "Juniper Robotics")
    client.post("/members/invite", data={"username": "koewen", "role": "lead"})
    m = db.execute("SELECT role, status FROM memberships WHERE org_id=? AND user_id=?", (jun, uid(db, "koewen"))).fetchone()
    assert tuple(m) == ("lead", "active")
    client.post(f"/members/{uid(db, 'koewen')}/role", data={"role": "admin"})
    assert db.execute("SELECT role FROM memberships WHERE org_id=? AND user_id=?",
                      (jun, uid(db, "koewen"))).fetchone()[0] == "admin"
    actions = [r[0] for r in db.execute("SELECT action FROM audit_events WHERE org_id=? ORDER BY id", (jun,))]
    assert "membership.invited" in actions and "membership.role_changed" in actions
    other = client.application.test_client()
    login(other, "koewen", org=jun)
    assert other.get("/").status_code == 200


def test_invite_reactivates_revoked_member(client, db):
    fern = org_id(db, FERNWOOD)
    login(client, "wyatt", org=fern)
    client.post(f"/members/{uid(db, 'koewen')}/revoke")
    client.post("/members/invite", data={"username": "koewen", "role": "lead"})
    assert db.execute("SELECT status FROM memberships WHERE org_id=? AND user_id=?",
                      (fern, uid(db, "koewen"))).fetchone()[0] == "active"


@pytest.mark.parametrize("data", [{"username": "nobody", "role": "lead"}, {"username": "sureh", "role": "lead"},
                                  {"username": "priya", "role": "owner"}])
def test_invalid_invites_rejected(client, db, data):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert client.post("/members/invite", data=data).status_code == 400


def test_lead_cannot_invite_or_change_roles(client, db):
    login(client, "sureh", org=org_id(db, FERNWOOD))
    assert client.post("/members/invite", data={"username": "priya", "role": "lead"}).status_code == 403
    assert client.post(f"/members/{uid(db, 'koewen')}/role", data={"role": "admin"}).status_code == 403


def test_last_admin_cannot_demote_self(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert client.post(f"/members/{uid(db, 'wyatt')}/role", data={"role": "lead"}).status_code == 400


def test_role_change_for_non_member_is_not_found(client, db):
    login(client, "wyatt", org=org_id(db, FERNWOOD))
    assert client.post(f"/members/{uid(db, 'priya')}/role", data={"role": "lead"}).status_code == 404


# ------------------------------------------------------------------ CAN-REQ-015 privacy / data flows
def test_privacy_page_discloses_data_flows_and_boundaries(client, db):
    login(client, "sureh", org=org_id(db, FERNWOOD))
    page = client.get("/privacy").data.decode()
    for text in ("Data flows", "SMTP", "not configured", "No model provider", "Retention", "until you reset",
                 "HIPAA", "not proof", "human approval", "Live RSS is off", "never stored in the database"):
        assert text in page, text
    assert 'href="/privacy"' in client.get("/").data.decode()
