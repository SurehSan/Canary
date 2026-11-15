"""Targeted threat guides — CAN-REQ-011.

Deterministic templates keyed by technique, checked against the PHP2Shell
demo. Links are limited to the finding's own sources plus framework guidance.
At most one targeted clarification is asked, and only when the organization's
inventory does not already answer it.
"""
from .fixtures import CHECK_POINT_URL, GHSA_OOM_URL, GHSA_STATE_URL, PHP_NET_URL, THN_URL

LABEL = "AI-generated draft for human review (demo template; no actions are executed)"
CIS_7 = {"title": "CIS Controls v8, Control 7: Continuous Vulnerability Management",
         "url": "https://www.cisecurity.org/controls/continuous-vulnerability-management"}

TEMPLATES = {
    "php2shell": [
        dict(action="Confirm the PHP version on every internet-facing service, starting with the customer billing portal.",
             rationale="Only versions below the fixed release on each branch are affected, and vendor packages may "
                       "carry a backported fix under an older version string.",
             checks="Run php -v on each host, or check the package changelog for CVE-2026-109618 and CVE-2026-109619; "
                    "compare with 8.5.12, 8.4.27, 8.3.36, and 8.2.35.",
             technique="Version and changelog verification against the vendor advisory.",
             basis="Organization context: inventory records PHP 8.3.30 on the billing portal",
             sources=[PHP_NET_URL], framework=[CIS_7]),
        dict(action="Upgrade PHP to a fixed release (8.3.36 for the 8.3 branch) and restart every PHP-FPM worker.",
             rationale="The PHP project says there are no complete mitigations; updating is the only safe choice.",
             checks="php -v reports a fixed version on every node, and every PHP-FPM worker has been restarted.",
             technique="Patch deployment with a full worker restart.",
             basis="Source-supported mitigation", sources=[PHP_NET_URL, GHSA_OOM_URL, GHSA_STATE_URL], framework=[CIS_7]),
        dict(action="Until the upgrade is live, set session.upload_progress.enabled = 0 in php.ini or the PHP-FPM pool "
                    "configuration, then restart the workers.",
             rationale="The PHP advisory lists this setting as a mitigation for CVE-2026-109619. It reduces exposure "
                       "but is not a complete fix.",
             checks="The setting shows Off for every pool after the restart (set it in configuration, not ini_set()).",
             technique="Temporary configuration hardening.",
             basis="Source-supported interim mitigation", sources=[PHP_NET_URL, GHSA_STATE_URL], framework=[]),
        dict(action="If the portal was reachable from the internet while it ran an affected version, look for signs "
                    "of compromise.",
             rationale="Exploitation attempts were reported soon after disclosure, and patching does not remove an "
                       "earlier compromise.",
             checks="Review web, PHP-FPM, and system logs since October 21 for unusual requests, worker crashes, new "
                    "processes, or new files, and compare with the indicators published in vendor advisories.",
             technique="Targeted compromise assessment.",
             basis="Generated guidance; depends on an organization fact that is not yet known",
             sources=[THN_URL, CHECK_POINT_URL], framework=[CIS_7],
             condition="Applies as an immediate action only if the portal is reachable from the internet.",
             question="internet_exposure"),
        dict(action="Rotate the payment provider API key and other secrets the portal can read only if step 4 finds "
                    "signs of compromise.",
             rationale="Rotation has a cost, and nothing yet ties an attack to this organization.",
             checks="Trigger only if step 4 finds indicators of compromise.",
             technique="Evidence-based credential rotation.",
             basis="Generated guidance; conditional on investigation findings",
             sources=[CHECK_POINT_URL, PHP_NET_URL], framework=[]),
    ],
}

QUESTIONS = {
    "internet_exposure": {
        "capability": "php",
        "known": {"internet_exposed_yes": "Yes", "internet_exposed_no": "No"},
        "text": "Is the {item} reachable from the internet?",
        "why": "This determines whether step 4 (looking for signs of compromise) is an immediate action or a "
               "precaution.",
        "options": ["Yes", "No", "Unknown"],
        "conditions": {
            "Yes": ("met", "Immediate action: the portal is reachable from the internet."),
            "No": ("not_met", "Precaution only: the respondent reports the portal is not reachable from the internet."),
            "Unknown": ("pending", "Conditional: internet exposure is Unknown. Verify before acting; do not assume "
                                   "either way."),
        },
    },
}

GENERIC = [
    dict(action="Read the cited source and identify the affected product, versions, and conditions.",
         rationale="Canary could not analyze this threat in detail; the source is the authority.",
         checks="Note affected versions and whether exploitation is reported.", technique="Source review.",
         basis="Generated guidance (limited)", sources=None, framework=[]),
    dict(action="Determine whether the affected technology is in use, and follow the vendor's or other authoritative guidance.",
         rationale="Specific mitigation steps should come from the vendor or advisory, not from a guess.",
         checks="Compare the affected product and versions against your inventory.",
         technique="Authoritative vendor/advisory guidance.", basis="Generated guidance (limited)", sources=None, framework=[]),
]


def condition_for_answer(key, answer):
    if answer == "Not applicable":
        return "not_met", "Marked not applicable by the respondent."
    conditions = QUESTIONS[key]["conditions"]
    return conditions.get(answer, conditions["Unknown"])


def _known_answer(spec, inventory):
    items = [i for i in inventory if spec["capability"] in (i.get("capabilities") or [])]
    for item in items:
        for tag, answer in spec["known"].items():
            if tag in item["capabilities"]:
                return item, answer
    return (items[0] if items else None), None


def _label(source):
    return source.get("source_label") or "Cited source"


def build_guide(technique, inventory, sources):
    by_url = {s["url"]: s for s in sources}
    template = TEMPLATES.get(technique)
    question = None
    steps = []
    for n, t in enumerate(template or GENERIC, start=1):
        if t["sources"] is None:  # generic: link to whatever the finding cites
            links = [{"title": _label(s), "url": s["url"]} for s in sources]
        else:
            links = [{"title": _label(by_url[u]), "url": u} for u in t["sources"] if u in by_url]
        links += t["framework"]
        step = {"position": n, "action": t["action"], "rationale": t["rationale"], "checks": t["checks"],
                "technique": t["technique"], "basis": t["basis"], "links": links,
                "condition": t.get("condition"), "condition_status": None, "condition_note": None}
        if t.get("question"):
            spec = QUESTIONS[t["question"]]
            item, answer = _known_answer(spec, inventory)
            if answer:
                step["condition_status"], step["condition_note"] = condition_for_answer(t["question"], answer)
                step["condition_note"] += " (from organization inventory)"
            else:
                step["condition_status"] = "pending"
                step["condition_note"] = "Awaiting answer to the targeted question."
                if question is None:  # one question at a time
                    question = {"key": t["question"], "step": n, "why": spec["why"], "options": spec["options"],
                                "text": spec["text"].format(item=item["name"] if item else "affected service")}
        steps.append(step)
    label = LABEL if template else LABEL + " - limited guide: Canary has no detailed template for this threat"
    return {"label": label, "steps": steps, "question": question}
