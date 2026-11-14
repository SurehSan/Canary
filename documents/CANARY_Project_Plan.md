# CANARY

## "Canary prepares you for the things you can't prepare for."

**Project concept and initial product plan**\
**Status:** Working concept; current deliverable is a local demo prototype\
**Example customer:** Prairie Valley Medical Center (fictional)

**Current prototype direction:** Build a locally run demo in one day that
represents all 16 requirements in `requirements/`, using working local
features or clearly labeled simulations. The coding agent may choose and
document the simplest suitable local technology stack and database/schema.
This is not a hosted MVP or production service. Fernwood
Labs is the primary fictional organization for the hallusquatting walkthrough;
Prairie Valley Medical Center remains an optional fictional example. Prototype
defaults and production limitations are defined in `design/README.md` and in
each requirement's Prototype design decisions section.

------------------------------------------------------------------------

## 1. Product overview

Canary is an AI-specific security alert system and plan generator. It
tracks new vulnerabilities and exploits affecting AI tools, models, and
LLM-powered applications, tells an organization which ones affect its
projects, and walks the team through fixing them.

### The problem

AI tools ship faster than teams can secure them. In February 2026, a
crafted GitHub issue prompt-injected the AI issue-triage bot of the Cline
coding assistant and led to an unauthorized npm release of its CLI
([Cline post-mortem](https://cline.bot/blog/post-mortem-unauthorized-cline-cli-npm),
February 24, 2026). IBM's 2026 *Cost of a Data Breach* study found that
one in four malicious breaches were AI-enabled, a 56% increase over the
previous year
([IBM newsroom](https://newsroom.ibm.com/2026-07-29-ibm-study-one-in-four-malicious-breaches-are-ai-enabled,-costing-companies-6-million-on-average),
July 29, 2026). Small teams, and many larger organizations, have no one
whose job is to track this.

> **Sources checked 2026-11-14 (CAN-REQ-016):** both statements above come
> from primary sources. The earlier "shadow AI in 43% of breaches" figure
> was removed: it appears only in secondary write-ups (which describe it as
> 43% of breached *organizations*, up from 20%), and IBM's public report
> page and press release do not state it. Confirm it in the full IBM report
> before using it. The "4,000 developers" figure for the Cline incident is
> also secondary and is not in Cline's post-mortem.

### What makes Canary different

-   **Curated intake:** a trusted-source list the customer sets by its
    priorities, plus AI filtering and ranking.
-   **Persistent context:** remembers the customer's AI stack, team, and
    past assessments, so alerts are specific to them.
-   **Framework-anchored questionnaire:** maps gaps to a standard (NIST
    AI RMF / OWASP Top 10 for LLM Applications), reweighted by current
    threats.
-   **Guided report:** prioritized mitigations with a short explanation
    of each risk, so the team learns as it fixes.

### The three core responsibilities

1.  **Monitor** --- Find new AI-related vulnerabilities, exploits,
    incidents, and advisories.
2.  **Inform** --- Explain what was discovered, why it may matter to the
    company, and what evidence supports the finding.
3.  **Prepare** --- Help the company create, review, and maintain
    contingency plans and recommended actions.

### Product goal

Help teams that build with or adopt AI tools catch emerging AI threats
early, understand them, and fix them, before they become breaches.

------------------------------------------------------------------------

## 2. Why the name Canary?

The name is inspired by the historical use of canaries in coal mines as
an early-warning signal for dangerous conditions.

Canary serves a similar purpose for organizations: it looks for warning
signs in the outside world and alerts a company when something may
affect it.

**Motto:**\
\> Canary prepares you for the things you can't prepare for.

------------------------------------------------------------------------

## 3. Target customers

Canary serves two kinds of customer:

-   **Small software teams** building with AI (coding assistants, LLM
    APIs, agents, RAG pipelines) that have no dedicated security person.
-   **Larger organizations adopting AI tools**, such as the fictional
    hospital below, where AI is spreading across departments faster than
    security can review it.

### Example: a small team

A fictional five-person startup builds a customer-support chatbot on an
LLM API, uses an AI coding assistant, and runs an open-source agent
framework. Canary records that stack, alerts the team when a
vulnerability affects one of those components, and walks the team
through the fix.

### Example: a hospital

Imagine a fictional hospital called **Prairie Valley Medical Center**
purchases Canary.

During onboarding, the hospital creates a company account and provides
information that helps Canary understand its organization.

Possible company profile information includes:

-   Organization name and industry.
-   Organization size and locations, if relevant.
-   Areas the organization wants to monitor.
-   AI stack inventory: models, LLM APIs, AI-enabled products, agents,
    coding assistants, and AI libraries, where authorized.
-   AI vendors and the data each one can access, where authorized.
-   Existing security policies and contingency plans, if the company
    chooses to provide them.
-   Employees or teams responsible for different types of alerts.

The hospital might select these monitoring areas:

-   AI clinical documentation (ambient scribe) tools.
-   AI features inside the electronic patient record system.
-   Patient-facing chatbots.
-   Shadow AI: unapproved AI tools used by staff.

The purpose is to make alerts relevant. A customer should not receive
every AI alert Canary discovers. It should receive the ones that match
its AI stack and priorities.

### Example AI risk areas by customer

  -----------------------------------------------------------------------
  Customer                            Example AI risks to monitor
  ----------------------------------- -----------------------------------
  Small software team                 Prompt injection, vulnerable AI
                                      coding tools and agent frameworks,
                                      leaked API keys, malicious model
                                      or package uploads

  Hospital                            Patient data leaking through AI
                                      tools, vulnerable AI scribe or EHR
                                      AI features, shadow AI use

  Bank                                LLM chatbot data leakage, AI-driven
                                      fraud, model supply-chain risk
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Main application interface

Canary should have a **simple, easy-to-understand interface**. Users
should be able to find important information and take action without
needing to be AI or cybersecurity specialists.

The initial application could have four main sections:

### 4.1 Dashboard

A high-level overview showing:

-   New and unread alerts.
-   Alerts requiring action.
-   High-priority threats.
-   Recently discovered industry events.
-   Open contingency plans.
-   Monitoring status.

### 4.2 Alerts

A central place to:

-   View new alerts.
-   Filter by priority, category, date, or status.
-   Read a short explanation.
-   Open the original source.
-   Assign an alert to a responsible team member.
-   Track investigation and remediation status.

### 4.3 Threat Intelligence

A more detailed view of external events and vulnerabilities, including:

-   What happened or was disclosed.
-   When it was published and when it was discovered.
-   Which industries or technologies may be affected.
-   Why the information may be relevant to this company.
-   What is known, unknown, and not yet verified.
-   Original source links and supporting evidence.

### 4.4 Contingency Plans

A place to:

-   Generate a proposed plan from a threat or scenario.
-   View and edit existing plans.
-   Assign owners and responsibilities.
-   Record approvals.
-   Track review dates and exercises.
-   Keep a history of plan updates.

------------------------------------------------------------------------

## 5. Notification and alert system

Notifications are one of Canary's most important features. The system
should make important information visible without overwhelming
employees.

A useful starting point is a four-level priority system.

  -----------------------------------------------------------------------
  Priority          Meaning           Example           Suggested
                                                        delivery
  ----------------- ----------------- ----------------- -----------------
  **P1 ---          Credible, urgent  A vulnerability   Immediate
  Critical**        threat with a     is actively       notification to
                    strong potential  exploited and the designated
                    connection to a   company's         responders
                    critical company  inventory         
                    system or         indicates a       
                    operation         potentially       
                                      affected critical 
                                      system            

  **P2 --- High**   Serious threat    A serious         Prompt
                    that may affect   vulnerability     notification and
                    the organization, affects a product assigned review
                    but exposure or   the company may   
                    urgency needs     use               
                    confirmation                        

  **P3 --- Medium** Relevant industry Another hospital  Daily digest
                    event or emerging experiences a
                    risk that         significant       
                    deserves          outage with       
                    investigation or  lessons relevant  
                    preparation       to the customer's 
                                      operations        

  **P4 ---          General industry  A daily summary   Daily digest
  Informational**   news, trends, and of healthcare     dashboard update
                    educational       cybersecurity     
                    information       developments      
  -----------------------------------------------------------------------

Priority should be based on more than a headline. Canary should consider
factors such as:

-   Severity of the issue.
-   Whether exploitation or real-world impact has been reported.
-   Whether the company appears to use an affected product or service.
-   Importance of the affected system to the company.
-   Reliability and recency of the sources.
-   Whether the information is new or a duplicate of an existing alert.

A priority label is a triage recommendation, not proof that the company
is affected.

### Search frequency versus notification frequency

These should be separate settings.

Canary may check important sources frequently but only notify employees
when a finding meets the organization's notification rules.

Current local prototype settings:

  -----------------------------------------------------------------------
  Activity                            Example starting frequency
  ----------------------------------- -----------------------------------
  Check enabled sources              Hourly local schedule, plus manual
                                      refresh; no real-time guarantee

  Reassess an open threat             On meaningful new information

  Send P1 notification                Immediately

  Send P2 notification                Next local processing cycle

  Send P3/P4 digest                   Daily
  -----------------------------------------------------------------------

These are demo settings, not guarantees of real-time discovery. Actual
collection depends on source update rates, available APIs, rate limits, and
the local application being available.

### Prototype email delivery

The local prototype sends real test emails through a team-configured
SMTP-compatible provider. It sends only to an explicit allowlist of
team-owned test email addresses; all other recipients are rejected. Every
subject includes **[CANARY DEMO - TEST]**, and each message states that it is a
demo notification, not evidence of a real incident. Provider credentials are
kept in local environment secrets. The application has no production-send
mode, does not silently fall back to a mock mailbox, and records delivery
success or failure. Collection cadence remains separate from notification
cadence.

### Notification recipients

Not every employee needs every alert. Companies should be able to assign
recipients and escalation rules.

The roles below describe the broader product concept. The local demo
prototype implements only Administrator and Cybersecurity Lead, as specified
in CAN-REQ-001.

  Team or role             Example notifications
  ------------------------ ---------------------------------------------
  IT security              Cybersecurity vulnerabilities and incidents
  Safety team              Operational and safety risks
  Medical equipment team   Equipment recalls and device safety notices
  Executive leadership     Critical organization-wide risks
  Emergency management     Infrastructure and disaster-related threats

The company should control who receives alerts, how they are escalated,
and which categories each team monitors.

------------------------------------------------------------------------

## 6. Contingency plan creation: the core workflow

When Canary discovers a potentially important threat, it should help the
company understand what happened, why it matters, and what actions may
be appropriate.

### Hospital example: a vulnerability in an AI tool connected to patient records

**Scenario:** Canary discovers a new security advisory (for example, a
prompt-injection flaw) for an AI documentation assistant that
integrates with electronic patient records.

#### Step 1 --- Collect the information

Canary retrieves the advisory and supporting information from reliable
sources. It records the original source, publication date, affected
product and versions, severity information, and any known exploitation
details.

#### Step 2 --- Determine relevance

Canary compares the advisory with the hospital's industry, monitoring
preferences, and any authorized software inventory.

It asks:

-   Does this affect healthcare organizations?
-   Does it affect a product or version the hospital uses?
-   Is exploitation known to be occurring?
-   What systems or operations could be affected?
-   What evidence supports the connection?

If the hospital does not use the affected product, Canary should not
present the finding as a confirmed exposure.

#### Step 3 --- Explain the finding

The alert should clearly explain:

-   **What happened:** A software vulnerability or security issue was
    disclosed.
-   **Why it may matter:** The hospital may use an affected product.
-   **Potential consequences:** Unauthorized access, disruption, or
    exposure of patient information, depending on the vulnerability.
-   **What is known:** Facts supported by the sources.
-   **What remains uncertain:** Whether the hospital is exposed or has
    been compromised.
-   **What to do next:** Verify product versions and follow the vendor's
    recommended guidance.

#### Step 4 --- Generate a guided report and contingency plan

The user selects **Create Plan**. Canary drafts a **guided report**:
prioritized mitigations, each paired with a short plain-language
explanation of the risk it addresses, so the team learns as it fixes.
For larger organizations, the report expands into a staged contingency
plan such as:

**Plan: Electronic Medical Record System Compromise**

  -----------------------------------------------------------------------
  Stage                               Example action
  ----------------------------------- -----------------------------------
  Preparation                         Document approved downtime
                                      procedures and responsibilities

  Detection                           Identify indicators of unauthorized
                                      access or system compromise

  Response                            Activate the hospital's approved
                                      cybersecurity response process

  Continuity                          Maintain patient care using
                                      approved alternative procedures

  Recovery                            Restore verified systems and
                                      validate data integrity

  Review                              Document lessons learned and update
                                      the plan
  -----------------------------------------------------------------------

The hospital's authorized personnel review, edit, approve, and assign
the plan. Canary should not independently make clinical decisions or
take high-impact actions on hospital systems.

#### Step 5 --- Track the issue

The alert remains trackable until the organization records an outcome,
such as:

-   Under investigation.
-   Exposure confirmed.
-   Mitigation in progress.
-   Resolved and verified.
-   Not applicable.
-   Risk formally accepted by an authorized person.

Canary should preserve a record of what was discovered, what evidence
was available, who reviewed it, and what actions were taken.

------------------------------------------------------------------------

## 7. Continuous external monitoring

Canary's monitoring system can be understood as three stages.

### Stage 1 --- Information collection

Collect information from a **trusted-source list that each customer
sets by its priorities**. Canary provides a recommended default list;
customers can add, remove, or reweight sources.

**AI vulnerabilities and exploits** - NIST National Vulnerability
Database and CISA Known Exploited Vulnerabilities Catalog (filtered to
AI products and libraries). - GitHub Security Advisories for AI
packages. - AI vendor security advisories (model providers, AI coding
tools, agent frameworks). - OWASP GenAI Security Project. - MITRE ATLAS.

**AI incidents and research** - AI Incident Database. - Trusted
security research organizations and AI-security researchers. - Public
incident reports and post-incident analyses. - Reputable news sources.

**Sector guidance (where relevant)** - HHS and FDA guidance on AI in
healthcare. - Government AI security advisories.

### Stage 2 --- AI analysis and filtering

The AI should:

1.  Identify the type of event or vulnerability.
2.  Extract important facts and affected products or industries.
3.  Verify information against original or authoritative sources where
    possible.
4.  Identify duplicate reports.
5.  Compare findings against company profile information and authorized
    inventories.
6.  Estimate relevance and priority.
7.  Explain uncertainty and identify what requires human verification.

### Stage 3 --- Company notification

Canary provides the relevant company with:

-   A concise alert.
-   A plain-language explanation.
-   Priority and relevance.
-   Evidence and source links.
-   Recommended next steps.
-   An option to create a contingency plan.

### Legal and responsible information collection

Canary should not depend on indiscriminate scraping of the internet.

Prefer official APIs, RSS feeds, public advisories, and web sources
whose terms permit the intended use. Respect website terms, copyright,
robots.txt where applicable, API rate limits, privacy laws, and access
restrictions.

Store factual findings, metadata, and source links where possible
instead of copying entire articles. Do not bypass paywalls,
authentication, or technical access controls. Keep source attribution
and publication dates.

------------------------------------------------------------------------

## 7a. Framework-anchored security questionnaire

During onboarding, and again periodically, Canary asks the team a short
questionnaire about how it builds and uses AI. Examples: Do you validate
LLM output before it reaches other systems? Who can install AI tools?
Are API keys rotated?

For the local prototype, use a concise question set pinned to the OWASP Top
10 for LLM Applications (2025 edition), including the demo's LLM03 Supply
Chain question. This is not a complete framework assessment; see
CAN-REQ-010 for prototype answer choices and scoring boundaries.

-   Questions map to a standard: the **NIST AI Risk Management
    Framework** and the **OWASP Top 10 for LLM Applications**.
-   Question weights are **reweighted by current threats**: if Canary
    is seeing a wave of prompt-injection exploits, related gaps rise in
    priority.
-   Answers are saved as part of the customer's persistent context, so
    future alerts and reports account for known gaps and past
    assessments.
-   Results feed the guided report: each gap becomes a prioritized
    mitigation with a short explanation.

------------------------------------------------------------------------

## 8. Company accounts and permissions

Canary is intended for organizations, so the account structure should
support a company workspace with multiple employees. For the local demo,
authentication uses seeded local accounts and is not production-grade.

### Broader product role concepts

  Role                    Example permissions
  ----------------------- -----------------------------------------------------
  Company administrator   Manage company settings, users, and access
  Safety team             Review relevant alerts and manage contingency plans
  Cybersecurity team      Investigate and manage cyber-related alerts
  Executive               View organization-wide risks and reports
  Employee                View assigned information and report incidents

### Local prototype account behavior

-   Local demo accounts with Administrator and Cybersecurity Lead roles only.
-   Simulated invitations using seeded accounts; no invitation email.
-   Organization-scoped role-based access and data isolation.
-   SSO, MFA, and production account recovery are outside prototype scope.

Each company's information must remain isolated from other customers.
Internal documents, asset inventories, and company-specific findings
must not be exposed to other organizations.

For real hospital use, the product would need appropriate security,
privacy, contractual, and regulatory safeguards. Any handling of
protected health information would require a carefully designed
compliance approach, including applicable HIPAA obligations.

------------------------------------------------------------------------

## 9. Suggested technology stack

The following is a possible stack for an initial implementation. The
team can adjust it based on experience and project requirements.

  -----------------------------------------------------------------------
  Component               Suggested technology    Purpose
  ----------------------- ----------------------- -----------------------
  Frontend                React / Next.js         User interface and
                                                  dashboard

  Backend                 Python / FastAPI        Application logic and
                                                  API

  Database                PostgreSQL              Company accounts,
                                                  alerts, and plans

  AI model                LLM API                 Summaries, analysis,
                                                  and plan drafts

  Document retrieval      RAG                     Retrieve relevant
                                                  company documents

  External information    APIs / RSS / permitted  Gather advisories and
                          sources                 reports

  Background jobs         Celery / Redis or       Scheduled monitoring
                          equivalent              and processing

  Authentication          Auth0 or equivalent     Company login and
                                                  identity management

  Notifications           Email service           Send alerts and digests
  -----------------------------------------------------------------------

The first version does not need a custom-trained AI model. An existing
language model can be used while the team builds the product's core
workflow around company context, source-backed intelligence, relevance
filtering, and contingency planning.

------------------------------------------------------------------------

## 10. Local demo prototype

The current deliverable is a locally run demo prototype, not a hosted MVP or
production service. It must represent every requirement CAN-REQ-001 through
CAN-REQ-016, using working local features or conspicuously labeled
simulations. The design overview and individual requirement decisions define
the exact behavior and boundaries.

### Prototype implementation sequence

1. Establish local startup/reset, demo accounts and roles, organization
   isolation, data model, and secret handling.
2. Implement organization profiles/inventory, source configuration, local
   collection, finding normalization, evidence, and deduplication.
3. Implement analysis with uncertainty, explainable match/priority, and the
   framework-mapped questionnaire.
4. Implement alert investigation, targeted guides, contingency plan review
   and approval, dashboard, and audit history.
5. Configure real test email delivery to an explicit team-owned address
   allowlist. Include conspicuous test labels, delivery outcomes, and rejection
   of every non-allowlisted address.
6. Walk through all 16 requirements and show each on a screen, in a saved
   record, or as a clearly labeled simulation.

### Primary demonstration

Use fictional Fernwood Labs and the hallusquatting flow in
`documents/hallusquatting-demo-flow.md`. The flow covers organization setup,
two Cybersecurity Leads, inventory and questionnaire context, source status
and collection, deduplication, evidence and uncertainty, a P2 Possible match,
real test email, alert triage, a targeted guide, human-approved plan, audit
history, and safe reset. The email goes only to a preconfigured team-owned
test inbox and is not a production alert.

Prairie Valley Medical Center remains an optional fictional organization for
showing a different industry context. All fictional assets and simulated
events must be labeled. Do not imply that fictional data or simulated
vulnerabilities are real, or that the prototype provides production security
or regulatory compliance.

------------------------------------------------------------------------

## 11. Important design principles

These principles should guide the project as it develops.

### Keep the interface simple

Users should be able to understand an alert quickly and find the next
action without navigating complicated menus.

### Make every important finding traceable

Show original sources, publication dates, evidence, and the reason a
finding was considered relevant.

### Separate facts from assumptions

Clearly distinguish confirmed facts, potential exposure, unverified
reports, and hypothetical risks.

### Avoid alert fatigue

Use deduplication, relevance filtering, priority levels, configurable
notifications, and digest summaries.

### Keep people in control

AI-generated plans are drafts and recommendations. Authorized personnel
must review and approve actions, especially in safety-critical
environments.

### Protect company information

Use strong authentication, access controls, encryption, tenant
isolation, and appropriate data retention policies.

### Learn from incidents

When new information becomes available, Canary should be able to update
an existing alert or plan and explain what changed.

------------------------------------------------------------------------

## 12. Product summary

**Canary is an AI-specific security alert system and plan generator.**

It tracks new AI vulnerabilities and exploits from sources the customer
trusts, tells the team which ones affect its projects, maps its gaps to
NIST AI RMF and the OWASP LLM Top 10, and walks the team through fixing
them with a guided report.

Its purpose is not to claim that every crisis can be predicted. Its
purpose is to help organizations recognize warning signs, learn from
events elsewhere, and become better prepared for unexpected situations.

> **Canary prepares you for the things you can't prepare for.**
