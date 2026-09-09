# Dental CRM Backend (`den_crm`)
## Technical Documentation and Beginner Learning Guide

**Audience:** Founders, product owners, and developers who are new to backend engineering  
**Stack:** FastAPI · Supabase (PostgreSQL) · Redis · Docker · Nginx  
**API version:** `/api/v1` · App version: `1.0.0`  
**Source of truth:** This guide maps concepts to the **actual files in this repository**, not an idealized design.

---

## How to use this document

1. Read **Section 1** first. It is the mental model for every later chapter.
2. Use **Section 2** as a map: “I opened this file — what is it?”
3. Use **Section 3** when you hear a buzzword (JWT, RBAC, idempotency) and want the exact code location.
4. Walk **Section 4** slowly. Those two traces are how a real request moves through the system.
5. Keep **Section 5** open as a glossary while you read.

Think of the backend as a **hospital reception desk**:

- The **client** is the patient.
- **Nginx** is the front door security and queue.
- **FastAPI** is the receptionist who knows which department to call.
- **Routers** are departments (Auth, Appointments, Revenue).
- **Services** are the doctors who apply rules.
- **Models** are clerks who write in the medical records (database).
- **Redis** is a sticky note board for “already done / currently busy / cached answers.”

---

# 1. System Overview and Architecture

## 1.1 What this system is

Dental CRM is a **multi-tenant REST API**. Multiple dental **organizations** can exist. Each organization has **clinics**. Users belong to an organization and (often) to specific clinics. Every request after login must prove **who you are** (authentication) and **what you are allowed to do** (authorization / RBAC), plus **which tenant’s data you may touch** (organization and clinic isolation).

Primary data store for CRM entities (users, leads, appointments, revenue, etc.) is **Supabase PostgreSQL**, accessed through the **Supabase Python client** (`PostgREST`). AI automation tables (prompt versions, AI runs, knowledge chunks) use **SQLAlchemy** via `app/database.py`. **Redis** stores short-lived operational state: rate limits, JWT revocation, cache, idempotency keys, webhook event IDs.

## 1.2 Textual architecture diagram (request lifecycle)

```
┌─────────────┐
│  Client     │  Browser, mobile app, Postman, Stripe/Twilio/Meta servers
│  (HTTPS)    │
└──────┬──────┘
       │  :80 / :443
       ▼
┌─────────────────────────────────────────┐
│  Nginx Gateway  (deploy/nginx/nginx.conf)│
│  • Gzip compression                     │
│  • Security headers                     │
│  • Rate zones: login 5r/m, API 30r/s    │
│  • Reverse proxy to backend:8000        │
└──────┬──────────────────────────────────┘
       │  proxy_pass http://dental_api
       ▼
┌─────────────────────────────────────────┐
│  FastAPI App  (backend/app/main.py)     │
│  Lifespan: init Supabase clients        │
│  CORS middleware                        │
│  Exception handlers (400–500, 429)      │
│  SlowAPI limiter attached to app.state  │
└──────┬──────────────────────────────────┘
       │  Router match on /api/v1/...
       ▼
┌─────────────────────────────────────────┐
│  Route layer  (backend/app/api/*.py)    │
│  1. Rate limit decorator (login, AI)    │
│  2. Pydantic body/query validation      │
│  3. Depends(get_current_user) → JWT     │
│  4. Optional Idempotency-Key            │
│  5. Role / tenant checks in the handler │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Service layer (backend/app/services/)  │
│  RBAC via has_permission(...)           │
│  Clinic/org boundary checks             │
│  Audit logging                          │
│  Cache get/set/invalidate               │
└──────┬──────────────────────────────────┘
       │
       ├──────────────┬──────────────┬─────────────────┐
       ▼              ▼              ▼                 ▼
┌────────────┐ ┌────────────┐ ┌────────────┐  ┌─────────────────┐
│ Supabase   │ │ SQLAlchemy │ │ Redis      │  │ External APIs   │
│ PostgreSQL │ │ (AI tables)│ │ cache,     │  │ Gemini (OpenAI  │
│ CRM tables │ │ get_db()   │ │ JWT block, │  │  compatible),   │
│            │ │            │ │ idempotency│  │ Stripe, Twilio, │
└────────────┘ └────────────┘ └────────────┘  │ Meta Lead Ads   │
                                              └─────────────────┘
```

**Docker Compose** (`docker-compose.yml`) runs three containers on `dental_network`:

| Service    | Image / build              | Responsibility |
|-----------|----------------------------|----------------|
| `gateway` | `nginx:alpine`             | Public entry, rate zones, proxy |
| `backend` | `deploy/Dockerfile` (Python 3.12 + Uvicorn workers) | Business API |
| `redis`   | `redis:7-alpine` (AOF persistence) | Shared cache / limiter / keys |

## 1.3 Why each technology exists in *this* project

| Technology | Why it was chosen here | Exact responsibility in this repo |
|------------|------------------------|-----------------------------------|
| **FastAPI** | Fast Python APIs, automatic OpenAPI (`/docs`, `/scalar`), `Depends()` for auth | Entire HTTP surface in `app/main.py` and `app/api/` |
| **Supabase** | Hosted PostgreSQL + REST-style client; RLS can sit at DB level | CRM CRUD via `app/core/supabase_client.py` and `app/models/*.py` |
| **Redis** | Fast key-value store with TTL | Rate limits, JWT `jti` blacklist, report/clinic/revenue cache, 24h idempotency, 7-day webhook dedupe. If Redis is down, `ResilientRedisClient` uses in-memory fallback |
| **Nginx** | Battle-tested reverse proxy | SSL-ready front door, Gzip, DDoS-style request limiting, forwards to Uvicorn |
| **Docker Compose** | Repeatable local/prod-like topology | One command starts gateway + API + Redis |
| **Pydantic** | Typed request/response contracts | `app/schemas/` — invalid JSON never reaches business logic (422) |
| **SlowAPI** | Drop-in HTTP rate limiting | `app/core/rate_limiter.py`; Redis URI when `REDIS_URL` is set |
| **python-jose JWT (HS256)** | Stateless sessions without storing every session in Postgres | Access (30 min) + refresh (7 days) in `app/services/auth.py` |
| **Gemini via OpenAI SDK** | One client library; Gemini exposes an OpenAI-compatible URL | `app/services/openai_service.py` |
| **SQLAlchemy + Alembic** | ORM + migrations for AI automation tables | `app/database.py`, `app/models/ai_automation.py`, `alembic/` |

## 1.4 Layered design (the rule of this codebase)

| Layer | Folder | Allowed to |
|-------|--------|------------|
| **API / Router** | `app/api/` | Parse HTTP, call services, return schemas. Should stay thin. |
| **Service** | `app/services/` | Permissions, tenant rules, orchestration, audit. |
| **Model** | `app/models/` | Talk to Supabase tables (or SQLAlchemy for AI). |
| **Schema** | `app/schemas/` | Shape of JSON in and out. No database calls. |
| **Core** | `app/core/` | Config, Redis, cache, JWT helpers, exceptions, roles. |

If you remember only one architecture rule: **routers do not contain the real business rules; services do.** (Some routers also enforce extra tenant checks — that is defense in depth.)

---

# 2. Project Directory and File-by-File Guide

## 2.1 Full directory tree (source and config; omitting `__pycache__` and binary PDFs)

```
den-orm/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   ├── README
│   └── versions/
│       ├── 88fe24ac8b12_baseline_schema.py
│       ├── 2c6db800bb3e_add_hashed_password_to_users.py
│       ├── 4679bc5e7f8b_add_ai_automation_tables.py
│       └── da46f6e2485e_add_rls_policies_to_users.py
├── docker-compose.yml
├── deploy/
│   ├── Dockerfile
│   └── nginx/nginx.conf
├── generate_hash.py
├── generate_comprehensive_audit_pdf.py
├── PROJECT_SUMMARY.md
├── README.md
├── documents/
│   ├── Dental_CRM_AI_Automation_Interactive_Platform_Specification.md
│   └── (this learning guide)
└── backend/
    ├── app/
    │   ├── main.py
    │   ├── database.py
    │   ├── __init__.py
    │   ├── api/          # HTTP routers
    │   ├── core/         # platform utilities
    │   ├── models/       # data access
    │   ├── schemas/      # Pydantic contracts
    │   └── services/     # business logic
    ├── tests/
    ├── migrations/001_initial_schema.sql
    ├── requirements.txt
    ├── README.md
    ├── QUICKSTART.md
    ├── DOCUMENTATION_URDU.md
    └── generate_change_report_pdf.py
```

---

## 2.2 Application entry and platform

### `backend/app/main.py`

**Purpose:** Creates the FastAPI application, wires middleware, routers, health checks, and docs.

**Key functions / objects:**

| Name | What it does |
|------|----------------|
| `lifespan(app)` | On startup: `init_supabase_clients()`. On shutdown: log only. |
| `app` | FastAPI instance: title from settings, version `1.0.0`. |
| `app.state.limiter` | SlowAPI limiter so `@limiter.limit` works on routes. |
| Exception handlers | Maps `AppException`, HTTP errors, validation, rate limit, and unhandled errors to JSON. |
| `CORSMiddleware` | Allows browser origins from `settings.cors_origins_list`. |
| `include_router(...)` | Mounts all feature routers under `settings.api_prefix` (`/api/v1`). |
| `root()` | `GET /` welcome JSON. |
| `health_check()` | `GET /health` — pings Redis, `SELECT 1` on SQLAlchemy engine, checks Gemini key. |
| `scalar_html()` | `GET /scalar` — Scalar API reference UI. |

**Dependencies:** `core.config`, `core.supabase_client`, `core.rate_limiter`, `core.redis_client`, `core.exceptions`, all `api.*` modules.

---

### `backend/app/database.py`

**Purpose:** SQLAlchemy engine for **AI automation tables** (not the main CRM Supabase client).

**Key items:**

| Name | What it does |
|------|----------------|
| `engine` | Connection pool; `pool_pre_ping=True`. SQLite fallback if `DATABASE_URL` missing. |
| `SessionLocal` | Session factory. |
| `Base` | Declarative base for ORM models. |
| `get_db()` | FastAPI dependency: yield a session, always close it. |

**Dependencies:** `core.config.settings`. Used by `api/ai.py` and `models/ai_automation.py`.

---

### `backend/app/core/config.py`

**Purpose:** Loads environment variables into a typed `Settings` object (`pydantic-settings`).

**Key class:** `Settings`

Important fields: `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM` (default `HS256`), `ACCESS_TOKEN_EXPIRE_MINUTES` (30), `REFRESH_TOKEN_EXPIRE_DAYS` (7), `API_V1_PREFIX` (`/api/v1`), Gemini keys/models, webhook secrets, Google OAuth IDs, `ALLOWED_ORIGINS`.

**Properties:** `api_prefix` (strips trailing slash), `cors_origins_list` (comma-split origins).

**Dependencies:** `.env` at repo/backend paths. Almost every module imports `settings`.

---

### `backend/app/core/roles.py`

**Purpose:** The permission catalog — the “who can do what” dictionary.

**Key classes / functions:**

| Name | What it does |
|------|----------------|
| `UserRole` | Six roles: `super_admin`, `org_admin`, `clinic_manager`, `agent`, `reception`, `finance`. |
| `Permission` | 50+ permission strings like `lead:create`, `payment:process`. |
| `ROLE_PERMISSIONS` | Map from role → set of permissions. Super Admin gets **all** permissions. |
| `get_role_permissions(role)` | Returns the set. |
| `has_permission(role, permission)` | True/False used in services. |
| `get_role_hierarchy()` | Ordered list high → low (informational). |

**Dependencies:** Imported by services (`user`, `lead`, `appointment`, `report`, etc.).

---

### `backend/app/core/auth_utils.py`

**Purpose:** Direct bcrypt hashing (avoids some passlib backend issues).

| Function | What it does |
|----------|----------------|
| `hash_password(password)` | bcrypt hash; truncates to 72 bytes. Used on register. |
| `verify_password(plain, hashed)` | bcrypt check. Used by `AuthService.authenticate_user`. |

---

### `backend/app/core/exceptions.py`

**Purpose:** One JSON error shape for the whole API.

Envelope:

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "...",
    "details": {},
    "timestamp": "..."
  }
}
```

| Name | What it does |
|------|----------------|
| `build_error_response(...)` | Builds that JSON. |
| `AppException` | Base domain error with HTTP status. |
| `NotFoundException` | 404 |
| `UnauthorizedException` | 401 |
| `ForbiddenException` | 403 |
| `ConflictException` | 409 |
| `app_exception_handler` | Catches `AppException`. |
| `http_exception_handler` | Catches FastAPI/Starlette `HTTPException`. |
| `validation_exception_handler` | 422 with field-level details. |
| `rate_limit_exception_handler` | 429. |
| `generic_exception_handler` | 500 without leaking stack traces. |

---

### `backend/app/core/redis_client.py`

**Purpose:** Talk to Redis, or pretend Redis exists using a dict with TTL.

| Class / object | What it does |
|----------------|----------------|
| `InMemoryFallbackStore` | `get/set/delete/exists/flushdb` with expiry. |
| `ResilientRedisClient` | Tries `REDIS_URL` (or localhost); on failure uses fallback. |
| `redis_client` | Global singleton used by cache, auth, idempotency, webhooks. |

`ping()` returns True if either live Redis **or** fallback is usable (health check treats this as Redis component OK even in fallback).

---

### `backend/app/core/cache.py`

**Purpose:** Application cache on top of `redis_client`.

| Name | What it does |
|------|----------------|
| `CacheManager._build_key` | `cache:{prefix}:{identifier}` |
| `CacheManager.get/set` | JSON serialize; default TTL 300 seconds. |
| `CacheManager.invalidate` | Deletes one key. |
| `cached_result(prefix, ttl)` | Decorator: hash args → get or call function → store. |

**Used by:** `api/reports.py`, `api/revenue.py` (`/totals/{clinic_id}`), `api/clinics.py` (`GET /{clinic_id}`).

---

### `backend/app/core/idempotency.py`

**Purpose:** “If the client retries the same payment, do not charge twice.”

| Name | What it does |
|------|----------------|
| `IDEMPOTENCY_TTL_SECONDS` | 24 hours. |
| `IN_PROGRESS_TTL_SECONDS` | 60-second processing lock. |
| `check_idempotency(key)` | Load `idempotency:{key}` from Redis. |
| `lock_idempotency_key(key)` | Set `{status: processing}` if empty. |
| `save_idempotent_response` | Store completed status + body. |
| `release_idempotency_lock` | Delete lock if still processing (on failure). |
| `execute_idempotent(request, key, action)` | Replay, 409 if in-flight, or run `action`. |

**Used by:** `POST /appointments/`, `POST /revenue/{id}/payment`, `POST /revenue/{id}/refund`.

---

### `backend/app/core/rate_limiter.py`

**Purpose:** SlowAPI limiter + clinic-aware key for AI routes.

| Name | What it does |
|------|----------------|
| `get_clinic_rate_limit_key(request)` | Uses `X-Clinic-ID`, `clinic_id` query, or JWT claims; else client IP. |
| `limiter` | Default **120/minute** per IP. Storage: Redis if `REDIS_URL` else `memory://`. |

Login uses `@limiter.limit("5/minute")`. AI summarize uses `@limiter.limit("10/minute", key_func=get_clinic_rate_limit_key)`.

---

### `backend/app/core/async_runner.py`

**Purpose:** Supabase client calls are **synchronous**. FastAPI is **async**. This file runs blocking `.execute()` in a worker thread so the event loop is not frozen.

| Function | What it does |
|----------|----------------|
| `run_in_thread(func, *args)` | `anyio.to_thread.run_sync`. |
| `execute_query(query)` | `await run_in_thread(query.execute)`. |

**Used by:** all Supabase models (`UserModel`, `LeadModel`, …).

---

### `backend/app/core/supabase_client.py`

**Purpose:** Two Supabase clients.

| Function | What it does |
|----------|----------------|
| `get_supabase_client()` | Anon key (limited). |
| `get_supabase_admin_client()` | Service role key (bypasses RLS — used by models). |
| `init_supabase_clients()` | Called at app startup. |
| `get_client()` / `get_admin_client()` | Lazy singletons. |

**Security note for learners:** Service role is powerful. Models use the **admin** client so the **application** must enforce RBAC. Database RLS (see Alembic `da46f6e2485e`) is a second fence when queries use user-scoped keys.

---

### `backend/app/core/__init__.py`

Re-exports settings, roles, and Supabase helpers for shorter imports.

---

## 2.3 API routers (`backend/app/api/`)

Each file creates `APIRouter(prefix=..., tags=...)`. `main.py` mounts them at `/api/v1`.

### `auth.py` — prefix `/auth`

| Endpoint | Function | Purpose |
|----------|----------|---------|
| `POST /register` (201) | `register` | Admin-only user create; hash password; `UserModel.create`. |
| `POST /login` | `login` | JSON or form; 5/min; `AuthService.login`. |
| `POST /refresh` | `refresh_token` | Token rotation. |
| `GET /me` | `get_current_user_info` | Current user from JWT. |
| `POST /logout` | `logout` | `revoke_token` on Bearer JWT. |
| `GET /oauth/google/url` | `get_google_oauth_url` | Builds Google authorize URL. |
| `POST /oauth/google` | `google_oauth_login` | Maps Google identity to CRM user; issues JWTs. |

**Dependencies:** `AuthService`, `UserModel`, `hash_password`, `limiter`, `settings`.

---

### `users.py` — prefix `/users`

| Endpoint | Function |
|----------|----------|
| `GET /` | `get_users` — paginated, tenant scoped |
| `GET /{user_id}` | `get_user` |
| `POST /` (201) | `create_user` — blocks finance/agent/reception; org/clinic boundary |
| `PUT /{user_id}` | `update_user` |
| `DELETE /{user_id}` (204) | `deactivate_user` (soft delete) |

---

### `organizations.py` — prefix `/organizations`

| Endpoint | Function |
|----------|----------|
| `GET /` | Super Admin: all orgs; others: own org only |
| `GET /{org_id}` | `get_organization` |
| `POST /` | Super Admin create |
| `PUT /{org_id}` | Update |

---

### `clinics.py` — prefix `/clinics`

| Endpoint | Function |
|----------|----------|
| `GET /` | List by org or assigned clinics |
| `GET /{clinic_id}` | Cached 5 minutes |
| `POST /` | Create (Super Admin / Org Admin) |
| `PUT /{clinic_id}` | Update + cache invalidate |

---

### `leads.py` — prefix `/leads`

| Endpoint | Function |
|----------|----------|
| `GET /` | Paginated; agent sees only assigned leads |
| `GET /{lead_id}` | One lead |
| `POST /` (201) | Create + tenant check |
| `PUT` / `PATCH /{lead_id}` | Full / partial update |
| `POST /{lead_id}/assign` | RPC-style assign → `ActionSuccessResponse` |
| `DELETE /{lead_id}` (204) | Soft delete (super/org admin) |

---

### `appointments.py` — prefix `/appointments`

| Endpoint | Function |
|----------|----------|
| `GET /` | Paginated list |
| `GET /upcoming` | Upcoming for a clinic |
| `GET /{id}` | One appointment |
| `POST /` (201) | Create + `Idempotency-Key` |
| `PUT` / `PATCH /{id}` | Update |
| `POST /{id}/cancel` | RPC cancel |
| `POST /{id}/checkin` | RPC check-in |
| `DELETE /{id}` (204) | Soft cancel |

---

### `revenue.py` — prefix `/revenue`

| Endpoint | Function |
|----------|----------|
| `GET /` | Paginated, role-scoped |
| `GET /outstanding` | Unpaid |
| `GET /totals/{clinic_id}` | Cached totals |
| `GET /{revenue_id}` | One record |
| `POST /` | Create + invalidate totals cache |
| `PUT /{revenue_id}` | Update |
| `POST /{id}/payment` | Idempotent payment |
| `POST /{id}/refund` | Idempotent refund |

---

### `reports.py` — prefix `/reports`

All GETs use `CacheManager` prefix `reports`, TTL 300s.

| Endpoint | Function |
|----------|----------|
| `/dashboard` | Role-specific dashboard |
| `/leads` | Lead report |
| `/revenue` | Revenue report |
| `/appointments` | Appointment report |
| `/performance/{user_id}` | User performance |

---

### `audit.py` — prefix `/audit`

| Endpoint | Who |
|----------|-----|
| `/entity/{type}/{id}` | Super Admin, Org Admin |
| `/user/{user_id}` | Admins or self |
| `/organization/{org_id}` | Admins; org admin own org only |
| `/security` | Super Admin only |

---

### `ai.py` — prefix `/ai`

| Endpoint | Function | Notes |
|----------|----------|--------|
| `POST /summarize-lead` | `summarize_lead_notes` | 10/min per clinic; Gemini; logs `AIRun` |
| `POST /feedback` | Feedback on a run |
| `POST /prompts`, `GET /prompts/active/{feature}` | Prompt versions (management roles) |
| `POST /usage` | Token cost log |
| `POST /automation-rules`, `GET /.../{org_id}` | Rules |
| `POST /automation-runs` | Rule execution log |
| `POST /knowledge/documents`, `/knowledge/chunks` | RAG metadata + embeddings |

`require_role(MANAGEMENT_ROLES)` is a **dependency factory**: it returns a function FastAPI injects, which 403s if role is not super_admin / org_admin / clinic_manager.

---

### `webhooks.py` — prefix `/webhooks`

**No JWT.** Callers are Stripe, Twilio, Meta. Trust is **HMAC signatures**.

| Endpoint | Function |
|----------|----------|
| `POST /stripe` | Verify `Stripe-Signature`, dedupe `event.id` |
| `POST /twilio` | Verify `X-Twilio-Signature`, parse form, dedupe `MessageSid` |
| `GET /meta-leads` | Challenge: return `hub.challenge` if token matches |
| `POST /meta-leads` | Verify `X-Hub-Signature-256` |

---

## 2.4 Services (`backend/app/services/`)

### `auth.py`

The security heart of the product.

| Function / class | Purpose |
|------------------|---------|
| `security = HTTPBearer()` | Requires `Authorization: Bearer <token>` |
| `is_token_revoked(jti)` | Redis `revoked:jti:{jti}` |
| `revoke_token(token)` | Decode JWT, store jti until `exp` |
| `create_access_token` | HS256, `jti`, `token_type=access`, 30 min |
| `create_refresh_token` | Same, `token_type=refresh`, 7 days |
| `decode_access_token` / `decode_refresh_token` | Verify signature, type, not revoked |
| `get_current_user` | FastAPI dependency: decode → load user → must be active |
| `get_current_super_admin` | Extra 403 if not super admin |
| `AuthService.authenticate_user` | Email + bcrypt |
| `AuthService.login` | Returns user + both tokens |
| `AuthService.rotate_tokens` | Revoke old refresh, issue new pair |

---

### `user.py` — `UserService`

`create_user`, `get_user`, `get_all_users`, `update_user`, `deactivate_user`, `get_users_by_organization`, `get_users_by_clinic`. Uses `has_permission` (`USER_CREATE`, `USER_VIEW`, `USER_MANAGE`, `USER_DELETE`) plus org/clinic scope.

---

### `organization.py` — `OrganizationService`

Create (super admin), get, update, list all. Tenant: org admins cannot read other orgs.

---

### `clinic.py` — `ClinicService`

Create/get/update/list by org or assigned clinics. Managers cannot see unassigned clinics.

---

### `lead.py` — `LeadService`

Create/get/update/assign/delete; list by clinic or organization. Agents scoped to `assigned_to`.

---

### `appointment.py` — `AppointmentService`

Create (permission `APPOINTMENT_CREATE` + clinic assignment), get with role filters, update (`APPOINTMENT_MANAGE`), cancel (`APPOINTMENT_CANCEL`), check-in (reception / clinic_manager / super_admin), list by clinic, upcoming. Writes **audit logs** on create/update/cancel/check-in.

---

### `revenue.py` — `RevenueService`

Create/get/update revenue; `process_payment` / `process_refund`; outstanding; totals. Permission-aware.

---

### `report.py` — `ReportService`

Dispatches dashboards by role (`_get_system_dashboard`, `_get_org_dashboard`, `_get_clinic_dashboard`, `_get_agent_dashboard`, `_get_reception_dashboard`, `_get_finance_dashboard`) plus lead/revenue/appointment/performance reports.

---

### `audit.py` — `AuditService`

`log_action(...)` writes an audit row (sanitizes secrets). Read helpers: entity, user, organization, security logs.

---

### `openai_service.py` — `OpenAIService`

`AsyncOpenAI` client with `base_url=https://generativelanguage.googleapis.com/v1beta/openai/`. `_call_model_with_retry` uses **tenacity**: up to `AI_MAX_RETRIES`, exponential backoff, retry on rate limit and timeout. `generate_lead_summary` tries primary model then `AI_FALLBACK_MODEL`.

---

### `ai_automation.py` — `AIAutomationService`

SQLAlchemy CRUD for prompt versions, runs, feedback, usage, automation rules/runs, knowledge documents/chunks.

---

### `webhook.py` — `WebhookService`

HMAC-SHA256 (Stripe, Meta), HMAC-SHA1 + Base64 (Twilio). Redis keys `webhook:event:{id}` for 7 days.

---

### `services/__init__.py`

Package marker.

---

## 2.5 Models (`backend/app/models/`)

Pattern: class with `TABLE_NAME`, static async methods, `get_admin_client()` + `execute_query`.

| File | Class | Typical methods |
|------|--------|-----------------|
| `user.py` | `UserModel` | create, get_by_id, get_by_email, get_by_email_with_password, get_all, update, delete (deactivate), get_by_organization/clinic |
| `organization.py` | `OrganizationModel` | create, get_by_id, update, delete, get_all, count |
| `clinic.py` | `ClinicModel` | create, get_by_id, update, delete, get_by_organization, get_by_ids |
| `lead.py` | `LeadModel` | CRUD, get_by_clinic/assigned_user/organization/status, search, soft delete |
| `appointment.py` | `AppointmentModel` | CRUD, get_by_clinic/lead/user/status, get_upcoming |
| `revenue.py` | `RevenueModel` | CRUD, get_by_clinic/org/lead, outstanding, totals, create_payment |
| `call.py` | `CallModel` | create, get_by_lead/user/clinic |
| `note.py` | `NoteModel` | CRUD, get_by_lead/clinic, internal notes |
| `task.py` | `TaskModel` | CRUD, get_by_user/clinic/lead, overdue |
| `audit.py` | `AuditModel` | create, get_by_entity/user/org/action, security logs |
| `ai_automation.py` | ORM classes | `AIPromptVersion`, `AIRun`, `AIFeedback`, `AIUsage`, `AutomationRule`, `AutomationRun`, `KnowledgeDocument`, `KnowledgeChunk` (pgvector) |
| `__init__.py` | exports | All CRM `*Model` classes |

**Note:** Call, note, and task **models/schemas exist**, but there is **no dedicated router** in `app/api/` yet. They are ready for future endpoints.

---

## 2.6 Schemas (`backend/app/schemas/`)

Pydantic v2 models. Common pattern: `*Base`, `*Create`, `*Update`, public `*` with `id` and timestamps.

| File | Key types |
|------|-----------|
| `user.py` | `UserCreate` (password min 8), `User`, `UserWithPassword` (internal), `UserLogin`, `Token`, `RefreshTokenRequest`, `GoogleAuthRequest`, `TokenData` |
| `organization.py` | Org create/update/read |
| `clinic.py` | Clinic + `ClinicAssignment` |
| `lead.py` | `LeadStatus`, `LeadSource`, Lead CRUD |
| `appointment.py` | `AppointmentStatus`, `AppointmentType`, CRUD |
| `revenue.py` | `PaymentStatus`, `PaymentType`, `Payment`, Revenue CRUD |
| `call.py` | `CallType`, `CallOutcome` |
| `note.py` | `NoteType` |
| `task.py` | `TaskStatus` |
| `report.py` | `ReportFilter`, `DashboardData`, `LeadReport`, `RevenueReport`, `AppointmentReport`, `UserPerformanceReport` |
| `audit.py` | `AuditAction`, `AuditLog` |
| `ai_automation.py` | Create/Response pairs for all AI tables |
| `common.py` | **`ActionSuccessResponse`** (`success`, `message`, `data`) |
| `pagination.py` | **`PaginatedResponse[T]`** (`data`, `total`, `page`, `limit`, `total_pages`) |
| `__init__.py` | Re-exports public schemas |

---

## 2.7 Tests (`backend/tests/`)

| File | What it proves |
|------|----------------|
| `conftest.py` | `TestClient`, flush Redis/fallback each test |
| `test_rate_limiter.py` | Login 5/minute |
| `test_refresh_token.py` | Rotation |
| `test_jwt_revocation.py` | Logout blacklist |
| `test_idempotency.py` | Replay vs first execution |
| `test_caching.py` | CacheManager set/get/invalidate |
| `test_exception_handling.py` | Standardized 404/422 JSON |
| `test_ai_fallback.py` | Primary fail → fallback model |
| `test_webhooks.py` | Signature / challenge paths |
| `test_soft_delete_and_pagination.py` | Envelope schema |
| `test_audit_remaining_features.py` | Health, PATCH, 204 deletes, assign response, OAuth URL, async runner |

---

## 2.8 Deploy, Docker, migrations, scripts

| File | Purpose |
|------|---------|
| `docker-compose.yml` | gateway, backend (`REDIS_URL=redis://redis:6379/0`), redis AOF |
| `deploy/Dockerfile` | Python 3.12, pip install, `uvicorn app.main:app --workers 4` |
| `deploy/nginx/nginx.conf` | Gzip, `limit_req_zone`, proxy, security headers; HTTPS redirect **commented** |
| `backend/requirements.txt` | fastapi, supabase, redis/slowapi (also installed in Dockerfile), openai, tenacity, jose, bcrypt, sqlalchemy, alembic, … |
| `backend/migrations/001_initial_schema.sql` | Original SQL schema for Supabase |
| `alembic/env.py` | Points at `Base.metadata` including AI models |
| `alembic/versions/*` | Baseline, hashed password, AI tables, RLS on users |
| `generate_hash.py` | Utility to bcrypt a password for seeding |
| `backend/generate_change_report_pdf.py` / `generate_comprehensive_audit_pdf.py` | PDF generators for audit/change reports |
| `backend/README.md`, `QUICKSTART.md`, `DOCUMENTATION_URDU.md` | Human setup notes |
| Root `README.md`, `PROJECT_SUMMARY.md` | Project overview |

---

# 3. Sixteen Architectural Features (Concept → Code → How it works)

## 3.1 REST Endpoints and Modular Routing

**(A) Plain English:** Instead of one giant file of URLs, each business area has its own router. FastAPI **includes** them under a common prefix.

**(B) Where:**

- Mount: `backend/app/main.py` (`app.include_router(..., prefix=settings.api_prefix)`)
- Prefix constant: `Settings.API_V1_PREFIX` in `core/config.py`
- Modules: `app/api/auth.py`, `users.py`, `organizations.py`, `clinics.py`, `leads.py`, `appointments.py`, `revenue.py`, `reports.py`, `audit.py`, `ai.py`, `webhooks.py`

**(C) How it works:** A request to `/api/v1/appointments/` matches the appointments router (`prefix="/appointments"`) + `GET /`. OpenAPI tags group them in `/docs`. There are **50+** operations across these routers (CRUD + RPC + reports + AI + webhooks + health).

---

## 3.2 HTTP Methods and RPC Actions

**(A)** HTTP verbs mean different intents: GET read, POST create, PUT replace, PATCH partial update, DELETE remove. **RPC-style** URLs like `/cancel` are POSTs that **do a named action**, not just store a document.

**(B)** Examples:

| Method | Location |
|--------|----------|
| GET/POST/PUT/PATCH/DELETE | `leads.py`, `appointments.py`, `users.py` |
| POST `/leads/{id}/assign` | `assign_lead` |
| POST `/appointments/{id}/cancel` | `cancel_appointment` |
| POST `/appointments/{id}/checkin` | `checkin_appointment` |
| POST `/revenue/{id}/payment` | `process_payment` |
| POST `/revenue/{id}/refund` | `process_refund` |

**(C)** PATCH and PUT both call the same service `update_*` with `AppointmentUpdate` / `LeadUpdate` (optional fields). DELETE often returns **204** with empty body. RPC endpoints return `ActionSuccessResponse`.

---

## 3.3 Request/Response Schemas and Pydantic

**(A)** A **schema** is a contract: “this JSON must include an email, and password at least 8 characters.” FastAPI uses Pydantic to reject bad data **before** your code runs.

**(B)** Schema modules listed in §2.6 (15+ files). Standard action wrapper: `app/schemas/common.py` → `ActionSuccessResponse`. Pagination: `app/schemas/pagination.py`.

**(C)** Example: `POST /auth/login` accepts `UserLogin`. Invalid email → **422** via `validation_exception_handler`. Successful login returns `Token` (`access_token`, `refresh_token`, `user`).

---

## 3.4 HTTP Status Codes and Error Handling

**(A)** Status codes are a shared language: 201 = created, 204 = success with no body, 401 = not logged in, 403 = logged in but not allowed, 404 = missing, 409 = conflict, 422 = invalid shape, 429 = slow down.

**(B)** Success codes in routers (`status.HTTP_201_CREATED`, `HTTP_204_NO_CONTENT`). Errors: `core/exceptions.py` + many `HTTPException` raises in services.

**(C)** Handlers in `main.py` convert every exception type into the same `{success: false, error: {...}}` JSON so frontends can parse errors uniformly.

| Code | Typical meaning in this API |
|------|-----------------------------|
| 200 | OK |
| 201 | User/lead/appointment created |
| 204 | Soft-deleted user/lead/appointment |
| 400 | Bad input (e.g. missing login fields, Stripe signature fail) |
| 401 | Bad/missing/revoked JWT |
| 403 | RBAC or tenant wall |
| 404 | Entity missing |
| 409 | Idempotency key still processing |
| 422 | Pydantic validation |
| 429 | SlowAPI or (at gateway) Nginx `limit_req` |
| 500 | Unexpected; message is generic |

---

## 3.5 Authentication and Token Blacklisting

**(A)** **Authentication** = proving you are the account owner. Passwords are stored as **bcrypt hashes**, never plaintext. After login you send a **JWT**. **Blacklisting** = even a valid JWT can be killed (logout) by storing its ID (`jti`) in Redis until it would have expired.

**(B)**

- Bearer extraction: `HTTPBearer` in `services/auth.py`
- Hash: `core/auth_utils.py` (login verify) and `hash_password` on register
- Revoke: `revoke_token`, `is_token_revoked`
- Logout: `api/auth.py` → `logout`

**(C)** Login issues a JWT with unique `jti`. `get_current_user` decodes, checks `token_type == access`, checks Redis `revoked:jti:{jti}`, loads user from DB. Logout writes that key with TTL ≈ remaining lifetime.

---

## 3.6 Authorization (RBAC) and Multi-Tenancy

**(A)** **RBAC** = your **role** is a badge that unlocks a set of **permissions**. **Multi-tenancy** = Org A must not see Org B’s patients, even if both users are “org_admin.” Clinic managers are further limited to `assigned_clinics`.

**(B)**

- Catalog: `core/roles.py` (`UserRole`, `Permission`, `ROLE_PERMISSIONS`, `has_permission`)
- Service checks: e.g. `AppointmentService.create_appointment` → `Permission.APPOINTMENT_CREATE`
- Extra router checks: `users.py` (who may create which roles), `leads.py` (org_id must match), `revenue.py` (finance vs clinic_manager)
- AI admin: `require_role` in `api/ai.py`
- Audit reads: `api/audit.py`

**(C)** Six roles (see README table). Example: Agent has `LEAD_MANAGE` but listing leads uses `LeadModel.get_by_assigned_user` so they never receive another agent’s pipeline. Org Admin creating a user for another `organization_id` gets **403**.

---

## 3.7 Access and Refresh Tokens

**(A)** **Access token** = short-lived hall pass (30 minutes) sent on every API call. **Refresh token** = longer pass (7 days) used only at `/auth/refresh` to get a new pair. **Rotation** = old refresh token is revoked so stolen refresh tokens cannot be reused forever.

**(B)** `create_access_token` / `create_refresh_token` / `AuthService.rotate_tokens` in `services/auth.py`. Endpoint: `POST /api/v1/auth/refresh` in `api/auth.py`. Settings: `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `JWT_ALGORITHM=HS256`.

**(C)** Both tokens include `sub` (user id), `email`, `role`, `organization_id`, `assigned_clinics`, `jti`, `exp`, `token_type`. Refresh endpoint refuses access tokens (`token_type` must be `refresh`). Then `revoke_token(old)` and mint new access + refresh.

---

## 3.8 Throttling and Rate Limiting

**(A)** Rate limiting is a speed bump so attackers cannot try thousands of passwords or burn your Gemini budget.

**(B)**

- App: `core/rate_limiter.py` + `@limiter.limit` on `login` and `summarize_lead_notes`
- Gateway: `deploy/nginx/nginx.conf` — `login_limit` 5r/m, `api_limit` 30r/s

**(C)** SlowAPI counts requests in Redis (or memory). Exceed → `RateLimitExceeded` → 429 JSON. Nginx **also** limits before the request hits Python (defense in depth). AI uses clinic-scoped keys so one clinic cannot starve others as easily as a global IP limit.

---

## 3.9 OAuth 2.0 (Google SSO)

**(A)** Instead of typing a CRM password, the user proves identity with Google, then this API issues **the same JWT pair** as password login.

**(B)** `GET /api/v1/auth/oauth/google/url` and `POST /api/v1/auth/oauth/google` in `api/auth.py`. Config: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`.

**(C)** URL endpoint concatenates Google’s authorize endpoint with client id, redirect URI, `openid email profile`. Token endpoint accepts `GoogleAuthRequest.id_token`, extracts email (including **dev mock** `mock_google_{email}`), looks up `UserModel.get_by_email`, rejects unknown/deactivated users, then `create_access_token` + `create_refresh_token`.

**Learner note:** Production-grade Google SSO should **verify** the ID token signature with Google’s keys (`google-auth` is already in `requirements.txt`). The current handler focuses on mapping a verified email to a pre-provisioned CRM user.

---

## 3.10 Universal Pagination

**(A)** Lists can be huge. Pagination returns **one page** plus metadata: total count, page number, page size, total pages.

**(B)** `PaginatedResponse[T]` in `schemas/pagination.py`. Used on `GET /users`, `/leads`, `/appointments`, `/revenue`.

**(C)** `PaginatedResponse.create(items, total, page, limit)` computes `total_pages`. Query params: `page` (min 1), `limit` (capped), optional `offset`. Services/models accept `limit`/`offset`/`return_count` where implemented; appointments currently slice an in-memory list after fetch.

---

## 3.11 Caching and Invalidation

**(A)** **Cache** = remember an expensive answer for a few minutes. **Invalidation** = throw it away when the underlying data changes so users do not see stale money totals.

**(B)** `CacheManager` in `core/cache.py`.

| Read (cached) | Write (invalidate) |
|---------------|-------------------|
| `GET /reports/*` | Reports currently expire by **TTL (5 min)**; writes do not flush all report keys |
| `GET /revenue/totals/{clinic_id}` | `POST /revenue`, payment, refund invalidate `revenue_totals` |
| `GET /clinics/{id}` | `PUT /clinics/{id}` invalidates `clinics` |

**(C)** Key = `cache:{prefix}:{id}`. Redis (or memory fallback). If Redis dies, cache still works locally per process (not shared across Uvicorn workers).

---

## 3.12 Idempotency

**(A)** Networks retry. Without idempotency, two identical “take $500” requests could take $1000. The client sends header **`Idempotency-Key: <unique-id>`**. The server remembers the first result for 24 hours.

**(B)** `execute_idempotent` in `core/idempotency.py`. Wired in `appointments.create_appointment`, `revenue.process_payment`, `revenue.process_refund`.

**(C)** No header → run normally. Header too long (>128) → 400. Existing `completed` → replay JSON + `X-Idempotent-Replay: true`. `processing` → 409. Else lock 60s, run action, save body 24h; on exception, release lock so a retry can proceed.

---

## 3.13 Webhooks Integration

**(A)** External systems **push** events to you. Anyone could POST fake “payment succeeded” unless you verify a **shared secret HMAC**. Providers also retry; Redis event IDs ignore duplicates.

**(B)** Router `api/webhooks.py`. Crypto `services/webhook.py`. Secrets in `Settings.WEBHOOK_*`.

**(C)** Stripe: parse `t=` and `v1=` from `Stripe-Signature`, HMAC-SHA256 of `timestamp.payload`. Twilio: HMAC-SHA1 of URL + sorted form fields, Base64 compare to `X-Twilio-Signature`. Meta: GET challenge; POST `sha256=` HMAC of raw body.

---

## 3.14 API Versioning

**(A)** Putting **v1** in the URL lets you later add `/api/v2` without breaking old mobile apps.

**(B)** `API_V1_PREFIX = "/api/v1"` in `core/config.py`; `settings.api_prefix` used in `main.py`. Nginx login location is hard-coded `/api/v1/auth/login`.

**(C)** All feature routers are mounted once under that prefix. Health and docs stay unversioned (`/health`, `/docs`) so load balancers stay simple. Transition readiness = new routers can be `include_router(..., prefix="/api/v2")` while v1 remains.

---

## 3.15 AI Engine Integration

**(A)** The CRM asks a language model to summarize lead notes. The code speaks the **OpenAI Chat Completions** protocol, but the **server** is Google Gemini. If Gemini is slow or rate-limited, **retry**; if the primary model is down, **fallback** to a cheaper/older model. Each successful summarize logs **tokens and estimated cost** into `ai_runs`.

**(B)**

- Client: `services/openai_service.py` (`AsyncOpenAI`, `tenacity.retry`)
- Config: `GEMINI_API_KEY`, `AI_PRIMARY_MODEL`, `AI_FALLBACK_MODEL`, `AI_MAX_RETRIES`, `AI_TIMEOUT_SECONDS`
- HTTP: `api/ai.py` `summarize_lead_notes`
- Persistence: `AIAutomationService.create_ai_run` → table `ai_runs` (`models/ai_automation.py`)

**(C)** See **Trace B** in Section 4.

---

## 3.16 API Gateway and Reverse Proxy

**(A)** A **reverse proxy** is a bouncer: clients talk only to Nginx. Nginx talks to Uvicorn on the private Docker network. That lets you add SSL, compression, and coarse rate limits without changing Python.

**(B)** `docker-compose.yml` service `gateway`. Config `deploy/nginx/nginx.conf`. App image `deploy/Dockerfile`.

**(C)** `upstream dental_api { server backend:8000; }`. Gzip on JSON. Zones: `api_limit` 30 requests/second/IP, `login_limit` 5/minute. Headers: `X-Frame-Options DENY`, `nosniff`, CSP. TLS listen 443 is defined at compose ports; the **HTTP→HTTPS redirect is commented** until certificates are installed. This is the “SSL termination / DDoS shielding” layer (request-flood shielding via `limit_req`, not a full WAF).

---

# 4. Step-by-Step Execution Traces

## Trace A — Login, then create an appointment (idempotency + RBAC + DB + cache)

**Story:** Receptionist Maya logs in and books a cleaning. Her phone retries the create request with the same `Idempotency-Key`.

```
Maya's app
   │
   │ 1. POST /api/v1/auth/login  {email, password}
   ▼
Nginx  (location /api/v1/auth/login → login_limit 5r/m)
   │
   ▼
FastAPI CORS → route auth.login
   │  SlowAPI 5/minute per IP
   │  Parse JSON or form
   ▼
AuthService.login
   │  UserModel.get_by_email_with_password
   │  bcrypt verify_password
   │  create_access_token + create_refresh_token  (HS256, jti)
   ▼
Response 200 Token { access_token, refresh_token, user }

Maya's app
   │ 2. POST /api/v1/appointments/
   │    Authorization: Bearer <access>
   │    Idempotency-Key: 8f3c-maya-booking-1
   │    body: AppointmentCreate JSON
   ▼
Nginx  location /  → api_limit 30r/s → proxy backend:8000
   ▼
FastAPI → appointments.create_appointment
   │  Pydantic validates AppointmentCreate
   │  Depends(get_current_user):
   │     HTTPBearer extracts token
   │     decode_access_token (signature, exp, token_type=access)
   │     is_token_revoked(jti)? if yes → 401
   │     UserModel.get_by_id; is_active?
   │  Tenant: if not super_admin, organization_id must match Maya's org
   │  execute_idempotent:
   │     Redis GET idempotency:8f3c-maya-booking-1
   │     miss → SET processing (60s)
   │     AppointmentService.create_appointment
   │        has_permission(role, APPOINTMENT_CREATE)? else 403
   │        clinic_id in assigned_clinics for agent/manager?
   │        AppointmentModel.create → Supabase insert (thread via execute_query)
   │        AuditService.log_action("appointment.create")
   │     save_idempotent_response 24h
   ▼
Response 201 Appointment

If Maya's app retries the same key:
   execute_idempotent finds status=completed
   → JSON replay + header X-Idempotent-Replay: true
   → NO second database insert
```

**Cache note:** Creating an appointment does **not** currently call `CacheManager.invalidate("reports", ...)`. Dashboard/appointment reports may stay cached up to **5 minutes**. Revenue totals cache is invalidated on **revenue** writes, not on appointments. Clinic metadata cache is unrelated unless the clinic record itself changes.

```
                     ┌──────────┐
  Login ────────────►│  Redis   │  (optional: limiter counters)
                     │          │
  Create appt ──────►│ idempotency:key = completed + body
                     └──────────┘
  Create appt ──────► Supabase "appointments" table
  Create appt ──────► Supabase "audit" table
```

---

## Trace B — Clinic user runs AI lead summary (limit, Gemini retry/fallback, cost log)

**Story:** Clinic manager Omar pastes call notes and clicks “Summarize.”

```
Omar's app
   │  POST /api/v1/ai/summarize-lead
   │  Authorization: Bearer <access>
   │  X-Clinic-ID: <clinic uuid>   (optional but used for rate key)
   │  { "lead_notes": "Patient asked about implants..." }
   ▼
Nginx api_limit → FastAPI
   ▼
ai.summarize_lead_notes
   │  @limiter.limit("10/minute", key_func=get_clinic_rate_limit_key)
   │     key = clinic:{id} from header, query, or JWT
   │     over quota → 429 RATE_LIMIT_EXCEEDED
   │  get_current_user (same JWT path as Trace A)
   │  Pydantic SummaryRequest (lead_notes required)
   │  start_time = now
   ▼
OpenAIService.generate_lead_summary(notes)
   │  messages = system + user notes
   │  _call_model_with_retry(AI_PRIMARY_MODEL)   # e.g. gemini-3.5-flash
   │     AsyncOpenAI → Gemini OpenAI-compatible URL
   │     tenacity: retry RateLimitError / APITimeoutError
   │               stop_after_attempt(AI_MAX_RETRIES)
   │               wait_exponential 2–10s
   │  if still failing:
   │     _call_model_with_retry(AI_FALLBACK_MODEL)  # e.g. gemini-2.5-flash
   │  if fallback fails → exception → HTTP 500 in router
   ▼
AIAutomationService.create_ai_run(db, AIRunCreate)
   │  feature_name=lead_summary
   │  model_name=AI_PRIMARY_MODEL
   │  prompt_tokens, completion_tokens, estimated_cost
   │  latency_ms, organization_id, user_id
   │  SQLAlchemy commit to ai_runs
   ▼
Response 200 SummaryResponse { success, ai_summary, intent }
```

```
[Omar] → Nginx → FastAPI JWT → SlowAPI (clinic key)
              → Gemini primary (+ retries)
              → Gemini fallback if needed
              → Postgres ai_runs (cost audit)
              → JSON summary
```

---

# 5. Beginner’s Glossary and Cheat Sheet

| Term | Simple analogy | In this project |
|------|----------------|-----------------|
| **JWT** | A signed paper wristband at a concert. Staff can check the stamp without calling the box office every time. | HS256 tokens in `create_access_token`. |
| **jti** | Serial number on the wristband. If stolen, security puts that number on a ban list. | Redis `revoked:jti:{jti}`. |
| **RBAC** | Job titles on hospital badges: receptionist vs surgeon. | `UserRole` + `Permission` in `roles.py`. |
| **Middleware** | A metal detector everyone walks through before any department. | CORS in `main.py`; SlowAPI; exception handlers. |
| **Schema** | A form that rejects scribbles (missing phone, bad email). | Pydantic in `app/schemas/`. |
| **Idempotency** | “If you already paid this invoice number, don’t pay again.” | `Idempotency-Key` + Redis 24h. |
| **HMAC** | A wax seal made with a secret stamp. If the wax doesn’t match, the letter is forged. | Stripe/Meta/Twilio webhook signatures. |
| **Dependency Injection** | FastAPI fills in “current user” for you, like a nurse handing the doctor the chart. | `Depends(get_current_user)`, `Depends(get_db)`. |
| **Redis** | A whiteboard of sticky notes that expire. Extremely fast, not the patient archive. | Cache, rate limits, locks, blacklists. |
| **Reverse proxy** | Front desk: visitors never walk into the operating room; the desk forwards messages inside. | Nginx → `backend:8000`. |
| **Supabase** | Hosted PostgreSQL plus an HTTP client to tables. | `get_admin_client().table(...).insert()`. |
| **FastAPI Router** | A department directory. | `APIRouter(prefix="/leads")`. |
| **Service vs Model** | Doctor (rules) vs records clerk (filing). | `*Service` vs `*Model`. |
| **Soft delete** | File marked “inactive,” not shredded. | User deactivate / lead delete returning 204. |
| **Multi-tenancy** | Separate filing cabinets per dental group. | `organization_id` + `assigned_clinics`. |
| **Rate limit** | “Only 5 password attempts per minute.” | SlowAPI + Nginx zones. |
| **Refresh token** | A visitor pass you trade at the desk for a new short wristband. | `POST /auth/refresh` with rotation. |
| **Pagination** | “Show me page 3 of 50 results.” | `PaginatedResponse`. |
| **Cache TTL** | Sticky note that falls off after 5 minutes. | `ttl=300` on reports. |
| **Event loop / async** | One receptionist handling many callers by not waiting on hold. Blocking DB calls go to a back office (`execute_query`). | `async_runner.py`. |
| **RLS** | Database itself refuses rows you shouldn’t see. | Alembic `da46f6e2485e_add_rls_policies_to_users.py`. |
| **OpenAPI / Scalar** | Auto-generated instruction booklet of every endpoint. | `/docs`, `/redoc`, `/scalar`. |

---

## Quick “where do I look?” index

| I want to… | Open this file |
|------------|----------------|
| Change token lifetime | `app/core/config.py` |
| Add a permission to Finance | `app/core/roles.py` |
| Understand login | `app/api/auth.py` + `app/services/auth.py` |
| Change appointment rules | `app/services/appointment.py` |
| Change JSON error shape | `app/core/exceptions.py` |
| Tune AI model names | `.env` + `config.py` + `openai_service.py` |
| Add a new REST resource | New `api/*.py` router + `include_router` in `main.py` |
| Change public rate limits | `deploy/nginx/nginx.conf` **and** SlowAPI decorators |

---

## How to convert this guide to PDF

Any of these work:

1. Open this Markdown file in VS Code / Cursor and print to PDF.
2. Use Pandoc: `pandoc documents/Dental_CRM_Backend_Technical_Learning_Guide.md -o documents/Dental_CRM_Backend_Technical_Learning_Guide.pdf`
3. Paste into Google Docs / Word and export PDF.

---

*Generated from the `den-orm` codebase as of the documentation date. If code and this guide disagree, trust the source files listed in each chapter.*
