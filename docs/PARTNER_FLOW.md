# EasyClaims — Partner Portal Flow

## Overview

A **Partner** is an organisation (broker, hospital, bank, employer, etc.) that onboards members onto the EasyClaims platform. Partners are created by the SuperAdmin. Each partner has their own login, can manage their enrolled members, view those members' policies, and see their plan catalogue.

All partner API calls live under `/api/v1/partner/`.

---

## 1. What a Partner Can Do

| Capability | API |
|---|---|
| Login (OTP) | `/auth/send-otp` + `/auth/verify-otp` |
| View / update own profile | `/partner/profile` |
| View available plans | `/partner/plans` |
| Onboard members | `POST /partner/members` |
| List / search members | `POST /partner/members/list` |
| View member detail | `GET /partner/members/{id}` |
| Switch member's plan | `PATCH /partner/members/{id}/plan` |
| List member policies (user-wise) | `POST /partner/policies/list` |
| View single policy | `GET /partner/policies/{id}` |
| Dashboard stats | `GET /partner/dashboard` |

---

## 2. Authentication Flow

### Step 1 — Request OTP

```
POST /api/v1/auth/send-otp

Body: { "email": "partner@healthbridge.in" }
```

### Step 2 — Verify OTP → receive token

```
POST /api/v1/auth/verify-otp

Body:
{
  "email": "partner@healthbridge.in",
  "otp": "123456"
}

Response:
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "user_type": "PARTNER",
    "default_partner_id": null      ← null for partner login (not relevant)
  }
}
```

The JWT payload contains `user_type: PARTNER`. Every `/partner/` endpoint validates this and then looks up the Partner record via the `user_id` in the token. This means one Partner user → one Partner account.

### Refresh / Logout

```
POST /api/v1/auth/refresh   Body: { "refresh_token": "..." }
POST /api/v1/auth/logout    Header: Authorization: Bearer <token>
```

---

## 3. Partner Profile

### Get profile

```
GET /api/v1/partner/profile
Header: Authorization: Bearer <token>

Response:
{
  "data": {
    "id": "6cd47d22-...",
    "name": "HealthBridge Brokers",
    "partner_type": "Broker",
    "city": "Mumbai",
    "status": "Active",
    "api_key": "122ad260b09b48dcbc8ced8374e41e35",
    "api_rate_limit": 600
  }
}
```

`api_key` is used for machine-to-machine calls where OAuth login is not practical.

### Update profile

```
PATCH /api/v1/partner/profile
Header: Authorization: Bearer <token>

Body (all optional):
{
  "name": "HealthBridge Brokers Pvt Ltd",
  "city": "Pune"
}
```

---

## 4. Plan Catalogue

Partners see only plans relevant to them: all **global** Active plans + any **partner-type** Active plans explicitly linked to them by the admin.

```
GET /api/v1/partner/plans
Header: Authorization: Bearer <token>

Response:
{
  "data": [
    {
      "id": "92150516-...",
      "name": "Secure",
      "price": 2999,
      "plan_type": "global",
      "status": "Active",
      "benefit_health": true,
      "benefit_life": false,
      "benefit_family_size": 4,
      "benefit_claim_slots": 10,
      "benefit_claim_type": "Standard",
      "benefit_voice": "English",
      ...
    }
  ]
}
```

---

## 5. Member Management

### Onboard a new member

```
POST /api/v1/partner/members
Header: Authorization: Bearer <token>

Body:
{
  "email": "newmember@example.com",
  "name": "Ravi Kumar",
  "mobile_no": "+91-9000000001",
  "plan_id": "92150516-da43-41b1-8921-3a35b952060e"
}

Response:
{
  "data": {
    "id": "uuid",
    "email": "newmember@example.com",
    "name": "Ravi Kumar",
    "enrollment": {
      "plan_id": "92150516-...",
      "status": "active",
      "end_date": "2027-06-16"
    }
  }
}
```

**What happens internally:**
1. If the email already exists as a CUSTOMER user → the existing user is re-enrolled under this partner
2. If new email → a CUSTOMER user is created, then enrolled
3. `UNIQUE(user_id, partner_id)` — one member can only be enrolled once per partner (but can be under multiple partners)
4. Enrollment `end_date` = today + 1 year

### List members (paginated + filterable)

```
POST /api/v1/partner/members/list
Header: Authorization: Bearer <token>

Body:
{
  "global_filter": "ravi",        ← searches name, email, mobile_no
  "sort_field": "created_at",
  "sort_order": -1,
  "filters": [
    { "field": "is_active", "operator": "equals", "value": true }
  ],
  "limit": 10,
  "skip": 0
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
        "enrollment": {
          "plan_id": "92150516-...",
          "status": "active",
          "end_date": "2027-06-16"
        }
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 10
  }
}
```

### Get member detail (with policies and family)

```
GET /api/v1/partner/members/{member_id}
Header: Authorization: Bearer <token>

Response:
{
  "data": {
    "id": "c0b50711-...",
    "email": "rahul@example.com",
    "name": "Rahul Sharma",
    "mobile_no": null,
    "enrollment": {
      "plan_id": "92150516-...",
      "status": "active",
      "end_date": "2027-06-16"
    },
    "family": [
      { "id": "...", "name": "Priya Sharma", "relation": "Spouse" }
    ],
    "policies": [
      {
        "id": "943eea11-...",
        "policy_number": "POL-2026-238296",
        "policy_type": "Health",
        "insurer": "Star Health",
        "status": "pending",
        "file_name": "ce58d319-....pdf"
      }
    ]
  }
}
```

Only returns the member if they are enrolled under this partner. Returns 404 for members of other partners.

### Switch a member's plan

```
PATCH /api/v1/partner/members/{member_id}/plan
Header: Authorization: Bearer <token>

Body: { "plan_id": "new-plan-uuid" }

Validation: new plan must be in this partner's catalogue (global or linked partner-type plan)
```

---

## 6. Policy Visibility — User-Wise Grouped

The partner policy list groups all policies by member, giving a clear "per-member" view.

```
POST /api/v1/partner/policies/list
Header: Authorization: Bearer <token>

Body:
{
  "global_filter": "",
  "sort_field": "created_at",
  "sort_order": -1,
  "filters": [
    { "field": "status", "operator": "equals", "value": "pending" }
  ],
  "limit": 10,
  "skip": 0
}

Response:
{
  "data": {
    "data": [
      {
        "member_id": "c0b50711-...",
        "member_name": "Rahul Sharma",
        "member_email": "rahul@example.com",
        "total_policies": 2,
        "policies": [
          {
            "id": "943eea11-...",
            "policy_number": "POL-2026-238296",
            "policy_type_id": "6e0c4c8f-...",
            "policy_type": "Health",
            "insurer": "Star Health",
            "sum_insured": 1000000,
            "status": "pending",
            "file_name": "ce58d319-....pdf",
            "created_at": "2026-06-16T11:55:04Z"
          },
          { ... policy 2 ... }
        ]
      }
    ],
    "total_members": 1,
    "total_policies": 2,
    "skip": 0,
    "limit": 10
  }
}
```

**Key behaviour:**
- Only sees policies of members enrolled under their own partner
- `total_policies` in the outer object = total matching policies across all members (before grouping)
- `total_policies` per member = count of that member's policies in this response
- Partners cannot see policies of members enrolled under other partners

### Get single policy detail

```
GET /api/v1/partner/policies/{policy_id}
Header: Authorization: Bearer <token>

Response:
{
  "data": {
    "id": "943eea11-...",
    "policy_number": "POL-2026-238296",
    "policy_type": "Health",
    "insurer": "Star Health",
    "sum_insured": 1000000,
    "status": "pending",
    "member_name": "Rahul Sharma",
    "member_email": "rahul@example.com",
    "extracted_fields": {},
    "storage_key": "6cd47d22-.../c0b50711-.../943eea11-.../ce58d319-....pdf",
    "file_name": "ce58d319-....pdf"
  }
}
```

Returns 404 if the policy belongs to a member of a different partner.

---

## 7. Dashboard

```
GET /api/v1/partner/dashboard
Header: Authorization: Bearer <token>

Response:
{
  "data": {
    "partner_id": "6cd47d22-...",
    "total_enrollments": 5,
    "active_enrollments": 4,
    "inactive_enrollments": 1
  }
}
```

---

## 8. Email Notifications Received by Partner

| Event | Email |
|---|---|
| Any enrolled member uploads a policy | Partner receives alert email with member name, email, policy number, type, status |

---

## Complete Partner Journey

```
1. SuperAdmin creates partner account
   POST /admin/partners
   └── Partner user account created with PARTNER role
   └── api_key generated (32-char hex)

2. Partner logs in
   POST /auth/send-otp  →  POST /auth/verify-otp
   └── Receives: access_token (user_type = PARTNER)

3. Partner views available plans
   GET /partner/plans
   └── Sees global plans + any plans admin linked to them

4. Partner onboards members
   POST /partner/members  (×N)
   └── One enrollment per member; re-enrolling existing user is allowed

5. Partner views member list (with search/filter)
   POST /partner/members/list

6. Partner views individual member detail
   GET /partner/members/{id}
   └── Sees enrollment, family, and policies

7. Partner switches a member's plan on request
   PATCH /partner/members/{id}/plan

8. Member uploads policy → partner gets email notification
   └── Partner views policies grouped by member:
       POST /partner/policies/list
       GET /partner/policies/{id}

9. Partner checks dashboard stats
   GET /partner/dashboard

10. Partner updates their profile
    PATCH /partner/profile
```

---

## Authorization Rules

| What | Rule |
|---|---|
| `user_type` in JWT | Must be `PARTNER` |
| Partner record | Resolved from `user_id` in token — cannot impersonate another partner |
| Member visibility | Only members enrolled under this partner |
| Policy visibility | Only policies of members enrolled under this partner |
| Plan visibility | Global Active plans + partner-linked Active plans |
| Plan switch | Target plan must be in this partner's catalogue |
