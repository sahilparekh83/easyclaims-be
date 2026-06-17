# EasyClaims — SuperAdmin Portal Flow

## Overview

The **SuperAdmin** has full control over the platform — they manage plans, partners, members, policy types, and can view all data across all partners. There is no self-registration for SuperAdmin; the first admin is seeded directly into the database.

All SuperAdmin API calls live under `/api/v1/admin/`.

---

## 1. What a SuperAdmin Can Do

| Domain | Capability | API |
|---|---|---|
| Auth | OTP login, refresh, logout | `/auth/*` |
| Plans | Full CRUD, activate/archive, link to partners | `/admin/plans/*` |
| Partners | Create, view, update, deactivate, regen API key | `/admin/partners/*` |
| Members | View all members (or filtered by partner), create, view detail | `/admin/members/*` |
| Policies | View all policies (or filtered by partner), view detail | `/admin/policies/*` |
| Policy Types | Full CRUD, activate/deactivate | `/admin/policy-types/*` |
| Dashboard | Platform-wide stats | `/admin/dashboard` |
| Users | Internal user management (roles, activation) | `/users/*` |

---

## 2. Authentication Flow

### Step 1 — Request OTP

```
POST /api/v1/auth/send-otp
Body: { "email": "admin@easyclaims.in" }
```

### Step 2 — Verify OTP → receive token

```
POST /api/v1/auth/verify-otp
Body: { "email": "admin@easyclaims.in", "otp": "123456" }

Response:
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "user_type": "SUPERADMIN",
    "default_partner_id": null
  }
}
```

JWT payload: `user_type: SUPERADMIN`. Every `/admin/` endpoint validates this.

---

## 3. Dashboard

```
GET /api/v1/admin/dashboard
Header: Authorization: Bearer <token>

Response:
{
  "data": {
    "total_members": 3,
    "active_plans": 3,
    "total_partners": 1,
    "active_enrollments": 1
  }
}
```

---

## 4. Plan Management

Plans are the membership products that members subscribe to. A plan has 14 benefit flags/fields.

**Plan types:**
- `global` — visible to all partners automatically
- `partner` — must be explicitly linked to a partner by admin

**Plan statuses:** `Draft` → `Active` → `Archived`

### List all plans

```
GET /api/v1/admin/plans
Header: Authorization: Bearer <token>

Response: [ { plan objects with all benefit fields } ]
```

### Create a plan

```
POST /api/v1/admin/plans
Header: Authorization: Bearer <token>

Body:
{
  "name": "Total Care",
  "price": 4999,
  "plan_type": "global",
  "benefits": {
    "health": true,
    "life": true,
    "dental": false,
    "vision": false,
    "mental_health": true,
    "maternity": false,
    "family_size": 6,
    "claim_slots": 20,
    "claim_type": "24x7 Priority",
    "voice_consultation": true,
    "voice_language": "English + Hindi",
    "wellness": true,
    "pharmacy": false,
    "ambulance": true
  }
}

benefit.claim_type: "Standard" | "Priority" | "24x7 Priority"
benefit.voice_language: "English" | "English + Hindi"
benefit.family_size: 1–10
benefit.claim_slots: 1–20
```

### Get plan detail

```
GET /api/v1/admin/plans/{plan_id}
Header: Authorization: Bearer <token>
```

### Update plan

```
PATCH /api/v1/admin/plans/{plan_id}
Header: Authorization: Bearer <token>

Body: same as create, all fields optional
```

### Activate / Archive a plan

```
POST /api/v1/admin/plans/{plan_id}/activate
POST /api/v1/admin/plans/{plan_id}/archive
```

- Only `Draft` plans can be activated
- Only `Active` plans can be archived

### Delete a plan

```
DELETE /api/v1/admin/plans/{plan_id}
```

Only allowed when status is `Draft`.

### Link / unlink a plan to a partner (partner-type plans only)

```
POST /api/v1/admin/plans/{plan_id}/partners
Body: { "partner_id": "uuid" }
Validation: plan.plan_type must be "partner"

DELETE /api/v1/admin/plans/{plan_id}/partners/{partner_id}

GET /api/v1/admin/plans/{plan_id}/partners   ← list all partners linked to this plan
```

---

## 5. Partner Management

### List all partners (paginated + filterable)

```
POST /api/v1/admin/partners/list
Header: Authorization: Bearer <token>

Body:
{
  "global_filter": "health",     ← searches name, partner_type, status, city
  "sort_field": "created_at",
  "sort_order": -1,
  "filters": [
    { "field": "status", "operator": "equals", "value": "Active" }
  ],
  "limit": 10,
  "skip": 0
}

filters[].field options: name | partner_type | status | city

Response:
{
  "data": {
    "data": [
      {
        "id": "6cd47d22-...",
        "user_id": "2d42b993-...",
        "name": "HealthBridge Brokers",
        "partner_type": "Broker",
        "city": "Mumbai",
        "status": "Active",
        "api_key": "122ad260b09b48dcbc8ced8374e41e35",
        "api_rate_limit": 600,
        "created_at": "2026-06-16T11:18:24Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 10
  }
}
```

### Create a partner

```
POST /api/v1/admin/partners
Header: Authorization: Bearer <token>

Body:
{
  "name": "AxisCare Insurance",
  "email": "admin@axiscare.in",
  "partner_type": "Insurance Company",
  "city": "Delhi",
  "api_rate_limit": 1000
}

What happens internally:
1. A PARTNER user account is created (email = partner login email)
2. A Partner record is created linked to that user
3. A 32-character hex api_key is auto-generated
4. PARTNER role is assigned

Response:
{
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "name": "AxisCare Insurance",
    "partner_type": "Insurance Company",
    "status": "Active",
    "api_key": "a3f8b2..."
  }
}
```

### Get partner detail

```
GET /api/v1/admin/partners/{partner_id}
Header: Authorization: Bearer <token>
```

### Update partner

```
PATCH /api/v1/admin/partners/{partner_id}
Header: Authorization: Bearer <token>

Body (all optional): { "name": "...", "city": "...", "api_rate_limit": 500 }
```

### Deactivate a partner

```
DELETE /api/v1/admin/partners/{partner_id}
```

Soft delete — sets `is_deleted=true, status=Inactive`. The partner cannot log in after this.

### Regenerate API key

```
POST /api/v1/admin/partners/{partner_id}/regenerate-key

Response: { "data": { "api_key": "new_32_char_hex..." } }
```

### List plans available to a partner

```
GET /api/v1/admin/partners/{partner_id}/plans
```

Returns global Active plans + partner-type Active plans linked to this partner.

---

## 6. Member Management

### List all members (paginated + filterable)

```
POST /api/v1/admin/members/list
Header: Authorization: Bearer <token>

Body:
{
  "global_filter": "rahul",      ← searches name, email, mobile_no
  "sort_field": "created_at",
  "sort_order": -1,
  "filters": [
    { "field": "is_active", "operator": "equals", "value": true }
  ],
  "limit": 10,
  "skip": 0,
  "partner_id": "6cd47d22-..."  ← optional: show only members enrolled under this partner
}

filters[].field options: name | email | mobile_no | is_active

Response:
{
  "data": {
    "data": [
      {
        "id": "c0b50711-...",
        "email": "rahul@example.com",
        "name": "Rahul Sharma",
        "mobile_no": null,
        "is_active": true,
        "enrollments": [
          {
            "partner_id": "6cd47d22-...",
            "plan_id": "92150516-...",
            "status": "active",
            "end_date": "2027-06-16"
          }
        ]
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 10
  }
}
```

**Two access modes:**
- **Direct (no `partner_id`)** — see all members across the entire platform
- **Partner-scoped (`partner_id` set)** — see only members enrolled under that partner

### Create a member (admin-side)

```
POST /api/v1/admin/members
Header: Authorization: Bearer <token>

Body:
{
  "email": "member@example.com",
  "name": "Sunita Patel",
  "mobile_no": "+91-9900000002",
  "plan_id": "92150516-...",
  "partner_id": "6cd47d22-..."
}
```

### Get member detail

```
GET /api/v1/admin/members/{member_id}
Header: Authorization: Bearer <token>

Response:
{
  "data": {
    "id": "...",
    "email": "rahul@example.com",
    "name": "Rahul Sharma",
    "mobile_no": null,
    "is_active": true,
    "enrollments": [
      { "partner_id": "...", "plan_id": "...", "status": "active", "end_date": "2027-06-16" }
    ],
    "profile": {
      "gender": "Male",
      "dob": "1990-04-15",
      "address_city": "Mumbai"
    },
    "family_count": 1,
    "policy_count": 2
  }
}
```

---

## 7. Policy Management

### List all policies (paginated + filterable)

```
POST /api/v1/admin/policies/list
Header: Authorization: Bearer <token>

Body:
{
  "global_filter": "Star",       ← searches policy_number, insurer, status, policy_type name, file_name
  "sort_field": "created_at",
  "sort_order": -1,
  "filters": [
    { "field": "status", "operator": "equals", "value": "pending" }
  ],
  "limit": 10,
  "skip": 0,
  "partner_id": "6cd47d22-..."  ← optional: see only policies under this partner
}

filters[].field options: policy_number | insurer | status | policy_type_id | file_name

Response:
{
  "data": {
    "data": [
      {
        "id": "943eea11-...",
        "policy_number": "POL-2026-238296",
        "policy_type_id": "6e0c4c8f-...",
        "policy_type": "Health",
        "insurer": "Star Health",
        "sum_insured": 1000000,
        "status": "pending",
        "member_id": "c0b50711-...",
        "member_name": "Rahul Sharma",
        "member_email": "rahul@example.com",
        "partner_id": "6cd47d22-...",
        "partner_name": "HealthBridge Brokers",
        "file_name": "ce58d319-....pdf",
        "created_at": "2026-06-16T11:55:04Z"
      }
    ],
    "total": 2,
    "skip": 0,
    "limit": 10
  }
}
```

**Two access modes:**
- **Direct (no `partner_id`)** — flat list of ALL policies across ALL partners with member + partner info
- **Partner-scoped (`partner_id` set)** — drill into a specific partner's policies

### Get single policy detail

```
GET /api/v1/admin/policies/{policy_id}
Header: Authorization: Bearer <token>

Response: same as list item + extracted_fields + storage_key (full bucket path)
{
  "data": {
    ...all list fields...,
    "extracted_fields": {},
    "storage_key": "6cd47d22-.../c0b50711-.../943eea11-.../ce58d319-....pdf"
  }
}
```

`storage_key` format: `{partner_id}/{user_id}/{policy_id}/{file_name}`

---

## 8. Policy Type Master Management

Policy types are a master table. Admin can add, rename, or deactivate types. Members see only active types when uploading.

**Default types seeded at migration:**
`Health`, `Life`, `Term`, `Motor`, `Travel`, `Home`, `Personal Accident`, `Endowment`

### List all policy types

```
GET /api/v1/admin/policy-types
Header: Authorization: Bearer <token>

Response:
{
  "data": [
    { "id": "6e0c4c8f-...", "name": "Health", "code": "health",
      "description": "Medical health insurance", "is_active": true, "created_at": "..." },
    ...
  ]
}
```

### Create a policy type

```
POST /api/v1/admin/policy-types
Header: Authorization: Bearer <token>

Body:
{
  "name": "Critical Illness",
  "code": "critical_illness",         ← auto-lowercased, spaces → underscores
  "description": "Critical illness cover"
}

Validation: code must be unique
```

### Get / Update a policy type

```
GET  /api/v1/admin/policy-types/{id}
PATCH /api/v1/admin/policy-types/{id}

PATCH Body (all optional):
{ "name": "...", "description": "...", "is_active": true }
```

### Activate / Deactivate

```
PATCH /api/v1/admin/policy-types/{id}/activate
PATCH /api/v1/admin/policy-types/{id}/deactivate
```

Deactivated types no longer appear in the public `/policy-types` listing, so members cannot upload policies of that type (existing policies are unaffected).

---

## 9. Public Policy Types Endpoint

This endpoint is used by the member upload UI — it requires no auth:

```
GET /api/v1/policy-types
(no auth required)

Response: only is_active=true types, ordered alphabetically
```

---

## 10. Internal User Management

Low-level user and role operations — for admin tooling / seeding.

### List / create / get / update / delete users

```
GET    /api/v1/users             (list all)
POST   /api/v1/users             (create user)
GET    /api/v1/users/me          (own profile)
GET    /api/v1/users/{id}        (user detail)
PATCH  /api/v1/users/{id}        (update)
DELETE /api/v1/users/{id}        (soft delete)
```

### Role assignment

```
POST   /api/v1/users/{id}/roles           Body: { "role_id": "uuid" }
DELETE /api/v1/users/{id}/roles/{role_id}
GET    /api/v1/roles                       (list all role definitions)
POST   /api/v1/roles                       Body: { "role_name": "...", "role_type": "..." }
```

---

## 11. Email Notifications SuperAdmin Receives

| Event | Email sent to |
|---|---|
| Any member uploads a policy | **All** SUPERADMIN users receive an alert with member, partner, policy number, and type |

---

## Complete SuperAdmin Journey

```
1. First admin seeded directly in DB (or via seed script)

2. Admin logs in
   POST /auth/send-otp  →  POST /auth/verify-otp
   └── Receives: access_token (user_type = SUPERADMIN)

3. Admin creates plan catalogue
   POST /admin/plans  (×N global plans)
   └── Activate each: POST /admin/plans/{id}/activate

4. Admin creates partner-specific plans (optional)
   POST /admin/plans  (plan_type="partner")
   POST /admin/plans/{id}/partners  ← link to partner

5. Admin creates partners
   POST /admin/partners
   └── Partner user account auto-created
   └── api_key auto-generated

6. Admin links partner-type plans to partners
   POST /admin/plans/{plan_id}/partners
   Body: { "partner_id": "..." }

7. Admin creates policy types (or uses seeded defaults)
   POST /admin/policy-types
   PATCH /admin/policy-types/{id}/activate

8. Partners begin onboarding members
   └── Admin monitors via:
       POST /admin/members/list
       POST /admin/members/list  Body: { "partner_id": "..." }  ← by partner

9. Members upload policies → admin gets email notification
   └── Admin reviews via:
       POST /admin/policies/list                         ← all policies
       POST /admin/policies/list  Body: { "partner_id": "..." }  ← by partner
       GET  /admin/policies/{id}                         ← detail + storage_key

10. Admin monitors platform health
    GET /admin/dashboard

11. Admin manages partner API keys
    POST /admin/partners/{id}/regenerate-key

12. Admin deactivates a partner if needed
    DELETE /admin/partners/{id}

13. Admin deactivates a policy type
    PATCH /admin/policy-types/{id}/deactivate
```

---

## Authorization Rules

| What | Rule |
|---|---|
| `user_type` in JWT | Must be `SUPERADMIN` |
| Scope | All data — no partner or user scoping |
| Plan delete | Only `Draft` status |
| Plan link to partner | Only `partner` type plans |
| Policy type deactivate | Existing policies unaffected; new uploads blocked |
| Partner delete | Soft delete only; user account preserved |

---

## Data Relationships (Architecture Reference)

```
SuperAdmin
│
├── Plans (global)  ────────────────────────────────────────────┐
│                                                                │
├── Partners                                                     │
│     ├── [linked to partner-type plans via partner_plans]  ────┘
│     │
│     └── Members (enrolled per partner via member_enrollments)
│               ├── MemberProfile (1:1)
│               ├── FamilyMembers (1:N)
│               ├── Nominees (1:N, share sum = 100%)
│               ├── DpdpConsent (1:N)
│               └── Policies (1:N per partner)
│                         └── PolicyType (FK to master table)
│                               storage_key: partner/user/policy/file.pdf
│
└── PolicyTypes (master — admin manages, members read)
```
