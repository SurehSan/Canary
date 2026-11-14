-- Canary local prototype schema (SQLite). Org-scoped tables carry org_id and
-- every application query filters on the selected organization.
-- Global tables: users, source_catalog, collection_runs, findings,
-- source_items, finding_revisions, questions (central collection, CAN-REQ-004).

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS audit_events;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS notification_rules;
DROP TABLE IF EXISTS notification_recipients;
DROP TABLE IF EXISTS org_settings;
DROP TABLE IF EXISTS answers;
DROP TABLE IF EXISTS assessments;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS relevance;
DROP TABLE IF EXISTS analyses;
DROP TABLE IF EXISTS finding_revisions;
DROP TABLE IF EXISTS source_items;
DROP TABLE IF EXISTS findings;
DROP TABLE IF EXISTS collection_runs;
DROP TABLE IF EXISTS org_sources;
DROP TABLE IF EXISTS source_catalog;
DROP TABLE IF EXISTS inventory_items;
DROP TABLE IF EXISTS memberships;
DROP TABLE IF EXISTS organizations;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    title TEXT,
    password_hash TEXT NOT NULL,
    is_demo INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE organizations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    size TEXT,
    location TEXT,
    monitoring_interests TEXT,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE memberships (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'lead')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    created_at TEXT NOT NULL,
    UNIQUE (org_id, user_id)
);

CREATE TABLE inventory_items (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT,
    product_key TEXT,
    version TEXT,                      -- NULL means Unknown; never a positive match
    version_status TEXT NOT NULL DEFAULT 'unknown' CHECK (version_status IN ('known', 'unknown', 'unconfirmed')),
    owner_team TEXT,
    criticality TEXT NOT NULL DEFAULT 'Unknown' CHECK (criticality IN ('Low', 'Medium', 'High', 'Critical', 'Unknown')),
    capabilities TEXT NOT NULL DEFAULT '[]',   -- JSON list of technology/capability tags
    capability_notes TEXT,
    data_access_notes TEXT,
    is_demo INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE source_catalog (
    id INTEGER PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    url TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('A', 'B', 'C')),
    topics TEXT,
    method TEXT NOT NULL,
    simulate_failure INTEGER NOT NULL DEFAULT 0   -- demo-only outage switch
);

CREATE TABLE org_sources (
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES source_catalog(id) ON DELETE CASCADE,
    enabled INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (org_id, source_id)
);

CREATE TABLE collection_runs (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES source_catalog(id) ON DELETE CASCADE,
    trigger TEXT NOT NULL CHECK (trigger IN ('manual', 'scheduled')),
    adapter TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    outcome TEXT CHECK (outcome IN ('success', 'success_no_new', 'failed', 'skipped')),
    attempts INTEGER NOT NULL DEFAULT 0,
    new_items INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE findings (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    technique TEXT,
    event_type TEXT,
    affected_products TEXT NOT NULL DEFAULT '[]',
    technique_tags TEXT NOT NULL DEFAULT '[]',
    industries TEXT NOT NULL DEFAULT '[]',
    identifiers TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1,
    is_simulated INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE source_items (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES source_catalog(id) ON DELETE SET NULL,
    source_label TEXT NOT NULL,
    tier TEXT NOT NULL,
    url TEXT NOT NULL,
    canonical_url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    published_at TEXT,                 -- NULL means not supplied by source
    retrieved_at TEXT NOT NULL,
    excerpt TEXT,
    source_note TEXT,
    identifiers TEXT NOT NULL DEFAULT '[]',
    technique TEXT,
    finding_id INTEGER REFERENCES findings(id) ON DELETE CASCADE,
    group_status TEXT NOT NULL CHECK (group_status IN ('primary', 'exact', 'proposed', 'confirmed')),
    group_basis TEXT,
    collection_run_id INTEGER REFERENCES collection_runs(id) ON DELETE SET NULL
);

CREATE TABLE finding_revisions (
    id INTEGER PRIMARY KEY,
    finding_id INTEGER NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    change_summary TEXT NOT NULL,
    snapshot TEXT NOT NULL,
    actor_label TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    finding_id INTEGER NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    finding_version INTEGER NOT NULL,
    provider TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE relevance (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    finding_id INTEGER NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    match_state TEXT NOT NULL CHECK (match_state IN ('confirmed', 'possible', 'industry_only', 'no_match')),
    match_evidence TEXT NOT NULL,
    score INTEGER NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('P1', 'P2', 'P3', 'P4')),
    factors TEXT NOT NULL,
    p1_gate_reason TEXT NOT NULL,
    as_of TEXT NOT NULL,
    override_priority TEXT,
    override_match_state TEXT,
    override_reason TEXT,
    override_by INTEGER REFERENCES users(id),
    override_at TEXT,
    UNIQUE (org_id, finding_id)
);

CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    finding_id INTEGER NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'new',
    assignee_id INTEGER REFERENCES users(id),
    category TEXT NOT NULL DEFAULT 'cybersecurity',
    unread INTEGER NOT NULL DEFAULT 1,
    has_update INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (org_id, finding_id)
);

CREATE TABLE questions (
    key TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    help TEXT NOT NULL,
    framework TEXT NOT NULL,
    framework_ref TEXT NOT NULL,
    framework_url TEXT NOT NULL,
    technique TEXT
);

CREATE TABLE assessments (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    respondent_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL,
    is_demo INTEGER NOT NULL DEFAULT 0,
    note TEXT
);

CREATE TABLE answers (
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_key TEXT NOT NULL REFERENCES questions(key),
    answer TEXT NOT NULL CHECK (answer IN ('Yes', 'No', 'Partial', 'Unknown', 'Not applicable')),
    PRIMARY KEY (assessment_id, question_key)
);

CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY,
    org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,   -- NULL = system/global event
    actor_id INTEGER REFERENCES users(id),
    actor_label TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER,
    summary TEXT NOT NULL,
    before_state TEXT,
    after_state TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE org_settings (
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (org_id, key)
);

-- Team-owned test address per member. Sends still require the env allowlist.
CREATE TABLE notification_recipients (
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (org_id, user_id)
);

CREATE TABLE notification_rules (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (org_id, category, user_id)
);

CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    kind TEXT NOT NULL CHECK (kind IN ('new', 'update', 'test')),
    cadence TEXT NOT NULL CHECK (cadence IN ('immediate', 'prompt', 'digest', 'manual')),
    priority TEXT,
    fingerprint TEXT,
    change_summary TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'rejected', 'blocked', 'suppressed')),
    recipient_email TEXT,
    subject TEXT,
    body TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    simulated INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    digest_batch TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sent_at TEXT
);
