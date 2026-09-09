## DENTAL LEAD MANAGEMENT CRM + AI PLATFORM

Full-Stack Rebuild, Public Website, Interactive UI and AI

Automation Roadmap

## MANDATORY PRODUCTION STACK

| Next.js 16.2 | React 19.2 | TypeScript 6.0 |
| --- | --- | --- |
| Supabase | Vercel + Node 24 LTS | Tailwind CSS 4.3 |

Prepared for lead generation, business continuity, intelligent automation and production

deployment

10 July 2026


## Document Control

## How to read and use this specification

| Item | Definition |
| --- | --- |
| Document purpose | Define the complete scope for rebuilding the dental CRM from scratch, including a public |
|   | conversion website, highly interactive dashboard and AI automation layer. |
| Primary outcome | A secure, company-owned platform covering public lead generation, CRM operations, AI-assisted |
|   | workflows and analytics, deployed to company-managed Supabase, Vercel and GitHub accounts. |
| Scope basis | Job description, stated workflows and a full-featured implementation assumption. Existing |
|   | screenshots must be mapped during discovery. |
| Delivery model | Phased implementation with staging, user acceptance testing, data migration and documented |
|   | handover. |
| Version rule | Use the latest stable compatible patch/minor versions at project start. Avoid canary, beta and |
|   | experimental dependencies in production. |
| Status | Client discussion draft. Final scope becomes contractual after discovery and screen-by-screen |
|   | sign-off. |

## Important estimation rule

A reliable fixed estimate requires access to the existing dashboard, workflows, database export, report formulas and all integrations. Without these, the estimate must include a discovery allowance and risk contingency.

## Contents

- 01 Executive Summary

- 02 Business Goals and Success Measures

- 03 Users, Roles and Permissions

- 04 End-to-End Workflows

- 05 Functional Modules

- 05A Public Website and Landing Experience

- 05B Interactive Dashboard UX

- 05C AI Automation and Copilot

- 06 Screens and Navigation

- 07 Data Model and Database Design

- 08 Mandatory Technology Stack

- 09 Application Architecture

- 10 Supabase Security and RLS

- 11 Integrations and Automation

- 12 Reporting and Analytics

- 13 Data Migration

- 14 DevOps and Environments

- 15 Security, Privacy and Reliability

- 16 Testing and Acceptance

- 17 Delivery Phases and Timeline

- 18 Effort, Team and Cost Model


- 19 Client Inputs and Access

- 20 Risks, Assumptions and Exclusions

- 21 Handover and Documentation

- Appendices

## SECTION 01

## Executive Summary

## What the client is asking to rebuild

The project is a full-stack reconstruction of an internally developed dental lead management and performance dashboard. The new system must preserve the essential workflows of the existing platform while removing dependency on the current developer or environment.

The result will be a multi-clinic, role-based CRM plus a public conversion website and AI-assisted operations layer. It will manage lead acquisition, appointments, calls, follow-ups, users, clinic access, revenue, performance reporting and approved automation. It will be developed using the latest stable Next.js and Supabase stack and deployed inside company-owned technical accounts.

## This is not a UI-only clone

The system includes a public landing website, highly interactive frontend application, database architecture, authentication, permissions, Row Level Security, AI orchestration, reporting logic, integrations, migration, deployment, testing and handover.

## Required business outcomes

- Business continuity: The company can operate even if the existing system or original developer is unavailable.

- Company ownership: Source code, database, deployments, keys and documentation remain under company- managed accounts.

- Workflow parity: Core lead, appointment, call and revenue workflows match the existing operational process.

- Secure access: Each user sees only the organizations, clinics and records permitted for their role.

- Reliable reporting: KPIs and revenue calculations are clearly defined, testable and reproducible.

- Lead generation: The public website converts campaign and organic traffic into qualified, attributed CRM leads.

- Intelligent assistance: AI reduces repetitive work while keeping users in control of messages and operational decisions.

- Maintainability: A new developer can understand, deploy and extend the system using the handover documents.

## Recommended delivery scope

| Delivery area | Included |
| --- | --- |
| Public experience | Conversion landing page, treatment discovery, clinic finder, consultation booking, SEO and CRM- |
|   | connected lead forms |
| Product | Lead CRM, appointments, calls, tasks, patients, treatments, revenue, interactive dashboards and |
|   | reports |
| AI and automation | Lead intelligence, communication drafting, summaries, next-best actions, semantic search and |
|   | management insights |
| Platform | Authentication, multi-clinic tenancy, role permissions, RLS, storage, audit logs and integrations |
| Delivery | GitHub repository, CI checks, staging, production, migration, QA, documentation and training |
| Operations | Monitoring, backups, logs, environment management and incident-ready handover |


## Business Goals and Success Measures

## Primary goals

- 1. Recreate the current platform workflows in a stable and maintainable codebase.

- 2. Centralize lead management across multiple dental clinics and teams.

- 3. Improve follow-up discipline through tasks, reminders and activity history.

- 4. Measure lead-to-appointment, appointment-to-treatment and lead-to-revenue conversion.

- 5. Protect patient and business data through database-level access controls.

- 6. Launch a high-converting public website that creates correctly attributed leads and appointments.

- 7. Use controlled AI automation to improve response speed, prioritization and management visibility.

- 8. Deploy a company-owned system with documentation and predictable supportability.

## Success measures

| Area | Minimum success criterion |
| --- | --- |
| Workflow parity | All agreed existing workflows pass client user-acceptance tests. |
| Access control | Cross-clinic and cross-role access tests show no unauthorized data exposure. |
| Performance | Core list pages are paginated and responsive at the expected lead volume. |
| Reporting | Approved KPI samples reconcile with manually calculated reference values. |
| Reliability | Staging and production deploy from GitHub with documented rollback steps. |
| Website conversion | Forms, quiz and bookings create attributed CRM records without duplication. |
| Interactive UX | Core workflows remain fast and usable through drill-downs, drawers, keyboard actions and |
|   | responsive layouts. |
| AI quality | Approved AI outputs meet defined accuracy, source, privacy, latency and human-review |
|   | requirements. |
| Handover | Client receives architecture, schema, deployment, AI operations, admin and user documentation. |


## Users, Roles and Permissions

## Role-based access with organization and clinic boundaries

## Permission Model at a Glance

| Scope | Clinic Manager ~~ Agent |   |
| --- | --- | --- |
| Super Admi | Org Admi | Finance |
| Organizations |   |   |
| Al | oun View |   |
| Clinics |   |   |
| Al | Manage Own cinic | View Own cinic View |
| Leads Al | Allorg Own | Assigned Basic Limited |
| Appointments |   |   |
| Al | Allorg own cinic | Assigned Manage View |
| Revenue |   |   |
| Al | Alorg Own | Manage own |
| Users |   | Self |
| Al | Manage Cinic team | self self |
| Reports |   |   |
| Al | Alorg | Personal Schedule Finance |
| Settings |   |   |
| Al | org Limited | Limited |

Final authorization is enforced in PostgreSQL Row Level Security, not only in the browser.

## Permission principle

The browser may hide unavailable actions, but the database must independently reject unauthorized reads and writes through Supabase Row Level Security policies.

## Recommended roles

| Role | Core access |
| --- | --- |
| Super Admin | All authorized organizations, system settings, audit logs, users, clinics, reports and integrations. |
| Organization Admin | All clinics and users within one organization; organization-wide reporting and configuration. |
| Clinic Manager | All leads, appointments, tasks and approved reports for assigned clinics. |
| Sales / Call Agent | Assigned leads, personal tasks, calls, appointment booking and personal performance. |
| Receptionist | Appointment calendar, patient check-in, rescheduling and approved contact details. |
| Finance / Reporting | Revenue, payment status, finance exports and selected performance reporting. |
| Read-only / Auditor | Approved dashboards and records without create, update or delete permissions. |

## Permission dimensions

- Organization membership and active status.


- Clinic membership and clinic-level scope.

- Functional role and granular permission flags.

- Record ownership or assignment where required.

- Sensitive field restrictions for finance and private notes.

- Action-specific rules for exports, deletions, user management and integrations.

## SECTION 04

## End-to-End Workflows

## Primary Lead-to-Revenue Workflow

Every transition creates an immutable activity entry. Status history, assignment history and revenue changes remain auditable.

## Lead lifecycle rules

- Every new lead receives an organization, clinic preference, source, status and created timestamp.

- Assignment changes are stored in a dedicated history table.

- Calls, notes, emails, SMS, tasks and appointments appear in one chronological activity timeline.

- Lead status changes require optional reasons, especially for lost, invalid, duplicate or declined leads.

- Appointment outcomes feed conversion and no-show reporting.

- Revenue is counted only according to the approved revenue-recognition rule.

- Closed records remain searchable and auditable unless retention rules require deletion.

## Secondary workflows

| Workflow | Typical sequence |
| --- | --- |
| User onboarding | Admin invite -> email verification -> profile completion -> role/clinic assignment -> active access |
| Appointment | Create -> confirm -> remind -> check in -> attended/no-show/cancelled -> outcome |
| Revenue | Treatment accepted -> estimated value -> deposit -> partial/full payment -> refund/cancellation if |
|   | needed |
| Data import | Upload CSV -> validate -> preview errors -> map fields -> import -> reconciliation report |
| Report export | Choose filters -> calculate server-side -> generate file -> log export -> secure download |
| Public lead journey | Landing page -> treatment quiz/form -> attribution -> duplicate check -> CRM lead -> assignment -> |
|   | confirmation |
| AI-assisted follow- | New activity -> summarize/classify -> recommend next action -> user approval -> communication -> |
| up | audit and feedback |


## Functional Modules

## Complete production scope

## 5.1 Authentication and Account Access

- Email and password login, password reset and secure session management.

- Admin invitation flow and user activation/deactivation.

- Optional MFA or passkeys after client approval and compatibility review.

- Login history, failed-attempt monitoring and inactivity timeout.

- Role-aware landing page after login.

## 5.2 Organization and Clinic Management

- Organization profile, branding, time zone, currency and settings.

- Clinic profiles, contact details, working hours, managers, targets and active status.

- Clinic membership for users and optional access to more than one clinic.

- Clinic-specific treatments, appointment durations and reporting targets.

## 5.3 Lead Management

- Create, edit, view, archive and restore leads.

- Contact data, treatment interest, source, campaign, clinic, assigned agent, priority and consent fields.

- Advanced search, filters, sorting, pagination and saved views.

- Bulk assignment, bulk status update and export.

- Duplicate detection by normalized phone and email; merge workflow with history preservation.

- Lead detail page with full timeline, appointments, tasks, calls, revenue, notes and files.

## 5.4 Lead Assignment

- Manual assignment by authorized managers.

- Optional round-robin and rules based on clinic, treatment, source, geography or workload.

- Assignment history with old user, new user, reason, actor and timestamp.

- Reassignment notifications and unassigned-lead queues.

## 5.5 Call and Communication Activity

- Manual incoming and outgoing call logging for the initial release.

- Call outcome, duration, notes, recording link and next follow-up.

- Optional telephony integration through provider webhooks.

- Email and SMS activity stored against the lead timeline.

- Failed delivery and retry status for automated messages.

## 5.6 Tasks and Follow-Ups

- Create call, email, SMS, appointment-confirmation and custom tasks.

- Due date/time, assignee, priority, status, reminders and completion notes.

- Today, upcoming, completed and overdue queues.

- Automatic task creation from selected statuses or call outcomes.


## 5.7 Appointment Management

- Calendar and list views with daily, weekly and monthly navigation.

- Clinic, treatment, provider, agent, date and status filters.

- Book from a lead; reschedule, cancel, check in, attend or mark no-show.

- Conflict checks and configurable appointment duration.

- Confirmation and reminder status; optional Google or Microsoft calendar integration.

## 5.8 Patient Conversion

- Convert qualified or successful leads into patient records without losing lead history.

- Patient profile with contact, clinic, appointments, treatments, payments, notes and files.

- Keep CRM and clinical scope separated unless the client explicitly requires medical records.

## 5.9 Treatment and Service Catalogue

- Treatment categories, names, estimated price range, duration and active status.

- Clinic availability and optional clinic-specific pricing.

- Use treatments in leads, appointments, revenue and performance reports.

## 5.10 Revenue and Payments

- Estimated treatment value, deposit, paid amount, outstanding amount and payment status.

- Link revenue to lead/patient, clinic, treatment, appointment and responsible agent.

- Payment history, refunds, cancellations and notes.

- Approved rules for when revenue appears in dashboards.

## 5.11 Dashboards and Reporting

- Organization, clinic, manager and agent-specific dashboards.

- Lead funnel, appointments, attendance, no-show, conversion, revenue and source performance.

- Date, clinic, agent, source, campaign, treatment and status filters.

- CSV/Excel exports; optional scheduled report delivery.

## 5.12 Notifications

- In-app notifications for new assignments, due tasks, appointments and important status changes.

- Email and SMS templates with variables and delivery logs.

- Per-user notification preferences and quiet-hour rules if required.

## 5.13 Documents and Files

- Private Supabase Storage buckets and signed download URLs.

- Allowed file types, size limits, metadata, uploader and access scope.

- Possible files: quote, consent, invoice, treatment plan or internal attachment.

## 5.14 Audit Logs

- Log authentication events, important record changes, permission changes, exports and deletes.

- Capture actor, organization, clinic, entity, action, old/new values, timestamp and request context.

- Provide searchable audit views to authorized administrators.

## 5.15 Settings and Integrations

- Lead statuses, sources, loss reasons, call outcomes, appointment statuses and templates.

- Integration credentials stored only in secure server-side environment variables or secrets.


- Webhook event history with signature validation, retries and failure diagnostics.

## 5.16 Public Website and Lead Acquisition

- Premium responsive homepage, treatment pages, clinic pages, consultation booking and campaign landing pages.

- Interactive treatment finder/qualification quiz with progressive questions and CRM handoff.

- Lead forms with UTM, referrer, campaign, consent, spam protection and duplicate handling.

- Admin-managed content blocks, testimonials, FAQs, clinic details, calls to action and legal pages.

- Technical SEO, structured metadata, performance budgets, accessibility and analytics consent controls.

## 5.17 AI Automation and Copilot

- Lead classification, explainable priority score, duplicate suggestions and missing-data prompts.

- Call/message summarization, intent and sentiment labels, next-best-action recommendations and reply drafts.

- Natural-language CRM assistant with strictly permissioned tools and source-linked answers.

- Appointment reminder optimization, no-show risk flags, recovery tasks and manager alerts.

- Narrative report summaries, anomaly detection and semantic search over approved CRM knowledge.

- Human approval, prompt versioning, model routing, cost controls, evaluation, audit and feedback tracking.


## Public Website and Landing Experience

## A high-converting frontend that captures, qualifies and books leads

## Public Website and Landing Experience

Conversion-first, responsive and directly connected to the CRM

## Recommended homepage sections

| Section | Purpose |
| --- | --- |
| Sticky navigation | Treatments, clinics, trust resources and persistent consultation CTA. |
| Interactive hero | Clear value proposition, treatment finder and booking entry point. |
| Trust and outcomes | Clinic coverage, response time, testimonials, ratings and approved result stories. |
| Treatment discovery | Visual treatment cards with suitability guidance and strong calls to action. |
| How it works | Enquiry, qualification, clinic match, appointment and treatment journey. |
| Clinic finder | Location search, map/list, services, hours and availability. |
| AI concierge | Non-clinical questions, lead qualification, booking assistance and live-team handoff. |
| FAQ and resources | Searchable answers, guides, financing information and objection handling. |
| Final conversion block | Short form, privacy assurance, urgent contact option and footer navigation. |

## Conversion and marketing requirements

- Campaign-specific landing pages with reusable sections and controlled content variants.

- UTM, click ID, referrer, landing URL and consent stored on the lead and first-touch activity.


- Multi-step forms with autosave, progress indicators, inline validation and abandonment events.

- Optional live appointment availability without exposing private calendar or patient data.

- Analytics events for CTA click, quiz start, quiz completion, form submit, booking and qualified lead.

- Core Web Vitals, image optimization, semantic HTML, WCAG-oriented accessibility and mobile-first layouts.

- Privacy, cookie consent, terms, contact preferences and clear non-emergency/non-clinical disclaimers. SECTION 05B

## Interactive Dashboard User Experience

A productivity-focused interface rather than static admin screens

| Experience area | Required interaction |
| --- | --- |
| Navigation | Collapsible sidebar, role workspaces, breadcrumbs, recent items and global command palette. |
| Lead workspace | Table/Kanban toggle, saved views, bulk actions, split-pane details and slide-over quick edit. |
| Activity timeline | Live updates, filters, expandable events, pinned notes and one-click follow-up actions. |
| Appointments | Drag-and-drop calendar where safe, conflict feedback, quick booking drawer and status shortcuts. |
| Analytics | Animated KPI cards, comparison periods, cross-filtering, chart drill-down and underlying record list. |
| Personalization | Reorderable dashboard widgets, density controls, saved filters and optional dark/light theme. |
| Speed | Optimistic feedback where safe, keyboard shortcuts, skeletons, prefetching and progressive loading. |
| Collaboration | Presence indicators, assignment notifications, comments and stale-edit/conflict protection. |
| Accessibility | Keyboard operation, focus management, reduced-motion support, readable contrast and screen-reader labels. |

## Interaction rule

Motion and rich interactions must clarify state and reduce effort. They must not hide critical information, reduce accessibility or introduce unsafe optimistic updates for revenue, permissions or patient-facing actions.

## SECTION 05C

## AI Automation and Copilot

Operational intelligence with explicit human approval and measurable quality


## Al Automation and Human-in-the-Loop

Provider-neutral Al serv

and

over

es with approval controls, audit trails

Almay recommend and draft

hanges,

icati

i

ions and any pati

| Capability | Trigger | Output / control |
| --- | --- | --- |
| Lead triage | New or updated lead | Treatment/source classification, completeness check and explainable priority |
|   |   | score. |
| Conversation intelligence | Call transcript or message | Summary, intent, objections, sentiment, commitments and recommended |
|   | thread | follow-up. |
| Agent copilot | User opens a lead | Next-best action, task proposal, reply draft and relevant history with source |
|   |   | links. |
| Appointment intelligence | Booking and reminder events | No-show risk flag, reminder channel/time recommendation and recovery |
|   |   | workflow. |
| Management intelligence | Scheduled or threshold event | Narrative KPI summary, anomalies, backlog risk and suggested investigation |
|   |   | links. |
| Knowledge assistant | Natural-language user question | Permission-filtered answer and tool results; no unrestricted SQL or cross- |
|   |   | clinic access. |
| Data quality | Import or record update | Duplicate candidates, inconsistent status/date warnings and normalization |
|   |   | suggestions. |

## AI governance requirements

- Provider-neutral implementation through the Vercel AI SDK and optional AI Gateway; model can be changed without rewriting business workflows.

- Zod/JSON schema structured outputs for every automation that writes classifications, tasks or recommendations.

- No autonomous clinical diagnosis, treatment recommendation, emergency triage or medical decision-making.

- Outbound messages, lead closure, material status changes, payments and destructive actions require user approval.

- Prompts, model, temperature/options, retrieved sources, token usage, latency, cost, output and user feedback are logged.

- PII minimization and redaction rules are applied before third-party model calls where the workflow permits.

- Offline evaluation set, acceptance thresholds, fallback behavior and kill switch are defined before production rollout.

- Long-running transcription, embeddings and batch analysis use queued/background jobs with retries and idempotency.


## Screens and Navigation

## Recommended application information architecture

| Route group | Purpose |
| --- | --- |
| /, /treatments/[slug], /clinics/[slug] | Public marketing, treatment and clinic pages |
| /book-consultation, /treatment-finder, | Interactive lead capture and appointment journey |
| /contact |   |
| /login, /forgot-password, /reset-password | Authentication |
| /dashboard | Role-aware KPI dashboard and alerts |
| /leads, /leads/new, /leads/[id] | Lead lists, creation and detail timeline |
| /appointments, /appointments/calendar, | Appointment list, calendar and details |
| /appointments/[id] |   |
| /patients, /patients/[id] | Converted patient profiles |
| /calls, /tasks | Call activity and follow-up queues |
| /revenue, /payments | Revenue and payment tracking |
| /reports | Analytics, filters and exports |
| /clinics, /clinics/[id] | Clinic setup and performance |
| /users, /users/[id] | User, role and clinic membership |
| /treatments, /lead-sources, /statuses | Operational configuration |
| /audit-logs, /notifications | Governance and user alerts |
| /ai/copilot, /ai/runs, /automations | AI assistant, run review, feedback and automation controls |
| /website/content, /website/forms | Landing content and public lead-form configuration |
| /settings, /integrations | Organization settings and external services |

## UI standards

- Premium, visually rich B2B interface with clear hierarchy, refined motion, consistent cards, tables, forms and status badges.

- Desktop-first productivity with responsive tablet and essential mobile support.

- Keyboard-friendly forms, accessible labels, clear validation and visible focus states.

- Server-side pagination and filtering for large lead volumes.

- Confirmation for destructive actions and undo/restore where possible.

- Skeleton loading, empty states, error states and retry actions on all data screens.

- Command palette, shortcuts, contextual drawers, chart drill-down, saved views and realtime updates where operationally useful.

- Animations use reduced-motion preferences and never delay primary actions or hide loading/error states.

## SECTION 07

## Data Model and Database Design

PostgreSQL schema designed for multi-clinic security and reporting


## Multi-tenant rule

Every business record must be traceable to an organization. Clinic-scoped records also include clinic_id. Access policies must use membership tables rather than trusting values supplied by the browser.

| Domain | Recommended tables |
| --- | --- |
| Identity and tenancy | organizations, clinics, profiles, organization_memberships, clinic_memberships, roles, |
|   | permissions, role_permissions |
| Lead CRM | leads, lead_sources, lead_statuses, lead_assignments, lead_status_history, lead_notes, |
|   | lead_activities, lead_documents, lead_merge_history |
| Operations | tasks, task_comments, calls, call_outcomes, communications, communication_templates, |
|   | notifications |
| Appointments and | appointments, appointment_status_history, patients, treatments, treatment_categories, |
| patients | clinic_treatments |
| Revenue | revenue_records, payments, refunds, revenue_adjustments |
| Website | website_pages, website_sections, content_versions, lead_forms, form_submissions, |
|   | marketing_attribution, consent_events |
| AI and automation | automation_rules, automation_runs, ai_runs, ai_prompt_versions, ai_feedback, ai_usage, |
|   | knowledge_documents, knowledge_chunks, embeddings |
| Platform | audit_logs, integration_settings, webhook_events, import_jobs, export_jobs, system_settings |

## Standard columns

| Column | Purpose |
| --- | --- |
| id | UUID primary key generated server-side. |
| organization_id | Tenant boundary and primary security filter. |
| clinic_id | Optional clinic boundary where applicable. |
| created_at / updated_at | UTC timestamps. |
| created_by / updated_by | Actor accountability. |
| deleted_at | Soft deletion where auditability is required. |
| metadata | Controlled JSONB only for non-critical extension data. |

## Important indexes

- organization_id and clinic_id on all high-volume tables.

- Normalized phone, email, assigned_user_id, lead_status_id and next_follow_up_at on leads.

- Appointment start_time, clinic_id and status.

- Revenue date, clinic, treatment and responsible agent.

- Activity timeline composite index by lead_id and created_at descending.

- Partial indexes for active, overdue, unassigned and non-deleted records.

- GIN/vector indexes for approved semantic-search content and indexes for AI run status, entity and created_at.


## Mandatory Technology Stack

## Latest stable, production-compatible versions as of 10 July 2026

## Mandatory implementation rule

Start with the versions below, then pin the latest stable security-patched releases that remain mutually compatible on the day development begins. Do not deploy canary or beta builds.

| Layer | Required choice | Implementation notes |
| --- | --- | --- |
|   |   | App Router, React Server Components, Route Handlers, Server |
| Application framework | Next.js 16.2 | Actions where appropriate, built-in performance and deployment |
|   |   | integration. |
| UI runtime | React 19.2 latest patched release | Use the patched stable line compatible with Next.js 16.2. |
| Language | TypeScript 6.0 | Strict mode, generated Supabase database types, no implicit any |
|   |   | in production code. |
| CSS | Tailwind CSS 4.3 | Responsive design system, CSS-first configuration and reusable |
|   |   | tokens. |
| Component system | shadcn/ui latest stable compatible | Accessible primitives customized for the website and dashboard |
|   |   | design system. |
| Interaction and motion | Motion for React latest stable | Route and component transitions, layout animation and reduced- |
|   | compatible | motion support. |
| Runtime | Node.js 24 LTS | Vercel default LTS runtime; define the major version in package |
|   |   | configuration. |
| Package manager | pnpm latest stable | Lockfile committed; frozen lockfile in CI. |
| Backend platform | Supabase managed platform | PostgreSQL, Auth, RLS, Storage, Realtime, Edge Functions, Cron |
|   |   | and logs. |
| Supabase SDK | @supabase/supabase-js + | Cookie-based SSR clients and server-side session handling. |
|   | @supabase/ssr latest stable |   |
| AI application layer | Vercel AI SDK latest stable | Streaming UI, structured outputs, provider abstraction, tool calling |
|   |   | and agent/copilot experiences. |
| AI model routing | Vercel AI Gateway or direct approved | Budget controls, usage visibility, provider fallback and model |
|   | provider | choice by workflow. |
| Vector search | Supabase pgvector | Permission-aware semantic search across approved summaries, |
|   |   | guides and knowledge documents. |
| Deployment | Vercel | Preview deployments, staging, production, domains, logs and |
|   |   | environment variables. |
| Source control | GitHub | Protected main branch, pull requests, reviews, CI checks and |
|   |   | release tags. |
| AI development tool | Claude Code | Allowed for scaffolding, refactoring and tests; architecture and |
|   |   | security remain developer responsibilities. |

## Core libraries

| Concern | Recommended library |
| --- | --- |
| Forms and validation | React Hook Form + Zod |
| Server/client data | Server Components first; TanStack Query only for interactive client caching |


| Concern | Recommended library |
| --- | --- |
| Tables | TanStack Table with server-side pagination/filtering |
| Charts | Recharts or another approved accessible chart library |
| Motion | Motion for React with reduced-motion support |
| Command interface | cmdk or shadcn command primitives |
| Dates | date-fns with organization time-zone rules |
| Testing | Vitest, React Testing Library and Playwright |
| Error monitoring | Sentry |
| Logging | Structured server logs plus Supabase and Vercel logs |
| Email | Resend, SendGrid, Mailgun or SES after client selection |
| Job processing | Supabase Cron/Edge Functions/background tasks for light jobs; Trigger.dev, QStash or |
|   | equivalent if durable long-running workflows require it |
| AI validation | Vercel AI SDK structured output + Zod schemas |
| Semantic retrieval | Supabase pgvector with tenant-aware retrieval functions |

## Supabase implementation requirements

- Use Supabase CLI migrations committed to GitHub; do not rely only on manual dashboard changes.

- Generate TypeScript types from the database and update them through CI or documented scripts.

- Use the new publishable and secret API key model. Never expose secret keys to the browser.

- Create separate Supabase projects for staging and production.

- Enable and test RLS on every exposed table and private storage bucket.

- Use database functions only when they simplify atomic operations and can be securely authorized.

- Enable pgvector only for approved semantic-search use cases; retrieval functions must enforce tenant and role scope.

- Keep AI provider credentials server-only and separate across staging and production.


SECTION 09

## Application Architecture

## Architecture decisions

- Next.js App Router is the single application for the public website, authenticated dashboard and secure server boundary.

- Read operations use server components or secure server functions wherever practical.

- Mutations validate input with Zod, authorize the actor, execute atomically and write audit events.

- Supabase RLS provides the final database authorization boundary.

- Long-running imports, exports, transcription, embeddings and AI batch analysis must not block interactive requests.

- External webhooks are verified, stored, processed idempotently and retried safely.

- No direct database secret or privileged service key is exposed in client-side JavaScript.

## Suggested repository structure

| Path | Purpose |
| --- | --- |
| app/ | Next.js routes, layouts, server components and route handlers |
| components/ | Reusable UI and feature components |
| features/ | Domain modules such as public website, leads, appointments, reports, automation and AI |
|   | copilot |
| lib/supabase/ | Browser, server and admin clients with strict separation |
| lib/auth/ | Session, authorization and role helpers |
| lib/validation/ | Zod schemas and shared constraints |


| Path | Purpose |
| --- | --- |
| lib/ai/ | Model registry, prompts, tools, policies, evaluations and usage controls |
| supabase/migrations/ | Versioned database migrations |
| supabase/functions/ | Edge Functions when required |
| tests/ | Unit, integration and end-to-end tests |
| docs/ | Architecture decisions, runbooks and handover material |


## Supabase Security and Row Level Security

## Authorization must be enforced at the database layer

Recommended access evaluation order: authenticated user -> active organization membership -> role permission -> clinic membership -> record assignment or ownership -> requested operation.

## Example policy intentions

| Actor | Read scope | Write scope |
| --- | --- | --- |
| Super Admin | All authorized organizations | According to administrative permission set |
| Organization Admin | All records in own organization | Organization and clinic operations |
| Clinic Manager | Records for assigned clinics | Manage clinic leads, appointments, tasks and approved |
|   |   | revenue actions |
| Agent | Assigned leads and permitted shared clinic queues | Update assigned leads, calls, notes, tasks and |
|   |   | appointments |
| Receptionist | Appointments and approved patient contact fields | Appointment operational actions |
|   | for assigned clinics |   |
| Finance | Approved revenue and payment records | Revenue and payment actions only |

## Security controls

- RLS enabled and tested on every table exposed through the Data API.

- Private storage buckets with policies and short-lived signed URLs.

- CSRF-safe session handling through the official SSR client pattern.

- Rate limits for authentication, imports, exports, search and integrations.

- Server-side validation even when the browser already validates the form.

- Explicit authorization checks for privileged server actions and admin clients.

- No patient data in application logs, analytics events or error messages unless required and redacted.

- Secret rotation and access review during handover.

## Healthcare data boundary

The initial scope is a CRM for leads, appointments and revenue. Storing diagnosis, clinical notes or protected medical records may trigger additional regulatory and contractual controls and must be separately assessed.

## SECTION 11

## Integrations and Automation

| Integration | Scope |
| --- | --- |
| Public website and | Next.js landing pages, treatment finder, clinic locator, forms and appointment handoff directly |
| booking | into the CRM. |
| Website lead capture | Secure form endpoint or webhook; spam controls; source/campaign attribution; duplicate |
|   | handling. |
| Email | Transactional confirmations, reminders, invitations and follow-ups; delivery and failure logs. |
| SMS / WhatsApp | Appointment reminders and follow-ups after provider selection and consent review. |


| Integration | Scope |
| --- | --- |
| Telephony | Optional Twilio, Aircall, RingCentral, Dialpad or existing provider webhooks. |
| Calendar | Optional Google or Microsoft calendar sync; conflict and ownership rules required. |
| Advertising | Optional Facebook/Meta and Google lead ingestion through APIs or automation platform. |
| CSV / Excel | Validated import, preview, error report and controlled export. |
| AI model providers | Vercel AI SDK/Gateway with one or more client-approved models, budgets, fallback and |
|   | observability. |
| Transcription | Optional approved speech-to-text provider for calls, with consent and retention controls. |
| Accounting / payments | Optional integration after provider and revenue source-of-truth are confirmed. |

## Automation examples

- Assign new leads using round-robin or clinic/treatment rules.

- Create a follow-up task when a call outcome is no answer or callback requested.

- Send appointment confirmation after booking and reminder before the appointment.

- Escalate overdue high-priority leads to a clinic manager.

- Notify managers about unassigned leads or unusual no-show rates.

- Generate scheduled management reports only after Phase 1 reporting is reconciled.

- Summarize calls and propose tasks without auto-sending or silently changing the lead status.

- Prioritize newly received leads using transparent factors and manager-adjustable thresholds.

- Draft personalized follow-ups from approved templates and CRM context for agent review.

- Create anomaly alerts for sudden drops in contact rate, attendance or clinic conversion.


SECTION 12

## Reporting and Analytics

## Reports must be defined mathematically before implementation

| KPI | Recommended definition |
| --- | --- |
| New leads | Count of leads created in the selected date range. |
| Contact rate | Leads with a successful contact outcome / eligible leads. |
| Appointment booking rate | Leads with an appointment booked / eligible leads. |
| Attendance rate | Attended appointments / appointments due in range. |
| No-show rate | No-show appointments / appointments due in range. |
| Treatment conversion | Treatment accepted / attended consultations. |
| Lead-to-sale conversion | Won leads / eligible leads. |
| Recognized revenue | Sum based on the client-approved recognition event and date. |
| Average treatment value | Recognized treatment value / converted patients. |
| Agent response time | Time from lead creation/assignment to first qualifying activity. |

## Required dashboards

| Dashboard | Minimum widgets |
| --- | --- |
| Executive | Leads, appointments, conversion, recognized revenue, trend, top clinics, sources and agents |
| Clinic | Clinic funnel, today appointments, no-show, follow-up backlog, team performance and revenue |
| Agent | Assigned leads, calls today, due tasks, booked appointments, personal conversion and revenue |
| Finance | Revenue, deposits, paid, outstanding, refunds, treatment and clinic breakdown |
| AI operations | Runs, success/failure, acceptance rate, edits, latency, tokens/cost, model and automation outcomes |
| Website growth | Traffic, CTA/quiz/form funnel, booking conversion, source/campaign quality and clinic demand |

## Revenue warning

The client must confirm whether revenue is counted at treatment acceptance, deposit receipt, invoice date, payment date or full settlement. Changing this decision changes historical reports.

## SECTION 13

## Data Migration

## Controlled transfer from the current dashboard

## Migration sequence

- 1. Obtain read-only access or exports from the existing platform.

- 2. Inventory tables, fields, statuses, clinics, users, dates, attachments and integrations.

- 3. Create a field-mapping workbook and transformation rules.


- 4. Clean invalid dates, malformed phones, duplicates and missing foreign keys.

- 5. Run a sample migration into staging and produce a reconciliation report.

- 6. Obtain client sign-off on sample records and aggregate totals.

- 7. Plan a cutover window and freeze or delta-sync the old system.

- 8. Run the production migration, validate totals and retain rollback backups.

## Migration deliverables

- Source-to-target field mapping.

- Import scripts and versioned migration utilities.

- Error and rejected-record report.

- Reconciliation totals by clinic, status and date.

- Backup and rollback plan.

- Signed migration acceptance checklist.

SECTION 14

## DevOps and Environments

| Environment | Purpose | Recommended setup |
| --- | --- | --- |
| Local development | Developer implementation and | Local Next.js, Supabase local stack where practical, seeded test data |
|   | unit testing |   |
| Staging | Client review and UAT | Separate Vercel project/environment and separate Supabase project |
| Production | Live operations | Protected production deployment, production Supabase, custom |
|   |   | domain and monitoring |

## GitHub and deployment controls

- Company-owned repository with protected main branch.

- Feature branches and pull requests with at least one review for critical changes.

- Automated type-check, lint, unit tests and build checks.

- Vercel preview deployment for each pull request.

- Separate environment variables for preview, staging and production.

- Database migrations reviewed and applied in order.

- Release tags and documented rollback process.

- Dependabot or equivalent dependency security alerts.


## Security, Privacy, Performance and Reliability

| Area | Requirement |
| --- | --- |
| Authentication | Secure cookies, reset flow, session expiry, account disable, optional MFA/passkeys. |
| Authorization | RLS, server authorization, least privilege and clinic boundaries. |
| Secrets | Vercel/Supabase secrets; no keys in GitHub or client bundles. |
| Data protection | TLS, private storage, signed URLs, backups and access review. |
| Auditability | Audit logs for sensitive changes, exports and permission updates. |
| Input protection | Validation, sanitization, file restrictions and webhook signatures. |
| Performance | Pagination, indexes, query plans, caching where safe and async exports. |
| Availability | Monitoring, error alerts, backups, restore test and operational runbook. |
| Retention | Client-approved retention and deletion policy for leads, activities and files. |

## Target performance expectations

- Fast first load for the dashboard shell and common list screens on normal business connections.

- Lead lists use server-side pagination and return only required columns.

- Common filters have supporting indexes and avoid unbounded queries.

- Heavy reports and exports use asynchronous generation when data volume requires it.

- Performance testing uses realistic clinic, lead, activity and appointment volumes.

SECTION 16

## Testing and Acceptance

| Test layer | Coverage |
| --- | --- |
| Unit | Validation, calculations, status transitions and permission helpers. |
| Integration | Database functions, RLS policies, server actions, imports and webhooks. |
| End-to-end | Login, lead lifecycle, calls, tasks, appointments, revenue and reporting. |
| Security | Cross-role, cross-clinic, direct URL/API access, file access and exports. |
| Migration | Field mapping, record counts, relationships, dates and rejected records. |
| Performance | Pagination, common filters, large timelines and report queries. |
| UAT | Client-approved scripts based on real operational workflows. |

## Minimum acceptance scenarios

- Admin creates a clinic, invites users and assigns roles.

- Lead enters from a manual form or integration and is assigned correctly.

- Agent logs calls, notes and follow-up tasks; timeline remains complete.

- Appointment is booked, confirmed, rescheduled and completed/no-show as expected.

- Revenue is added and appears correctly in approved reports.

- Unauthorized users cannot read or change out-of-scope records.


- Client can deploy a documented release and restore from backup procedures.

SECTION 17

## Delivery Phases and Timeline

| Phase | Deliverables | Typical duration |
| --- | --- | --- |
| 1. Discovery and parity | Dashboard access, screen inventory, website content, workflows, KPIs, AI use cases, data | 1-2 weeks |
| mapping | policy and final backlog. |   |
| 2. UX and solution design | Landing wireframes, interactive dashboard prototype, design system, schema, permissions | 2-3 weeks |
|   | and architecture sign-off. |   |
| 3. Foundation | Repository, Next.js, Supabase projects, migrations, Auth, tenancy, RLS, CI, AI foundation | 2-3 weeks |
|   | and staging. |   |
| 4. Public website | Homepage, treatment/clinic pages, forms, quiz, attribution, booking handoff, SEO and | 2-4 weeks |
|   | analytics. |   |
| 5. Core CRM | Leads, assignment, interactive workspace, timeline, notes, calls, tasks, search, filters and | 4-6 weeks |
|   | imports. |   |
| 6. Appointments and patients | Interactive calendar, appointment lifecycle, reminders and patient conversion. | 2-3 weeks |
| 7. Revenue and analytics | Revenue, payments, KPI calculations, drill-down dashboards and exports. | 2-4 weeks |
| 8. AI automation | Triage, summaries, copilot, semantic search, approved workflows, evaluations and | 3-6 weeks |
|   | observability. |   |
| 9. Integrations | Email/SMS, telephony, calendar, ads and selected external providers. | 1-3 weeks |
| 10. QA and migration | Security, accessibility, AI evaluation, UAT, performance, migration rehearsals and cutover. | 2-4 weeks |
| 11. Handover | Production deployment, website/AI/admin documentation, training and support transition. | 1 week |

## Realistic delivery range

One experienced senior full-stack developer: approximately 20-28 weeks for the complete website, interactive CRM and governed AI scope. A focused team can target roughly 13-18 weeks, depending on content, integrations, model evaluation, data quality and approval speed.


## SECTION 18

## Effort, Team and Cost Model

| Workstream | Estimated hours |
| --- | --- |
| Discovery, website content and architecture | 80-130 |
| Interactive UX/UI and design system | 120-200 |
| Public website, forms, quiz and SEO | 130-220 |
| Foundation, Auth and RLS | 100-170 |
| Lead CRM and activity workspace | 170-270 |
| Calls, tasks and communications | 90-150 |
| Appointments and patient conversion | 110-180 |
| Revenue, interactive dashboards and reports | 150-250 |
| AI automation, copilot and evaluations | 180-340 |
| External integrations and durable jobs | 100-220 |
| Migration and reconciliation | 70-150 |
| Testing, deployment and documentation | 130-210 |

## Indicative total

Approximately 1,430-2,490 hours for the full website, interactive CRM and AI automation scope. The lower end assumes approved content, limited integrations and focused AI use cases; the upper end includes complex parity, migration, telephony/transcription, extensive automation and advanced UI behavior.

## Recommended team

| Role | Allocation | Responsibility |
| --- | --- | --- |
| Senior full-stack lead | Full time | Architecture, Next.js, Supabase, RLS, complex workflows, review and |
|   |   | deployment |
| Frontend / interaction | Full time during core UI | Public website, rich dashboard interactions, motion, data visualization, |
| developer |   | responsive UI and accessibility |
| AI application engineer | Part or full time during AI | AI SDK, tools, retrieval, prompts, evaluations, safety, observability and cost |
|   | phase | controls |
| QA engineer | Part time, increasing | Test plans, regression, permission tests and UAT support |
|   | near UAT |   |
| UI/UX designer | Part time during design Wireframes, design system and workflow usability |   |
| Client product owner | Ongoing | Business rules, access, decisions, approvals and acceptance |

## Cost calculation method

Estimated project cost = approved hours x hourly rate + third-party subscriptions + optional post-launch support. A milestone contract should reserve contingency for unknown existing-system behavior and data quality.


## Client Inputs and Access Required

| Category | Required items |
| --- | --- |
| Existing system | Admin and role-based test accounts, screenshots, screen recordings and complete workflow |
|   | demonstrations. |
| Source and data | GitHub/source if available, Supabase/database access or exports, file exports and sample records. |
| Business rules | Roles, statuses, sources, treatments, assignment rules, appointment process, loss reasons and |
|   | revenue formulas. |
| Integrations | Provider names, account access, API docs, webhook samples, template content and sender |
|   | identities. |
| Technical accounts | Company GitHub, Vercel, Supabase, domain/DNS, email and optional SiteGround/DigitalOcean |
|   | access. |
| Design and website | Logo, colors, typography, approved imagery, treatments, clinic content, testimonials, FAQs, legal |
|   | copy and preferred interactive style. |
| AI policy and | Approved AI use cases, provider constraints, message templates, call samples/transcripts, |
| knowledge | knowledge sources, redaction rules and human-approval policy. |
| Operations | Expected clinics, users, monthly leads, activity volume, exports, uptime expectations and retention |
|   | policy. |

## Discovery questions that block a fixed estimate

- 1. Will source code and the current database schema be provided?

- 2. Must all historical leads, calls, appointments, revenue and files be migrated?

- 3. How many organizations, clinics, users and roles are active?

- 4. Are calls manually logged or integrated with a phone provider?

- 5. Which event makes revenue reportable?

- 6. Are email, SMS, WhatsApp, calendar or ad-platform integrations currently used?

- 7. Is exact UI replication required or can the usability be improved?

- 8. Does the system store any clinical or regulated health information?

- 9. What is the required cutover method and acceptable downtime?

- 10. Who signs off workflow parity and report accuracy?

- 11. Which public pages, campaigns, treatments, clinics and booking paths are required at launch?

- 12. Which AI capabilities are launch-critical, what data may be sent to models, and who approves quality and patient- facing outputs?


## Risks, Assumptions and Exclusions

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Limited access to current platform | Hidden workflows and | Paid discovery, screen recording and parity checklist before |
|   | underestimated scope | fixed milestones |
| Undefined revenue formulas | Reports do not match | Approve KPI definitions with sample calculations |
|   | expectations |   |
| Poor source data quality | Migration delays and inaccurate | Profile, clean and rehearse migration with reconciliation |
|   | history |   |
| Complex telephony/calendar integration | Provider-specific delays | Separate integration milestone and test credentials early |
| Overly broad roles | Security exposure | Least-privilege role matrix and automated RLS tests |
| Fast-changing requirements | Rework and timeline expansion | Signed backlog, change-control and prioritized releases |
| AI hallucination or unsafe actions | Incorrect advice or operational | Restrict use cases, structured output, source links, human |
|   | changes | approval, evaluations and kill switch |
| AI privacy and cost | Sensitive data exposure or | PII policy, server-only keys, provider review, budgets, model |
|   | uncontrolled spend | routing and usage alerts |
| Public website content delays | Launch blocked by missing | Content inventory, placeholders, owner and approval dates in |
|   | clinic/treatment assets | discovery |
| Healthcare compliance expansion | Additional security/legal scope | Explicitly separate CRM from clinical records and obtain |
|   |   | specialist review |

## Assumptions

- Client provides timely access, decisions, sample data and UAT participants.

- Initial release is a browser-based internal dashboard, not a native mobile application.

- English is the initial interface language unless localization is separately scoped.

- Supabase and Vercel managed cloud services are acceptable to the client.

- Expected workload fits managed Supabase and Vercel after sizing; enterprise requirements may change hosting choices.

## Not included unless added to scope

- Electronic medical records, diagnosis, prescriptions or clinical charting.

- Native iOS/Android applications.

- Custom VoIP infrastructure or call-center software.

- Payment gateway, accounting or insurance integrations not specifically selected.

- Autonomous clinical diagnosis, treatment recommendations, emergency triage or unreviewed medical communication.

- 24/7 operational support and formal compliance certification.

## SECTION 21

## Documentation, Handover and Post-Launch

| Deliverable | Contents |
| --- | --- |
| Architecture document | System context, components, data flow and security boundaries. |
| Database guide | Schema overview, migrations, important functions, indexes and RLS policy explanation. |


| Deliverable | Contents |
| --- | --- |
| Deployment runbook | Local setup, environment variables, staging, production, rollback and domains. |
| Admin guide | Clinics, users, roles, statuses, sources, treatments, templates and integrations. |
| Website/content guide | Landing sections, clinic/treatment content, forms, attribution, SEO and campaign page workflow. |
| User guide | Leads, calls, tasks, appointments, AI copilot, revenue, reports and exports. |
| AI operations guide | Approved use cases, model/prompt registry, evaluations, feedback, budgets, privacy, fallback |
|   | and kill switch. |
| Migration record | Mapping, import scripts, reconciliation and rollback artifacts. |
| Operations runbook | Monitoring, logs, backup, restore, secret rotation and incident steps. |
| Training | Recorded administrator walkthrough and live handover session. |

## Recommended warranty and support

- Initial defect warranty after production launch for issues within the agreed scope.

- Separate support retainer for monitoring, dependency updates, small changes and user assistance.

- Quarterly permission, backup and dependency review for a business-critical internal system.


## Appendix A - Suggested Status Catalogues

| Catalogue | Suggested values |
| --- | --- |
| Lead status | New, Unassigned, Assigned, Contact Attempted, Contacted, Interested, Follow-up Required, |
|   | Appointment Booked, Attended, No-show, Treatment Accepted, Won, Lost, Invalid, Duplicate |
| Appointment status | Pending, Booked, Confirmed, Rescheduled, Cancelled, Checked In, Attended, No-show, Completed |
| Call outcome | Answered, No Answer, Busy, Voicemail, Wrong Number, Callback Requested, Interested, Not |
|   | Interested, Appointment Booked |
| Task status | Pending, In Progress, Completed, Overdue, Cancelled |
| Payment status | Estimated, Deposit Received, Partially Paid, Fully Paid, Refunded, Cancelled |
| Priority | Low, Normal, High, Urgent |

## SECTION B

## Appendix B - Core Acceptance Checklist

- Company owns GitHub, Supabase, Vercel, domain and integration accounts.

- Staging and production are isolated.

- Database migrations can recreate the schema.

- All exposed tables and storage buckets have tested RLS policies.

- Roles and clinic boundaries pass negative security tests.

- Lead timeline records all approved activities.

- Appointment workflow matches operations.

- Revenue and KPI calculations reconcile against agreed samples.

- Migration totals reconcile and rejected records are documented.

- Error monitoring, backups and restore instructions are active.

- Admin and deployment documents are delivered.

- Public forms, quiz and booking create correctly attributed CRM records.

- Interactive views, drill-downs, drawers and keyboard flows pass usability and accessibility checks.

- AI runs are permission-scoped, logged, evaluated and require approval for controlled actions.

- Client completes UAT and signs production acceptance.

## SECTION C

## Appendix C - Official Technology References

Next.js 16.2 release: https://nextjs.org/blog/next-16-2 [URL 🔗](https://nextjs.org/blog/next-16-2)

Next.js version 16 upgrade guidance: https://nextjs.org/docs/app/guides/upgrading/version-16 [URL 🔗](https://nextjs.org/docs/app/guides/upgrading/version-16)

React 19.2 release: https://react.dev/blog/2025/10/01/react-19-2 [URL 🔗](https://react.dev/blog/2025/10/01/react-19-2)

TypeScript 6.0 release notes: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html [URL 🔗](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html)

Tailwind CSS 4.3 release: https://tailwindcss.com/blog/tailwindcss-v4-3 [URL 🔗](https://tailwindcss.com/blog/tailwindcss-v4-3)


Supabase documentation: https://supabase.com/docs [URL 🔗](https://supabase.com/docs)

Supabase with Next.js: https://supabase.com/docs/guides/getting-started/quickstarts/nextjs [URL 🔗](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)

Supabase SSR client guidance: https://supabase.com/docs/guides/auth/server-side/creating-a-client [URL 🔗](https://supabase.com/docs/guides/auth/server-side/creating-a-client)

Supabase API key migration: https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys [URL 🔗](https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys)

Vercel AI SDK: https://vercel.com/docs/ai-sdk [URL 🔗](https://vercel.com/docs/ai-sdk)

Vercel AI Gateway: https://vercel.com/docs/ai-gateway [URL 🔗](https://vercel.com/docs/ai-gateway)

AI SDK structured data: https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data [URL 🔗](https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data)

Supabase Background Tasks: https://supabase.com/docs/guides/functions/background-tasks [URL 🔗](https://supabase.com/docs/guides/functions/background-tasks)

Supabase Semantic Search: https://supabase.com/docs/guides/functions/examples/semantic-search [URL 🔗](https://supabase.com/docs/guides/functions/examples/semantic-search)

Vercel supported Node.js versions: https://vercel.com/docs/functions/runtimes/node-js/node-js-versions [URL 🔗](https://vercel.com/docs/functions/runtimes/node-js/node-js-versions)

Technology versions in this document were verified against official release and documentation pages on 10 July 2026.

## Final recommendation

Proceed with a paid discovery and parity-mapping milestone before committing to a fixed full-build price. The first milestone should produce the signed public-site sitemap, content inventory, interactive screen prototype, role matrix, schema, report definitions, AI use-case and data policy, integration list and final delivery backlog.
