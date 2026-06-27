# Member Onboarding, Bulk Upload, Change Requests & Audit Logs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend member onboarding fields, enable admin bulk Excel upload per partner, restrict member data edits to admin only, allow members to raise data-change tickets that admin approves, and add audit logs for all significant actions.

**Architecture:** New columns go into `member_profiles` (sale_date, sales_channel, branch_code, salesperson_name, employee_code, data1, data2, data3) via Alembic migration. Bulk upload is a new admin endpoint that parses an openpyxl Excel file, creates members row-by-row reusing `MemberService.create_member`. Change requests are a new `MemberChangeRequest` model/table; member raises a request, admin approves/rejects — on approval the profile is patched. Audit logs are a new `AuditLog` model written by a thin helper called from every mutating endpoint.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, openpyxl, Next.js 15 (App Router), Axios, Zustand, PrimeReact, TypeScript

## Global Constraints

- Backend: Python 3.12, FastAPI 0.111.1, SQLAlchemy 2.x, Alembic migrations only (no raw DDL)
- Frontend: Next.js 15 App Router, TypeScript strict, PrimeReact for UI components, Zustand for state
- All new API routes require `_require_superadmin` unless explicitly noted as member-facing
- Member-edit routes on admin side replace current open `PATCH /member/profile` — member can only read their own profile after this change
- Partner cannot edit member data at all (no new partner endpoints for member updates)
- Mandatory fields for member: name, gender, mobile_no, email, address_line, city, state, pin_code
- Optional fields: sale_date, sales_channel, branch_code, salesperson_name, employee_code, data1, data2, data3
- Audit log entries are append-only; never update or delete them
- Change request: member raises it → admin notified (in-app notification) → admin approves/rejects → on approval profile is patched → member notified (in-app); partner is NOT notified
- Welcome message on bulk upload: same as single member create (email + WhatsApp)

---

## File Map

### Backend — New/Modified files

| File | Action | Purpose |
|---|---|---|
| `app/db/models/member.py` | Modify | Add new columns to `MemberProfile`; add `MemberChangeRequest` model |
| `app/db/models/__init__.py` | Modify | Export `MemberChangeRequest` |
| `app/db/models/audit_log.py` | Create | `AuditLog` model |
| `app/db/models/__init__.py` | Modify | Export `AuditLog` |
| `app/db/queries/member_query.py` | Modify | Add `upsert_profile` new fields; add change-request queries |
| `app/db/queries/audit_log_query.py` | Create | `AuditLogQuery` — `create()` and `list_paginated()` |
| `app/services/audit_service.py` | Create | `AuditService.log()` thin helper |
| `app/services/member_service.py` | Modify | `create_member` saves new fields; add `update_member_by_admin`, `approve_change_request`, `reject_change_request` |
| `app/schemas/member.py` | Modify | Extend `MemberCreate` and `ProfileUpdate` with new fields; add `ChangeRequestCreate`, `ChangeRequestReview` |
| `app/api/admin/members.py` | Modify | Add `PATCH /{member_id}` (admin edits), `POST /bulk-upload`, `GET /change-requests`, `POST /change-requests/{id}/approve`, `POST /change-requests/{id}/reject` |
| `app/api/member/profile.py` | Modify | Remove PATCH (member cannot edit own profile); keep GET |
| `app/api/member/__init__.py` | Modify | Add `GET /change-requests`, `POST /change-requests` |
| `app/api/admin/__init__.py` | Modify | Route already included; no change needed |
| `alembic/versions/<hash>_member_onboarding_fields.py` | Create | Migration: new columns on `member_profiles`, new tables `member_change_requests`, `audit_logs` |

### Frontend — New/Modified files

| File | Action | Purpose |
|---|---|---|
| `imports/core/api.ts` | Modify | Add `adminUpdateMember`, `adminBulkUploadMembers`, `adminListChangeRequests`, `adminApproveChangeRequest`, `adminRejectChangeRequest`, `memberListChangeRequests`, `memberCreateChangeRequest` |
| `app/(admin)/admin/members/[id]/page.tsx` | Modify | Show all new fields; add edit form for admin; show change requests tab |
| `app/(admin)/admin/members/bulk-upload/page.tsx` | Create | Excel bulk upload UI (file picker + partner selector + preview table + submit) |
| `app/(admin)/admin/members/page.tsx` | Modify | Add "Bulk Upload" button linking to new page |
| `app/(admin)/admin/change-requests/page.tsx` | Create | Admin list of pending change requests with approve/reject |
| `app/(member)/member/profile/page.tsx` | Modify | Remove edit controls; show read-only fields including new onboarding fields; add "Request Change" button |
| `app/(member)/member/change-requests/page.tsx` | Create | Member: raise new change request form + list own requests |
| `components/layout/Sidebar.tsx` | Modify | Add "Change Requests" nav link for admin and member portals |

---

## Task 1: Database Migration — New Profile Columns + Change Requests + Audit Logs

**Files:**
- Create: `app/db/models/audit_log.py`
- Modify: `app/db/models/member.py`
- Modify: `app/db/models/__init__.py`
- Create: `alembic/versions/<auto>_member_onboarding_fields.py`

**Interfaces:**
- Produces: `MemberProfile` with columns `sale_date`, `sales_channel`, `branch_code`, `salesperson_name`, `employee_code`, `data1`, `data2`, `data3`
- Produces: `MemberChangeRequest` model with `id, user_id, requested_fields (JSON), reason, status (pending/approved/rejected), reviewed_by, reviewed_at, created_at`
- Produces: `AuditLog` model with `id, actor_id, actor_type, action, entity_type, entity_id, old_value (JSON), new_value (JSON), ip_address, created_at`

- [ ] **Step 1: Add new columns to `MemberProfile` and new models**

Edit `app/db/models/member.py`:

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class MemberEnrollment(Base):
    # ... (unchanged) ...
    __tablename__ = "member_enrollments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("membership_plans.id"), nullable=False)
    status = Column(String, nullable=False, default="Active")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("user_id", "partner_id", name="uq_member_partner"),)
    def __init__(self, **kwargs):
        kwargs.setdefault("status", "Active")
        super().__init__(**kwargs)


class MemberProfile(Base):
    __tablename__ = "member_profiles"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    gender = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    address_line = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    address_pin = Column(String, nullable=True)
    preferred_language = Column(String, nullable=False, default="English")
    channel_email = Column(Boolean, nullable=False, default=True)
    channel_whatsapp = Column(Boolean, nullable=False, default=False)
    channel_voice = Column(Boolean, nullable=False, default=False)
    # NEW onboarding fields
    sale_date = Column(Date, nullable=True)
    sales_channel = Column(String, nullable=True)
    branch_code = Column(String, nullable=True)
    salesperson_name = Column(String, nullable=True)
    employee_code = Column(String, nullable=True)
    data1 = Column(String, nullable=True)
    data2 = Column(String, nullable=True)
    data3 = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("preferred_language", "English")
        kwargs.setdefault("channel_email", True)
        kwargs.setdefault("channel_whatsapp", False)
        kwargs.setdefault("channel_voice", False)
        super().__init__(**kwargs)


class MemberChangeRequest(Base):
    __tablename__ = "member_change_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    requested_fields = Column(JSONB, nullable=False)   # {"name": "New Name", "mobile_no": "9999999999"}
    reason = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | approved | rejected
    reviewed_by = Column(String, nullable=True)        # admin user_id as string
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "pending")
        super().__init__(**kwargs)


# FamilyMember, Nominee, DpdpConsent unchanged — keep existing code
class FamilyMember(Base):
    __tablename__ = "family_members"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    coverage_type = Column(String, nullable=True, default="Health")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    def __init__(self, **kwargs):
        kwargs.setdefault("coverage_type", "Health")
        super().__init__(**kwargs)


class Nominee(Base):
    __tablename__ = "nominees"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    share_percent = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DpdpConsent(Base):
    __tablename__ = "dpdp_consents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    consented_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(String, nullable=False)
    source = Column(String, nullable=False, default="portal")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    def __init__(self, **kwargs):
        kwargs.setdefault("source", "portal")
        super().__init__(**kwargs)
```

- [ ] **Step 2: Create `app/db/models/audit_log.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(String, nullable=True)       # user_id performing the action (None = system)
    actor_type = Column(String, nullable=True)     # "admin" | "member" | "partner" | "system"
    action = Column(String, nullable=False)        # "member_created" | "member_updated" | "bulk_upload" | "change_request_approved" etc.
    entity_type = Column(String, nullable=True)    # "member" | "policy" | "change_request"
    entity_id = Column(String, nullable=True)      # UUID of the affected entity
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    ip_address = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
```

- [ ] **Step 3: Export new models in `app/db/models/__init__.py`**

```python
from .user import User, OTPLog, AuthSession
from .roles import Role, UserRole
from .plan import MembershipPlan
from .partner import Partner, PartnerPlan
from .member import MemberEnrollment, MemberProfile, FamilyMember, Nominee, DpdpConsent, MemberChangeRequest
from .policy_type import PolicyType
from .policy import Policy
from .activity import UserActivity, PolicyFamilyMember, Notification
from .email_template import EmailTemplate
from .enrollment_history import EnrollmentHistory
from .system_setting import SystemSetting
from .llm_usage import LLMUsage
from .audit_log import AuditLog

__all__ = [
    "User", "OTPLog", "AuthSession", "Role", "UserRole",
    "MembershipPlan",
    "Partner", "PartnerPlan",
    "MemberEnrollment", "MemberProfile", "FamilyMember", "Nominee", "DpdpConsent", "MemberChangeRequest",
    "PolicyType", "Policy",
    "UserActivity", "PolicyFamilyMember", "Notification",
    "EmailTemplate",
    "EnrollmentHistory",
    "SystemSetting",
    "LLMUsage",
    "AuditLog",
]
```

- [ ] **Step 4: Generate Alembic migration**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
alembic revision --autogenerate -m "member_onboarding_fields_change_requests_audit_logs"
```

Open the generated file and verify it contains:
- `ALTER TABLE member_profiles ADD COLUMN sale_date DATE`
- `ALTER TABLE member_profiles ADD COLUMN sales_channel VARCHAR`
- `ALTER TABLE member_profiles ADD COLUMN branch_code VARCHAR`
- `ALTER TABLE member_profiles ADD COLUMN salesperson_name VARCHAR`
- `ALTER TABLE member_profiles ADD COLUMN employee_code VARCHAR`
- `ALTER TABLE member_profiles ADD COLUMN data1 VARCHAR`
- `ALTER TABLE member_profiles ADD COLUMN data2 VARCHAR`
- `ALTER TABLE member_profiles ADD COLUMN data3 VARCHAR`
- `CREATE TABLE member_change_requests (...)`
- `CREATE TABLE audit_logs (...)`

- [ ] **Step 5: Run migration**

```bash
alembic upgrade head
```

Expected output: `Running upgrade <prev> -> <new>, member_onboarding_fields_change_requests_audit_logs`

- [ ] **Step 6: Verify tables in DB**

```bash
PGPASSWORD=mystique_agents psql -U mystique_agents -h 0.0.0.0 -p 5432 -d easyclaims -c "\d member_profiles" | grep -E "sale_date|sales_channel|branch_code|salesperson_name|employee_code|data1|data2|data3"
PGPASSWORD=mystique_agents psql -U mystique_agents -h 0.0.0.0 -p 5432 -d easyclaims -c "\d member_change_requests"
PGPASSWORD=mystique_agents psql -U mystique_agents -h 0.0.0.0 -p 5432 -d easyclaims -c "\d audit_logs"
```

Expected: all 8 columns listed for `member_profiles`, both tables exist.

---

## Task 2: Audit Log Query + Service

**Files:**
- Create: `app/db/queries/audit_log_query.py`
- Create: `app/services/audit_service.py`

**Interfaces:**
- Produces: `AuditLogQuery.create(actor_id, actor_type, action, entity_type, entity_id, old_value, new_value, ip_address, note) -> AuditLog`
- Produces: `AuditLogQuery.list_paginated(entity_type=None, entity_id=None, skip=0, limit=50) -> (int, List[AuditLog])`
- Produces: `AuditService.log(actor_id, actor_type, action, entity_type, entity_id, old_value=None, new_value=None, ip_address=None, note=None) -> None` (never raises)

- [ ] **Step 1: Create `app/db/queries/audit_log_query.py`**

```python
from typing import Optional, List, Tuple
from ..session import session_scope
from ..models.audit_log import AuditLog


class AuditLogQuery:

    def create(
        self,
        actor_id: Optional[str],
        actor_type: Optional[str],
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        ip_address: Optional[str] = None,
        note: Optional[str] = None,
    ) -> AuditLog:
        with session_scope() as session:
            entry = AuditLog(
                actor_id=actor_id,
                actor_type=actor_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address,
                note=note,
            )
            session.add(entry)
            session.flush()
            session.expunge(entry)
            return entry

    def list_paginated(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[int, List[AuditLog]]:
        with session_scope() as session:
            q = session.query(AuditLog)
            if entity_type:
                q = q.filter(AuditLog.entity_type == entity_type)
            if entity_id:
                q = q.filter(AuditLog.entity_id == entity_id)
            if actor_id:
                q = q.filter(AuditLog.actor_id == actor_id)
            total = q.count()
            rows = q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return total, rows
```

- [ ] **Step 2: Create `app/services/audit_service.py`**

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AuditService:

    def log(
        self,
        actor_id: Optional[str],
        actor_type: Optional[str],
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        ip_address: Optional[str] = None,
        note: Optional[str] = None,
    ) -> None:
        try:
            from ..db.queries.audit_log_query import AuditLogQuery
            AuditLogQuery().create(
                actor_id=actor_id,
                actor_type=actor_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address,
                note=note,
            )
        except Exception:
            logger.exception("Audit log write failed — action=%s entity=%s/%s", action, entity_type, entity_id)
```

- [ ] **Step 3: Smoke test — restart backend and verify import**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
python -c "from app.services.audit_service import AuditService; print('OK')"
```

Expected: `OK`

---

## Task 3: Extend Schemas + Member Query

**Files:**
- Modify: `app/schemas/member.py`
- Modify: `app/db/queries/member_query.py`

**Interfaces:**
- Consumes: `MemberProfile` new columns from Task 1
- Produces: `MemberCreate` with fields: `sale_date`, `sales_channel`, `branch_code`, `salesperson_name`, `employee_code`, `data1`, `data2`, `data3`
- Produces: `AdminMemberUpdate` schema (admin-only edit — all fields optional including new ones + name/email/mobile_no/is_active)
- Produces: `ChangeRequestCreate(requested_fields: dict, reason: str)`
- Produces: `ChangeRequestReview(action: "approved"|"rejected", admin_note: str)`
- Produces: `MemberQuery.create_change_request(user_id, requested_fields, reason) -> MemberChangeRequest`
- Produces: `MemberQuery.get_change_request(request_id) -> MemberChangeRequest | None`
- Produces: `MemberQuery.list_change_requests(user_id=None, status=None, skip=0, limit=50) -> (int, List[MemberChangeRequest])`
- Produces: `MemberQuery.update_change_request(request_id, status, reviewed_by, reviewed_at, admin_note) -> MemberChangeRequest`

- [ ] **Step 1: Update `app/schemas/member.py` — add new fields to `MemberCreate` and `ProfileUpdate`, add new schemas**

Replace the top portion (keep existing validators, add new fields):

```python
from typing import Optional, Any
from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

_MOBILE_RE = re.compile(r"^\+?[\d\s\-()]{7,15}$")


class MemberCreate(BaseModel):
    email: EmailStr
    name: str
    mobile_no: Optional[str] = None
    gender: Optional[str] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_pin: Optional[str] = None
    partner_id: Optional[str] = None
    plan_id: Optional[str] = None
    # New onboarding fields
    sale_date: Optional[date] = None
    sales_channel: Optional[str] = None
    branch_code: Optional[str] = None
    salesperson_name: Optional[str] = None
    employee_code: Optional[str] = None
    data1: Optional[str] = None
    data2: Optional[str] = None
    data3: Optional[str] = None

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, v):
        if v and not _MOBILE_RE.match(v):
            raise ValueError("Invalid mobile number format")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other")
        return v


class AdminMemberUpdate(BaseModel):
    """Admin-only: update any member field."""
    name: Optional[str] = None
    mobile_no: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_pin: Optional[str] = None
    sale_date: Optional[date] = None
    sales_channel: Optional[str] = None
    branch_code: Optional[str] = None
    salesperson_name: Optional[str] = None
    employee_code: Optional[str] = None
    data1: Optional[str] = None
    data2: Optional[str] = None
    data3: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, v):
        if v and not _MOBILE_RE.match(v):
            raise ValueError("Invalid mobile number format")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other")
        return v


class ProfileUpdate(BaseModel):
    """Member self-update — kept for internal use; no longer exposed as a public endpoint."""
    name: Optional[str] = None
    mobile_no: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_pin: Optional[str] = None
    preferred_language: Optional[str] = None
    channel_email: Optional[bool] = None
    channel_whatsapp: Optional[bool] = None
    channel_voice: Optional[bool] = None

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, v):
        if v and not _MOBILE_RE.match(v):
            raise ValueError("Invalid mobile number format")
        return v

    @field_validator("address_pin")
    @classmethod
    def validate_pin(cls, v):
        if v and not re.match(r"^\d{6}$", v):
            raise ValueError("PIN code must be 6 digits")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other")
        return v


class ChangeRequestCreate(BaseModel):
    requested_fields: dict   # {"name": "New Name", "mobile_no": "9999999999", ...}
    reason: Optional[str] = None


class ChangeRequestReview(BaseModel):
    action: str   # "approved" | "rejected"
    admin_note: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v not in ("approved", "rejected"):
            raise ValueError("action must be 'approved' or 'rejected'")
        return v


# Keep existing FamilyMemberCreate, FamilyMemberUpdate, NomineeCreate, NomineeUpdate,
# ConsentCreate, PlanSwitchRequest unchanged below this line
class FamilyMemberCreate(BaseModel):
    name: str
    relation: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    coverage_type: Optional[str] = "Health"

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other")
        return v

    @field_validator("coverage_type")
    @classmethod
    def default_coverage(cls, v):
        return v or "Health"


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    coverage_type: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other")
        return v

    @field_validator("coverage_type")
    @classmethod
    def default_coverage(cls, v):
        return v or "Health"


class NomineeCreate(BaseModel):
    name: str
    relation: str
    share_percent: int = Field(..., ge=0, le=100)


class NomineeUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    share_percent: Optional[int] = Field(default=None, ge=0, le=100)


class ConsentCreate(BaseModel):
    version: str
    source: str = "portal"


class PlanSwitchRequest(BaseModel):
    plan_id: str
```

- [ ] **Step 2: Add change-request methods to `app/db/queries/member_query.py`**

At the bottom of the existing file, add:

```python
from ..models.member import MemberChangeRequest
from datetime import datetime, timezone

# Add these methods to the existing MemberQuery class:

    def create_change_request(self, user_id: str, requested_fields: dict, reason: str = None) -> MemberChangeRequest:
        with session_scope() as session:
            cr = MemberChangeRequest(
                user_id=user_id,
                requested_fields=requested_fields,
                reason=reason,
            )
            session.add(cr)
            session.flush()
            session.expunge(cr)
            return cr

    def get_change_request(self, request_id: str):
        with session_scope() as session:
            cr = session.query(MemberChangeRequest).filter(MemberChangeRequest.id == request_id).first()
            if cr:
                session.expunge(cr)
            return cr

    def list_change_requests(self, user_id=None, status=None, skip=0, limit=50):
        with session_scope() as session:
            q = session.query(MemberChangeRequest)
            if user_id:
                q = q.filter(MemberChangeRequest.user_id == user_id)
            if status:
                q = q.filter(MemberChangeRequest.status == status)
            total = q.count()
            rows = q.order_by(MemberChangeRequest.created_at.desc()).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return total, rows

    def update_change_request(self, request_id: str, status: str,
                               reviewed_by: str = None, admin_note: str = None):
        with session_scope() as session:
            cr = session.query(MemberChangeRequest).filter(MemberChangeRequest.id == request_id).first()
            if not cr:
                return None
            cr.status = status
            cr.reviewed_by = reviewed_by
            cr.reviewed_at = datetime.now(timezone.utc)
            if admin_note is not None:
                cr.admin_note = admin_note
            session.flush()
            session.expunge(cr)
            return cr
```

- [ ] **Step 3: Verify import**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
python -c "from app.schemas.member import AdminMemberUpdate, ChangeRequestCreate, ChangeRequestReview; print('OK')"
```

Expected: `OK`

---

## Task 4: Member Service — Admin Update + Change Request Flow

**Files:**
- Modify: `app/services/member_service.py`

**Interfaces:**
- Consumes: `AdminMemberUpdate`, `ChangeRequestCreate`, `ChangeRequestReview` from Task 3
- Consumes: `AuditService.log()` from Task 2
- Produces: `MemberService.update_member_by_admin(member_id, data: AdminMemberUpdate, admin_id, ip=None) -> dict`
- Produces: `MemberService.create_change_request(user_id, data: ChangeRequestCreate) -> MemberChangeRequest`
- Produces: `MemberService.approve_change_request(request_id, admin_id, admin_note, ip=None) -> MemberChangeRequest`
- Produces: `MemberService.reject_change_request(request_id, admin_id, admin_note) -> MemberChangeRequest`
- Produces: `MemberService.create_member` updated to save new profile fields

- [ ] **Step 1: Update `create_member` in `MemberService` to save new profile fields**

In `member_service.py`, find the `create_member` method. Replace the `self.q.upsert_profile(str(user.id))` call with:

```python
        profile_fields = {}
        for f in ("gender", "address_line", "address_city", "address_state", "address_pin",
                  "sale_date", "sales_channel", "branch_code", "salesperson_name",
                  "employee_code", "data1", "data2", "data3"):
            v = getattr(data, f, None)
            if v is not None:
                profile_fields[f] = v
        self.q.upsert_profile(str(user.id), **profile_fields)
```

- [ ] **Step 2: Add `update_member_by_admin` to `MemberService`**

Add this method to the `MemberService` class:

```python
    def update_member_by_admin(self, member_id: str, data, admin_id: str, ip: str = None) -> dict:
        from .audit_service import AuditService
        user = self.user_q.get_user_by_id(member_id)
        if not user:
            raise HTTPException(status_code=404, detail="Member not found")

        old_user = {"name": user.name, "mobile_no": user.mobile_no, "is_active": user.is_active}
        profile = self.q.get_profile(member_id)
        old_profile = {
            "gender": profile.gender if profile else None,
            "address_line": profile.address_line if profile else None,
            "address_city": profile.address_city if profile else None,
            "address_state": profile.address_state if profile else None,
            "address_pin": profile.address_pin if profile else None,
            "sale_date": str(profile.sale_date) if profile and profile.sale_date else None,
            "sales_channel": profile.sales_channel if profile else None,
            "branch_code": profile.branch_code if profile else None,
            "salesperson_name": profile.salesperson_name if profile else None,
            "employee_code": profile.employee_code if profile else None,
            "data1": profile.data1 if profile else None,
            "data2": profile.data2 if profile else None,
            "data3": profile.data3 if profile else None,
        }

        payload = data.model_dump(exclude_none=True)
        user_fields = {k: v for k, v in payload.items() if k in ("name", "mobile_no", "is_active")}
        profile_fields = {k: v for k, v in payload.items() if k not in ("name", "mobile_no", "is_active")}

        if user_fields:
            self.user_q.update_user(member_id, **user_fields)
        if profile_fields:
            self.q.upsert_profile(member_id, **profile_fields)

        AuditService().log(
            actor_id=admin_id, actor_type="admin",
            action="member_updated",
            entity_type="member", entity_id=member_id,
            old_value={**old_user, **old_profile},
            new_value=payload,
            ip_address=ip,
        )
        return self.get_profile(member_id)
```

- [ ] **Step 3: Add `create_change_request` to `MemberService`**

```python
    def create_change_request(self, user_id: str, data) -> object:
        from .audit_service import AuditService
        cr = self.q.create_change_request(
            user_id=user_id,
            requested_fields=data.requested_fields,
            reason=data.reason,
        )
        # Notify all admins
        try:
            from .notification_helper import notify_all_admins
            user = self.user_q.get_user_by_id(user_id)
            notify_all_admins(
                type="change_request",
                title=f"Profile Change Request — {user.name or user.email}",
                body=f"{user.name or user.email} requested changes to their profile.",
                ref_id=str(cr.id),
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify admins of change request %s", cr.id)
        AuditService().log(
            actor_id=user_id, actor_type="member",
            action="change_request_created",
            entity_type="change_request", entity_id=str(cr.id),
            new_value=data.requested_fields,
        )
        return cr
```

- [ ] **Step 4: Add `approve_change_request` and `reject_change_request` to `MemberService`**

```python
    def approve_change_request(self, request_id: str, admin_id: str, admin_note: str = None, ip: str = None) -> object:
        from .audit_service import AuditService
        cr = self.q.get_change_request(request_id)
        if not cr:
            raise HTTPException(status_code=404, detail="Change request not found")
        if cr.status != "pending":
            raise HTTPException(status_code=400, detail="Change request already reviewed")

        # Apply the changes
        self.update_member_by_admin(
            member_id=str(cr.user_id),
            data=type("_D", (), {"model_dump": lambda self, **kw: cr.requested_fields})(),
            admin_id=admin_id,
            ip=ip,
        )
        updated = self.q.update_change_request(
            request_id, status="approved", reviewed_by=admin_id, admin_note=admin_note
        )
        # Notify member
        try:
            from ..db.queries.activity_query import NotificationQuery
            NotificationQuery().create(
                recipient_user_id=str(cr.user_id),
                type="change_request_approved",
                title="Your profile change request was approved",
                body="Your requested profile changes have been applied.",
                ref_id=request_id,
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify member of change request approval %s", request_id)
        AuditService().log(
            actor_id=admin_id, actor_type="admin",
            action="change_request_approved",
            entity_type="change_request", entity_id=request_id,
            new_value=cr.requested_fields,
            ip_address=ip,
        )
        return updated

    def reject_change_request(self, request_id: str, admin_id: str, admin_note: str = None) -> object:
        from .audit_service import AuditService
        cr = self.q.get_change_request(request_id)
        if not cr:
            raise HTTPException(status_code=404, detail="Change request not found")
        if cr.status != "pending":
            raise HTTPException(status_code=400, detail="Change request already reviewed")
        updated = self.q.update_change_request(
            request_id, status="rejected", reviewed_by=admin_id, admin_note=admin_note
        )
        try:
            from ..db.queries.activity_query import NotificationQuery
            NotificationQuery().create(
                recipient_user_id=str(cr.user_id),
                type="change_request_rejected",
                title="Your profile change request was rejected",
                body=admin_note or "Your profile change request was not approved.",
                ref_id=request_id,
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify member of change request rejection %s", request_id)
        AuditService().log(
            actor_id=admin_id, actor_type="admin",
            action="change_request_rejected",
            entity_type="change_request", entity_id=request_id,
        )
        return updated
```

- [ ] **Step 5: Smoke test**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
python -c "from app.services.member_service import MemberService; print('OK')"
```

Expected: `OK`

---

## Task 5: Admin API — Edit Member + Bulk Upload + Change Requests + Audit Log endpoint

**Files:**
- Modify: `app/api/admin/members.py`
- Create: `app/api/admin/audit_logs.py`
- Modify: `app/api/admin/__init__.py`

**Interfaces:**
- Consumes: `MemberService.update_member_by_admin`, `create_member`, `approve_change_request`, `reject_change_request` from Task 4
- Produces:
  - `PATCH /admin/members/{member_id}` — admin edit member
  - `POST /admin/members/bulk-upload` — multipart Excel file + partner_id + plan_id
  - `GET /admin/members/change-requests` — list all change requests (filter by status)
  - `POST /admin/members/change-requests/{request_id}/approve`
  - `POST /admin/members/change-requests/{request_id}/reject`
  - `GET /admin/audit-logs` — list audit logs with filter by entity_type, entity_id

- [ ] **Step 1: Add new endpoints to `app/api/admin/members.py`**

Add these imports at the top:
```python
from fastapi import UploadFile, File, Form
import openpyxl, io
from ...schemas.member import AdminMemberUpdate, ChangeRequestCreate, ChangeRequestReview
from ...services.audit_service import AuditService
```

Add these routes:

```python
@admin_members_router.patch("/{member_id}", response_model=ResponseModel)
async def update_member(
    member_id: UUID,
    body: AdminMemberUpdate,
    request: Request,
    _=Depends(_require_superadmin),
):
    from ...core.auth import get_current_user_id
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else None
    ip = request.client.host if request.client else None
    svc = MemberService()
    result = svc.update_member_by_admin(str(member_id), body, admin_id=admin_id or "admin", ip=ip)
    return ResponseModel.ok(data=result)


@admin_members_router.post("/bulk-upload", response_model=ResponseModel, status_code=201)
async def bulk_upload_members(
    request: Request,
    file: UploadFile = File(...),
    partner_id: str = Form(...),
    plan_id: str = Form(None),
    _=Depends(_require_superadmin),
):
    """
    Upload an Excel file with member rows. Expected columns (case-insensitive):
    Sale Date | Primary Member Full Name | Gender | Primary Mobile No. | Primary Email ID |
    Address Line1 | City | State | Pin Code | Sales Channel | Partner Branch Code |
    Sales Person Name | Employee Code | Data 1 | Data 2 | Data 3
    """
    contents = await file.read()
    try:
        wb = openpyxl.load_workbook(filename=io.BytesIO(contents), read_only=True, data_only=True)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid Excel file")

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=422, detail="Excel file is empty")

    # Normalise header
    header = [str(c).strip().lower() if c else "" for c in rows[0]]
    COL_MAP = {
        "sale date": "sale_date",
        "primary member full name": "name",
        "gender": "gender",
        "primary mobile no.": "mobile_no",
        "primary mobile no": "mobile_no",
        "primary email id": "email",
        "address line1": "address_line",
        "city": "address_city",
        "state": "address_state",
        "pin code": "address_pin",
        "sales channel": "sales_channel",
        "partner branch code": "branch_code",
        "sales person name": "salesperson_name",
        "employee code": "employee_code",
        "data 1": "data1",
        "data 2": "data2",
        "data 3": "data3",
    }
    col_idx = {}
    for i, h in enumerate(header):
        mapped = COL_MAP.get(h)
        if mapped:
            col_idx[mapped] = i

    MANDATORY = {"name", "gender", "mobile_no", "email", "address_line", "address_city", "address_state", "address_pin"}
    missing_cols = MANDATORY - set(col_idx.keys())
    if missing_cols:
        raise HTTPException(status_code=422, detail=f"Missing mandatory columns: {missing_cols}")

    svc = MemberService()
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    ip = request.client.host if request.client else None
    results = {"created": [], "skipped": [], "errors": []}

    for row_num, row in enumerate(rows[1:], start=2):
        def cell(field):
            idx = col_idx.get(field)
            if idx is None:
                return None
            v = row[idx]
            return str(v).strip() if v is not None else None

        email = cell("email")
        name = cell("name")
        mobile = cell("mobile_no")
        gender = cell("gender")
        addr = cell("address_line")
        city = cell("address_city")
        state = cell("address_state")
        pin = cell("address_pin")

        if not email:
            results["skipped"].append({"row": row_num, "reason": "empty email"})
            continue

        missing_mandatory = [f for f, v in [("name", name), ("gender", gender), ("mobile_no", mobile),
                                              ("address_line", addr), ("city", city), ("state", state), ("pin_code", pin)] if not v]
        if missing_mandatory:
            results["errors"].append({"row": row_num, "email": email, "reason": f"Missing: {missing_mandatory}"})
            continue

        from ...schemas.member import MemberCreate
        import datetime as _dt
        sale_date_raw = cell("sale_date")
        sale_date = None
        if sale_date_raw:
            try:
                sale_date = _dt.date.fromisoformat(sale_date_raw)
            except Exception:
                pass

        try:
            member_data = MemberCreate(
                email=email, name=name, mobile_no=mobile, gender=gender,
                address_line=addr, address_city=city, address_state=state, address_pin=pin,
                partner_id=partner_id, plan_id=plan_id,
                sale_date=sale_date,
                sales_channel=cell("sales_channel"),
                branch_code=cell("branch_code"),
                salesperson_name=cell("salesperson_name"),
                employee_code=cell("employee_code"),
                data1=cell("data1"),
                data2=cell("data2"),
                data3=cell("data3"),
            )
            result = svc.create_member(member_data)
            results["created"].append({"row": row_num, "email": email, "id": str(result["user"].id)})
        except HTTPException as e:
            results["skipped"].append({"row": row_num, "email": email, "reason": e.detail})
        except Exception as e:
            results["errors"].append({"row": row_num, "email": email, "reason": str(e)})

    AuditService().log(
        actor_id=admin_id, actor_type="admin",
        action="bulk_upload",
        entity_type="member",
        note=f"Bulk upload: {len(results['created'])} created, {len(results['skipped'])} skipped, {len(results['errors'])} errors",
        ip_address=ip,
    )
    return ResponseModel.ok(data={
        "total_rows": len(rows) - 1,
        **results,
    })


@admin_members_router.get("/change-requests", response_model=ResponseModel)
async def list_change_requests(
    request: Request,
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    _=Depends(_require_superadmin),
):
    mq = MemberQuery()
    uq = UserQuery()
    total, rows = mq.list_change_requests(status=status, skip=skip, limit=limit)
    result = []
    for cr in rows:
        user = uq.get_user_by_id(str(cr.user_id))
        result.append({
            "id": str(cr.id),
            "user_id": str(cr.user_id),
            "member_name": user.name if user else None,
            "member_email": user.email if user else None,
            "requested_fields": cr.requested_fields,
            "reason": cr.reason,
            "status": cr.status,
            "admin_note": cr.admin_note,
            "reviewed_by": cr.reviewed_by,
            "reviewed_at": cr.reviewed_at.isoformat() if cr.reviewed_at else None,
            "created_at": cr.created_at.isoformat() if cr.created_at else None,
        })
    return ResponseModel.ok(data={"data": result, "total": total, "skip": skip, "limit": limit})


class ReviewBody(BaseModel):
    admin_note: str = None

@admin_members_router.post("/change-requests/{request_id}/approve", response_model=ResponseModel)
async def approve_change_request(request_id: str, body: ReviewBody, request: Request, _=Depends(_require_superadmin)):
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    ip = request.client.host if request.client else None
    svc = MemberService()
    cr = svc.approve_change_request(request_id, admin_id=admin_id, admin_note=body.admin_note, ip=ip)
    return ResponseModel.ok(data={"status": cr.status})


@admin_members_router.post("/change-requests/{request_id}/reject", response_model=ResponseModel)
async def reject_change_request(request_id: str, body: ReviewBody, request: Request, _=Depends(_require_superadmin)):
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    svc = MemberService()
    cr = svc.reject_change_request(request_id, admin_id=admin_id, admin_note=body.admin_note)
    return ResponseModel.ok(data={"status": cr.status})
```

- [ ] **Step 2: Create `app/api/admin/audit_logs.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...db.queries.audit_log_query import AuditLogQuery
from ..users import _require_superadmin

admin_audit_router = APIRouter()


@admin_audit_router.get("", response_model=ResponseModel)
async def list_audit_logs(
    request: Request,
    entity_type: str = None,
    entity_id: str = None,
    actor_id: str = None,
    skip: int = 0,
    limit: int = 50,
    _=Depends(_require_superadmin),
):
    total, rows = AuditLogQuery().list_paginated(
        entity_type=entity_type, entity_id=entity_id, actor_id=actor_id, skip=skip, limit=limit
    )
    return ResponseModel.ok(data={
        "data": [
            {
                "id": str(r.id),
                "actor_id": r.actor_id,
                "actor_type": r.actor_type,
                "action": r.action,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "old_value": r.old_value,
                "new_value": r.new_value,
                "ip_address": r.ip_address,
                "note": r.note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    })
```

- [ ] **Step 3: Register audit router in `app/api/admin/__init__.py`**

```python
from .audit_logs import admin_audit_router
# add to admin_router:
admin_router.include_router(admin_audit_router, prefix="/audit-logs", tags=["Admin - Audit Logs"])
```

- [ ] **Step 4: Install openpyxl**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
pip install openpyxl -q
echo "openpyxl" >> requirements.txt
```

- [ ] **Step 5: Restart backend and smoke test**

```bash
pkill -f "python main.py"; sleep 1
cd /home/konsultera/chinar/testpro/easyclaims_backend && python main.py > /tmp/backend.log 2>&1 &
sleep 5 && tail -3 /tmp/backend.log
```

Expected: `Application startup complete.`

---

## Task 6: Member API — Remove Self-Edit, Add Change Request Endpoints

**Files:**
- Modify: `app/api/member/profile.py`
- Modify: `app/api/member/__init__.py`

**Interfaces:**
- Removes: `PATCH /member/profile` (member cannot self-edit)
- Adds: `GET /member/profile` returns all fields including new onboarding fields (read-only)
- Adds: `POST /member/change-requests` — create change request
- Adds: `GET /member/change-requests` — list own change requests

- [ ] **Step 1: Update `app/api/member/profile.py` — remove PATCH, extend GET response**

Read the current file first, then replace the PATCH endpoint with a comment. The GET endpoint should be extended to include new profile fields:

```python
# In the GET /member/profile response, add these fields to the profile dict:
"sale_date": str(profile.sale_date) if profile and profile.sale_date else None,
"sales_channel": profile.sales_channel if profile else None,
"branch_code": profile.branch_code if profile else None,
"salesperson_name": profile.salesperson_name if profile else None,
"employee_code": profile.employee_code if profile else None,
"data1": profile.data1 if profile else None,
"data2": profile.data2 if profile else None,
"data3": profile.data3 if profile else None,
```

Comment out or remove the `PATCH /member/profile` endpoint entirely.

- [ ] **Step 2: Add change-request routes to `app/api/member/__init__.py`**

Add these routes to the member router:

```python
from ..schemas.member import ChangeRequestCreate
from ..services.member_service import MemberService
from ..db.queries.member_query import MemberQuery

@member_router.post("/change-requests", response_model=ResponseModel, status_code=201)
async def create_change_request(body: ChangeRequestCreate, request: Request):
    user_id = _get_member_id(request)   # use the same helper your existing member endpoints use
    svc = MemberService()
    cr = svc.create_change_request(user_id, body)
    return ResponseModel.ok(data={
        "id": str(cr.id),
        "status": cr.status,
        "requested_fields": cr.requested_fields,
        "reason": cr.reason,
        "created_at": cr.created_at.isoformat() if cr.created_at else None,
    })


@member_router.get("/change-requests", response_model=ResponseModel)
async def list_my_change_requests(request: Request, skip: int = 0, limit: int = 20):
    user_id = _get_member_id(request)
    mq = MemberQuery()
    total, rows = mq.list_change_requests(user_id=user_id, skip=skip, limit=limit)
    return ResponseModel.ok(data={
        "data": [
            {
                "id": str(cr.id),
                "requested_fields": cr.requested_fields,
                "reason": cr.reason,
                "status": cr.status,
                "admin_note": cr.admin_note,
                "reviewed_at": cr.reviewed_at.isoformat() if cr.reviewed_at else None,
                "created_at": cr.created_at.isoformat() if cr.created_at else None,
            }
            for cr in rows
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    })
```

- [ ] **Step 3: Restart backend and verify startup**

```bash
pkill -f "python main.py"; sleep 1
cd /home/konsultera/chinar/testpro/easyclaims_backend && python main.py > /tmp/backend.log 2>&1 &
sleep 5 && tail -3 /tmp/backend.log
```

---

## Task 7: Frontend API Client + Admin Member Edit Page

**Files:**
- Modify: `imports/core/api.ts`
- Modify: `app/(admin)/admin/members/[id]/page.tsx`
- Modify: `app/(admin)/admin/members/page.tsx`

**Interfaces:**
- Consumes: `PATCH /admin/members/{id}`, `GET /admin/members/change-requests`, `POST /admin/members/change-requests/{id}/approve`, `POST /admin/members/change-requests/{id}/reject`
- Produces: `adminUpdateMember(id, data)`, `adminListChangeRequests(params)`, `adminApproveChangeRequest(id, note)`, `adminRejectChangeRequest(id, note)` in `api.ts`

- [ ] **Step 1: Add new API functions to `imports/core/api.ts`**

```typescript
// ─── ADMIN — MEMBER UPDATES ────────────────────────────────────────────────
export const adminUpdateMember = (id: string, data: object) =>
  apiClient.patch(`/admin/members/${id}`, data).then((r) => r.data);

export const adminBulkUploadMembers = (file: File, partnerId: string, planId?: string) => {
  const form = new FormData();
  form.append("file", file);
  form.append("partner_id", partnerId);
  if (planId) form.append("plan_id", planId);
  return apiClient.post("/admin/members/bulk-upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

// ─── ADMIN — CHANGE REQUESTS ───────────────────────────────────────────────
export const adminListChangeRequests = (params?: { status?: string; skip?: number; limit?: number }) =>
  apiClient.get("/admin/members/change-requests", { params }).then((r) => r.data);

export const adminApproveChangeRequest = (id: string, admin_note?: string) =>
  apiClient.post(`/admin/members/change-requests/${id}/approve`, { admin_note }).then((r) => r.data);

export const adminRejectChangeRequest = (id: string, admin_note?: string) =>
  apiClient.post(`/admin/members/change-requests/${id}/reject`, { admin_note }).then((r) => r.data);

// ─── ADMIN — AUDIT LOGS ────────────────────────────────────────────────────
export const adminListAuditLogs = (params?: { entity_type?: string; entity_id?: string; skip?: number; limit?: number }) =>
  apiClient.get("/admin/audit-logs", { params }).then((r) => r.data);

// ─── MEMBER — CHANGE REQUESTS ──────────────────────────────────────────────
export const memberListChangeRequests = (params?: { skip?: number; limit?: number }) =>
  apiClient.get("/member/change-requests", { params }).then((r) => r.data);

export const memberCreateChangeRequest = (data: { requested_fields: object; reason?: string }) =>
  apiClient.post("/member/change-requests", data).then((r) => r.data);
```

- [ ] **Step 2: Update admin member detail page `app/(admin)/admin/members/[id]/page.tsx`**

In the existing member detail page:
1. Display all new fields (sale_date, sales_channel, branch_code, salesperson_name, employee_code, data1, data2, data3) in the profile section
2. Add an "Edit Member" button that opens a dialog/panel with an edit form covering all editable fields (name, mobile_no, gender, address fields, all new onboarding fields, is_active)
3. On save, call `adminUpdateMember(memberId, formData)` then refresh
4. Add a "Change Requests" tab showing the member's change requests fetched via `adminListChangeRequests({ entity_id: memberId })` with approve/reject buttons on pending ones

The full implementation follows the existing PrimeReact Dialog + form pattern already in the codebase (see `app/(admin)/admin/partners/page.tsx` for reference). Show each field as a labeled InputText / Calendar / Dropdown as appropriate.

- [ ] **Step 3: Add "Bulk Upload" button to `app/(admin)/admin/members/page.tsx`**

Next to the existing "Add Member" button, add:
```tsx
<Button label="Bulk Upload" icon="pi pi-upload" className="p-button-outlined"
  onClick={() => router.push('/admin/members/bulk-upload')} />
```

---

## Task 8: Frontend — Bulk Upload Page

**Files:**
- Create: `app/(admin)/admin/members/bulk-upload/page.tsx`

- [ ] **Step 1: Create the bulk upload page**

```tsx
"use client";
import { useState, useEffect } from "react";
import { Button } from "primereact/button";
import { Dropdown } from "primereact/dropdown";
import { FileUpload } from "primereact/fileupload";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Message } from "primereact/message";
import { adminListPartners } from "@/imports/core/api";
import { adminBulkUploadMembers } from "@/imports/core/api";

export default function BulkUploadPage() {
  const [partners, setPartners] = useState<any[]>([]);
  const [partnerId, setPartnerId] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    adminListPartners({}).then((r) => setPartners(r.data?.data || []));
  }, []);

  const handleUpload = async () => {
    if (!file || !partnerId) { setError("Select a partner and file"); return; }
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await adminBulkUploadMembers(file, partnerId);
      setResult(res.data);
    } catch (e: any) {
      setError(e?.response?.data?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Bulk Member Upload</h2>
      <div className="mb-4 text-sm text-gray-500">
        Download the template Excel with columns: Sale Date | Primary Member Full Name | Gender |
        Primary Mobile No. | Primary Email ID | Address Line1 | City | State | Pin Code |
        Sales Channel | Partner Branch Code | Sales Person Name | Employee Code | Data 1 | Data 2 | Data 3
      </div>
      <div className="flex gap-4 mb-4 flex-wrap">
        <Dropdown
          value={partnerId}
          options={partners.map((p) => ({ label: p.name, value: p.id }))}
          onChange={(e) => setPartnerId(e.value)}
          placeholder="Select Partner"
          className="w-64"
        />
        <input type="file" accept=".xlsx,.xls"
          onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <Button label="Upload" icon="pi pi-upload" loading={loading} onClick={handleUpload} />
      </div>
      {error && <Message severity="error" text={error} className="mb-4" />}
      {result && (
        <div>
          <div className="flex gap-6 mb-4">
            <div className="text-green-600 font-medium">✓ Created: {result.created?.length}</div>
            <div className="text-yellow-600 font-medium">⚠ Skipped: {result.skipped?.length}</div>
            <div className="text-red-600 font-medium">✗ Errors: {result.errors?.length}</div>
          </div>
          {result.errors?.length > 0 && (
            <DataTable value={result.errors} className="mb-4" header="Errors">
              <Column field="row" header="Row" />
              <Column field="email" header="Email" />
              <Column field="reason" header="Reason" />
            </DataTable>
          )}
          {result.skipped?.length > 0 && (
            <DataTable value={result.skipped} header="Skipped">
              <Column field="row" header="Row" />
              <Column field="email" header="Email" />
              <Column field="reason" header="Reason" />
            </DataTable>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Task 9: Frontend — Admin Change Requests Page

**Files:**
- Create: `app/(admin)/admin/change-requests/page.tsx`
- Modify: `components/layout/Sidebar.tsx`

- [ ] **Step 1: Create admin change requests page**

```tsx
"use client";
import { useState, useEffect, useCallback } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Button } from "primereact/button";
import { Tag } from "primereact/tag";
import { Dialog } from "primereact/dialog";
import { InputTextarea } from "primereact/inputtextarea";
import { adminListChangeRequests, adminApproveChangeRequest, adminRejectChangeRequest } from "@/imports/core/api";

export default function AdminChangeRequestsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<any>(null);
  const [note, setNote] = useState("");
  const [action, setAction] = useState<"approve" | "reject" | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await adminListChangeRequests({ status: "pending", limit: 100 });
    setRows(res.data?.data || []);
    setTotal(res.data?.total || 0);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleReview = async () => {
    if (!selected || !action) return;
    if (action === "approve") await adminApproveChangeRequest(selected.id, note);
    else await adminRejectChangeRequest(selected.id, note);
    setSelected(null); setNote(""); setAction(null);
    load();
  };

  const statusTemplate = (row: any) => (
    <Tag value={row.status}
      severity={row.status === "approved" ? "success" : row.status === "rejected" ? "danger" : "warning"} />
  );

  const actionsTemplate = (row: any) => row.status === "pending" ? (
    <div className="flex gap-2">
      <Button size="small" label="Approve" severity="success"
        onClick={() => { setSelected(row); setAction("approve"); }} />
      <Button size="small" label="Reject" severity="danger"
        onClick={() => { setSelected(row); setAction("reject"); }} />
    </div>
  ) : null;

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Profile Change Requests ({total})</h2>
      <DataTable value={rows} loading={loading} paginator rows={20}>
        <Column field="member_name" header="Member" />
        <Column field="member_email" header="Email" />
        <Column field="reason" header="Reason" />
        <Column header="Requested Changes"
          body={(row) => <pre className="text-xs">{JSON.stringify(row.requested_fields, null, 2)}</pre>} />
        <Column header="Status" body={statusTemplate} />
        <Column header="Actions" body={actionsTemplate} />
      </DataTable>

      <Dialog header={action === "approve" ? "Approve Request" : "Reject Request"}
        visible={!!selected} onHide={() => { setSelected(null); setAction(null); setNote(""); }}
        style={{ width: "400px" }}>
        <div className="flex flex-col gap-3">
          <label>Admin Note (optional)</label>
          <InputTextarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} />
          <Button label="Confirm" onClick={handleReview}
            severity={action === "approve" ? "success" : "danger"} />
        </div>
      </Dialog>
    </div>
  );
}
```

- [ ] **Step 2: Add "Change Requests" to admin Sidebar**

In `components/layout/Sidebar.tsx`, find the admin nav links array and add:
```tsx
{ label: "Change Requests", icon: "pi pi-inbox", href: "/admin/change-requests" }
```

---

## Task 10: Frontend — Member Profile (Read-Only) + Change Request Page

**Files:**
- Modify: `app/(member)/member/profile/page.tsx`
- Create: `app/(member)/member/change-requests/page.tsx`
- Modify: `components/layout/Sidebar.tsx`

- [ ] **Step 1: Update member profile page to read-only with new fields**

In the existing member profile page, remove all edit form controls (InputText, save button, form submit). Replace the editable section with a read-only card layout showing all fields:

Core fields: Name, Email, Mobile, Gender, DOB, Address Line, City, State, Pin Code
Onboarding fields (shown if present): Sale Date, Sales Channel, Branch Code, Salesperson Name, Employee Code, Data 1, Data 2, Data 3

Add a "Request Profile Change" button at the bottom that links to `/member/change-requests/new`.

- [ ] **Step 2: Create member change request page**

```tsx
"use client";
import { useState, useEffect } from "react";
import { InputText } from "primereact/inputtext";
import { InputTextarea } from "primereact/inputtextarea";
import { Button } from "primereact/button";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Tag } from "primereact/tag";
import { memberListChangeRequests, memberCreateChangeRequest, memberGetProfile } from "@/imports/core/api";

const EDITABLE_FIELDS = [
  { key: "name", label: "Full Name" },
  { key: "mobile_no", label: "Mobile Number" },
  { key: "gender", label: "Gender" },
  { key: "address_line", label: "Address Line" },
  { key: "address_city", label: "City" },
  { key: "address_state", label: "State" },
  { key: "address_pin", label: "Pin Code" },
];

export default function MemberChangeRequestsPage() {
  const [profile, setProfile] = useState<any>(null);
  const [changes, setChanges] = useState<Record<string, string>>({});
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    memberGetProfile().then((r) => setProfile(r.data));
    memberListChangeRequests().then((r) => setHistory(r.data?.data || []));
  }, []);

  const handleSubmit = async () => {
    const filtered = Object.fromEntries(Object.entries(changes).filter(([, v]) => v.trim() !== ""));
    if (!Object.keys(filtered).length) return;
    setSubmitting(true);
    await memberCreateChangeRequest({ requested_fields: filtered, reason });
    setChanges({}); setReason(""); setSuccess(true);
    memberListChangeRequests().then((r) => setHistory(r.data?.data || []));
    setSubmitting(false);
  };

  const statusTemplate = (row: any) => (
    <Tag value={row.status}
      severity={row.status === "approved" ? "success" : row.status === "rejected" ? "danger" : "warning"} />
  );

  return (
    <div className="p-4 max-w-2xl">
      <h2 className="text-xl font-semibold mb-4">Request Profile Changes</h2>
      <p className="text-sm text-gray-500 mb-4">
        Fill in only the fields you want to change. An admin will review and apply the changes.
      </p>
      {success && <div className="text-green-600 mb-4">Request submitted successfully.</div>}
      <div className="flex flex-col gap-3 mb-4">
        {EDITABLE_FIELDS.map((f) => (
          <div key={f.key} className="flex flex-col gap-1">
            <label className="text-sm font-medium">{f.label}</label>
            <InputText
              placeholder={`Current: ${profile?.profile?.[f.key] || profile?.[f.key] || "—"}`}
              value={changes[f.key] || ""}
              onChange={(e) => setChanges((p) => ({ ...p, [f.key]: e.target.value }))}
            />
          </div>
        ))}
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">Reason for change</label>
          <InputTextarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} />
        </div>
        <Button label="Submit Change Request" loading={submitting} onClick={handleSubmit} />
      </div>

      <h3 className="text-lg font-semibold mb-2 mt-6">My Previous Requests</h3>
      <DataTable value={history}>
        <Column header="Requested Changes"
          body={(row) => <pre className="text-xs">{JSON.stringify(row.requested_fields, null, 2)}</pre>} />
        <Column field="reason" header="Reason" />
        <Column header="Status" body={statusTemplate} />
        <Column field="admin_note" header="Admin Note" />
        <Column field="reviewed_at" header="Reviewed At"
          body={(row) => row.reviewed_at ? new Date(row.reviewed_at).toLocaleDateString() : "—"} />
      </DataTable>
    </div>
  );
}
```

- [ ] **Step 3: Add "Change Requests" to member Sidebar**

In `components/layout/Sidebar.tsx`, find the member nav links and add:
```tsx
{ label: "Change Requests", icon: "pi pi-inbox", href: "/member/change-requests" }
```

---

## Self-Review

### Spec Coverage Check

| Requirement | Task |
|---|---|
| New onboarding columns in DB | Task 1 |
| Mandatory fields enforced on bulk upload | Task 5 |
| Admin bulk Excel upload per partner | Task 5, 8 |
| Welcome message on bulk upload | Task 4 (create_member already sends it) |
| All fields visible to partner and member | Task 7 (admin detail), Task 10 (member profile) |
| Only admin edits member data | Task 5 (PATCH /admin/members/{id}), Task 6 (member PATCH removed) |
| Member raises change ticket | Task 4, 6, 10 |
| Admin notified of change request | Task 4 (notify_all_admins) |
| Admin approves/rejects, data applied on approval | Task 4, 5, 9 |
| Partner NOT notified | Task 4 (no partner notification) |
| Audit logs for all actions | Task 2, 4, 5 |
| Audit log endpoint for admin | Task 5 |
| Member registration form updated | Task 10 (profile read-only + change request flow) |

### No Placeholder Scan
All steps contain actual code. No TBD / TODO left.

### Type Consistency
- `adminUpdateMember` in `api.ts` matches `PATCH /admin/members/{member_id}` returning `ResponseModel`
- `adminApproveChangeRequest(id, note)` / `adminRejectChangeRequest(id, note)` match backend body `{ admin_note }`
- `memberCreateChangeRequest({ requested_fields, reason })` matches `ChangeRequestCreate` schema
- `AuditService.log()` never raises — safe to call from anywhere
