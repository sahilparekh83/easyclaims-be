# EasyClaims CRM — API Design Spec (v2)

## Overview

Extend `easyclaims_backend` with a full CRM layer covering three portals: SuperAdmin, Partner, and Customer (Member). The existing auth system (OTP login, JWE tokens, session management, user/role tables) is already in place and is not modified — only extended.

---

## Portals & Access Control

| Portal | `user_type` | Route Prefix | Scope |
|---|---|---|---|
| SuperAdmin | `SUPERADMIN` | `/api/v1/admin/` | Full system control |
| Partner | `PARTNER` | `/api/v1/partner/` | Own members only |
| Customer | `CUSTOMER` | `/api/v1/me/` | Own data, scoped by X-Partner-Id |

`user_type` enum gains a third value: `PARTNER`. JWT payload includes `user_type`.

---

## Member ↔ Partner: Many-to-Many via Enrollments

A member (CUSTOMER user) can be enrolled under **multiple partners simultaneously**, each with their own plan assignment. The `member_enrollments` table is the join:

```
user_id + partner_id → UNIQUE (one enrollment per member per partner)
```

There is **no `partner_id` on the `users` table**. Partner context for member sessions is carried via the `X-Partner-Id` request header (CUSTOMER logins only).

---

## Plan Types: Global vs Partner

`membership_plans.plan_type` = `'global'` | `'partner'`

- **Global** — automatically visible to all partners. No linking required.
- **Partner** — must be explicitly linked to one or more specific partners via the `partner_plans` junction table.

When a partner views their available plans (to assign to a member), they see:
- All `Active` + `global` plans
- All `Active` + `partner` plans linked to their `partner_id`

---

## X-Partner-Id Header (Customer sessions only)

After login, a CUSTOMER's JWT contains no partner_id. The client:

1. Calls `GET /me/partners` → receives all enrollments + partner details
2. Selects the first active enrollment as default (`is_default: true` in response)
3. Sends `X-Partner-Id: <partner_id>` header with every `/me/` request

The `_require_customer_enrollment` dependency reads this header, finds the `member_enrollments` row for `(user_id, partner_id)`, and returns the enrollment object. All `/me/` routes use this enrollment as their scope.

If `X-Partner-Id` is absent, the dependency auto-selects the first active enrollment.

**Login response** (for CUSTOMER users) includes `default_partner_id` — the partner_id of their first active enrollment — so the client can set the header immediately after login without a second API call.

---

## Database Schema (new tables)

### `membership_plans`
```sql
id           UUID PK
name         VARCHAR NOT NULL UNIQUE
tagline      VARCHAR NOT NULL DEFAULT ''
info_text    TEXT
price        INTEGER NOT NULL DEFAULT 0
cycle        VARCHAR NOT NULL DEFAULT 'Annual'   -- 'Annual'|'Half-yearly'|'Quarterly'
plan_type    VARCHAR NOT NULL DEFAULT 'global'   -- 'global'|'partner'
status       VARCHAR NOT NULL DEFAULT 'Draft'    -- 'Draft'|'Active'|'Archived'
color        VARCHAR DEFAULT 'var(--blue-500)'
popular      BOOLEAN DEFAULT FALSE
is_deleted   BOOLEAN DEFAULT FALSE
-- Benefits
benefit_family              INTEGER DEFAULT 2
benefit_slots               INTEGER DEFAULT 3
benefit_claim               VARCHAR DEFAULT 'Standard'
benefit_aiqa                BOOLEAN DEFAULT TRUE
benefit_aicalls             BOOLEAN DEFAULT FALSE
benefit_voice               VARCHAR DEFAULT 'English'
benefit_vault               BOOLEAN DEFAULT TRUE
benefit_rm                  BOOLEAN DEFAULT FALSE
benefit_concierge           BOOLEAN DEFAULT FALSE
benefit_teleconsult_sessions INTEGER DEFAULT 0
benefit_hospital_cash       BOOLEAN DEFAULT FALSE
benefit_wellness_sessions   INTEGER DEFAULT 0
benefit_emergency_assist    BOOLEAN DEFAULT FALSE
benefit_legal_assist        BOOLEAN DEFAULT FALSE
created_at   TIMESTAMPTZ DEFAULT now()
updated_at   TIMESTAMPTZ DEFAULT now()
```

### `partners`
```sql
id             UUID PK
user_id        UUID FK → users(id) UNIQUE
name           VARCHAR NOT NULL
partner_type   VARCHAR NOT NULL DEFAULT 'Broker'
city           VARCHAR
status         VARCHAR NOT NULL DEFAULT 'Active'
api_key        VARCHAR UNIQUE
api_rate_limit INTEGER DEFAULT 600
is_deleted     BOOLEAN DEFAULT FALSE
created_at     TIMESTAMPTZ DEFAULT now()
updated_at     TIMESTAMPTZ DEFAULT now()
```

### `partner_plans` (junction: which partner-type plans are available to which partners)
```sql
id         UUID PK
partner_id UUID FK → partners(id)
plan_id    UUID FK → membership_plans(id)
created_at TIMESTAMPTZ DEFAULT now()
UNIQUE(partner_id, plan_id)
```

### `member_enrollments` (replaces member_subscriptions; many-to-many member↔partner)
```sql
id         UUID PK
user_id    UUID FK → users(id)
partner_id UUID FK → partners(id)
plan_id    UUID FK → membership_plans(id)
status     VARCHAR NOT NULL DEFAULT 'active'   -- 'active'|'pending'|'expiring'|'inactive'
start_date DATE NOT NULL
end_date   DATE NOT NULL
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
UNIQUE(user_id, partner_id)
```

### `member_profiles` (1:1 with CUSTOMER users)
```sql
user_id           UUID PK FK → users(id)
gender            VARCHAR
dob               DATE
address_line      VARCHAR
address_city      VARCHAR
address_state     VARCHAR
address_pin       VARCHAR
preferred_language VARCHAR DEFAULT 'English'
channel_email     BOOLEAN DEFAULT TRUE
channel_whatsapp  BOOLEAN DEFAULT FALSE
channel_voice     BOOLEAN DEFAULT FALSE
created_at        TIMESTAMPTZ DEFAULT now()
updated_at        TIMESTAMPTZ DEFAULT now()
```

### `family_members`
```sql
id            UUID PK
user_id       UUID FK → users(id)
name          VARCHAR NOT NULL
relation      VARCHAR NOT NULL
gender        VARCHAR
dob           DATE
coverage_type VARCHAR DEFAULT 'Health'
created_at    TIMESTAMPTZ DEFAULT now()
updated_at    TIMESTAMPTZ DEFAULT now()
```

### `nominees`
```sql
id            UUID PK
user_id       UUID FK → users(id)
name          VARCHAR NOT NULL
relation      VARCHAR NOT NULL
share_percent INTEGER NOT NULL
created_at    TIMESTAMPTZ DEFAULT now()
updated_at    TIMESTAMPTZ DEFAULT now()
```

### `dpdp_consents`
```sql
id           UUID PK
user_id      UUID FK → users(id)
consented_at TIMESTAMPTZ NOT NULL
version      VARCHAR NOT NULL
source       VARCHAR NOT NULL DEFAULT 'portal'
created_at   TIMESTAMPTZ DEFAULT now()
```

### `policies`
```sql
id               UUID PK
user_id          UUID FK → users(id)
partner_id       UUID FK → partners(id)   -- scoped to enrollment
policy_number    VARCHAR UNIQUE
policy_type      VARCHAR NOT NULL          -- 'Health'|'Motor'|'Life'
insurer          VARCHAR
sum_insured      BIGINT
start_date       DATE
end_date         DATE
status           VARCHAR DEFAULT 'pending' -- 'pending'|'review'|'approved'
ai_confidence    INTEGER
file_path        VARCHAR
extracted_fields JSONB DEFAULT '{}'
is_deleted       BOOLEAN DEFAULT FALSE
created_at       TIMESTAMPTZ DEFAULT now()
updated_at       TIMESTAMPTZ DEFAULT now()
```

---

## API Routes

### Public plan catalog (any authenticated user)
```
GET  /api/v1/plans           active global plans (all users see these)
GET  /api/v1/plans/{id}      plan detail
```

### SuperAdmin (`/api/v1/admin/`)

**Plans**
```
GET    /plans                       list all plans (all statuses, all types)
POST   /plans                       create plan (plan_type required)
GET    /plans/{id}
PATCH  /plans/{id}
POST   /plans/{id}/activate
POST   /plans/{id}/archive
DELETE /plans/{id}                  soft-delete Draft plans only
POST   /plans/{id}/partners         link partner-type plan to a partner {partner_id}
DELETE /plans/{id}/partners/{pid}   unlink
GET    /plans/{id}/partners         list partners this plan is linked to
```

**Partners**
```
GET    /partners
POST   /partners                    creates PARTNER user + partner record + api_key
GET    /partners/{id}
PATCH  /partners/{id}
DELETE /partners/{id}
POST   /partners/{id}/regenerate-key
GET    /partners/{id}/plans         plans available to this partner (global + linked partner-type)
```

**Members**
```
GET    /members                     all customers (paginated, filter by partner_id/status)
POST   /members                     create member + enrollment {partner_id, plan_id}
GET    /members/{id}                full detail: profile + all enrollments + family + policies
PATCH  /members/{id}                update member info
```

**Dashboard**
```
GET    /dashboard                   system-wide stats
```

### Partner (`/api/v1/partner/`)

**Profile**
```
GET    /profile
PATCH  /profile
```

**Plans** (plans available to this partner)
```
GET    /plans                       global active + their linked partner-type plans
```

**Members**
```
GET    /members                     members enrolled under this partner
POST   /members                     register member under this partner + assign plan
GET    /members/{id}                member detail (their enrollment + family + policies)
PATCH  /members/{id}/plan           switch member's plan (within this partner's available plans)
```

**Dashboard**
```
GET    /dashboard
```

### Customer (`/api/v1/me/`) — all routes require X-Partner-Id header

**Partners & enrollment switcher**
```
GET    /partners                    list all enrollments (all partners member is under)
                                    first active = is_default:true
```

**Plan** (scoped to active enrollment)
```
GET    /plan                        current enrollment plan detail
PUT    /plan                        switch plan within current partner's available plans
```

**Profile**
```
GET    /profile
PATCH  /profile
```

**Family**
```
GET    /family
POST   /family
PATCH  /family/{id}
DELETE /family/{id}
```

**Nominees**
```
GET    /nominees
POST   /nominees                    validates total share% ≤ 100
PATCH  /nominees/{id}
DELETE /nominees/{id}
```

**Consent**
```
GET    /consent                     latest DPDP consent
POST   /consent                     record new consent
```

**Policies** (scoped to active enrollment's partner_id)
```
GET    /policies
POST   /policies                    upload PDF (multipart/form-data)
GET    /policies/{id}
DELETE /policies/{id}
```

**Dashboard**
```
GET    /dashboard                   personal stats across all enrollments
```

---

## Login Response for CUSTOMER

After `POST /auth/verify-otp` for a CUSTOMER user, response includes:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "default_partner_id": "<uuid or null if no enrollments yet>"
}
```
`default_partner_id` is the `partner_id` of the first active enrollment. Client stores this and sends it as `X-Partner-Id` header with all `/me/` calls.

---

## `_require_customer_enrollment` dependency

Reads `X-Partner-Id` header. Looks up `member_enrollments` for `(user_id, partner_id)`. If header absent, auto-selects first active enrollment. Returns the enrollment row. Raises 403 if the enrollment doesn't belong to this user.

---

## File Structure (new files)

```
app/
  constants.py                         MODIFIED — add PARTNER to UserType
  db/
    models/
      plan.py                          NEW — MembershipPlan
      partner.py                       NEW — Partner, PartnerPlan
      member.py                        NEW — MemberProfile, MemberEnrollment, FamilyMember, Nominee, DpdpConsent
      policy.py                        NEW — Policy
    queries/
      plan_query.py                    NEW
      partner_query.py                 NEW
      member_query.py                  NEW
      policy_query.py                  NEW
  schemas/
    plan.py                            NEW
    partner.py                         NEW
    member.py                          NEW
    policy.py                          NEW
  services/
    plan_service.py                    NEW
    partner_service.py                 NEW
    member_service.py                  NEW
    policy_service.py                  NEW
  api/
    deps.py                            NEW — _require_partner, _require_customer, _require_customer_enrollment
    admin/
      __init__.py, plans.py, partners.py, members.py, dashboard.py
    partner/
      __init__.py, profile.py, plans.py, members.py, dashboard.py
    me/
      __init__.py, partners.py, plan.py, profile.py, family.py,
      nominees.py, consent.py, policies.py, dashboard.py
    plans.py                           NEW — public catalog
  services/auth_service.py             MODIFIED — include default_partner_id in login response
  configs/base.py                      MODIFIED — add UPLOAD_DIR
```
