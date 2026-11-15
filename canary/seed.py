"""Demo seed and full reset — CAN-REQ-015/016.

All organizations, people, and inventory below are FICTIONAL demo data.
Demo accounts share the documented local password "demo" (demo-only auth).
"""
import json
from functools import lru_cache

from werkzeug.security import generate_password_hash

from flask import current_app

from .db import audit, init_schema, now_iso
from .fixtures import SOURCE_CATALOG

DEMO_PASSWORD = "demo"

USERS = [
    ("wyatt", "Wyatt", "CTO, Fernwood Labs (fictional)"),
    ("sureh", "Sureh", "Backend engineer, Fernwood Labs (fictional)"),
    ("koewen", "Koewen", "Platform engineer, Fernwood Labs (fictional)"),
    ("priya", "Priya", "IT director, Prairie Valley Medical Center (fictional)"),
]

ORGS = {
    "Fernwood Labs": {
        "industry": "Software", "size": "5 people", "location": "Unknown",
        "interests": "AI coding agents, AI supply chain, LLM APIs, web application security",
        "members": [("wyatt", "admin"), ("sureh", "lead"), ("koewen", "lead")],
        "sources": ["php-net", "thehackernews", "csa", "ghsa", "owasp-genai"],
        "inventory": [
            dict(name="Customer billing portal (PHP-FPM)", category="Web application", product_key="php",
                 version="8.3.30", owner_team="Platform", criticality="Critical", capabilities=["php"],
                 capability_notes="Runtime: PHP 8.3.30 under PHP-FPM; serves customer invoices and payment pages",
                 data_access_notes="Reads customer billing records and the payment provider API key (fictional)"),
            dict(name="AI coding assistant", category="Coding assistant", product_key="ai-coding-assistant",
                 owner_team="Engineering", criticality="High",
                 capabilities=["ai_coding_agent", "auto_install_packages"],
                 capability_notes="Automatic package installation: ON"),
            dict(name="Python runtime agent framework", category="Agent framework", product_key="python-agent-runtime",
                 owner_team="Platform", criticality="Critical", capabilities=["agent_runtime", "python_packages"],
                 capability_notes="Production package-install permission: Unconfirmed",
                 data_access_notes="Runs Ledgerly's bookkeeping agent; can reach customer API keys (fictional)"),
            dict(name="LLM API provider", category="LLM API", product_key="llm-api", owner_team="Engineering",
                 criticality="Critical", capabilities=["llm_api"],
                 data_access_notes="Receives bookkeeping prompts (fictional sample data only)"),
            dict(name="Package sources: PyPI and npm", category="Package registry", product_key="pypi-npm",
                 owner_team="Engineering", criticality="Unknown", capabilities=["package_registry"]),
        ],
        "assessment": {"dep-review": "No", "patch-sla": "No"},
        "routes": [("cybersecurity", "koewen")],
    },
    "Prairie Valley Medical Center": {
        "industry": "Healthcare", "size": "Unknown", "location": "Unknown",
        "interests": "Clinical AI assistants, patient-facing chatbots",
        "members": [("priya", "admin")],
        "sources": ["ghsa", "owasp-genai"],
        "inventory": [
            dict(name="Ambient clinical documentation assistant", category="AI-enabled product (vendor SaaS)",
                 product_key="clinical-scribe", owner_team="Clinical informatics", criticality="High",
                 capabilities=["clinical_scribe", "llm_api"]),
            dict(name="Patient-portal chatbot", category="Chatbot", product_key="portal-chatbot",
                 owner_team="Digital", criticality="Medium", capabilities=["chatbot", "llm_api"]),
        ],
        "assessment": None,
        "routes": [("cybersecurity", "priya")],
    },
}

QUESTIONS = [
    ("patch-sla", "Are critical security patches applied to internet-facing systems within 72 hours?",
     "Attackers often exploit critical flaws within days of a fix being published. A short, agreed patch window "
     "for internet-facing systems closes that gap.",
     "CIS Critical Security Controls v8", "Safeguard 7.4: Perform automated application patch management",
     "https://www.cisecurity.org/controls/continuous-vulnerability-management", "php2shell"),
    ("dep-review", "Are AI-suggested dependencies reviewed before install?",
     "Coding assistants and agents can suggest or install packages. A human or allowlist review before install "
     "blocks hallucinated or malicious package names.",
     "OWASP Top 10 for LLM Applications 2025", "LLM03:2025 Supply Chain",
     "https://genai.owasp.org/llmrisk/llm032025-supply-chain/", None),
    ("agent-permissions", "Are AI agents limited to the minimum tools and permissions they need?",
     "Agents with broad permissions (installing software, running commands, reaching keys) can do more harm "
     "if manipulated.",
     "OWASP Top 10 for LLM Applications 2025", "LLM06:2025 Excessive Agency",
     "https://genai.owasp.org/llmrisk/llm062025-excessive-agency/", None),
    ("untrusted-content", "Is content fetched by AI tools treated as untrusted input?",
     "Web pages, repos, and documents can carry hidden instructions that steer a model (prompt injection).",
     "OWASP Top 10 for LLM Applications 2025", "LLM01:2025 Prompt Injection",
     "https://genai.owasp.org/llmrisk/llm01-prompt-injection/", None),
    ("output-handling", "Is model output validated before it is executed or shown to customers?",
     "Model output passed to shells, databases, or browsers without checks can trigger unintended actions.",
     "OWASP Top 10 for LLM Applications 2025", "LLM05:2025 Improper Output Handling",
     "https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/", None),
]


@lru_cache(maxsize=1)
def _demo_hash():
    return generate_password_hash(DEMO_PASSWORD)


def reset_demo(conn):
    """Delete every record (seeded and user-entered) and restore the seed state."""
    init_schema(conn)
    seed(conn)
    conn.commit()


def seed(conn):
    ts = now_iso()
    user_ids = {}
    for username, name, title in USERS:
        cur = conn.execute("INSERT INTO users (username, display_name, title, password_hash, is_demo)"
                           " VALUES (?,?,?,?,1)", (username, name, title, _demo_hash()))
        user_ids[username] = cur.lastrowid
    source_ids = {}
    for s in SOURCE_CATALOG:
        cur = conn.execute("INSERT INTO source_catalog (key, name, type, url, tier, topics, method)"
                           " VALUES (?,?,?,?,?,?,?)",
                           (s["key"], s["name"], s["type"], s["url"], s["tier"], s["topics"], s["method"]))
        source_ids[s["key"]] = cur.lastrowid
    for q in QUESTIONS:
        conn.execute("INSERT INTO questions (key, text, help, framework, framework_ref, framework_url, technique)"
                     " VALUES (?,?,?,?,?,?,?)", q)
    for org_name, spec in ORGS.items():
        cur = conn.execute("INSERT INTO organizations (name, industry, size, location, monitoring_interests, is_demo,"
                           " created_at, updated_at) VALUES (?,?,?,?,?,1,?,?)",
                           (org_name, spec["industry"], spec["size"], spec["location"], spec["interests"], ts, ts))
        org_id = cur.lastrowid
        for username, role in spec["members"]:
            conn.execute("INSERT INTO memberships (org_id, user_id, role, created_at) VALUES (?,?,?,?)",
                         (org_id, user_ids[username], role, ts))
        for key, sid in source_ids.items():
            conn.execute("INSERT INTO org_sources (org_id, source_id, enabled) VALUES (?,?,?)",
                         (org_id, sid, 1 if key in spec["sources"] else 0))
        for item in spec["inventory"]:
            conn.execute(
                "INSERT INTO inventory_items (org_id, name, category, product_key, version, version_status, owner_team,"
                " criticality, capabilities, capability_notes, data_access_notes, is_demo, updated_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?)",
                (org_id, item["name"], item["category"], item["product_key"], item.get("version"),
                 "known" if item.get("version") else "unknown", item["owner_team"], item["criticality"],
                 json.dumps(item["capabilities"]), item.get("capability_notes"), item.get("data_access_notes"), ts))
        test_addrs = current_app.config.get("TEST_RECIPIENTS") or {}
        for username, _role in spec["members"]:
            if username in test_addrs:  # team-owned test address mapped to a fictional person
                conn.execute("INSERT INTO notification_recipients (org_id, user_id, email, updated_at) VALUES (?,?,?,?)",
                             (org_id, user_ids[username], test_addrs[username], ts))
        for category, username in spec["routes"]:
            conn.execute("INSERT INTO notification_rules (org_id, category, user_id) VALUES (?,?,?)",
                         (org_id, category, user_ids[username]))
        if spec["assessment"]:
            admin = user_ids[spec["members"][0][0]]
            cur = conn.execute("INSERT INTO assessments (org_id, respondent_id, created_at, is_demo, note)"
                               " VALUES (?,?,?,1,?)", (org_id, admin, ts, "Initial assessment (fictional demo context)"))
            for key, answer in spec["assessment"].items():
                conn.execute("INSERT INTO answers (assessment_id, question_key, answer) VALUES (?,?,?)",
                             (cur.lastrowid, key, answer))
        audit(conn, org_id=org_id, actor_id=None, actor_label="System (demo seed)", action="demo.seeded",
              target_type="organization", target_id=org_id, summary=f"Seeded fictional demo organization {org_name}")
