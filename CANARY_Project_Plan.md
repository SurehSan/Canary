# CANARY

## "Canary prepares you for the things you can't prepare for."

**Project concept and initial product plan**\
**Status:** Working concept / team discussion document\
**Example customer:** Prairie Valley Medical Center (fictional)

------------------------------------------------------------------------

## 1. Product overview

Canary is an AI-powered risk intelligence and contingency-planning
platform designed to help organizations identify, understand, and
prepare for emerging threats.

Organizations cannot predict or prepare in advance for every possible
event. New technologies, changing attack methods, unexpected failures,
and events at other organizations can create risks that were not
previously considered. Advances in AI may accelerate how quickly these
risks emerge and evolve.

Canary helps close that preparedness gap by continuously gathering
information from reliable external sources, identifying threats that may
be relevant to a particular organization, explaining why they matter,
and helping the organization develop a plan of action.

### The three core responsibilities

1.  **Monitor** --- Find new vulnerabilities, incidents, advisories, and
    industry developments.
2.  **Inform** --- Explain what was discovered, why it may matter to the
    company, and what evidence supports the finding.
3.  **Prepare** --- Help the company create, review, and maintain
    contingency plans and recommended actions.

### Product goal

Help organizations become more resilient by identifying emerging
threats, educating decision-makers, and preparing actionable contingency
plans before unexpected events become major problems.

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

## 3. Example customer: a hospital

Imagine a fictional hospital called **Prairie Valley Medical Center**
purchases Canary.

During onboarding, the hospital creates a company account and provides
information that helps Canary understand its organization.

Possible company profile information includes:

-   Organization name and industry.
-   Organization size and locations, if relevant.
-   Areas the organization wants to monitor.
-   Software, hardware, and equipment inventory, where authorized.
-   Suppliers and important operational dependencies, where authorized.
-   Existing security policies and contingency plans, if the company
    chooses to provide them.
-   Employees or teams responsible for different types of alerts.

The hospital might select these monitoring areas:

-   Cybersecurity.
-   Electronic patient records.
-   Medical equipment and device safety.
-   Hospital infrastructure.
-   Supply chain and critical vendors.

The purpose is to make alerts relevant. A hospital should not receive
every alert that Canary discovers. It should receive information that is
relevant to healthcare organizations and, where the hospital has
supplied an inventory, potentially relevant to its own systems and
operations.

### Example industry relevance

  -----------------------------------------------------------------------
  Organization type                   Example areas to monitor
  ----------------------------------- -----------------------------------
  Hospital                            Patient-record software
                                      vulnerabilities, ransomware,
                                      medical device recalls, supply
                                      disruptions

  Nuclear power plant                 Industrial control system
                                      vulnerabilities, infrastructure
                                      threats, safety advisories

  Bank                                Financial fraud, data breaches,
                                      banking system vulnerabilities

  Manufacturer                        Industrial equipment failures,
                                      supply chain disruption,
                                      operational technology security

  Technology company                  Software vulnerabilities, cloud
                                      security, data breaches
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

  **P3 --- Medium** Relevant industry Another hospital  Daily or
                    event or emerging experiences a     scheduled digest
                    risk that         significant       
                    deserves          outage with       
                    investigation or  lessons relevant  
                    preparation       to the customer's 
                                      operations        

  **P4 ---          General industry  A weekly summary  Weekly digest or
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

Possible initial settings for a prototype:

  -----------------------------------------------------------------------
  Activity                            Example starting frequency
  ----------------------------------- -----------------------------------
  Check high-priority security feeds  Every 15--30 minutes, subject to
                                      source limits

  Check general industry sources      Every 1--3 hours

  Reassess an open threat             When meaningful new information
                                      arrives

  Send informational digest           Weekly

  Review unresolved alerts            Daily
  -----------------------------------------------------------------------

These are proposed settings, not guarantees of real-time discovery.
Actual frequency depends on source update rates, available APIs, rate
limits, and operating costs.

### Notification recipients

Not every employee needs every alert. Companies should be able to assign
recipients and escalation rules.

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

### Hospital example: a vulnerability affecting electronic patient records

**Scenario:** Canary discovers a new security advisory for a software
product used by healthcare organizations.

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

#### Step 4 --- Generate a proposed contingency plan

The user selects **Create Plan**. Canary drafts a plan such as:

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

Collect information from permitted, reliable sources, such as:

**Cybersecurity** - CISA advisories and the Known Exploited
Vulnerabilities Catalog. - NIST National Vulnerability Database. -
Vendor security advisories. - Relevant government cybersecurity
advisories. - Trusted cybersecurity research organizations.

**Healthcare and safety** - HHS cybersecurity and healthcare guidance. -
FDA medical device safety communications and recalls. - Manufacturer
notices. - Relevant public health and infrastructure advisories.

**Industry and organizational events** - Reputable news sources. -
Public incident reports. - Industry publications. - Research reports and
post-incident analyses.

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

## 8. Company accounts and permissions

Canary is intended for organizations, so the account structure should
support a company workspace with multiple employees.

### Suggested roles

  Role                    Example permissions
  ----------------------- -----------------------------------------------------
  Company administrator   Manage company settings, users, and access
  Safety team             Review relevant alerts and manage contingency plans
  Cybersecurity team      Investigate and manage cyber-related alerts
  Executive               View organization-wide risks and reports
  Employee                View assigned information and report incidents

### Login and account features

-   Email and password login.
-   Company creation and invitation system.
-   Optional company single sign-on (SSO).
-   Multi-factor authentication.
-   Role-based access control.
-   Separate company workspaces and data.

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

## 10. Proposed minimum viable product (MVP)

The first version should demonstrate the central Canary workflow without
attempting to become a complete enterprise security platform.

### MVP development order

1.  **Company registration and login**
    -   Create company accounts.
    -   Select an industry.
    -   Add company details.
    -   Configure monitoring preferences.
2.  **Simple dashboard**
    -   Display recent threats.
    -   Show priority levels.
    -   Show unread alerts.
    -   Display saved contingency plans.
3.  **External information collection**
    -   Connect to a small number of public cybersecurity sources.
    -   Retrieve new advisories and incidents.
    -   Summarize findings with AI.
    -   Preserve original source links and dates.
4.  **Industry-specific filtering**
    -   Identify affected industries and products.
    -   Compare findings against company interests and supplied
        inventory.
    -   Filter irrelevant information.
    -   Prioritize findings for review.
5.  **Contingency plan generation**
    -   Let users select a finding or enter a scenario.
    -   Generate a proposed plan.
    -   Allow editing and approval.
    -   Save plans for future reference.
6.  **Notification system**
    -   Send email notifications.
    -   Implement priority-based alerts.
    -   Provide daily or weekly summaries.

### Suggested initial demonstration

Use the fictional Prairie Valley Medical Center as the test
organization.

Demonstrate this sequence:

1.  The hospital creates a Canary account and selects healthcare as its
    industry.
2.  The hospital selects cybersecurity and patient-record systems as
    monitoring interests.
3.  Canary retrieves a sample or real public security advisory.
4.  The AI summarizes the advisory and explains why it may matter to the
    hospital.
5.  The hospital receives an alert with a priority and source links.
6.  A user requests a contingency plan.
7.  Canary generates a draft plan.
8.  An authorized hospital employee reviews and approves or edits it.
9.  The alert and plan remain available in the dashboard.

For a prototype, use simulated company inventories and clearly label any
fictional incidents or findings. Do not imply that a simulated
vulnerability is real.

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

**Canary is an AI-powered risk intelligence and contingency-planning
platform.**

It monitors external information, identifies emerging threats relevant
to a particular organization, explains why those threats matter, and
helps the organization prepare an actionable response.

Its purpose is not to claim that every crisis can be predicted. Its
purpose is to help organizations recognize warning signs, learn from
events elsewhere, and become better prepared for unexpected situations.

> **Canary prepares you for the things you can't prepare for.**
