# Data and technical requirements

## Core entities

The initial data model shall include Organization, User, Role, OrganizationProfile, Asset, AIUseCase, Vendor, Incident, IncidentClaim, Source, SharingPolicy, RelevanceDecision, Notification, Assessment, Question, Answer, ActionPlan, ActionItem, Evidence, Comment, Feedback, AuditEvent, and ModelRun.

Each entity shall have a stable identifier, tenant or sharing scope, created/updated timestamps, actor, and lifecycle status. Incidents and recommendations shall be versioned; published versions must remain reproducible.

## Interfaces and integrations

TECH-010. Provide documented REST or GraphQL APIs for organizations, incidents, notifications, assessments, plans, evidence, and audit exports.

TECH-011. Provide webhooks for incident publication, critical notification delivery, plan assignment, overdue items, and corrections.

TECH-012. Design integration boundaries for SIEM, ticketing, identity providers, email, vulnerability feeds, and document repositories. Integrations must be optional and fail without exposing tenant data.

## Reliability and operations

TECH-020. Target 99.9% monthly availability for authenticated product functions, excluding announced maintenance.

TECH-021. Critical approved notifications shall be queued durably and retried with deduplication. No incident should generate duplicate alerts because of a worker retry.

TECH-022. Publish an approved critical notification within 15 minutes of approval under normal load; display progress when source ingestion or AI processing takes longer.

TECH-023. Define initial targets of RPO 24 hours and RTO 8 hours, then tighten them after usage and risk review.

TECH-024. Provide health checks, queue depth, source freshness, model error, notification delivery, authorization-denial, and data-leakage alerts, without logging sensitive content.

TECH-025. Use feature flags for new models, source classes, notification policies, and integrations. Every flag must have an owner and removal date.
