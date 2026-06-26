"""
Demo data import script.
- Deletes all CUSTOMER users and their related data
- Creates 11 realistic members from Augmented_Data PDFs
- Imports policies with mixed statuses (active/pending/rejected/need_review)
- NO emails or WhatsApp messages sent
"""

import uuid, shutil, os
from datetime import date, datetime, timezone, timedelta
from app.db.session import session_scope
from app.db.models.user import User
from app.db.models.policy import Policy
from app.db.models.member import MemberEnrollment, MemberProfile
from app.db.models.partner import Partner
from app.constants import UserType
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
PDF_BASE = "/home/konsultera/Personal/Easy_Claims/easyclaims/Og_data/Augmented_Data"

# ─── IDs from existing DB ─────────────────────────────────────────────────────
PARTNER = {
    "healthbridge":  "6cd47d22-9412-46e5-ad7a-3a274d141f29",
    "wellness":      "00dfeec1-f697-413a-93ed-f437a9cf9a53",
    "careplus":      "c93adfb1-c37a-4db3-8426-6e24c30101bf",
    "medisure":      "f25c2437-b295-4017-af89-83c477c10185",
    "apex":          "f867d0d4-21dc-4219-acfe-32d022addd05",
}
PLAN = {
    "secure":     "92150516-da43-41b1-8921-3a35b952060e",
    "total_care": "5f7f9533-8ee3-4b58-a41e-b1279e48952a",
    "essential":  "c1e14f37-6d41-4fac-8c62-ea3b0e607ff8",
}
PTYPE = {
    "health": "6e0c4c8f-a7c7-44a1-b9f2-d9f8fa2ad8ae",
    "motor":  "ef31fd4a-1e92-425b-b94b-636dff3e8f08",
    "travel": "e7a749f9-5cbc-45fe-81de-ce4910a5ed84",
    "home":   "762df8dc-2dde-4a91-aae9-8bb5aff5f1e3",
}

def d(y, m, day): return date(y, m, day)

# ─── Member + policy definitions ─────────────────────────────────────────────
MEMBERS = [
    {
        "name": "Paresh Jayantilal Lakhani",
        "email": "paresh.lakhani@demo.easyclaims.in",
        "mobile": "9876501001",
        "partner": "healthbridge",
        "plan": "total_care",
        "enroll_start": d(2025, 1, 10),
        "enroll_end":   d(2027, 1, 9),
        "policies": [
            {
                "file": "Health Insurance/PARESH JAYANTILAL LAKHANI BASE POLICY COPY 26-27.pdf",
                "type": "health",
                "status": "active",
                "insurer": "Star Health Insurance",
                "sum_insured": 500000,
                "start_date": d(2026, 4, 1),
                "end_date":   d(2027, 3, 31),
                "policy_number": "SHI/H/2026/001",
            }
        ],
    },
    {
        "name": "Tapan Ranjit Sampat",
        "email": "tapan.sampat@demo.easyclaims.in",
        "mobile": "9876501002",
        "partner": "healthbridge",
        "plan": "secure",
        "enroll_start": d(2024, 8, 15),
        "enroll_end":   d(2026, 8, 14),
        "policies": [
            {
                "file": "Health Insurance/Tapan Ranjit Sampat POLICY COPY 26-29.pdf",
                "type": "health",
                "status": "active",
                "insurer": "HDFC Ergo Health",
                "sum_insured": 1000000,
                "start_date": d(2026, 3, 1),
                "end_date":   d(2029, 2, 28),
                "policy_number": "HDFC/H/2026/042",
            }
        ],
    },
    {
        "name": "Umesh Merchant",
        "email": "umesh.merchant@demo.easyclaims.in",
        "mobile": "9876501003",
        "partner": "medisure",
        "plan": "essential",
        "enroll_start": d(2025, 6, 1),
        "enroll_end":   d(2026, 5, 31),
        "policies": [
            {
                "file": "Health Insurance/UMESH MERCHANT POLICY COPY 26-31.pdf",
                "type": "health",
                "status": "pending",
                "insurer": "Niva Bupa Health Insurance",
                "sum_insured": 300000,
                "start_date": d(2026, 5, 1),
                "end_date":   d(2031, 4, 30),
                "policy_number": "NIVA/H/2026/088",
            }
        ],
    },
    {
        "name": "Vinay Shantikumar Ashar",
        "email": "vinay.ashar@demo.easyclaims.in",
        "mobile": "9876501004",
        "partner": "careplus",
        "plan": "total_care",
        "enroll_start": d(2025, 9, 20),
        "enroll_end":   d(2026, 9, 19),
        "policies": [
            {
                "file": "Health Insurance/Vinay Shantikumar Ashar BASE POLICY COPY 26-27.pdf",
                "type": "health",
                "status": "need_review",
                "insurer": "Bajaj Allianz General Insurance",
                "sum_insured": 750000,
                "start_date": d(2026, 4, 1),
                "end_date":   d(2027, 3, 31),
                "policy_number": None,
            }
        ],
    },
    {
        "name": "Aakash Surendra Khandelwal",
        "email": "aakash.khandelwal@demo.easyclaims.in",
        "mobile": "9876501005",
        "partner": "apex",
        "plan": "secure",
        "enroll_start": d(2025, 3, 5),
        "enroll_end":   d(2027, 3, 4),
        "policies": [
            {
                "file": "Motor Insurance/AAKASH SURENDRA KHANDELWAL policy done (2).pdf",
                "type": "motor",
                "status": "active",
                "insurer": "ICICI Lombard",
                "sum_insured": 800000,
                "start_date": d(2025, 7, 1),
                "end_date":   d(2026, 6, 30),
                "policy_number": "ICL/M/2025/305",
            }
        ],
    },
    {
        "name": "Hemang Mehta",
        "email": "hemang.mehta@demo.easyclaims.in",
        "mobile": "9876501006",
        "partner": "wellness",
        "plan": "total_care",
        "enroll_start": d(2024, 11, 1),
        "enroll_end":   d(2026, 10, 31),
        "policies": [
            {
                "file": "Travel Insurance/HEMANG MEHTA.pdf",
                "type": "travel",
                "status": "active",
                "insurer": "Tata AIG",
                "sum_insured": 2000000,
                "start_date": d(2026, 1, 10),
                "end_date":   d(2026, 12, 31),
                "policy_number": "TAIG/T/2026/017",
            }
        ],
    },
    {
        "name": "Karishma Haldankar",
        "email": "karishma.haldankar@demo.easyclaims.in",
        "mobile": "9876501007",
        "partner": "medisure",
        "plan": "essential",
        "enroll_start": d(2025, 7, 15),
        "enroll_end":   d(2026, 7, 14),
        "policies": [
            {
                "file": "Travel Insurance/Karishma Haldankar.pdf",
                "type": "travel",
                "status": "pending",
                "insurer": "New India Assurance",
                "sum_insured": 1500000,
                "start_date": d(2026, 6, 1),
                "end_date":   d(2026, 12, 31),
                "policy_number": None,
            }
        ],
    },
    {
        "name": "Marzban Maneck Painter",
        "email": "marzban.painter@demo.easyclaims.in",
        "mobile": "9876501008",
        "partner": "careplus",
        "plan": "secure",
        "enroll_start": d(2024, 5, 10),
        "enroll_end":   d(2026, 5, 9),
        "policies": [
            {
                "file": "Travel Insurance/MARZBAN MANECK PAINTER.pdf",
                "type": "travel",
                "status": "rejected",
                "insurer": "Reliance General Insurance",
                "sum_insured": 1000000,
                "start_date": d(2025, 12, 1),
                "end_date":   d(2026, 11, 30),
                "policy_number": None,
            }
        ],
    },
    {
        "name": "Nita Gokani",
        "email": "nita.gokani@demo.easyclaims.in",
        "mobile": "9876501009",
        "partner": "healthbridge",
        "plan": "essential",
        "enroll_start": d(2025, 2, 20),
        "enroll_end":   d(2027, 2, 19),
        "policies": [
            {
                "file": "Travel Insurance/NITA GOKANI.pdf",
                "type": "travel",
                "status": "active",
                "insurer": "HDFC Ergo",
                "sum_insured": 2500000,
                "start_date": d(2026, 3, 15),
                "end_date":   d(2026, 9, 14),
                "policy_number": "HDFC/T/2026/091",
            }
        ],
    },
    {
        "name": "Pravin Kumar Gokani",
        "email": "pravin.gokani@demo.easyclaims.in",
        "mobile": "9876501010",
        "partner": "apex",
        "plan": "total_care",
        "enroll_start": d(2025, 4, 1),
        "enroll_end":   d(2027, 3, 31),
        "policies": [
            {
                "file": "Travel Insurance/Pravin Kumar Gokani.pdf",
                "type": "travel",
                "status": "pending",
                "insurer": "SBI General Insurance",
                "sum_insured": 3000000,
                "start_date": d(2026, 5, 20),
                "end_date":   d(2026, 11, 19),
                "policy_number": None,
            },
            {
                "file": "Home Insurance/policy_document_131200-11-2026-1097.pdf",
                "type": "home",
                "status": "active",
                "insurer": "LIC Housing",
                "sum_insured": 5000000,
                "start_date": d(2026, 1, 1),
                "end_date":   d(2027, 12, 31),
                "policy_number": "LIC/HOME/2026/1097",
            },
        ],
    },
    {
        "name": "Vijay Natwarlal Mundra",
        "email": "vijay.mundra@demo.easyclaims.in",
        "mobile": "9876501011",
        "partner": "wellness",
        "plan": "secure",
        "enroll_start": d(2024, 12, 1),
        "enroll_end":   d(2026, 11, 30),
        "policies": [
            {
                "file": "Travel Insurance/VIJAY NATWARLAL MUNDRA.pdf",
                "type": "travel",
                "status": "rejected",
                "insurer": "United India Insurance",
                "sum_insured": 1000000,
                "start_date": d(2025, 11, 1),
                "end_date":   d(2026, 10, 31),
                "policy_number": None,
            }
        ],
    },
]


def copy_policy_file(pdf_rel_path, storage_key):
    src = os.path.join(PDF_BASE, pdf_rel_path)
    dst = os.path.join(UPLOADS_DIR, storage_key)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        return True
    else:
        print(f"  WARNING: source file not found: {src}")
        return False


def run():
    with session_scope() as s:
        # ── 1. Delete all existing CUSTOMER data ──────────────────────────────
        print("Deleting existing customer data...")
        customer_ids = s.execute(
            text("SELECT id FROM users WHERE user_type='CUSTOMER'")
        ).fetchall()
        cids = [str(r[0]) for r in customer_ids]
        print(f"  Found {len(cids)} customer users to delete")

        if cids:
            ids_sql = ", ".join([f"'{c}'" for c in cids])
            # Delete in FK-safe order
            s.execute(text(f"DELETE FROM policy_family_members WHERE policy_id IN (SELECT id FROM policies WHERE user_id IN ({ids_sql}))"))
            s.execute(text(f"DELETE FROM enrollment_history WHERE enrollment_id IN (SELECT id FROM member_enrollments WHERE user_id IN ({ids_sql}))"))
            s.execute(text(f"DELETE FROM nominees WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM family_members WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM dpdp_consents WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM member_profiles WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM notifications WHERE recipient_user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM user_activity WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM otp_log WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM auth_sessions WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM user_roles WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM policies WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM member_enrollments WHERE user_id IN ({ids_sql})"))
            s.execute(text(f"DELETE FROM users WHERE user_type='CUSTOMER'"))
            s.commit()
            print("  Deleted all existing customer data.")

        # ── 2. Import new members ─────────────────────────────────────────────
        print("\nImporting new members...")
        for m in MEMBERS:
            uid = uuid.uuid4()
            partner_id = PARTNER[m["partner"]]
            plan_id = PLAN[m["plan"]]

            # Create user
            user = User(
                id=uid,
                email=m["email"],
                name=m["name"],
                mobile_no=m["mobile"],
                user_type=UserType.CUSTOMER,
                is_active=True,
                is_deleted=False,
            )
            s.add(user)
            s.flush()

            # Create enrollment
            enroll_id = uuid.uuid4()
            enrollment = MemberEnrollment(
                id=enroll_id,
                user_id=uid,
                partner_id=partner_id,
                plan_id=plan_id,
                status="Active",
                start_date=m["enroll_start"],
                end_date=m["enroll_end"],
            )
            s.add(enrollment)
            s.flush()

            # Create profile — all notifications OFF (no msgs during import)
            profile = MemberProfile(
                user_id=uid,
                preferred_language="English",
                channel_email=False,
                channel_whatsapp=False,
                channel_voice=False,
            )
            s.add(profile)

            # Create policies
            for pol in m["policies"]:
                policy_id = uuid.uuid4()
                fname = os.path.basename(pol["file"])
                storage_key = f"{partner_id}/{uid}/{enroll_id}/{policy_id}.pdf"

                copied = copy_policy_file(pol["file"], storage_key)

                policy = Policy(
                    id=policy_id,
                    user_id=uid,
                    partner_id=partner_id,
                    policy_type_id=PTYPE[pol["type"]],
                    policy_number=pol.get("policy_number"),
                    insurer=pol["insurer"],
                    sum_insured=pol["sum_insured"],
                    start_date=pol["start_date"],
                    end_date=pol["end_date"],
                    status=pol["status"],
                    ai_confidence=None,
                    storage_key=storage_key,
                    file_name=fname,
                    is_deleted=False,
                )
                s.add(policy)

            s.flush()
            print(f"  ✓ {m['name']} ({len(m['policies'])} polic{'y' if len(m['policies'])==1 else 'ies'})")

        s.commit()
        print("\nDone! Summary:")
        total_members = s.execute(text("SELECT COUNT(*) FROM users WHERE user_type='CUSTOMER'")).scalar()
        total_policies = s.execute(text("SELECT COUNT(*) FROM policies WHERE is_deleted=false")).scalar()
        status_rows = s.execute(text("SELECT status, COUNT(*) FROM policies WHERE is_deleted=false GROUP BY status")).fetchall()
        print(f"  Members: {total_members}")
        print(f"  Policies: {total_policies}")
        for row in status_rows:
            print(f"    {row[0]}: {row[1]}")


if __name__ == "__main__":
    run()
