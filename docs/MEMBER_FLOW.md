# EasyClaims — Member (Customer) Portal Flow

## Overview

A **Member** is an individual enrolled under one or more Partners. Members never register directly — they are onboarded by a Partner. Once enrolled, a member logs in, manages their profile, family, nominees, policies, and consents through the `/api/v1/me/` namespace.

All `/me/` calls are **partner-scoped** via the `X-Partner-Id` header. After login the client receives a `default_partner_id` so it can set this header automatically.

---

## 1. Authentication Flow

### Step 1 — Request OTP

```
POST /api/v1/auth/send-otp

Body:
{
  "email": "rahul@example.com"
}

Response:
{
  "success": true,
  "data": { "message": "OTP sent successfully" }
}
```

- OTP is 6 digits, valid for `OTP_EXPIRE_MINUTES` (default 10 min)
- Max `OTP_MAX_ATTEMPTS` attempts before lockout (default 3)
- OTP is bcrypt-hashed before DB storage — never stored plain

### Step 2 — Verify OTP → receive token

```
POST /api/v1/auth/verify-otp

Body:
{
  "email": "rahul@example.com",
  "otp": "123456"
}

Response:
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "user_type": "CUSTOMER",
    "default_partner_id": "6cd47d22-9412-46e5-ad7a-3a274d141f29"
  }
}
```

**`default_partner_id`** — the first active enrollment's partner. The frontend must send this as `X-Partner-Id` on every `/me/` request unless the user explicitly switches partner context.

Token is a **JWE** (JSON Web Encryption, `dir + A256GCM`). It contains:
- `sub` — user UUID
- `user_type` — `CUSTOMER`
- `jti` — unique token ID (for revocation)
- `exp` — expiry timestamp

### Step 3 — Refresh token

```
POST /api/v1/auth/refresh

Body: { "refresh_token": "eyJhbGci..." }

Response: { "access_token": "...", "refresh_token": "..." }
```

### Step 4 — Logout

```
POST /api/v1/auth/logout

Header: Authorization: Bearer <access_token>
```

Invalidates the JTI in the auth session table so the token cannot be reused.

---

## 2. Partner Context — `X-Partner-Id` Header

Every `/me/` call that touches enrollment, plan, or policy data requires this header:

```
X-Partner-Id: 6cd47d22-9412-46e5-ad7a-3a274d141f29
```

**Fallback behaviour:** If the header is absent, the system auto-resolves the first active enrollment. This means the header is optional after the initial login if the member has only one partner.

---

## 3. List My Partners

```
GET /api/v1/me/partners
Header: Authorization: Bearer <token>

Response:
{
  "data": [
    {
      "partner_id": "6cd47d22-...",
      "partner_name": "HealthBridge Brokers",
      "partner_type": "Broker",
      "enrollment_status": "active",
      "end_date": "2027-06-16",
      "plan": {
        "id": "...", "name": "Secure", "price": 2999,
        "benefit_health": true, "benefit_life": true, ...
      },
      "is_default": true
    }
  ]
}
```

Use this to populate a partner-switcher UI. Set the selected partner's `partner_id` as `X-Partner-Id` for subsequent calls.

---

## 4. Profile Management

### Get profile

```
GET /api/v1/me/profile
Header: Authorization: Bearer <token>

Response:
{
  "data": {
    "id": "c0b50711-...",
    "email": "rahul@example.com",
    "name": "Rahul Sharma",
    "mobile_no": "+91-9876543210",
    "gender": "Male",
    "dob": "1990-04-15",
    "address_line": "12 MG Road",
    "address_city": "Mumbai",
    "address_state": "Maharashtra",
    "address_pin": "400001",
    "preferred_language": "English",
    "channel_email": true,
    "channel_whatsapp": false,
    "channel_voice": false
  }
}
```

### Update profile

```
PATCH /api/v1/me/profile
Header: Authorization: Bearer <token>

Body (all fields optional):
{
  "name": "Rahul Sharma",
  "mobile_no": "+91-9876543210",
  "gender": "Male",
  "dob": "1990-04-15",
  "address_line": "12 MG Road",
  "address_city": "Mumbai",
  "address_state": "Maharashtra",
  "address_pin": "400001",
  "preferred_language": "English",
  "channel_email": true,
  "channel_whatsapp": true,
  "channel_voice": false
}
```

---

## 5. Family Members

Dependants covered under the member's health plan.

### List family

```
GET /api/v1/me/family
Header: Authorization: Bearer <token>
```

### Add family member

```
POST /api/v1/me/family
Header: Authorization: Bearer <token>

Body:
{
  "name": "Priya Sharma",
  "relation": "Spouse",
  "dob": "1992-08-20",
  "gender": "Female"
}

Validation: family_size ≤ plan.benefit_family_size (default max 10)
```

### Update / Remove

```
PATCH /api/v1/me/family/{member_id}
DELETE /api/v1/me/family/{member_id}
```

---

## 6. Nominees

Beneficiaries for life / term policies. Total share across all nominees must equal 100%.

### List nominees

```
GET /api/v1/me/nominees
Header: Authorization: Bearer <token>
```

### Add nominee

```
POST /api/v1/me/nominees
Header: Authorization: Bearer <token>

Body:
{
  "name": "Anita Sharma",
  "relation": "Spouse",
  "dob": "1992-08-20",
  "share_percent": 60
}

Validation: existing shares + new share ≤ 100
```

### Update / Remove

```
PATCH /api/v1/me/nominees/{nominee_id}
DELETE /api/v1/me/nominees/{nominee_id}
```

---

## 7. Current Plan

### Get active plan + enrollment details

```
GET /api/v1/me/plan
Header: Authorization: Bearer <token>
Header: X-Partner-Id: <partner_id>

Response:
{
  "data": {
    "enrollment": {
      "partner_id": "6cd47d22-...",
      "status": "active",
      "start_date": "2026-06-16",
      "end_date": "2027-06-16"
    },
    "plan": {
      "id": "...", "name": "Secure", "price": 2999,
      "plan_type": "global",
      "benefit_health": true,
      "benefit_life": false,
      "benefit_family_size": 4,
      "benefit_claim_slots": 10,
      "benefit_claim_type": "Standard",
      ...
    }
  }
}
```

### Switch plan (self-service)

```
PUT /api/v1/me/plan
Header: Authorization: Bearer <token>
Header: X-Partner-Id: <partner_id>

Body: { "plan_id": "uuid-of-new-plan" }

Validation: new plan must be available for this partner (global or partner-linked)
```

---

## 8. Policies

### List available policy types (public, no auth needed)

```
GET /api/v1/policy-types

Response:
{
  "data": [
    { "id": "6e0c4c8f-...", "code": "health",  "name": "Health",  "is_active": true },
    { "id": "35c5cb11-...", "code": "life",    "name": "Life",    "is_active": true },
    { "id": "ef31fd4a-...", "code": "motor",   "name": "Motor",   "is_active": true },
    { "id": "e7a749f9-...", "code": "travel",  "name": "Travel",  "is_active": true },
    ...
  ]
}
```

Call this first to populate a dropdown before the upload form.

### Upload a policy document

```
POST /api/v1/me/policies
Header: Authorization: Bearer <token>
Header: X-Partner-Id: <partner_id>
Content-Type: multipart/form-data

Form fields:
  policy_type_id  (UUID from /policy-types)
  insurer         (string, optional)
  sum_insured     (integer in ₹, optional)
  file            (PDF only, max 10 MB)

Response:
{
  "data": {
    "id": "943eea11-...",
    "policy_number": "POL-2026-238296",
    "policy_type_id": "6e0c4c8f-...",
    "policy_type": "Health",
    "insurer": "Star Health",
    "sum_insured": 1000000,
    "status": "pending",
    "file_name": "ce58d319-....pdf",
    "extracted_fields": {},
    "created_at": "2026-06-16T11:55:04Z"
  }
}
```

**On upload, three email notifications are sent automatically (non-blocking):**
1. Confirmation to the member
2. Alert to the partner
3. Alert to all SuperAdmins

**File storage path in bucket:** `{partner_id}/{user_id}/{policy_id}/{uuid}.pdf`

### List my policies (paginated + filterable)

```
POST /api/v1/me/policies/list
Header: Authorization: Bearer <token>
Header: X-Partner-Id: <partner_id>

Body:
{
  "global_filter": "Star",       ← searches policy_number, insurer, status, policy_type, file_name
  "sort_field": "created_at",
  "sort_order": -1,              ← -1 = newest first, 1 = oldest first
  "filters": [
    { "field": "status", "operator": "equals", "value": "pending" }
  ],
  "limit": 10,
  "skip": 0
}

filters[].field options: policy_number | insurer | status | policy_type_id | file_name
filters[].operator options: equals | notEquals | contains | startsWith | endsWith

Response:
{
  "data": {
    "data": [ { policy objects } ],
    "total": 2,
    "skip": 0,
    "limit": 10
  }
}
```

### Get single policy

```
GET /api/v1/me/policies/{policy_id}
Header: Authorization: Bearer <token>
Header: X-Partner-Id: <partner_id>
```

### Delete (soft delete) a policy

```
DELETE /api/v1/me/policies/{policy_id}
Header: Authorization: Bearer <token>
Header: X-Partner-Id: <partner_id>
```

---

## 9. DPDP Consent

The Digital Personal Data Protection Act consent must be recorded before sensitive data is processed.

### Get latest consent

```
GET /api/v1/me/consent
Header: Authorization: Bearer <token>
```

### Record consent

```
POST /api/v1/me/consent
Header: Authorization: Bearer <token>

Body:
{
  "version": "1.0",
  "consented_at": "2026-06-16T10:00:00Z"
}
```

---

## 10. Dashboard (summary)

```
GET /api/v1/me/dashboard
Header: Authorization: Bearer <token>

Response:
{
  "data": {
    "enrollment_count": 1,
    "active_enrollments": [
      { "partner_id": "...", "plan_id": "...", "status": "active", "end_date": "2027-06-16" }
    ],
    "family_count": 2,
    "policy_count": 2,
    "policies_by_status": { "pending": 2 }
  }
}
```

---

## Complete Member Journey

```
1. Partner creates member account (POST /partner/members)
   └── Member receives email with their login credentials

2. Member logs in
   POST /auth/send-otp  →  POST /auth/verify-otp
   └── Receives: access_token + default_partner_id

3. Frontend stores default_partner_id, sends as X-Partner-Id on every request

4. Member completes profile
   PATCH /me/profile

5. Member adds family members
   POST /me/family  (×N)

6. Member adds nominees (total share = 100%)
   POST /me/nominees  (×N)

7. Member views/switches plan
   GET /me/plan  →  PUT /me/plan (optional)

8. Member uploads policy documents
   GET /policy-types  →  POST /me/policies (multipart PDF)
   └── Partner + all SuperAdmins receive email notification

9. Member tracks policy status
   POST /me/policies/list  (filter by status)

10. Member records DPDP consent
    POST /me/consent

11. Member views dashboard
    GET /me/dashboard

12. Token expires → refresh
    POST /auth/refresh

13. Logout
    POST /auth/logout
```

---

## Authorization Rules

| What | Rule |
|---|---|
| `user_type` in JWT | Must be `CUSTOMER` |
| `X-Partner-Id` | Must match an active enrollment for this user |
| Policy access | Only own policies; partner-scoped |
| Family / nominees | Only own data |
| Plan switch | New plan must be available to the partner |
| Nominee share | Sum across all nominees ≤ 100% |
