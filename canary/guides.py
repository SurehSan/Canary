"""Targeted threat guides — CAN-REQ-011.

Deterministic templates keyed by technique, checked against the
hallusquatting demo. Links are limited to the finding's own sources plus
framework guidance. At most one targeted clarification is asked, and only when
the organization's inventory does not already answer it.
"""
from .analysis import CSA_URL, THN_URL, XYGENI_URL

LABEL = "AI-generated draft for human review (demo template; no actions are executed)"
OWASP_LLM03 = {"title": "OWASP LLM03:2025 Supply Chain", "url": "https://genai.owasp.org/llmrisk/llm032025-supply-chain/"}
OWASP_LLM06 = {"title": "OWASP LLM06:2025 Excessive Agency", "url": "https://genai.owasp.org/llmrisk/llm062025-excessive-agency/"}

TEMPLATES = {
    "package-hallucination-squatting": [
        dict(action="Review recent lockfile and package-manager changes for unfamiliar or suspicious dependencies.",
             rationale="An agent that installed a hallucinated or attacker-registered package would leave a trace in "
                       "lockfiles and install history.",
             checks="Diff lockfiles over the last 90 days; list packages added by AI tools; check each new package's "
                    "registry publisher and first-publish date.",
             technique="Dependency review against the registry (publisher identity, package age, download history).",
             basis="Generated guidance based on source-supported technique", sources=[CSA_URL, THN_URL], framework=[OWASP_LLM03]),
        dict(action="Turn off automatic package installation for coding agents and require human approval for new dependencies.",
             rationale="Auto-install lets a hallucinated name become installed code without anyone seeing it.",
             checks="Confirm the coding assistant's auto-run / auto-install setting is off for every developer.",
             technique="Human-in-the-loop approval for package installs; avoid skip-confirmation modes.",
             basis="Organization context: inventory records auto-install ON", sources=[THN_URL], framework=[OWASP_LLM06]),
        dict(action="Pin and allowlist dependencies, for example through a lockfile and an approved internal mirror.",
             rationale="Pinned, allowlisted dependencies stop new unreviewed names from resolving.",
             checks="CI fails on unpinned or unlisted packages; hash verification is enabled.",
             technique="Lockfile pinning, hash checking, internal package mirror/allowlist.",
             basis="Generated guidance based on source-supported mitigation", sources=[CSA_URL], framework=[OWASP_LLM03]),
        dict(action="Check whether the runtime agent can install packages in production; if it can, restrict that "
                    "permission and isolate the agent from customer keys.",
             rationale="A runtime agent that can install packages could pull attacker code next to production secrets.",
             checks="Review the runtime's IAM/container permissions and network egress to package registries.",
             technique="Least-privilege runtime: read-only filesystem/no installer, egress restrictions, secret isolation.",
             basis="Generated guidance; depends on an organization fact that is not yet known",
             sources=[THN_URL], framework=[OWASP_LLM06],
             condition="Applies as an immediate action only if the runtime agent can install packages in production.",
             question="install_permission"),
        dict(action="Rotate credentials only if the investigation finds evidence they may have been exposed.",
             rationale="Rotation has a cost; no evidence currently ties a malicious package to this organization.",
             checks="Trigger only if steps 1 or 4 find a suspicious package or install permission with key access.",
             technique="Evidence-based credential rotation.",
             basis="Generated guidance; conditional on investigation findings", sources=[XYGENI_URL, THN_URL],
             framework=[OWASP_LLM03]),
    ],
}

QUESTIONS = {
    "install_permission": {
        "capability": "agent_runtime",
        "known": {"install_permission_yes": "Yes", "install_permission_no": "No"},
        "text": "Does the {item} have permission to install packages in production?",
        "why": "This determines whether step 4 is an immediate action or a precaution to evaluate.",
        "options": ["Yes", "No", "Unknown"],
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


def condition_for_answer(answer):
    if answer == "Yes":
        return "met", "Immediate action: the runtime agent can install packages in production."
    if answer == "No":
        return "not_met", "Precaution only: the respondent reports the runtime agent cannot install packages in production."
    if answer == "Not applicable":
        return "not_met", "Marked not applicable by the respondent."
    return "pending", "Conditional: install permission is Unknown. Verify before acting; do not assume either way."


def _known_answer(spec, inventory):
    items = [i for i in inventory if spec["capability"] in (i.get("capabilities") or [])]
    for item in items:
        for tag, answer in spec["known"].items():
            if tag in item["capabilities"]:
                return item, answer
    return (items[0] if items else None), None


def build_guide(technique, inventory, sources):
    by_url = {s["url"]: s for s in sources}
    template = TEMPLATES.get(technique)
    question = None
    steps = []
    for n, t in enumerate(template or GENERIC, start=1):
        if t["sources"] is None:  # generic: link to whatever the finding cites
            links = [{"title": "Cited source", "url": s["url"]} for s in sources]
        else:
            links = [{"title": "Cited source", "url": u} for u in t["sources"] if u in by_url]
        links += t["framework"]
        step = {"position": n, "action": t["action"], "rationale": t["rationale"], "checks": t["checks"],
                "technique": t["technique"], "basis": t["basis"], "links": links,
                "condition": t.get("condition"), "condition_status": None, "condition_note": None}
        if t.get("question"):
            spec = QUESTIONS[t["question"]]
            item, answer = _known_answer(spec, inventory)
            if answer:
                step["condition_status"], step["condition_note"] = condition_for_answer(answer)
                step["condition_note"] += " (from organization inventory)"
            else:
                step["condition_status"] = "pending"
                step["condition_note"] = "Awaiting answer to the targeted question."
                if question is None:  # one question at a time
                    question = {"key": t["question"], "step": n, "why": spec["why"], "options": spec["options"],
                                "text": spec["text"].format(item=item["name"] if item else "runtime agent")}
        steps.append(step)
    label = LABEL if template else LABEL + " - limited guide: Canary has no detailed template for this threat"
    return {"label": label, "steps": steps, "question": question}
