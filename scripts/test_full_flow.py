"""
Full flow test: SuperAdmin → Plans → Partner → Member → Login → Profile → Family →
                Policy upload (with family member link) → Notifications → Partner checks
"""
import sys
import time
import uuid
import json
import bcrypt
import requests
import psycopg
from datetime import datetime, timezone, timedelta

BASE = "http://localhost:8000/api/v1"

DB_DSN = "host=0.0.0.0 port=5432 dbname=easyclaims user=mystique_agents password=mystique_agents"

OK = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
HEAD = "\033[1;94m"
RESET = "\033[0m"

errors = []


def section(title):
    print(f"\n{HEAD}{'─'*60}{RESET}")
    print(f"{HEAD}  {title}{RESET}")
    print(f"{HEAD}{'─'*60}{RESET}")


def check(label, cond, extra=""):
    if cond:
        print(f"  {OK} {label}" + (f"  ({extra})" if extra else ""))
    else:
        print(f"  {FAIL} {label}" + (f"  ({extra})" if extra else ""))
        errors.append(label)


def api(method, path, token=None, json_body=None, files=None, data=None,
        headers_extra=None, expected=None):
    url = f"{BASE}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if headers_extra:
        headers.update(headers_extra)
    resp = requests.request(method, url, json=json_body, files=files, data=data, headers=headers)
    if expected and resp.status_code not in expected:
        print(f"  {FAIL} {method} {path} → {resp.status_code} (expected {expected})")
        print(f"       {resp.text[:300]}")
        errors.append(f"{method} {path} status {resp.status_code}")
    return resp


def insert_and_get_otp(email: str) -> str:
    """Insert a known OTP directly into DB (bypasses SMTP). Returns raw OTP."""
    raw = "999888"
    hashed = bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"User {email} not found")
            user_id = row[0]
            cur.execute(
                "UPDATE otp_log SET is_used = TRUE WHERE email = %s AND is_used = FALSE",
                (email,)
            )
            cur.execute(
                """INSERT INTO otp_log (id, user_id, email, otp_code, expires_at, is_used, attempts)
                   VALUES (%s, %s, %s, %s, %s, FALSE, 0)""",
                (str(uuid.uuid4()), str(user_id), email, hashed, expires)
            )
        conn.commit()
    return raw


def login(email: str) -> str:
    otp = insert_and_get_otp(email)
    resp = api("POST", "/auth/verify-otp",
               json_body={"email": email, "otp": otp}, expected=[200])
    data = resp.json().get("data", {})
    token = data.get("access_token", "")
    check(f"Login {email}", bool(token), f"user_type={data.get('user_type')}")
    return token, data


def ensure_superadmin(email: str = "admin@easyclaims.in"):
    """Ensure superadmin exists in DB."""
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                uid = str(uuid.uuid4())
                cur.execute(
                    """INSERT INTO users (id, email, name, user_type, is_active, is_deleted, created_at, updated_at)
                       VALUES (%s, %s, %s, 'SUPERADMIN', TRUE, FALSE, now(), now())""",
                    (uid, email, "Super Admin")
                )
                conn.commit()
                print(f"  {OK} Created superadmin {email}")
            else:
                print(f"  {OK} Superadmin exists: {email}")


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

RUN_ID = str(uuid.uuid4())[:8]

ADMIN_EMAIL = "admin@easyclaims.in"
PARTNER_EMAIL = f"partner_{RUN_ID}@test.com"
MEMBER_EMAIL = f"member_{RUN_ID}@test.com"

section("0. Ensure SuperAdmin exists")
ensure_superadmin(ADMIN_EMAIL)

section("1. SuperAdmin login")
admin_token, admin_data = login(ADMIN_EMAIL)
check("Admin token received", bool(admin_token))
check("Admin user_type = SUPERADMIN", admin_data.get("user_type") == "SUPERADMIN")

# ── Policy Types ──────────────────────────────────────────────────────────────
section("2. Policy Types (public + admin)")
r = api("GET", "/policy-types", expected=[200])
pt_list = r.json().get("data", [])
check("Public policy types list", len(pt_list) >= 8, f"{len(pt_list)} types")
health_pt = next((pt for pt in pt_list if pt["code"] == "health"), None)
check("Health policy type exists", health_pt is not None)
HEALTH_PT_ID = health_pt["id"] if health_pt else None

# Admin: list policy types
r = api("GET", "/admin/policy-types", token=admin_token, expected=[200])
admin_pt = r.json().get("data", [])
check("Admin policy types list", len(admin_pt) >= 8, f"{len(admin_pt)} types")

# Admin: create new policy type
_pt_suffix = str(uuid.uuid4())[:8]
r = api("POST", "/admin/policy-types", token=admin_token,
        json_body={"name": f"Test Cyber {_pt_suffix}", "code": f"test_cyber_{_pt_suffix}",
                   "description": "Cyber insurance for testing"},
        expected=[200, 201])
new_pt = r.json().get("data", {})
check("Admin create policy type", bool(new_pt.get("id")), new_pt.get("name"))
NEW_PT_ID = new_pt.get("id")

# ── Plans ─────────────────────────────────────────────────────────────────────
section("3. Admin: Create Plans")
r = api("POST", "/admin/plans", token=admin_token, json_body={
    "name": f"Test Secure Plan {RUN_ID}",
    "price": 2999,
    "plan_type": "global",
    "benefits": {
        "health": True, "life": True, "dental": False, "vision": False,
        "mental_health": True, "maternity": False, "family_size": 6,
        "claim_slots": 15, "claim_type": "Standard",
        "voice_consultation": True, "voice_language": "English",
        "wellness": True, "pharmacy": False, "ambulance": True,
    }
}, expected=[200, 201])
plan_data = r.json().get("data", {})
check("Create global plan", bool(plan_data.get("id")), plan_data.get("name"))
PLAN_ID = plan_data.get("id")

# Activate plan
r = api("POST", f"/admin/plans/{PLAN_ID}/activate", token=admin_token, expected=[200])
check("Activate plan", r.json().get("data", {}).get("status") == "Active")

# List plans
r = api("GET", "/admin/plans", token=admin_token, expected=[200])
plans = r.json().get("data", [])
check("Admin list plans", len(plans) >= 1, f"{len(plans)} plans")

# ── Partner ───────────────────────────────────────────────────────────────────
section("4. Admin: Create Partner")
r = api("POST", "/admin/partners", token=admin_token, json_body={
    "name": f"Test Brokers Ltd {RUN_ID}",
    "email": PARTNER_EMAIL,
    "partner_type": "Broker",
    "city": "Mumbai",
    "api_rate_limit": 600,
}, expected=[200, 201])
partner_data = r.json().get("data", {})
check("Create partner", bool(partner_data.get("id")), partner_data.get("name"))
PARTNER_ID = partner_data.get("id")
check("Partner has api_key", bool(partner_data.get("api_key")))

# Admin list partners
r = api("POST", "/admin/partners/list", token=admin_token, json_body={
    "global_filter": "Test Brokers", "sort_field": "created_at", "sort_order": -1,
    "filters": [], "limit": 10, "skip": 0,
}, expected=[200])
partner_list = r.json().get("data", {}).get("data", [])
check("Admin list partners", len(partner_list) >= 1, f"{len(partner_list)} found")

# Admin: get partner detail
r = api("GET", f"/admin/partners/{PARTNER_ID}", token=admin_token, expected=[200])
check("Admin get partner detail", r.json().get("data", {}).get("id") == PARTNER_ID)

# Admin: partner plans
r = api("GET", f"/admin/partners/{PARTNER_ID}/plans", token=admin_token, expected=[200])
check("Admin partner plans", len(r.json().get("data", [])) >= 1)

# ── Partner login ─────────────────────────────────────────────────────────────
section("5. Partner Login")
partner_token, partner_auth = login(PARTNER_EMAIL)
check("Partner token received", bool(partner_token))
check("Partner user_type = PARTNER", partner_auth.get("user_type") == "PARTNER")

# Partner profile
r = api("GET", "/partner/profile", token=partner_token, expected=[200])
partner_profile = r.json().get("data", {})
check("Partner get profile", "Test Brokers Ltd" in partner_profile.get("name", ""))

# Partner plans
r = api("GET", "/partner/plans", token=partner_token, expected=[200])
partner_plans = r.json().get("data", [])
check("Partner see plans", len(partner_plans) >= 1, f"{len(partner_plans)} plans")
partner_plan_id = partner_plans[0]["id"] if partner_plans else PLAN_ID

# Partner dashboard
r = api("GET", "/partner/dashboard", token=partner_token, expected=[200])
check("Partner dashboard", "total_enrollments" in r.json().get("data", {}))

# ── Member creation ───────────────────────────────────────────────────────────
section("6. Partner: Create Member (welcome email triggered)")
r = api("POST", "/partner/members", token=partner_token, json_body={
    "email": MEMBER_EMAIL,
    "name": "Rahul Test",
    "mobile_no": "+91-9876543210",
    "plan_id": partner_plan_id,
}, expected=[200, 201])
member_data = r.json().get("data", {})
check("Create member", bool(member_data.get("id")), member_data.get("email"))
MEMBER_ID = member_data.get("id")
check("Member enrollment created", member_data.get("enrollment", {}).get("status") == "active")
check("Member plan assigned", bool(member_data.get("enrollment", {}).get("plan_id")))

# Partner: member list — check has_logged_in = False (new member never logged in)
r = api("POST", "/partner/members/list", token=partner_token, json_body={
    "global_filter": "Rahul Test", "sort_field": "created_at", "sort_order": -1,
    "filters": [], "limit": 10, "skip": 0,
}, expected=[200])
member_list = r.json().get("data", {}).get("data", [])
check("Partner member list", len(member_list) >= 1)
new_member = next((m for m in member_list if m.get("email") == MEMBER_EMAIL), None)
check("Member in partner list", new_member is not None)
if new_member:
    check("Member has_logged_in = False (never logged in)", new_member.get("has_logged_in") == False)

# Partner: member detail (before login)
r = api("GET", f"/partner/members/{MEMBER_ID}", token=partner_token, expected=[200])
md = r.json().get("data", {})
check("Partner member detail", md.get("email") == MEMBER_EMAIL)
check("Member login_count = 0 (before login)", md.get("login_count") == 0)

# ── Member login ──────────────────────────────────────────────────────────────
section("7. Member Login (OTP) + Activity Tracking")
member_token, member_auth = login(MEMBER_EMAIL)
check("Member token received", bool(member_token))
check("Member user_type = CUSTOMER", member_auth.get("user_type") == "CUSTOMER")
check("default_partner_id returned", bool(member_auth.get("default_partner_id")))
DEFAULT_PARTNER_ID = member_auth.get("default_partner_id")

# After login, partner sees has_logged_in = True
r = api("GET", f"/partner/members/{MEMBER_ID}", token=partner_token, expected=[200])
md = r.json().get("data", {})
check("Member has_logged_in = True (after login)", md.get("has_logged_in") == True)
check("login_count >= 1", md.get("login_count", 0) >= 1)
check("first_login_at set", bool(md.get("first_login_at")))

# Member dashboard
r = api("GET", "/me/dashboard", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID}, expected=[200])
dash = r.json().get("data", {})
check("Member dashboard", "enrollment_count" in dash)
check("Member has active enrollment", dash.get("active_enrollments", []).__len__() >= 1)

# ── Member profile ────────────────────────────────────────────────────────────
section("8. Member: Update Profile")
r = api("PATCH", "/me/profile", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
        json_body={
            "name": "Rahul Test Updated",
            "gender": "Male",
            "dob": "1990-05-15",
            "address_line": "12 MG Road",
            "address_city": "Mumbai",
            "address_state": "Maharashtra",
            "address_pin": "400001",
            "channel_email": True,
            "channel_whatsapp": True,
        }, expected=[200])
profile = r.json().get("data", {})
check("Update profile", profile.get("user", {}).get("name") == "Rahul Test Updated"
      or profile.get("name") == "Rahul Test Updated")
check("Profile gender set", profile.get("profile", {}).get("gender") == "Male"
      or profile.get("gender") == "Male")

# Get profile
r = api("GET", "/me/profile", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID}, expected=[200])
check("Get profile", bool(r.json().get("data")))

# ── Family members ────────────────────────────────────────────────────────────
section("9. Member: Add Family Members")
family_ids = []
for fm_data in [
    {"name": "Priya Test", "relation": "Spouse", "gender": "Female", "dob": "1993-06-20"},
    {"name": "Arjun Test", "relation": "Son", "gender": "Male", "dob": "2018-03-10"},
]:
    r = api("POST", "/me/family", token=member_token,
            headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
            json_body=fm_data, expected=[200, 201])
    fm = r.json().get("data", {})
    check(f"Add family member: {fm_data['name']}", bool(fm.get("id")))
    if fm.get("id"):
        family_ids.append(fm["id"])

# List family
r = api("GET", "/me/family", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID}, expected=[200])
fam_list = r.json().get("data", [])
check("List family members", len(fam_list) >= 2, f"{len(fam_list)} members")

# ── Nominees ──────────────────────────────────────────────────────────────────
section("10. Member: Add Nominees")
r = api("POST", "/me/nominees", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
        json_body={"name": "Priya Test", "relation": "Spouse",
                   "dob": "1993-06-20", "share_percent": 60},
        expected=[200, 201])
check("Add nominee 1 (60%)", bool(r.json().get("data", {}).get("id")))

r = api("POST", "/me/nominees", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
        json_body={"name": "Arjun Test", "relation": "Son",
                   "dob": "2018-03-10", "share_percent": 40},
        expected=[200, 201])
check("Add nominee 2 (40%)", bool(r.json().get("data", {}).get("id")))

r = api("GET", "/me/nominees", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID}, expected=[200])
nominees = r.json().get("data", [])
check("Nominees total share = 100%", sum(n["share_percent"] for n in nominees) == 100)

# ── Policy Upload ─────────────────────────────────────────────────────────────
section("11. Member: Upload Policy (with family member links)")
# Create minimal PDF bytes
pdf_bytes = (
    b"%PDF-1.4\n1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
    b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n"
    b"3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>>\nendobj\n"
    b"xref\n0 4\n0000000000 65535 f\n"
    b"0000000015 00000 n\n0000000068 00000 n\n0000000125 00000 n\n"
    b"trailer\n<</Size 4 /Root 1 0 R>>\nstartxref\n195\n%%EOF"
)

# Upload with family members linked (both family members)
fm_ids_str = ",".join(family_ids) if family_ids else ""
r = api("POST", "/me/policies", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
        data={
            "policy_type_id": HEALTH_PT_ID,
            "insurer": "Star Health Insurance",
            "sum_insured": "1000000",
            "family_member_ids": fm_ids_str,
        },
        files={"file": ("health_policy.pdf", pdf_bytes, "application/pdf")},
        expected=[200, 201])
policy_resp = r.json().get("data", {})
check("Upload policy", bool(policy_resp.get("id")), policy_resp.get("policy_number"))
POLICY_ID = policy_resp.get("id")
check("Policy type = Health", policy_resp.get("policy_type") == "Health")
check("Policy status = pending", policy_resp.get("status") == "pending")
linked_fms = policy_resp.get("linked_family_members", [])
check("Policy linked to family members", len(linked_fms) >= 2, f"{len(linked_fms)} linked")

# Get policy detail — includes linked family
r = api("GET", f"/me/policies/{POLICY_ID}", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID}, expected=[200])
policy_detail = r.json().get("data", {})
check("Get policy detail", policy_detail.get("id") == POLICY_ID)
check("Policy detail has linked_family_members",
      len(policy_detail.get("linked_family_members", [])) >= 2)

# List policies — family members included per policy
r = api("POST", "/me/policies/list", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
        json_body={"global_filter": "", "sort_field": "created_at",
                   "sort_order": -1, "filters": [], "limit": 10, "skip": 0},
        expected=[200])
policy_list = r.json().get("data", {}).get("data", [])
check("Member list policies", len(policy_list) >= 1)
if policy_list:
    check("Policy in list has linked_family_members",
          "linked_family_members" in policy_list[0])

# PATCH policy — update family member links (keep only first one)
if len(family_ids) >= 2:
    r = api("PATCH", f"/me/policies/{POLICY_ID}", token=member_token,
            headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
            json_body={"family_member_ids": [family_ids[0]]},
            expected=[200])
    updated_policy = r.json().get("data", {})
    check("PATCH policy: reduce to 1 family member",
          len(updated_policy.get("linked_family_members", [])) == 1)

    # Test duplicate prevention — patch back with same id twice
    r = api("PATCH", f"/me/policies/{POLICY_ID}", token=member_token,
            headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
            json_body={"family_member_ids": [family_ids[0], family_ids[0]]},
            expected=[200])
    no_dup = r.json().get("data", {})
    check("No duplicate links (same fm_id twice = still 1)",
          len(no_dup.get("linked_family_members", [])) == 1)

# ── Upload second policy (Motor) ──────────────────────────────────────────────
motor_pt = next((pt for pt in pt_list if pt["code"] == "motor"), None)
if motor_pt:
    r = api("POST", "/me/policies", token=member_token,
            headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
            data={
                "policy_type_id": motor_pt["id"],
                "insurer": "HDFC ERGO",
                "sum_insured": "500000",
            },
            files={"file": ("motor_policy.pdf", pdf_bytes, "application/pdf")},
            expected=[200, 201])
    check("Upload 2nd policy (Motor)", bool(r.json().get("data", {}).get("id")))
    MOTOR_POLICY_ID = r.json().get("data", {}).get("id")

# ── DPDP Consent ──────────────────────────────────────────────────────────────
section("12. Member: Record DPDP Consent")
r = api("POST", "/me/consent", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID},
        json_body={"version": "1.0", "consented_at": "2026-06-16T10:00:00Z"},
        expected=[200, 201])
check("Record consent", bool(r.json().get("data", {}).get("id")))

# ── Partner: Policy view (user-wise) ─────────────────────────────────────────
section("13. Partner: View Policies (user-wise grouped)")
r = api("POST", "/partner/policies/list", token=partner_token, json_body={
    "global_filter": "", "sort_field": "created_at", "sort_order": -1,
    "filters": [], "limit": 10, "skip": 0,
}, expected=[200])
pp = r.json().get("data", {})
check("Partner policies list", pp.get("total_policies", 0) >= 2)
check("User-wise grouping", len(pp.get("data", [])) >= 1)
if pp.get("data"):
    member_row = pp["data"][0]
    check("Policy row has member_id", bool(member_row.get("member_id")))
    check("Policy row has policies list", len(member_row.get("policies", [])) >= 1)

# Partner: get single policy
r = api("GET", f"/partner/policies/{POLICY_ID}", token=partner_token, expected=[200])
pp_detail = r.json().get("data", {})
check("Partner get policy detail", pp_detail.get("id") == POLICY_ID)
check("Partner policy has storage_key", bool(pp_detail.get("storage_key")))

# ── Notifications ─────────────────────────────────────────────────────────────
section("14. Partner: UI Notifications (policy upload trigger)")
r = api("GET", "/partner/notifications", token=partner_token, expected=[200])
notifs = r.json().get("data", {})
check("Partner has notifications", notifs.get("total", 0) >= 1)
check("Partner has unread notifications", notifs.get("unread_count", 0) >= 1)
notif_list = notifs.get("data", [])
if notif_list:
    notif_id = notif_list[0]["id"]
    check("Notification type = policy_uploaded", notif_list[0].get("type") == "policy_uploaded")
    check("Notification is_read = False", notif_list[0].get("is_read") == False)

    # Mark single notification as read
    r = api("PATCH", f"/partner/notifications/{notif_id}/read", token=partner_token, expected=[200])
    check("Mark notification as read", r.json().get("data", {}).get("message") is not None)

    # Mark all as read
    r = api("PATCH", "/partner/notifications/read-all", token=partner_token, expected=[200])
    check("Mark all partner notifications as read", "marked_read" in r.json().get("data", {}))

    # Delete notification
    if len(notif_list) > 1:
        r = api("DELETE", f"/partner/notifications/{notif_list[1]['id']}",
                token=partner_token, expected=[200])
        check("Delete partner notification", bool(r.json().get("data")))

# ── Admin: UI Notifications ───────────────────────────────────────────────────
section("15. Admin: UI Notifications")
r = api("GET", "/admin/notifications", token=admin_token, expected=[200])
admin_notifs = r.json().get("data", {})
check("Admin has notifications", admin_notifs.get("total", 0) >= 1)
admin_notif_list = admin_notifs.get("data", [])
if admin_notif_list:
    check("Admin notification is policy_uploaded",
          admin_notif_list[0].get("type") == "policy_uploaded")

    # Mark all read
    r = api("PATCH", "/admin/notifications/read-all", token=admin_token, expected=[200])
    check("Admin mark all notifications read", "marked_read" in r.json().get("data", {}))

    # Delete one
    r = api("DELETE", f"/admin/notifications/{admin_notif_list[0]['id']}",
            token=admin_token, expected=[200])
    check("Admin delete notification", bool(r.json().get("data")))

# ── Admin: Full member/policy oversight ───────────────────────────────────────
section("16. Admin: Full Platform Oversight")

# Dashboard
r = api("GET", "/admin/dashboard", token=admin_token, expected=[200])
dash = r.json().get("data", {})
check("Admin dashboard", "total_members" in dash and "total_partners" in dash)

# Members — all
r = api("POST", "/admin/members/list", token=admin_token, json_body={
    "global_filter": "", "sort_field": "created_at", "sort_order": -1,
    "filters": [], "limit": 10, "skip": 0,
}, expected=[200])
check("Admin list all members", r.json().get("data", {}).get("total", 0) >= 1)

# Members — by partner
r = api("POST", "/admin/members/list", token=admin_token, json_body={
    "global_filter": "", "sort_field": "created_at", "sort_order": -1,
    "filters": [], "limit": 10, "skip": 0,
    "partner_id": PARTNER_ID,
}, expected=[200])
check("Admin list members by partner", r.json().get("data", {}).get("total", 0) >= 1)

# Admin: member detail
r = api("GET", f"/admin/members/{MEMBER_ID}", token=admin_token, expected=[200])
check("Admin get member detail", r.json().get("data", {}).get("email") == MEMBER_EMAIL)

# Policies — all
r = api("POST", "/admin/policies/list", token=admin_token, json_body={
    "global_filter": "", "sort_field": "created_at", "sort_order": -1,
    "filters": [], "limit": 10, "skip": 0,
}, expected=[200])
check("Admin list all policies", r.json().get("data", {}).get("total", 0) >= 2)

# Policies — by partner
r = api("POST", "/admin/policies/list", token=admin_token, json_body={
    "global_filter": "", "sort_field": "created_at", "sort_order": -1,
    "filters": [], "limit": 10, "skip": 0,
    "partner_id": PARTNER_ID,
}, expected=[200])
check("Admin list policies by partner", r.json().get("data", {}).get("total", 0) >= 2)

# Admin: policy detail
r = api("GET", f"/admin/policies/{POLICY_ID}", token=admin_token, expected=[200])
pd = r.json().get("data", {})
check("Admin get policy detail", pd.get("id") == POLICY_ID)
check("Admin policy has storage_key", bool(pd.get("storage_key")))
check("Admin policy has partner_name", bool(pd.get("partner_name")))
check("Admin policy has member_name", bool(pd.get("member_name")))

# Admin: regenerate partner API key
r = api("POST", f"/admin/partners/{PARTNER_ID}/regenerate-key",
        token=admin_token, expected=[200])
check("Admin regen partner API key", bool(r.json().get("data", {}).get("api_key")))

# ── Me partners list ──────────────────────────────────────────────────────────
section("17. Member: Partners & Plan view")
r = api("GET", "/me/partners", token=member_token, expected=[200])
me_partners = r.json().get("data", [])
check("Member list partners", len(me_partners) >= 1)
if me_partners:
    check("Partner has plan details", bool(me_partners[0].get("plan")))

r = api("GET", "/me/plan", token=member_token,
        headers_extra={"X-Partner-Id": DEFAULT_PARTNER_ID}, expected=[200])
check("Member get current plan", bool(r.json().get("data", {}).get("plan")))

# ── Summary ───────────────────────────────────────────────────────────────────
section("RESULTS")
if errors:
    print(f"\n  {FAIL} {len(errors)} checks FAILED:")
    for e in errors:
        print(f"      - {e}")
    sys.exit(1)
else:
    print(f"\n  {OK} All checks PASSED!")
    print(f"\n  Summary:")
    print(f"    Admin:   {ADMIN_EMAIL}")
    print(f"    Partner: {PARTNER_EMAIL}")
    print(f"    Member:  {MEMBER_EMAIL}")
    print(f"    Plan ID: {PLAN_ID}")
    print(f"    Partner ID: {PARTNER_ID}")
    print(f"    Policy ID: {POLICY_ID}")
