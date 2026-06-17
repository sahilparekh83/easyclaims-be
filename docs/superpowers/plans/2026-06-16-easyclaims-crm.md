# EasyClaims CRM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CRM layer — Plans (global/partner-type), Partners, Member Enrollments (many-to-many member↔partner), and Policies across three portals: SuperAdmin, Partner, Customer.

**Architecture:** Member↔Partner is many-to-many via `member_enrollments`. Plans have `plan_type` (global|partner); partner-type plans are linked to specific partners via `partner_plans` junction. Customer sessions carry `X-Partner-Id` header to scope `/me/` requests to a specific enrollment. Login response includes `default_partner_id` for CUSTOMER users.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 sync, psycopg3, Alembic, Pydantic v2, python-multipart

**Task 1 (PARTNER enum) already done — commit ffd508f.**

---

### Task 2: CRM Models

**Files:**
- Create: `app/db/models/plan.py`
- Create: `app/db/models/partner.py`
- Create: `app/db/models/member.py`
- Create: `app/db/models/policy.py`
- Modify: `app/db/models/__init__.py`

**Do NOT add partner_id to users table.**

- [ ] **Step 1: Create `app/db/models/plan.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    tagline = Column(String, nullable=False, default="")
    info_text = Column(Text, nullable=True)
    price = Column(Integer, nullable=False, default=0)
    cycle = Column(String, nullable=False, default="Annual")
    plan_type = Column(String, nullable=False, default="global")
    status = Column(String, nullable=False, default="Draft")
    color = Column(String, nullable=True, default="var(--blue-500)")
    popular = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    benefit_family = Column(Integer, nullable=False, default=2)
    benefit_slots = Column(Integer, nullable=False, default=3)
    benefit_claim = Column(String, nullable=False, default="Standard")
    benefit_aiqa = Column(Boolean, nullable=False, default=True)
    benefit_aicalls = Column(Boolean, nullable=False, default=False)
    benefit_voice = Column(String, nullable=False, default="English")
    benefit_vault = Column(Boolean, nullable=False, default=True)
    benefit_rm = Column(Boolean, nullable=False, default=False)
    benefit_concierge = Column(Boolean, nullable=False, default=False)
    benefit_teleconsult_sessions = Column(Integer, nullable=False, default=0)
    benefit_hospital_cash = Column(Boolean, nullable=False, default=False)
    benefit_wellness_sessions = Column(Integer, nullable=False, default=0)
    benefit_emergency_assist = Column(Boolean, nullable=False, default=False)
    benefit_legal_assist = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("plan_type", "global")
        kwargs.setdefault("status", "Draft")
        kwargs.setdefault("popular", False)
        kwargs.setdefault("is_deleted", False)
        kwargs.setdefault("benefit_family", 2)
        kwargs.setdefault("benefit_slots", 3)
        kwargs.setdefault("benefit_claim", "Standard")
        kwargs.setdefault("benefit_aiqa", True)
        kwargs.setdefault("benefit_aicalls", False)
        kwargs.setdefault("benefit_voice", "English")
        kwargs.setdefault("benefit_vault", True)
        kwargs.setdefault("benefit_rm", False)
        kwargs.setdefault("benefit_concierge", False)
        kwargs.setdefault("benefit_teleconsult_sessions", 0)
        kwargs.setdefault("benefit_hospital_cash", False)
        kwargs.setdefault("benefit_wellness_sessions", 0)
        kwargs.setdefault("benefit_emergency_assist", False)
        kwargs.setdefault("benefit_legal_assist", False)
        super().__init__(**kwargs)
```

- [ ] **Step 2: Create `app/db/models/partner.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Partner(Base):
    __tablename__ = "partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    partner_type = Column(String, nullable=False, default="Broker")
    city = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Active")
    api_key = Column(String, unique=True, nullable=True)
    api_rate_limit = Column(Integer, nullable=False, default=600)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", foreign_keys=[user_id])

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "Active")
        kwargs.setdefault("api_rate_limit", 600)
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)


class PartnerPlan(Base):
    __tablename__ = "partner_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("membership_plans.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    partner = relationship("Partner")
    plan = relationship("MembershipPlan")

    __table_args__ = (
        UniqueConstraint("partner_id", "plan_id", name="uq_partner_plan"),
    )
```

- [ ] **Step 3: Create `app/db/models/member.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class MemberEnrollment(Base):
    __tablename__ = "member_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("membership_plans.id"), nullable=False)
    status = Column(String, nullable=False, default="active")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    plan = relationship("MembershipPlan")
    partner = relationship("Partner")

    __table_args__ = (
        UniqueConstraint("user_id", "partner_id", name="uq_member_partner"),
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "active")
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
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("preferred_language", "English")
        kwargs.setdefault("channel_email", True)
        kwargs.setdefault("channel_whatsapp", False)
        kwargs.setdefault("channel_voice", False)
        super().__init__(**kwargs)


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
```

- [ ] **Step 4: Create `app/db/models/policy.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    policy_number = Column(String, nullable=True, unique=True)
    policy_type = Column(String, nullable=False)
    insurer = Column(String, nullable=True)
    sum_insured = Column(BigInteger, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String, nullable=False, default="pending")
    ai_confidence = Column(Integer, nullable=True)
    file_path = Column(String, nullable=True)
    extracted_fields = Column(JSONB, nullable=True, default=dict)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "pending")
        kwargs.setdefault("is_deleted", False)
        kwargs.setdefault("extracted_fields", {})
        super().__init__(**kwargs)
```

- [ ] **Step 5: Update `app/db/models/__init__.py`**

```python
from .user import User, OTPLog, AuthSession
from .roles import Role, UserRole
from .plan import MembershipPlan
from .partner import Partner, PartnerPlan
from .member import MemberEnrollment, MemberProfile, FamilyMember, Nominee, DpdpConsent
from .policy import Policy

__all__ = [
    "User", "OTPLog", "AuthSession", "Role", "UserRole",
    "MembershipPlan",
    "Partner", "PartnerPlan",
    "MemberEnrollment", "MemberProfile", "FamilyMember", "Nominee", "DpdpConsent",
    "Policy",
]
```

- [ ] **Step 6: Verify imports**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
MODE=DEV python -c "from app.db.models import MembershipPlan, Partner, PartnerPlan, MemberEnrollment, MemberProfile, FamilyMember, Nominee, DpdpConsent, Policy; print('OK')"
```
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add app/db/models/
git commit -m "feat: CRM models — plan, partner, partner_plans, member_enrollments, policy"
```

---

### Task 3: Alembic migration for all CRM tables + seed data

**Files:**
- Create: `alembic/versions/xxxx_crm_tables.py` (autogenerated)
- Create: `alembic/seed_crm.py`

- [ ] **Step 1: Generate migration**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
MODE=DEV alembic revision --autogenerate -m "crm_tables"
```

Open the generated file and verify it creates these tables in this order:
1. `membership_plans`
2. `partners`
3. `partner_plans` (FK → partners, membership_plans)
4. `member_enrollments` (FK → users, partners, membership_plans)
5. `member_profiles` (FK → users)
6. `family_members` (FK → users)
7. `nominees` (FK → users)
8. `dpdp_consents` (FK → users)
9. `policies` (FK → users, partners)

If autogenerate puts them out of FK order, manually reorder the `op.create_table` calls in `upgrade()`.

- [ ] **Step 2: Apply migration**

```bash
MODE=DEV alembic upgrade head
```
Expected: no errors.

- [ ] **Step 3: Create `alembic/seed_crm.py`**

```python
import os
os.environ.setdefault("MODE", "DEV")
from app.db.session import session_scope
from app.db.models.plan import MembershipPlan

PLANS = [
    dict(name="Essential", tagline="Everyday cover for individuals",
         info_text="Get started with essential health membership coverage.", price=1499,
         cycle="Annual", plan_type="global", status="Active", color="var(--blue-500)",
         benefit_family=2, benefit_slots=3, benefit_claim="Standard",
         benefit_aiqa=True, benefit_vault=True),
    dict(name="Secure", tagline="Complete protection for families",
         info_text="Full-family coverage with priority claim assistance.", price=2999,
         cycle="Annual", plan_type="global", status="Active", color="var(--green-500)", popular=True,
         benefit_family=4, benefit_slots=6, benefit_claim="Priority",
         benefit_aiqa=True, benefit_aicalls=True, benefit_voice="English + Hindi",
         benefit_vault=True, benefit_concierge=True),
    dict(name="Total Care", tagline="Premium concierge membership",
         info_text="24×7 priority care with dedicated RM and concierge filing.", price=4999,
         cycle="Annual", plan_type="global", status="Active", color="var(--blue-900)",
         benefit_family=6, benefit_slots=12, benefit_claim="24×7 Priority",
         benefit_aiqa=True, benefit_aicalls=True, benefit_voice="English + Hindi",
         benefit_vault=True, benefit_rm=True, benefit_concierge=True),
]

with session_scope() as session:
    for p in PLANS:
        exists = session.query(MembershipPlan).filter_by(name=p["name"]).first()
        if not exists:
            session.add(MembershipPlan(**p))
            print(f"Seeded: {p['name']}")
        else:
            print(f"Already exists: {p['name']}")
```

Run it:
```bash
MODE=DEV python alembic/seed_crm.py
```

- [ ] **Step 4: Commit**

```bash
git add alembic/
git commit -m "feat: CRM migration + seed global plans"
```

---

### Task 4: Plan schema + query + service

**Files:**
- Create: `app/schemas/plan.py`
- Create: `app/db/queries/plan_query.py`
- Create: `app/services/plan_service.py`

- [ ] **Step 1: Create `app/schemas/plan.py`**

```python
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator


class BenefitsSchema(BaseModel):
    family: int = 2
    slots: int = 3
    claim: str = "Standard"
    aiqa: bool = True
    aicalls: bool = False
    voice: str = "English"
    vault: bool = True
    rm: bool = False
    concierge: bool = False
    teleconsult_sessions: int = 0
    hospital_cash: bool = False
    wellness_sessions: int = 0
    emergency_assist: bool = False
    legal_assist: bool = False

    @field_validator("family")
    @classmethod
    def family_range(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("family must be 1–10")
        return v

    @field_validator("slots")
    @classmethod
    def slots_range(cls, v):
        if not 1 <= v <= 20:
            raise ValueError("slots must be 1–20")
        return v

    @field_validator("claim")
    @classmethod
    def claim_valid(cls, v):
        if v not in ("Standard", "Priority", "24×7 Priority"):
            raise ValueError("invalid claim value")
        return v

    @field_validator("voice")
    @classmethod
    def voice_valid(cls, v):
        if v not in ("English", "English + Hindi"):
            raise ValueError("invalid voice value")
        return v


class PlanCreate(BaseModel):
    name: str
    tagline: str = ""
    info_text: Optional[str] = None
    price: int
    cycle: str = "Annual"
    plan_type: str = "global"
    status: str = "Draft"
    color: Optional[str] = "var(--blue-500)"
    popular: bool = False
    benefits: BenefitsSchema = BenefitsSchema()

    @field_validator("cycle")
    @classmethod
    def cycle_valid(cls, v):
        if v not in ("Annual", "Half-yearly", "Quarterly"):
            raise ValueError("invalid cycle")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v):
        if v not in ("Draft", "Active", "Archived"):
            raise ValueError("invalid status")
        return v

    @field_validator("plan_type")
    @classmethod
    def plan_type_valid(cls, v):
        if v not in ("global", "partner"):
            raise ValueError("plan_type must be 'global' or 'partner'")
        return v


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    info_text: Optional[str] = None
    price: Optional[int] = None
    cycle: Optional[str] = None
    plan_type: Optional[str] = None
    color: Optional[str] = None
    popular: Optional[bool] = None
    benefits: Optional[BenefitsSchema] = None
```

- [ ] **Step 2: Create `app/db/queries/plan_query.py`**

```python
from typing import Optional, List
from ..models.plan import MembershipPlan
from ..models.partner import PartnerPlan
from ..session import session_scope


class PlanQuery:
    def get_by_id(self, plan_id: str) -> Optional[MembershipPlan]:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(
                MembershipPlan.id == plan_id, MembershipPlan.is_deleted == False
            ).first()
            if p:
                session.expunge(p)
            return p

    def get_by_name(self, name: str) -> Optional[MembershipPlan]:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(
                MembershipPlan.name == name, MembershipPlan.is_deleted == False
            ).first()
            if p:
                session.expunge(p)
            return p

    def list_all(self, skip: int = 0, limit: int = 100) -> List[MembershipPlan]:
        with session_scope() as session:
            plans = session.query(MembershipPlan).filter(
                MembershipPlan.is_deleted == False
            ).offset(skip).limit(limit).all()
            for p in plans:
                session.expunge(p)
            return plans

    def list_active_global(self) -> List[MembershipPlan]:
        with session_scope() as session:
            plans = session.query(MembershipPlan).filter(
                MembershipPlan.status == "Active",
                MembershipPlan.plan_type == "global",
                MembershipPlan.is_deleted == False,
            ).all()
            for p in plans:
                session.expunge(p)
            return plans

    def list_for_partner(self, partner_id: str) -> List[MembershipPlan]:
        """Returns global active plans + active partner-type plans linked to this partner."""
        with session_scope() as session:
            # global active plans
            global_plans = session.query(MembershipPlan).filter(
                MembershipPlan.status == "Active",
                MembershipPlan.plan_type == "global",
                MembershipPlan.is_deleted == False,
            ).all()
            # partner-linked plans
            linked_ids = [
                row.plan_id for row in
                session.query(PartnerPlan).filter(PartnerPlan.partner_id == partner_id).all()
            ]
            partner_plans = []
            if linked_ids:
                partner_plans = session.query(MembershipPlan).filter(
                    MembershipPlan.id.in_(linked_ids),
                    MembershipPlan.status == "Active",
                    MembershipPlan.is_deleted == False,
                ).all()
            all_plans = global_plans + partner_plans
            for p in all_plans:
                session.expunge(p)
            return all_plans

    def get_first_active(self) -> Optional[MembershipPlan]:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(
                MembershipPlan.status == "Active",
                MembershipPlan.plan_type == "global",
                MembershipPlan.is_deleted == False,
            ).order_by(MembershipPlan.created_at).first()
            if p:
                session.expunge(p)
            return p

    def create(self, **kwargs) -> MembershipPlan:
        with session_scope() as session:
            p = MembershipPlan(**kwargs)
            session.add(p)
            session.flush()
            session.expunge(p)
            return p

    def update(self, plan_id: str, **kwargs) -> Optional[MembershipPlan]:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
            if not p:
                return None
            for k, v in kwargs.items():
                setattr(p, k, v)
            session.flush()
            session.expunge(p)
            return p

    def soft_delete(self, plan_id: str) -> bool:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
            if not p:
                return False
            p.is_deleted = True
            return True

    # ── Partner-plan linking ─────────────────────────────────────────────────
    def link_partner(self, plan_id: str, partner_id: str) -> bool:
        with session_scope() as session:
            exists = session.query(PartnerPlan).filter_by(
                plan_id=plan_id, partner_id=partner_id
            ).first()
            if exists:
                return False
            session.add(PartnerPlan(plan_id=plan_id, partner_id=partner_id))
            return True

    def unlink_partner(self, plan_id: str, partner_id: str) -> bool:
        with session_scope() as session:
            row = session.query(PartnerPlan).filter_by(
                plan_id=plan_id, partner_id=partner_id
            ).first()
            if not row:
                return False
            session.delete(row)
            return True

    def list_linked_partners(self, plan_id: str) -> List[str]:
        with session_scope() as session:
            rows = session.query(PartnerPlan).filter(PartnerPlan.plan_id == plan_id).all()
            return [str(r.partner_id) for r in rows]
```

- [ ] **Step 3: Create `app/services/plan_service.py`**

```python
from typing import List
from fastapi import HTTPException
from ..db.queries.plan_query import PlanQuery
from ..db.models.plan import MembershipPlan
from ..schemas.plan import PlanCreate, PlanUpdate


def _benefits_to_db(b) -> dict:
    return {
        "benefit_family": b.family, "benefit_slots": b.slots,
        "benefit_claim": b.claim, "benefit_aiqa": b.aiqa,
        "benefit_aicalls": b.aicalls, "benefit_voice": b.voice,
        "benefit_vault": b.vault, "benefit_rm": b.rm,
        "benefit_concierge": b.concierge,
        "benefit_teleconsult_sessions": b.teleconsult_sessions,
        "benefit_hospital_cash": b.hospital_cash,
        "benefit_wellness_sessions": b.wellness_sessions,
        "benefit_emergency_assist": b.emergency_assist,
        "benefit_legal_assist": b.legal_assist,
    }


class PlanService:
    def __init__(self):
        self.query = PlanQuery()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[MembershipPlan]:
        return self.query.list_all(skip=skip, limit=limit)

    def list_active_global(self) -> List[MembershipPlan]:
        return self.query.list_active_global()

    def list_for_partner(self, partner_id: str) -> List[MembershipPlan]:
        return self.query.list_for_partner(partner_id)

    def get_by_id(self, plan_id: str) -> MembershipPlan:
        p = self.query.get_by_id(plan_id)
        if not p:
            raise HTTPException(status_code=404, detail="Plan not found")
        return p

    def create(self, data: PlanCreate) -> MembershipPlan:
        if self.query.get_by_name(data.name):
            raise HTTPException(status_code=409, detail="Plan name already exists")
        kwargs = {
            "name": data.name, "tagline": data.tagline, "info_text": data.info_text,
            "price": data.price, "cycle": data.cycle, "plan_type": data.plan_type,
            "status": data.status, "color": data.color, "popular": data.popular,
            **_benefits_to_db(data.benefits),
        }
        return self.query.create(**kwargs)

    def update(self, plan_id: str, data: PlanUpdate) -> MembershipPlan:
        self.get_by_id(plan_id)
        kwargs = data.model_dump(exclude_none=True)
        if "benefits" in kwargs:
            benefits_obj = data.benefits
            kwargs.pop("benefits")
            kwargs.update(_benefits_to_db(benefits_obj))
        p = self.query.update(plan_id, **kwargs)
        if not p:
            raise HTTPException(status_code=404, detail="Plan not found")
        return p

    def activate(self, plan_id: str) -> MembershipPlan:
        self.get_by_id(plan_id)
        return self.query.update(plan_id, status="Active")

    def archive(self, plan_id: str) -> MembershipPlan:
        self.get_by_id(plan_id)
        return self.query.update(plan_id, status="Archived")

    def delete(self, plan_id: str) -> None:
        plan = self.get_by_id(plan_id)
        if plan.status != "Draft":
            raise HTTPException(status_code=409, detail="Only Draft plans can be deleted")
        self.query.soft_delete(plan_id)

    def link_partner(self, plan_id: str, partner_id: str) -> None:
        plan = self.get_by_id(plan_id)
        if plan.plan_type != "partner":
            raise HTTPException(status_code=409, detail="Only partner-type plans can be linked")
        self.query.link_partner(plan_id, partner_id)

    def unlink_partner(self, plan_id: str, partner_id: str) -> None:
        if not self.query.unlink_partner(plan_id, partner_id):
            raise HTTPException(status_code=404, detail="Link not found")
```

- [ ] **Step 4: Run tests**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
MODE=DEV pytest tests/ -q --tb=short
```
Expected: existing tests pass.

- [ ] **Step 5: Commit**

```bash
git add app/schemas/plan.py app/db/queries/plan_query.py app/services/plan_service.py
git commit -m "feat: plan schema, query, service with plan_type and partner linking"
```

---

### Task 5: Partner schema + query + service

**Files:**
- Create: `app/schemas/partner.py`
- Create: `app/db/queries/partner_query.py`
- Create: `app/services/partner_service.py`

- [ ] **Step 1: Create `app/schemas/partner.py`**

```python
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class PartnerCreate(BaseModel):
    name: str
    partner_type: str = "Broker"
    city: Optional[str] = None
    email: EmailStr
    mobile_no: Optional[str] = None


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    partner_type: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    api_rate_limit: Optional[int] = None


class PartnerResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    partner_type: str
    city: Optional[str]
    status: str
    api_key: Optional[str]
    api_rate_limit: int

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Create `app/db/queries/partner_query.py`**

```python
from typing import Optional, List
from ..models.partner import Partner
from ..session import session_scope


class PartnerQuery:
    def get_by_id(self, partner_id: str) -> Optional[Partner]:
        with session_scope() as session:
            p = session.query(Partner).filter(
                Partner.id == partner_id, Partner.is_deleted == False
            ).first()
            if p:
                session.expunge(p)
            return p

    def get_by_user_id(self, user_id: str) -> Optional[Partner]:
        with session_scope() as session:
            p = session.query(Partner).filter(
                Partner.user_id == user_id, Partner.is_deleted == False
            ).first()
            if p:
                session.expunge(p)
            return p

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Partner]:
        with session_scope() as session:
            partners = session.query(Partner).filter(
                Partner.is_deleted == False
            ).offset(skip).limit(limit).all()
            for p in partners:
                session.expunge(p)
            return partners

    def create(self, user_id: str, name: str, partner_type: str,
               city: str = None, api_key: str = None) -> Partner:
        with session_scope() as session:
            p = Partner(user_id=user_id, name=name, partner_type=partner_type,
                        city=city, api_key=api_key)
            session.add(p)
            session.flush()
            session.expunge(p)
            return p

    def update(self, partner_id: str, **kwargs) -> Optional[Partner]:
        with session_scope() as session:
            p = session.query(Partner).filter(Partner.id == partner_id).first()
            if not p:
                return None
            for k, v in kwargs.items():
                setattr(p, k, v)
            session.flush()
            session.expunge(p)
            return p

    def soft_delete(self, partner_id: str) -> bool:
        with session_scope() as session:
            p = session.query(Partner).filter(Partner.id == partner_id).first()
            if not p:
                return False
            p.is_deleted = True
            p.status = "Inactive"
            return True
```

- [ ] **Step 3: Create `app/services/partner_service.py`**

```python
import uuid
from typing import List
from fastapi import HTTPException
from ..db.queries.partner_query import PartnerQuery
from ..db.queries.user_query import UserQuery
from ..db.models.partner import Partner
from ..schemas.partner import PartnerCreate, PartnerUpdate
from ..constants import UserType


class PartnerService:
    def __init__(self):
        self.query = PartnerQuery()
        self.user_query = UserQuery()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Partner]:
        return self.query.list_all(skip=skip, limit=limit)

    def get_by_id(self, partner_id: str) -> Partner:
        p = self.query.get_by_id(partner_id)
        if not p:
            raise HTTPException(status_code=404, detail="Partner not found")
        return p

    def get_by_user_id(self, user_id: str) -> Partner:
        p = self.query.get_by_user_id(user_id)
        if not p:
            raise HTTPException(status_code=404, detail="Partner record not found for this user")
        return p

    def create(self, data: PartnerCreate) -> Partner:
        existing = self.user_query.get_user_by_email(str(data.email))
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        user = self.user_query.create_user(
            email=str(data.email), name=data.name,
            user_type=UserType.PARTNER, mobile_no=data.mobile_no,
        )
        api_key = str(uuid.uuid4()).replace("-", "")
        return self.query.create(
            user_id=str(user.id), name=data.name,
            partner_type=data.partner_type, city=data.city, api_key=api_key,
        )

    def update(self, partner_id: str, data: PartnerUpdate) -> Partner:
        self.get_by_id(partner_id)
        kwargs = data.model_dump(exclude_none=True)
        p = self.query.update(partner_id, **kwargs)
        if not p:
            raise HTTPException(status_code=404, detail="Partner not found")
        return p

    def delete(self, partner_id: str) -> None:
        self.get_by_id(partner_id)
        self.query.soft_delete(partner_id)

    def regenerate_api_key(self, partner_id: str) -> Partner:
        self.get_by_id(partner_id)
        new_key = str(uuid.uuid4()).replace("-", "")
        return self.query.update(partner_id, api_key=new_key)
```

- [ ] **Step 4: Commit**

```bash
git add app/schemas/partner.py app/db/queries/partner_query.py app/services/partner_service.py
git commit -m "feat: partner schema, query, service"
```

---

### Task 6: Member schema + query + service (enrollment-based)

**Files:**
- Create: `app/schemas/member.py`
- Create: `app/db/queries/member_query.py`
- Create: `app/services/member_service.py`

- [ ] **Step 1: Create `app/schemas/member.py`**

```python
from typing import Optional, List
from uuid import UUID
from datetime import date
from pydantic import BaseModel, EmailStr


class MemberCreate(BaseModel):
    email: EmailStr
    name: str
    mobile_no: Optional[str] = None
    partner_id: str
    plan_id: Optional[str] = None


class ProfileUpdate(BaseModel):
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


class FamilyMemberCreate(BaseModel):
    name: str
    relation: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    coverage_type: Optional[str] = "Health"


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    coverage_type: Optional[str] = None


class NomineeCreate(BaseModel):
    name: str
    relation: str
    share_percent: int


class NomineeUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    share_percent: Optional[int] = None


class ConsentCreate(BaseModel):
    version: str
    source: str = "portal"


class PlanSwitchRequest(BaseModel):
    plan_id: str
```

- [ ] **Step 2: Create `app/db/queries/member_query.py`**

```python
from datetime import date
from typing import Optional, List
from ..models.member import MemberProfile, MemberEnrollment, FamilyMember, Nominee, DpdpConsent
from ..session import session_scope


class MemberQuery:
    # ── Enrollments ──────────────────────────────────────────────────────────
    def get_enrollment(self, user_id: str, partner_id: str) -> Optional[MemberEnrollment]:
        with session_scope() as session:
            e = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == user_id,
                MemberEnrollment.partner_id == partner_id,
            ).first()
            if e:
                session.expunge(e)
            return e

    def list_enrollments(self, user_id: str) -> List[MemberEnrollment]:
        with session_scope() as session:
            rows = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == user_id
            ).order_by(MemberEnrollment.created_at).all()
            for r in rows:
                session.expunge(r)
            return rows

    def list_by_partner(self, partner_id: str, skip: int = 0, limit: int = 100) -> List[MemberEnrollment]:
        with session_scope() as session:
            rows = session.query(MemberEnrollment).filter(
                MemberEnrollment.partner_id == partner_id
            ).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return rows

    def create_enrollment(self, user_id: str, partner_id: str, plan_id: str) -> MemberEnrollment:
        today = date.today()
        end = today.replace(year=today.year + 1)
        with session_scope() as session:
            existing = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == user_id,
                MemberEnrollment.partner_id == partner_id,
            ).first()
            if existing:
                existing.plan_id = plan_id
                existing.start_date = today
                existing.end_date = end
                existing.status = "active"
                session.flush()
                session.expunge(existing)
                return existing
            e = MemberEnrollment(
                user_id=user_id, partner_id=partner_id, plan_id=plan_id,
                start_date=today, end_date=end,
            )
            session.add(e)
            session.flush()
            session.expunge(e)
            return e

    def update_enrollment(self, user_id: str, partner_id: str, **kwargs) -> Optional[MemberEnrollment]:
        with session_scope() as session:
            e = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == user_id,
                MemberEnrollment.partner_id == partner_id,
            ).first()
            if not e:
                return None
            for k, v in kwargs.items():
                setattr(e, k, v)
            session.flush()
            session.expunge(e)
            return e

    def get_first_active_enrollment(self, user_id: str) -> Optional[MemberEnrollment]:
        with session_scope() as session:
            e = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == user_id,
                MemberEnrollment.status == "active",
            ).order_by(MemberEnrollment.created_at).first()
            if e:
                session.expunge(e)
            return e

    # ── Profile ──────────────────────────────────────────────────────────────
    def get_profile(self, user_id: str) -> Optional[MemberProfile]:
        with session_scope() as session:
            p = session.query(MemberProfile).filter(MemberProfile.user_id == user_id).first()
            if p:
                session.expunge(p)
            return p

    def upsert_profile(self, user_id: str, **kwargs) -> MemberProfile:
        with session_scope() as session:
            p = session.query(MemberProfile).filter(MemberProfile.user_id == user_id).first()
            if p:
                for k, v in kwargs.items():
                    setattr(p, k, v)
            else:
                p = MemberProfile(user_id=user_id, **kwargs)
                session.add(p)
            session.flush()
            session.expunge(p)
            return p

    # ── Family ───────────────────────────────────────────────────────────────
    def list_family(self, user_id: str) -> List[FamilyMember]:
        with session_scope() as session:
            rows = session.query(FamilyMember).filter(FamilyMember.user_id == user_id).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_family_member(self, member_id: str, user_id: str) -> Optional[FamilyMember]:
        with session_scope() as session:
            m = session.query(FamilyMember).filter(
                FamilyMember.id == member_id, FamilyMember.user_id == user_id
            ).first()
            if m:
                session.expunge(m)
            return m

    def create_family_member(self, user_id: str, **kwargs) -> FamilyMember:
        with session_scope() as session:
            m = FamilyMember(user_id=user_id, **kwargs)
            session.add(m)
            session.flush()
            session.expunge(m)
            return m

    def update_family_member(self, member_id: str, user_id: str, **kwargs) -> Optional[FamilyMember]:
        with session_scope() as session:
            m = session.query(FamilyMember).filter(
                FamilyMember.id == member_id, FamilyMember.user_id == user_id
            ).first()
            if not m:
                return None
            for k, v in kwargs.items():
                setattr(m, k, v)
            session.flush()
            session.expunge(m)
            return m

    def delete_family_member(self, member_id: str, user_id: str) -> bool:
        with session_scope() as session:
            m = session.query(FamilyMember).filter(
                FamilyMember.id == member_id, FamilyMember.user_id == user_id
            ).first()
            if not m:
                return False
            session.delete(m)
            return True

    # ── Nominees ─────────────────────────────────────────────────────────────
    def list_nominees(self, user_id: str) -> List[Nominee]:
        with session_scope() as session:
            rows = session.query(Nominee).filter(Nominee.user_id == user_id).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_nominee(self, nominee_id: str, user_id: str) -> Optional[Nominee]:
        with session_scope() as session:
            n = session.query(Nominee).filter(
                Nominee.id == nominee_id, Nominee.user_id == user_id
            ).first()
            if n:
                session.expunge(n)
            return n

    def total_share(self, user_id: str, exclude_id: str = None) -> int:
        with session_scope() as session:
            q = session.query(Nominee).filter(Nominee.user_id == user_id)
            if exclude_id:
                q = q.filter(Nominee.id != exclude_id)
            return sum(n.share_percent for n in q.all())

    def create_nominee(self, user_id: str, **kwargs) -> Nominee:
        with session_scope() as session:
            n = Nominee(user_id=user_id, **kwargs)
            session.add(n)
            session.flush()
            session.expunge(n)
            return n

    def update_nominee(self, nominee_id: str, user_id: str, **kwargs) -> Optional[Nominee]:
        with session_scope() as session:
            n = session.query(Nominee).filter(
                Nominee.id == nominee_id, Nominee.user_id == user_id
            ).first()
            if not n:
                return None
            for k, v in kwargs.items():
                setattr(n, k, v)
            session.flush()
            session.expunge(n)
            return n

    def delete_nominee(self, nominee_id: str, user_id: str) -> bool:
        with session_scope() as session:
            n = session.query(Nominee).filter(
                Nominee.id == nominee_id, Nominee.user_id == user_id
            ).first()
            if not n:
                return False
            session.delete(n)
            return True

    # ── Consent ──────────────────────────────────────────────────────────────
    def get_latest_consent(self, user_id: str) -> Optional[DpdpConsent]:
        with session_scope() as session:
            c = session.query(DpdpConsent).filter(
                DpdpConsent.user_id == user_id
            ).order_by(DpdpConsent.created_at.desc()).first()
            if c:
                session.expunge(c)
            return c

    def create_consent(self, user_id: str, consented_at, version: str, source: str) -> DpdpConsent:
        with session_scope() as session:
            c = DpdpConsent(user_id=user_id, consented_at=consented_at,
                            version=version, source=source)
            session.add(c)
            session.flush()
            session.expunge(c)
            return c
```

- [ ] **Step 3: Create `app/services/member_service.py`**

```python
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from ..db.queries.member_query import MemberQuery
from ..db.queries.user_query import UserQuery
from ..db.queries.plan_query import PlanQuery
from ..db.queries.partner_query import PartnerQuery
from ..db.models.member import MemberEnrollment, MemberProfile, FamilyMember, Nominee, DpdpConsent
from ..schemas.member import (
    MemberCreate, ProfileUpdate,
    FamilyMemberCreate, FamilyMemberUpdate,
    NomineeCreate, NomineeUpdate,
    ConsentCreate,
)
from ..constants import UserType


class MemberService:
    def __init__(self):
        self.q = MemberQuery()
        self.user_q = UserQuery()
        self.plan_q = PlanQuery()
        self.partner_q = PartnerQuery()

    def create_member(self, data: MemberCreate) -> dict:
        existing = self.user_q.get_user_by_email(str(data.email))
        if existing:
            # Allow re-enrollment under a new partner for existing member
            user = existing
        else:
            user = self.user_q.create_user(
                email=str(data.email), name=data.name,
                user_type=UserType.CUSTOMER, mobile_no=data.mobile_no,
            )

        partner = self.partner_q.get_by_id(data.partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")

        if data.plan_id:
            plan = self.plan_q.get_by_id(data.plan_id)
            if not plan or plan.status != "Active":
                raise HTTPException(status_code=404, detail="Plan not found or not active")
            plan_id = data.plan_id
        else:
            available = self.plan_q.list_for_partner(data.partner_id)
            if not available:
                raise HTTPException(status_code=422, detail="No active plans available for this partner")
            plan_id = str(available[0].id)

        enrollment = self.q.create_enrollment(str(user.id), data.partner_id, plan_id)
        self.q.upsert_profile(str(user.id))
        return {"user": user, "enrollment": enrollment}

    # ── Enrollments ──────────────────────────────────────────────────────────
    def list_enrollments(self, user_id: str) -> List[MemberEnrollment]:
        return self.q.list_enrollments(user_id)

    def get_enrollment(self, user_id: str, partner_id: str) -> MemberEnrollment:
        e = self.q.get_enrollment(user_id, partner_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return e

    def get_active_enrollment(self, user_id: str, partner_id: Optional[str]) -> MemberEnrollment:
        """Used by X-Partner-Id dependency. Falls back to first active if partner_id is None."""
        if partner_id:
            e = self.q.get_enrollment(user_id, partner_id)
            if not e:
                raise HTTPException(status_code=403, detail="No enrollment found for this partner")
            return e
        e = self.q.get_first_active_enrollment(user_id)
        if not e:
            raise HTTPException(status_code=404, detail="No active enrollment found")
        return e

    def switch_plan(self, user_id: str, partner_id: str, plan_id: str) -> MemberEnrollment:
        available = self.plan_q.list_for_partner(partner_id)
        available_ids = [str(p.id) for p in available]
        if plan_id not in available_ids:
            raise HTTPException(status_code=404, detail="Plan not available for this partner")
        e = self.q.update_enrollment(user_id, partner_id, plan_id=plan_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return e

    # ── Profile ──────────────────────────────────────────────────────────────
    def get_profile(self, user_id: str) -> dict:
        user = self.user_q.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        profile = self.q.get_profile(user_id)
        return {"user": user, "profile": profile}

    def update_profile(self, user_id: str, data: ProfileUpdate) -> dict:
        user_field_names = {"name", "mobile_no"}
        user_fields, profile_fields = {}, {}
        for field, value in data.model_dump(exclude_none=True).items():
            if field in user_field_names:
                user_fields[field] = value
            else:
                profile_fields[field] = value
        if user_fields:
            self.user_q.update_user(user_id, **user_fields)
        if profile_fields:
            self.q.upsert_profile(user_id, **profile_fields)
        return self.get_profile(user_id)

    # ── Family ───────────────────────────────────────────────────────────────
    def list_family(self, user_id: str) -> List[FamilyMember]:
        return self.q.list_family(user_id)

    def add_family_member(self, user_id: str, data: FamilyMemberCreate) -> FamilyMember:
        return self.q.create_family_member(user_id, **data.model_dump())

    def update_family_member(self, user_id: str, member_id: str, data: FamilyMemberUpdate) -> FamilyMember:
        m = self.q.update_family_member(member_id, user_id, **data.model_dump(exclude_none=True))
        if not m:
            raise HTTPException(status_code=404, detail="Family member not found")
        return m

    def delete_family_member(self, user_id: str, member_id: str) -> None:
        if not self.q.delete_family_member(member_id, user_id):
            raise HTTPException(status_code=404, detail="Family member not found")

    # ── Nominees ─────────────────────────────────────────────────────────────
    def list_nominees(self, user_id: str) -> List[Nominee]:
        return self.q.list_nominees(user_id)

    def add_nominee(self, user_id: str, data: NomineeCreate) -> Nominee:
        current = self.q.total_share(user_id)
        if current + data.share_percent > 100:
            raise HTTPException(status_code=422,
                                detail=f"Total share would exceed 100% (current: {current}%)")
        return self.q.create_nominee(user_id, **data.model_dump())

    def update_nominee(self, user_id: str, nominee_id: str, data: NomineeUpdate) -> Nominee:
        kwargs = data.model_dump(exclude_none=True)
        if "share_percent" in kwargs:
            current = self.q.total_share(user_id, exclude_id=nominee_id)
            if current + kwargs["share_percent"] > 100:
                raise HTTPException(status_code=422, detail="Total share would exceed 100%")
        n = self.q.update_nominee(nominee_id, user_id, **kwargs)
        if not n:
            raise HTTPException(status_code=404, detail="Nominee not found")
        return n

    def delete_nominee(self, user_id: str, nominee_id: str) -> None:
        if not self.q.delete_nominee(nominee_id, user_id):
            raise HTTPException(status_code=404, detail="Nominee not found")

    # ── Consent ──────────────────────────────────────────────────────────────
    def get_consent(self, user_id: str) -> DpdpConsent:
        c = self.q.get_latest_consent(user_id)
        if not c:
            raise HTTPException(status_code=404, detail="No consent record found")
        return c

    def record_consent(self, user_id: str, data: ConsentCreate) -> DpdpConsent:
        return self.q.create_consent(
            user_id, consented_at=datetime.now(timezone.utc),
            version=data.version, source=data.source,
        )
```

- [ ] **Step 4: Commit**

```bash
git add app/schemas/member.py app/db/queries/member_query.py app/services/member_service.py
git commit -m "feat: member schema, query, service with enrollment-based many-to-many"
```

---

### Task 7: Policy schema + query + service + UPLOAD_DIR

**Files:**
- Create: `app/schemas/policy.py`
- Create: `app/db/queries/policy_query.py`
- Create: `app/services/policy_service.py`
- Modify: `app/configs/base.py`

- [ ] **Step 1: Add UPLOAD_DIR to `app/configs/base.py`**

In the `Settings` class, after `SMTP_TLS`:
```python
    # ── File Upload ───────────────────────────────────────────────────────────
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
```

- [ ] **Step 2: Create `app/schemas/policy.py`**

```python
from typing import Optional, Any, Dict
from uuid import UUID
from datetime import date
from pydantic import BaseModel


class PolicyCreate(BaseModel):
    policy_type: str
    insurer: Optional[str] = None
    sum_insured: Optional[int] = None


class PolicyResponse(BaseModel):
    id: UUID
    policy_number: Optional[str]
    policy_type: str
    insurer: Optional[str]
    sum_insured: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    ai_confidence: Optional[int]
    extracted_fields: Optional[Dict[str, Any]]

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Create `app/db/queries/policy_query.py`**

```python
from typing import Optional, List
from ..models.policy import Policy
from ..session import session_scope


class PolicyQuery:
    def list_by_user_partner(self, user_id: str, partner_id: str) -> List[Policy]:
        with session_scope() as session:
            rows = session.query(Policy).filter(
                Policy.user_id == user_id,
                Policy.partner_id == partner_id,
                Policy.is_deleted == False,
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def list_by_user(self, user_id: str) -> List[Policy]:
        with session_scope() as session:
            rows = session.query(Policy).filter(
                Policy.user_id == user_id, Policy.is_deleted == False
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_by_id(self, policy_id: str, user_id: str = None) -> Optional[Policy]:
        with session_scope() as session:
            q = session.query(Policy).filter(
                Policy.id == policy_id, Policy.is_deleted == False
            )
            if user_id:
                q = q.filter(Policy.user_id == user_id)
            p = q.first()
            if p:
                session.expunge(p)
            return p

    def create(self, user_id: str, partner_id: str, policy_number: str, **kwargs) -> Policy:
        with session_scope() as session:
            p = Policy(user_id=user_id, partner_id=partner_id,
                       policy_number=policy_number, **kwargs)
            session.add(p)
            session.flush()
            session.expunge(p)
            return p

    def soft_delete(self, policy_id: str, user_id: str) -> bool:
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == policy_id, Policy.user_id == user_id
            ).first()
            if not p:
                return False
            p.is_deleted = True
            return True
```

- [ ] **Step 4: Create `app/services/policy_service.py`**

```python
import os
import uuid
from datetime import datetime
from typing import List
from fastapi import HTTPException, UploadFile
from ..db.queries.policy_query import PolicyQuery
from ..db.models.policy import Policy
from ..schemas.policy import PolicyCreate
from ..configs.common import get_settings


def _gen_policy_number() -> str:
    return f"POL-{datetime.now().year}-{str(uuid.uuid4().int)[:6].zfill(6)}"


class PolicyService:
    def __init__(self):
        self.query = PolicyQuery()

    def list_policies(self, user_id: str, partner_id: str) -> List[Policy]:
        return self.query.list_by_user_partner(user_id, partner_id)

    def get_policy(self, user_id: str, policy_id: str) -> Policy:
        p = self.query.get_by_id(policy_id, user_id=user_id)
        if not p:
            raise HTTPException(status_code=404, detail="Policy not found")
        return p

    async def upload_policy(self, user_id: str, partner_id: str,
                            data: PolicyCreate, file: UploadFile) -> Policy:
        settings = get_settings()
        if file.content_type not in ("application/pdf", "application/octet-stream"):
            raise HTTPException(status_code=422, detail="Only PDF files are accepted")
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="File exceeds 10MB limit")
        if not contents.startswith(b"%PDF"):
            raise HTTPException(status_code=422, detail="File does not appear to be a valid PDF")
        upload_dir = os.path.join(settings.UPLOAD_DIR, "policies", user_id)
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}.pdf")
        with open(file_path, "wb") as f:
            f.write(contents)
        return self.query.create(
            user_id=user_id, partner_id=partner_id,
            policy_number=_gen_policy_number(),
            policy_type=data.policy_type, insurer=data.insurer,
            sum_insured=data.sum_insured, file_path=file_path,
        )

    def delete_policy(self, user_id: str, policy_id: str) -> None:
        if not self.query.soft_delete(policy_id, user_id):
            raise HTTPException(status_code=404, detail="Policy not found")
```

- [ ] **Step 5: Commit**

```bash
git add app/schemas/policy.py app/db/queries/policy_query.py app/services/policy_service.py app/configs/base.py
git commit -m "feat: policy schema, query, service + UPLOAD_DIR"
```

---

### Task 8: API deps + login response default_partner_id + public plans + router scaffolds

**Files:**
- Create: `app/api/deps.py`
- Modify: `app/api/auth.py` (add default_partner_id to verify-otp response)
- Create: `app/api/plans.py`
- Create: `app/api/admin/__init__.py`
- Create: `app/api/partner/__init__.py`
- Create: `app/api/me/__init__.py`
- Modify: `app/api/__init__.py`

- [ ] **Step 1: Create `app/api/deps.py`**

```python
from typing import Optional
from fastapi import HTTPException, Request
from ..db.queries.partner_query import PartnerQuery
from ..services.member_service import MemberService
from ..constants import UserType


def _require_partner(request: Request):
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    if payload.get("user_type") != UserType.PARTNER:
        raise HTTPException(status_code=403, detail="Partner access required")
    partner = PartnerQuery().get_by_user_id(payload["sub"])
    if not partner:
        raise HTTPException(status_code=404, detail="Partner record not found")
    return partner


def _require_customer(request: Request):
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    if payload.get("user_type") != UserType.CUSTOMER:
        raise HTTPException(status_code=403, detail="Customer access required")
    return payload


def _require_customer_enrollment(request: Request):
    """Reads X-Partner-Id header, resolves enrollment. Falls back to first active."""
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    if payload.get("user_type") != UserType.CUSTOMER:
        raise HTTPException(status_code=403, detail="Customer access required")
    user_id = payload["sub"]
    partner_id: Optional[str] = request.headers.get("X-Partner-Id")
    svc = MemberService()
    enrollment = svc.get_active_enrollment(user_id, partner_id)
    return enrollment
```

- [ ] **Step 2: Modify `app/api/auth.py` verify-otp to include default_partner_id**

Find the `verify_otp` function. After `user_query.create_auth_session(...)`, add:

```python
    # Resolve default_partner_id for CUSTOMER users
    default_partner_id = None
    if user.user_type.value == "CUSTOMER":
        from ..db.queries.member_query import MemberQuery
        first_enrollment = MemberQuery().get_first_active_enrollment(str(user.id))
        if first_enrollment:
            default_partner_id = str(first_enrollment.partner_id)
```

Then change the final return to:
```python
    return ResponseModel.ok(data={
        **TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ).model_dump(),
        "default_partner_id": default_partner_id,
    })
```

- [ ] **Step 3: Create `app/api/plans.py` (public — active global plans)**

```python
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ..schemas.base import ResponseModel
from ..services.plan_service import PlanService
from .users import _require_authenticated

plans_router = APIRouter()


def _plan_to_dict(plan) -> dict:
    return {
        "id": str(plan.id),
        "name": plan.name,
        "tagline": plan.tagline,
        "info_text": plan.info_text,
        "price": plan.price,
        "cycle": plan.cycle,
        "plan_type": plan.plan_type,
        "status": plan.status,
        "color": plan.color,
        "popular": plan.popular,
        "benefits": {
            "family": plan.benefit_family,
            "slots": plan.benefit_slots,
            "claim": plan.benefit_claim,
            "aiqa": plan.benefit_aiqa,
            "aicalls": plan.benefit_aicalls,
            "voice": plan.benefit_voice,
            "vault": plan.benefit_vault,
            "rm": plan.benefit_rm,
            "concierge": plan.benefit_concierge,
            "teleconsult_sessions": plan.benefit_teleconsult_sessions,
            "hospital_cash": plan.benefit_hospital_cash,
            "wellness_sessions": plan.benefit_wellness_sessions,
            "emergency_assist": plan.benefit_emergency_assist,
            "legal_assist": plan.benefit_legal_assist,
        },
    }


@plans_router.get("", response_model=ResponseModel)
async def list_active_plans(request: Request, _=Depends(_require_authenticated)):
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in PlanService().list_active_global()])


@plans_router.get("/{plan_id}", response_model=ResponseModel)
async def get_plan(plan_id: UUID, request: Request, _=Depends(_require_authenticated)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().get_by_id(str(plan_id))))
```

- [ ] **Step 4: Create empty router inits**

`app/api/admin/__init__.py`:
```python
from fastapi import APIRouter
admin_router = APIRouter()
```

`app/api/partner/__init__.py`:
```python
from fastapi import APIRouter
partner_router = APIRouter()
```

`app/api/me/__init__.py`:
```python
from fastapi import APIRouter
me_router = APIRouter()
```

- [ ] **Step 5: Update `app/api/__init__.py`**

```python
from fastapi import APIRouter
from .auth import auth_router
from .users import users_router
from .roles import roles_router
from .plans import plans_router
from .admin import admin_router
from .partner import partner_router
from .me import me_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(roles_router, prefix="/roles", tags=["Roles"])
api_router.include_router(plans_router, prefix="/plans", tags=["Plans"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_router.include_router(partner_router, prefix="/partner", tags=["Partner"])
api_router.include_router(me_router, prefix="/me", tags=["Me"])


@api_router.get("/health", tags=["Health"])
async def health():
    from ..configs.common import get_settings
    settings = get_settings()
    return {"status": "ok", "mode": "DEV" if settings.DEBUG else "PROD"}
```

- [ ] **Step 6: Verify app starts**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
MODE=DEV python -c "from app.application import create_application; app = create_application(); print('OK')"
```
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add app/api/
git commit -m "feat: deps, X-Partner-Id enrollment resolver, default_partner_id in login, public plans, router scaffolds"
```

---

### Task 9: SuperAdmin routes

**Files:**
- Create: `app/api/admin/plans.py`
- Create: `app/api/admin/partners.py`
- Create: `app/api/admin/members.py`
- Create: `app/api/admin/dashboard.py`
- Modify: `app/api/admin/__init__.py`

- [ ] **Step 1: Create `app/api/admin/plans.py`**

```python
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...schemas.plan import PlanCreate, PlanUpdate
from ...services.plan_service import PlanService
from ..users import _require_superadmin
from ..plans import _plan_to_dict

admin_plans_router = APIRouter()


class LinkPartnerBody(BaseModel):
    partner_id: str


@admin_plans_router.get("", response_model=ResponseModel)
async def list_plans(request: Request, skip: int = 0, limit: int = 100,
                     _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in PlanService().list_all(skip=skip, limit=limit)])


@admin_plans_router.post("", response_model=ResponseModel, status_code=201)
async def create_plan(body: PlanCreate, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().create(body)))


@admin_plans_router.get("/{plan_id}", response_model=ResponseModel)
async def get_plan(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().get_by_id(str(plan_id))))


@admin_plans_router.patch("/{plan_id}", response_model=ResponseModel)
async def update_plan(plan_id: UUID, body: PlanUpdate, request: Request,
                      _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().update(str(plan_id), body)))


@admin_plans_router.post("/{plan_id}/activate", response_model=ResponseModel)
async def activate_plan(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().activate(str(plan_id))))


@admin_plans_router.post("/{plan_id}/archive", response_model=ResponseModel)
async def archive_plan(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().archive(str(plan_id))))


@admin_plans_router.delete("/{plan_id}", response_model=ResponseModel)
async def delete_plan(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    PlanService().delete(str(plan_id))
    return ResponseModel.ok(data={"message": "Plan deleted"})


@admin_plans_router.post("/{plan_id}/partners", response_model=ResponseModel, status_code=201)
async def link_partner(plan_id: UUID, body: LinkPartnerBody, request: Request,
                       _=Depends(_require_superadmin)):
    PlanService().link_partner(str(plan_id), body.partner_id)
    return ResponseModel.ok(data={"message": "Partner linked to plan"})


@admin_plans_router.delete("/{plan_id}/partners/{partner_id}", response_model=ResponseModel)
async def unlink_partner(plan_id: UUID, partner_id: UUID, request: Request,
                         _=Depends(_require_superadmin)):
    PlanService().unlink_partner(str(plan_id), str(partner_id))
    return ResponseModel.ok(data={"message": "Partner unlinked from plan"})


@admin_plans_router.get("/{plan_id}/partners", response_model=ResponseModel)
async def list_linked_partners(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    partner_ids = PlanService().query.list_linked_partners(str(plan_id))
    return ResponseModel.ok(data={"partner_ids": partner_ids})
```

- [ ] **Step 2: Create `app/api/admin/partners.py`**

```python
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerCreate, PartnerUpdate
from ...services.partner_service import PartnerService
from ..users import _require_superadmin

admin_partners_router = APIRouter()


def _p(p) -> dict:
    return {"id": str(p.id), "user_id": str(p.user_id), "name": p.name,
            "partner_type": p.partner_type, "city": p.city, "status": p.status,
            "api_key": p.api_key, "api_rate_limit": p.api_rate_limit}


@admin_partners_router.get("", response_model=ResponseModel)
async def list_partners(request: Request, skip: int = 0, limit: int = 100,
                        _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=[_p(p) for p in PartnerService().list_all(skip=skip, limit=limit)])


@admin_partners_router.post("", response_model=ResponseModel, status_code=201)
async def create_partner(body: PartnerCreate, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_p(PartnerService().create(body)))


@admin_partners_router.get("/{partner_id}", response_model=ResponseModel)
async def get_partner(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_p(PartnerService().get_by_id(str(partner_id))))


@admin_partners_router.patch("/{partner_id}", response_model=ResponseModel)
async def update_partner(partner_id: UUID, body: PartnerUpdate, request: Request,
                         _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_p(PartnerService().update(str(partner_id), body)))


@admin_partners_router.delete("/{partner_id}", response_model=ResponseModel)
async def delete_partner(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    PartnerService().delete(str(partner_id))
    return ResponseModel.ok(data={"message": "Partner deactivated"})


@admin_partners_router.post("/{partner_id}/regenerate-key", response_model=ResponseModel)
async def regen_key(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    p = PartnerService().regenerate_api_key(str(partner_id))
    return ResponseModel.ok(data={"api_key": p.api_key})


@admin_partners_router.get("/{partner_id}/plans", response_model=ResponseModel)
async def partner_plans(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    from ...services.plan_service import PlanService
    from ..plans import _plan_to_dict
    plans = PlanService().list_for_partner(str(partner_id))
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in plans])
```

- [ ] **Step 3: Create `app/api/admin/members.py`**

```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from ...schemas.base import ResponseModel
from ...schemas.member import MemberCreate
from ...services.member_service import MemberService
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ...constants import UserType
from ..users import _require_superadmin

admin_members_router = APIRouter()


def _enrollment_dict(e) -> dict:
    return {"partner_id": str(e.partner_id), "plan_id": str(e.plan_id),
            "status": e.status, "end_date": str(e.end_date)}


@admin_members_router.get("", response_model=ResponseModel)
async def list_members(request: Request, skip: int = 0, limit: int = 100,
                       partner_id: str = None, _=Depends(_require_superadmin)):
    from ...db.session import session_scope
    from ...db.models.user import User
    mq = MemberQuery()
    with session_scope() as session:
        q = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False
        )
        users = q.offset(skip).limit(limit).all()
        for u in users:
            session.expunge(u)
    result = []
    for u in users:
        enrollments = mq.list_enrollments(str(u.id))
        if partner_id and not any(str(e.partner_id) == partner_id for e in enrollments):
            continue
        result.append({
            "id": str(u.id), "email": u.email, "name": u.name,
            "mobile_no": u.mobile_no, "is_active": u.is_active,
            "enrollments": [_enrollment_dict(e) for e in enrollments],
        })
    return ResponseModel.ok(data=result)


@admin_members_router.post("", response_model=ResponseModel, status_code=201)
async def create_member(body: MemberCreate, request: Request, _=Depends(_require_superadmin)):
    svc = MemberService()
    result = svc.create_member(body)
    user = result["user"]
    enrollment = result["enrollment"]
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "enrollment": _enrollment_dict(enrollment),
    })


@admin_members_router.get("/{member_id}", response_model=ResponseModel)
async def get_member(member_id: UUID, request: Request, _=Depends(_require_superadmin)):
    uq = UserQuery()
    mq = MemberQuery()
    user = uq.get_user_by_id(str(member_id))
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")
    enrollments = mq.list_enrollments(str(member_id))
    profile = mq.get_profile(str(member_id))
    family = mq.list_family(str(member_id))
    policies = PolicyQuery().list_by_user(str(member_id))
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "mobile_no": user.mobile_no, "is_active": user.is_active,
        "enrollments": [_enrollment_dict(e) for e in enrollments],
        "profile": {
            "gender": profile.gender if profile else None,
            "dob": str(profile.dob) if profile and profile.dob else None,
            "address_city": profile.address_city if profile else None,
        },
        "family_count": len(family),
        "policy_count": len(policies),
    })
```

- [ ] **Step 4: Create `app/api/admin/dashboard.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ..users import _require_superadmin

admin_dashboard_router = APIRouter()


@admin_dashboard_router.get("", response_model=ResponseModel)
async def get_dashboard(request: Request, _=Depends(_require_superadmin)):
    from ...db.session import session_scope
    from ...db.models.user import User
    from ...db.models.plan import MembershipPlan
    from ...db.models.partner import Partner
    from ...db.models.member import MemberEnrollment
    from ...constants import UserType
    with session_scope() as session:
        total_members = session.query(User).filter(
            User.user_type == UserType.CUSTOMER, User.is_deleted == False).count()
        active_plans = session.query(MembershipPlan).filter(
            MembershipPlan.status == "Active", MembershipPlan.is_deleted == False).count()
        total_partners = session.query(Partner).filter(Partner.is_deleted == False).count()
        active_enrollments = session.query(MemberEnrollment).filter(
            MemberEnrollment.status == "active").count()
    return ResponseModel.ok(data={
        "total_members": total_members, "active_plans": active_plans,
        "total_partners": total_partners, "active_enrollments": active_enrollments,
    })
```

- [ ] **Step 5: Update `app/api/admin/__init__.py`**

```python
from fastapi import APIRouter
from .plans import admin_plans_router
from .partners import admin_partners_router
from .members import admin_members_router
from .dashboard import admin_dashboard_router

admin_router = APIRouter()
admin_router.include_router(admin_plans_router, prefix="/plans", tags=["Admin - Plans"])
admin_router.include_router(admin_partners_router, prefix="/partners", tags=["Admin - Partners"])
admin_router.include_router(admin_members_router, prefix="/members", tags=["Admin - Members"])
admin_router.include_router(admin_dashboard_router, prefix="/dashboard", tags=["Admin - Dashboard"])
```

- [ ] **Step 6: Verify startup**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
MODE=DEV python -c "from app.application import create_application; create_application(); print('OK')"
```

- [ ] **Step 7: Commit**

```bash
git add app/api/admin/
git commit -m "feat: SuperAdmin routes — plans (with partner linking), partners, members, dashboard"
```

---

### Task 10: Partner portal routes

**Files:**
- Create: `app/api/partner/profile.py`
- Create: `app/api/partner/plans.py`
- Create: `app/api/partner/members.py`
- Create: `app/api/partner/dashboard.py`
- Modify: `app/api/partner/__init__.py`

- [ ] **Step 1: Create `app/api/partner/profile.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerUpdate
from ...services.partner_service import PartnerService
from ..deps import _require_partner

partner_profile_router = APIRouter()


def _p(p) -> dict:
    return {"id": str(p.id), "user_id": str(p.user_id), "name": p.name,
            "partner_type": p.partner_type, "city": p.city, "status": p.status,
            "api_rate_limit": p.api_rate_limit}


@partner_profile_router.get("", response_model=ResponseModel)
async def get_profile(request: Request, partner=Depends(_require_partner)):
    return ResponseModel.ok(data=_p(partner))


@partner_profile_router.patch("", response_model=ResponseModel)
async def update_profile(body: PartnerUpdate, request: Request, partner=Depends(_require_partner)):
    updated = PartnerService().update(str(partner.id), body)
    return ResponseModel.ok(data=_p(updated))
```

- [ ] **Step 2: Create `app/api/partner/plans.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...services.plan_service import PlanService
from ..deps import _require_partner
from ..plans import _plan_to_dict

partner_plans_router = APIRouter()


@partner_plans_router.get("", response_model=ResponseModel)
async def list_partner_plans(request: Request, partner=Depends(_require_partner)):
    plans = PlanService().list_for_partner(str(partner.id))
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in plans])
```

- [ ] **Step 3: Create `app/api/partner/members.py`**

```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...schemas.member import MemberCreate
from ...services.member_service import MemberService
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ..deps import _require_partner

partner_members_router = APIRouter()


class SwitchPlanBody(BaseModel):
    plan_id: str


@partner_members_router.get("", response_model=ResponseModel)
async def list_members(request: Request, skip: int = 0, limit: int = 100,
                       partner=Depends(_require_partner)):
    mq = MemberQuery()
    uq = UserQuery()
    enrollments = mq.list_by_partner(str(partner.id), skip=skip, limit=limit)
    result = []
    for e in enrollments:
        user = uq.get_user_by_id(str(e.user_id))
        if user:
            result.append({
                "id": str(user.id), "email": user.email, "name": user.name,
                "mobile_no": user.mobile_no,
                "enrollment": {"plan_id": str(e.plan_id), "status": e.status,
                               "end_date": str(e.end_date)},
            })
    return ResponseModel.ok(data=result)


@partner_members_router.post("", response_model=ResponseModel, status_code=201)
async def create_member(body: MemberCreate, request: Request, partner=Depends(_require_partner)):
    body.partner_id = str(partner.id)
    result = MemberService().create_member(body)
    user = result["user"]
    enrollment = result["enrollment"]
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "enrollment": {"plan_id": str(enrollment.plan_id), "status": enrollment.status,
                       "end_date": str(enrollment.end_date)},
    })


@partner_members_router.get("/{member_id}", response_model=ResponseModel)
async def get_member(member_id: UUID, request: Request, partner=Depends(_require_partner)):
    mq = MemberQuery()
    enrollment = mq.get_enrollment(str(member_id), str(partner.id))
    if not enrollment:
        raise HTTPException(status_code=404, detail="Member not found under this partner")
    uq = UserQuery()
    user = uq.get_user_by_id(str(member_id))
    family = mq.list_family(str(member_id))
    policies = PolicyQuery().list_by_user_partner(str(member_id), str(partner.id))
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "enrollment": {"plan_id": str(enrollment.plan_id), "status": enrollment.status,
                       "end_date": str(enrollment.end_date)},
        "family": [{"id": str(f.id), "name": f.name, "relation": f.relation} for f in family],
        "policies": [{"id": str(p.id), "type": p.policy_type, "status": p.status} for p in policies],
    })


@partner_members_router.patch("/{member_id}/plan", response_model=ResponseModel)
async def switch_member_plan(member_id: UUID, body: SwitchPlanBody, request: Request,
                             partner=Depends(_require_partner)):
    svc = MemberService()
    enrollment = svc.switch_plan(str(member_id), str(partner.id), body.plan_id)
    return ResponseModel.ok(data={"plan_id": str(enrollment.plan_id), "status": enrollment.status})
```

- [ ] **Step 4: Create `app/api/partner/dashboard.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...db.session import session_scope
from ...db.models.member import MemberEnrollment
from ..deps import _require_partner

partner_dashboard_router = APIRouter()


@partner_dashboard_router.get("", response_model=ResponseModel)
async def get_dashboard(request: Request, partner=Depends(_require_partner)):
    with session_scope() as session:
        total = session.query(MemberEnrollment).filter(
            MemberEnrollment.partner_id == partner.id).count()
        active = session.query(MemberEnrollment).filter(
            MemberEnrollment.partner_id == partner.id,
            MemberEnrollment.status == "active").count()
    return ResponseModel.ok(data={
        "partner_id": str(partner.id), "total_enrollments": total,
        "active_enrollments": active, "inactive_enrollments": total - active,
    })
```

- [ ] **Step 5: Update `app/api/partner/__init__.py`**

```python
from fastapi import APIRouter
from .profile import partner_profile_router
from .plans import partner_plans_router
from .members import partner_members_router
from .dashboard import partner_dashboard_router

partner_router = APIRouter()
partner_router.include_router(partner_profile_router, prefix="/profile", tags=["Partner - Profile"])
partner_router.include_router(partner_plans_router, prefix="/plans", tags=["Partner - Plans"])
partner_router.include_router(partner_members_router, prefix="/members", tags=["Partner - Members"])
partner_router.include_router(partner_dashboard_router, prefix="/dashboard", tags=["Partner - Dashboard"])
```

- [ ] **Step 6: Commit**

```bash
git add app/api/partner/
git commit -m "feat: Partner portal routes — profile, plans, members, dashboard"
```

---

### Task 11: Customer (me) routes — partners list, plan, profile, family, nominees, consent

**Files:**
- Create: `app/api/me/partners.py`
- Create: `app/api/me/plan.py`
- Create: `app/api/me/profile.py`
- Create: `app/api/me/family.py`
- Create: `app/api/me/nominees.py`
- Create: `app/api/me/consent.py`

- [ ] **Step 1: Create `app/api/me/partners.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...services.member_service import MemberService
from ...db.queries.partner_query import PartnerQuery
from ...services.plan_service import PlanService
from ..deps import _require_customer
from ..plans import _plan_to_dict

me_partners_router = APIRouter()


@me_partners_router.get("", response_model=ResponseModel)
async def list_my_partners(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    svc = MemberService()
    pq = PartnerQuery()
    ps = PlanService()
    enrollments = svc.list_enrollments(user_id)
    first_enrollment = enrollments[0] if enrollments else None
    result = []
    for idx, e in enumerate(enrollments):
        partner = pq.get_by_id(str(e.partner_id))
        plan = ps.get_by_id(str(e.plan_id))
        result.append({
            "partner_id": str(e.partner_id),
            "partner_name": partner.name if partner else None,
            "partner_type": partner.partner_type if partner else None,
            "enrollment_status": e.status,
            "end_date": str(e.end_date),
            "plan": _plan_to_dict(plan),
            "is_default": idx == 0,
        })
    return ResponseModel.ok(data=result)
```

- [ ] **Step 2: Create `app/api/me/plan.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import PlanSwitchRequest
from ...services.member_service import MemberService
from ...services.plan_service import PlanService
from ..deps import _require_customer_enrollment
from ..plans import _plan_to_dict

me_plan_router = APIRouter()


@me_plan_router.get("", response_model=ResponseModel)
async def get_my_plan(request: Request, enrollment=Depends(_require_customer_enrollment)):
    plan = PlanService().get_by_id(str(enrollment.plan_id))
    return ResponseModel.ok(data={
        "enrollment": {
            "partner_id": str(enrollment.partner_id),
            "status": enrollment.status,
            "start_date": str(enrollment.start_date),
            "end_date": str(enrollment.end_date),
        },
        "plan": _plan_to_dict(plan),
    })


@me_plan_router.put("", response_model=ResponseModel)
async def switch_plan(body: PlanSwitchRequest, request: Request,
                      enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    svc = MemberService()
    updated = svc.switch_plan(user_id, str(enrollment.partner_id), body.plan_id)
    return ResponseModel.ok(data={
        "partner_id": str(updated.partner_id),
        "plan_id": str(updated.plan_id),
        "status": updated.status,
    })
```

- [ ] **Step 3: Create `app/api/me/profile.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import ProfileUpdate
from ...services.member_service import MemberService
from ..deps import _require_customer

me_profile_router = APIRouter()


def _build_profile(user, profile) -> dict:
    return {
        "id": str(user.id), "email": user.email, "name": user.name,
        "mobile_no": user.mobile_no,
        "gender": profile.gender if profile else None,
        "dob": str(profile.dob) if profile and profile.dob else None,
        "address_line": profile.address_line if profile else None,
        "address_city": profile.address_city if profile else None,
        "address_state": profile.address_state if profile else None,
        "address_pin": profile.address_pin if profile else None,
        "preferred_language": profile.preferred_language if profile else "English",
        "channel_email": profile.channel_email if profile else True,
        "channel_whatsapp": profile.channel_whatsapp if profile else False,
        "channel_voice": profile.channel_voice if profile else False,
    }


@me_profile_router.get("", response_model=ResponseModel)
async def get_profile(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    result = MemberService().get_profile(user_id)
    return ResponseModel.ok(data=_build_profile(result["user"], result["profile"]))


@me_profile_router.patch("", response_model=ResponseModel)
async def update_profile(body: ProfileUpdate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    result = MemberService().update_profile(user_id, body)
    return ResponseModel.ok(data=_build_profile(result["user"], result["profile"]))
```

- [ ] **Step 4: Create `app/api/me/family.py`**

```python
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import FamilyMemberCreate, FamilyMemberUpdate
from ...services.member_service import MemberService
from ..deps import _require_customer

me_family_router = APIRouter()


def _f(f) -> dict:
    return {"id": str(f.id), "name": f.name, "relation": f.relation,
            "gender": f.gender, "dob": str(f.dob) if f.dob else None,
            "coverage_type": f.coverage_type}


@me_family_router.get("", response_model=ResponseModel)
async def list_family(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=[_f(m) for m in MemberService().list_family(user_id)])


@me_family_router.post("", response_model=ResponseModel, status_code=201)
async def add_family(body: FamilyMemberCreate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=_f(MemberService().add_family_member(user_id, body)))


@me_family_router.patch("/{member_id}", response_model=ResponseModel)
async def update_family(member_id: UUID, body: FamilyMemberUpdate, request: Request,
                        _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=_f(MemberService().update_family_member(user_id, str(member_id), body)))


@me_family_router.delete("/{member_id}", response_model=ResponseModel)
async def delete_family(member_id: UUID, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    MemberService().delete_family_member(user_id, str(member_id))
    return ResponseModel.ok(data={"message": "Family member removed"})
```

- [ ] **Step 5: Create `app/api/me/nominees.py`**

```python
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import NomineeCreate, NomineeUpdate
from ...services.member_service import MemberService
from ..deps import _require_customer

me_nominees_router = APIRouter()


def _n(n) -> dict:
    return {"id": str(n.id), "name": n.name, "relation": n.relation,
            "share_percent": n.share_percent}


@me_nominees_router.get("", response_model=ResponseModel)
async def list_nominees(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=[_n(n) for n in MemberService().list_nominees(user_id)])


@me_nominees_router.post("", response_model=ResponseModel, status_code=201)
async def add_nominee(body: NomineeCreate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=_n(MemberService().add_nominee(user_id, body)))


@me_nominees_router.patch("/{nominee_id}", response_model=ResponseModel)
async def update_nominee(nominee_id: UUID, body: NomineeUpdate, request: Request,
                         _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    return ResponseModel.ok(data=_n(MemberService().update_nominee(user_id, str(nominee_id), body)))


@me_nominees_router.delete("/{nominee_id}", response_model=ResponseModel)
async def delete_nominee(nominee_id: UUID, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    MemberService().delete_nominee(user_id, str(nominee_id))
    return ResponseModel.ok(data={"message": "Nominee removed"})
```

- [ ] **Step 6: Create `app/api/me/consent.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import ConsentCreate
from ...services.member_service import MemberService
from ..deps import _require_customer

me_consent_router = APIRouter()


@me_consent_router.get("", response_model=ResponseModel)
async def get_consent(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    c = MemberService().get_consent(user_id)
    return ResponseModel.ok(data={"id": str(c.id), "consented_at": c.consented_at.isoformat(),
                                   "version": c.version, "source": c.source})


@me_consent_router.post("", response_model=ResponseModel, status_code=201)
async def record_consent(body: ConsentCreate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    c = MemberService().record_consent(user_id, body)
    return ResponseModel.ok(data={"id": str(c.id), "consented_at": c.consented_at.isoformat(),
                                   "version": c.version, "source": c.source})
```

- [ ] **Step 7: Commit**

```bash
git add app/api/me/partners.py app/api/me/plan.py app/api/me/profile.py app/api/me/family.py app/api/me/nominees.py app/api/me/consent.py
git commit -m "feat: Customer me routes — partners list, plan, profile, family, nominees, consent"
```

---

### Task 12: Customer policies + dashboard + wire all me routers + smoke test

**Files:**
- Create: `app/api/me/policies.py`
- Create: `app/api/me/dashboard.py`
- Modify: `app/api/me/__init__.py`

- [ ] **Step 1: Create `app/api/me/policies.py`**

```python
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from ...schemas.base import ResponseModel
from ...schemas.policy import PolicyCreate
from ...services.policy_service import PolicyService
from ..deps import _require_customer_enrollment

me_policies_router = APIRouter()


def _pol(p) -> dict:
    return {"id": str(p.id), "policy_number": p.policy_number, "policy_type": p.policy_type,
            "insurer": p.insurer, "sum_insured": p.sum_insured,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "status": p.status, "ai_confidence": p.ai_confidence,
            "extracted_fields": p.extracted_fields}


@me_policies_router.get("", response_model=ResponseModel)
async def list_policies(request: Request, enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    policies = PolicyService().list_policies(user_id, str(enrollment.partner_id))
    return ResponseModel.ok(data=[_pol(p) for p in policies])


@me_policies_router.post("", response_model=ResponseModel, status_code=201)
async def upload_policy(
    request: Request,
    policy_type: str = Form(...),
    insurer: Optional[str] = Form(None),
    sum_insured: Optional[int] = Form(None),
    file: UploadFile = File(...),
    enrollment=Depends(_require_customer_enrollment),
):
    user_id = request.state.user_payload["sub"]
    data = PolicyCreate(policy_type=policy_type, insurer=insurer, sum_insured=sum_insured)
    policy = await PolicyService().upload_policy(user_id, str(enrollment.partner_id), data, file)
    return ResponseModel.ok(data=_pol(policy))


@me_policies_router.get("/{policy_id}", response_model=ResponseModel)
async def get_policy(policy_id: UUID, request: Request,
                     enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    policy = PolicyService().get_policy(user_id, str(policy_id))
    return ResponseModel.ok(data=_pol(policy))


@me_policies_router.delete("/{policy_id}", response_model=ResponseModel)
async def delete_policy(policy_id: UUID, request: Request,
                        enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    PolicyService().delete_policy(user_id, str(policy_id))
    return ResponseModel.ok(data={"message": "Policy removed"})
```

- [ ] **Step 2: Create `app/api/me/dashboard.py`**

```python
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...services.member_service import MemberService
from ...db.queries.policy_query import PolicyQuery
from ..deps import _require_customer

me_dashboard_router = APIRouter()


@me_dashboard_router.get("", response_model=ResponseModel)
async def get_dashboard(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    svc = MemberService()
    enrollments = svc.list_enrollments(user_id)
    family = svc.list_family(user_id)
    all_policies = PolicyQuery().list_by_user(user_id)
    by_status = {}
    for p in all_policies:
        by_status[p.status] = by_status.get(p.status, 0) + 1
    return ResponseModel.ok(data={
        "enrollment_count": len(enrollments),
        "active_enrollments": [
            {"partner_id": str(e.partner_id), "plan_id": str(e.plan_id),
             "status": e.status, "end_date": str(e.end_date)}
            for e in enrollments if e.status == "active"
        ],
        "family_count": len(family),
        "policy_count": len(all_policies),
        "policies_by_status": by_status,
    })
```

- [ ] **Step 3: Update `app/api/me/__init__.py`**

```python
from fastapi import APIRouter
from .partners import me_partners_router
from .plan import me_plan_router
from .profile import me_profile_router
from .family import me_family_router
from .nominees import me_nominees_router
from .consent import me_consent_router
from .policies import me_policies_router
from .dashboard import me_dashboard_router

me_router = APIRouter()
me_router.include_router(me_partners_router, prefix="/partners", tags=["Me - Partners"])
me_router.include_router(me_plan_router, prefix="/plan", tags=["Me - Plan"])
me_router.include_router(me_profile_router, prefix="/profile", tags=["Me - Profile"])
me_router.include_router(me_family_router, prefix="/family", tags=["Me - Family"])
me_router.include_router(me_nominees_router, prefix="/nominees", tags=["Me - Nominees"])
me_router.include_router(me_consent_router, prefix="/consent", tags=["Me - Consent"])
me_router.include_router(me_policies_router, prefix="/policies", tags=["Me - Policies"])
me_router.include_router(me_dashboard_router, prefix="/dashboard", tags=["Me - Dashboard"])
```

- [ ] **Step 4: Ensure python-multipart installed**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
pip show python-multipart || pip install "python-multipart>=0.0.9"
```

Check `pyproject.toml` dependencies list. If `python-multipart` is missing, add:
```toml
"python-multipart>=0.0.9",
```

- [ ] **Step 5: Full smoke test**

```bash
cd /home/konsultera/chinar/testpro/easyclaims_backend
MODE=DEV uvicorn main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/openapi.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
paths = sorted(d['paths'].keys())
print(f'{len(paths)} routes registered')
for p in paths:
    print(p)
"
kill %1
```
Expected: 35+ routes, all prefixes visible (/admin/, /partner/, /me/, /plans/).

- [ ] **Step 6: Run full test suite**

```bash
MODE=DEV pytest tests/ -q --tb=short
```
Expected: all existing tests pass.

- [ ] **Step 7: Commit**

```bash
git add app/api/me/ pyproject.toml
git commit -m "feat: Customer me routes — policies, dashboard + wire all me routers"
```

---

## Summary

| Task | Done |
|---|---|
| 1 — PARTNER enum | ✅ |
| 2 — CRM models | |
| 3 — Migration + seed | |
| 4 — Plan layer | |
| 5 — Partner layer | |
| 6 — Member layer (enrollment-based) | |
| 7 — Policy layer | |
| 8 — Deps + login default_partner_id + scaffolds | |
| 9 — SuperAdmin routes | |
| 10 — Partner routes | |
| 11 — Customer me routes (partners, plan, profile, family, nominees, consent) | |
| 12 — Customer me routes (policies, dashboard) + wire-up | |
