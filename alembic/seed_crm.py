import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
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
         cycle="Annual", plan_type="global", status="Active", color="var(--green-500)",
         popular=True,
         benefit_family=4, benefit_slots=6, benefit_claim="Priority",
         benefit_aiqa=True, benefit_aicalls=True, benefit_voice="English + Hindi",
         benefit_vault=True, benefit_concierge=True),
    dict(name="Total Care", tagline="Premium concierge membership",
         info_text="24x7 priority care with dedicated RM and concierge filing.", price=4999,
         cycle="Annual", plan_type="global", status="Active", color="var(--blue-900)",
         benefit_family=6, benefit_slots=12, benefit_claim="Standard",
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
