import json
import logging
import os

logger = logging.getLogger(__name__)


def seed_roles():
    from app.db.queries.role_query import RoleQuery
    roles_path = os.path.join(os.path.dirname(__file__), "roles.json")
    with open(roles_path) as f:
        roles_data = json.load(f)
    rq = RoleQuery()
    rq.seed_roles(roles_data)
    logger.info("Roles seeded: %d entries", len(roles_data))


EMAIL_TEMPLATES = [
    {
        "slug": "otp_login",
        "description": "OTP sent during login",
        "subject": "Your EasyClaims Login OTP",
        "html_body": """<html><body>
<p>Hello,</p>
<p>Your one-time password (OTP) for EasyClaims login is:</p>
<h2 style="letter-spacing:4px;font-family:monospace;">{{ otp }}</h2>
<p>This OTP is valid for {{ otp_expire_minutes }} minutes.</p>
<p>If you did not request this, please ignore this email.</p>
<p style="color:#888;font-size:12px;">— EasyClaims Team</p>
</body></html>""",
    },
    {
        "slug": "welcome_member",
        "description": "Sent to a new member when their account is created",
        "subject": "Welcome to EasyClaims — Your Account is Ready",
        "html_body": """<html><body>
<p>Hi {{ member_name }},</p>
<p>Your EasyClaims account has been set up by <strong>{{ partner_name }}</strong>.</p>
<p>You can now log in and manage your health insurance policies in one place.</p>
<table style="border-collapse:collapse;margin:16px 0">
  <tr><td style="padding:4px 12px 4px 0;color:#666">Login Email</td><td><strong>{{ email }}</strong></td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Login Method</td><td>OTP (One-Time Password sent to this email)</td></tr>
</table>
<p style="margin:20px 0">
  <a href="{{ login_url }}" style="background:#0066cc;color:#fff;padding:10px 24px;text-decoration:none;border-radius:4px;">Login to EasyClaims</a>
</p>
<p style="color:#888;font-size:13px;">If you have any questions, reply to this email or contact your partner.</p>
<p>— EasyClaims Team</p>
</body></html>""",
    },
    {
        "slug": "policy_uploaded_member",
        "description": "Sent to member when a policy is uploaded",
        "subject": "Policy Uploaded — {{ policy_number }}",
        "html_body": """<html><body>
<p>Dear {{ member_name }},</p>
<p>Your <strong>{{ policy_type }}</strong> policy has been successfully uploaded to EasyClaims.</p>
<table style="border-collapse:collapse;margin:16px 0">
  <tr><td style="padding:4px 12px 4px 0;color:#666">Policy Number</td><td><strong>{{ policy_number }}</strong></td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Type</td><td>{{ policy_type }}</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Status</td><td>Under Review</td></tr>
</table>
<p>Our team will review your document and update the status shortly.</p>
<p>— EasyClaims Team</p>
</body></html>""",
    },
    {
        "slug": "policy_uploaded_partner",
        "description": "Sent to partner when a member uploads a policy",
        "subject": "New Policy Uploaded by Member — {{ policy_number }}",
        "html_body": """<html><body>
<p>Dear {{ partner_name }},</p>
<p>A member under your account has uploaded a new policy document.</p>
<table style="border-collapse:collapse;margin:16px 0">
  <tr><td style="padding:4px 12px 4px 0;color:#666">Member</td><td><strong>{{ member_name }}</strong> ({{ member_email }})</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Policy Number</td><td><strong>{{ policy_number }}</strong></td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Type</td><td>{{ policy_type }}</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Status</td><td>Pending Review</td></tr>
</table>
<p>Log in to the partner portal to review the uploaded document.</p>
<p>— EasyClaims System</p>
</body></html>""",
    },
    {
        "slug": "policy_uploaded_admin",
        "description": "Sent to admin when a policy is uploaded",
        "subject": "[Admin] New Policy Upload — {{ policy_number }}",
        "html_body": """<html><body>
<p>A new policy has been uploaded and requires review.</p>
<table style="border-collapse:collapse;margin:16px 0">
  <tr><td style="padding:4px 12px 4px 0;color:#666">Policy Number</td><td><strong>{{ policy_number }}</strong></td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Type</td><td>{{ policy_type }}</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Member</td><td>{{ member_name }} ({{ member_email }})</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Partner</td><td>{{ partner_name }}</td></tr>
</table>
<p>— EasyClaims System</p>
</body></html>""",
    },
    {
        "slug": "plan_expiry_warning",
        "description": "Sent to member 2 days before plan expires",
        "subject": "Your EasyClaims Plan Expires in {{ days_left }} Day{% if days_left != 1 %}s{% endif %}",
        "html_body": """<html><body>
<p>Dear {{ member_name }},</p>
<p>This is a reminder that your EasyClaims plan is expiring soon.</p>
<table style="border-collapse:collapse;margin:16px 0;background:#fff8e1;border:1px solid #ffe082;border-radius:8px">
  <tr><td style="padding:8px 16px;color:#666">Plan</td><td style="padding:8px 16px"><strong>{{ plan_name }}</strong></td></tr>
  <tr><td style="padding:8px 16px;color:#666">Expiry Date</td><td style="padding:8px 16px"><strong style="color:#e65100">{{ end_date }}</strong></td></tr>
  <tr><td style="padding:8px 16px;color:#666">Days Remaining</td><td style="padding:8px 16px"><strong>{{ days_left }} day{% if days_left != 1 %}s{% endif %}</strong></td></tr>
</table>
<p>Please contact your partner or log in to renew your plan before it expires.</p>
<p>— EasyClaims Team</p>
</body></html>""",
    },
    {
        "slug": "plan_expired_member",
        "description": "Sent to member when their plan has expired",
        "subject": "Your EasyClaims Plan Has Expired",
        "html_body": """<html><body>
<p>Dear {{ member_name }},</p>
<p>Your EasyClaims plan has expired. Please contact your partner to renew your plan and restore access.</p>
<table style="border-collapse:collapse;margin:16px 0;background:#ffebee;border:1px solid #ffcdd2;border-radius:8px">
  <tr><td style="padding:8px 16px;color:#666">Plan</td><td style="padding:8px 16px"><strong>{{ plan_name }}</strong></td></tr>
  <tr><td style="padding:8px 16px;color:#666">Expired On</td><td style="padding:8px 16px"><strong style="color:#c62828">{{ end_date }}</strong></td></tr>
</table>
<p>— EasyClaims Team</p>
</body></html>""",
    },
    {
        "slug": "plan_expired_partner",
        "description": "Sent to partner when a member's plan expires",
        "subject": "Member Plan Expired — {{ member_name }}",
        "html_body": """<html><body>
<p>Dear {{ partner_name }},</p>
<p>A member's EasyClaims plan has expired and they may need renewal.</p>
<table style="border-collapse:collapse;margin:16px 0">
  <tr><td style="padding:4px 12px 4px 0;color:#666">Member</td><td><strong>{{ member_name }}</strong> ({{ member_email }})</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Plan</td><td>{{ plan_name }}</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Expired On</td><td><strong style="color:#c62828">{{ end_date }}</strong></td></tr>
</table>
<p>Log in to the partner portal to renew this member's enrollment.</p>
<p>— EasyClaims System</p>
</body></html>""",
    },
    {
        "slug": "plan_changed",
        "description": "Sent to member when their plan is changed",
        "subject": "Your EasyClaims Plan Has Been Updated",
        "html_body": """<html><body>
<p>Dear {{ member_name }},</p>
<p>Your EasyClaims plan has been updated.</p>
<table style="border-collapse:collapse;margin:16px 0">
  <tr><td style="padding:4px 12px 4px 0;color:#666">Previous Plan</td><td>{{ old_plan }}</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">New Plan</td><td><strong>{{ new_plan }}</strong></td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666">Changed By</td><td>{{ changed_by }}</td></tr>
</table>
<p>If you did not expect this change, please contact your partner.</p>
<p>— EasyClaims Team</p>
</body></html>""",
    },
    {
        "slug": "enrollment_renewed",
        "description": "Sent to member when their enrollment is renewed",
        "subject": "Your EasyClaims Plan Has Been Renewed",
        "html_body": """<html><body>
<p>Dear {{ member_name }},</p>
<p>Great news! Your EasyClaims plan has been renewed.</p>
<table style="border-collapse:collapse;margin:16px 0;background:#e8f5e9;border:1px solid #c8e6c9;border-radius:8px">
  <tr><td style="padding:8px 16px;color:#666">Plan</td><td style="padding:8px 16px"><strong>{{ plan_name }}</strong></td></tr>
  <tr><td style="padding:8px 16px;color:#666">New Expiry Date</td><td style="padding:8px 16px"><strong style="color:#2e7d32">{{ end_date }}</strong></td></tr>
</table>
<p>— EasyClaims Team</p>
</body></html>""",
    },
    {
        "slug": "welcome_member_new_partner",
        "description": "Sent to an existing member when they are enrolled under a new/additional partner",
        "subject": "You've Been Enrolled with {{ partner_name }} on EasyClaims",
        "html_body": """<html><body style="font-family:Arial,sans-serif;color:#222;max-width:600px;margin:0 auto">
<div style="background:#0a2257;padding:20px 28px;border-radius:10px 10px 0 0">
  <span style="color:#fff;font-size:22px;font-weight:800;letter-spacing:1px">EasyClaims</span>
  <span style="color:#93c5fd;font-size:13px;margin-left:12px">Your Health Benefits, Simplified</span>
</div>
<div style="background:#fff;border:1px solid #e2e8f0;border-top:none;padding:28px;border-radius:0 0 10px 10px">
  <p>Hi <strong>{{ member_name }}</strong>,</p>
  <p>You have been enrolled under a new partner on EasyClaims:</p>
  <table style="border-collapse:collapse;width:100%;margin:16px 0;background:#f8faff;border-radius:8px;border:1px solid #dbeafe">
    <tr><td style="padding:10px 16px;color:#555;font-size:13px;width:140px">Partner</td><td style="padding:10px 16px"><strong>{{ partner_name }}</strong></td></tr>
  </table>
  <p>Your existing EasyClaims account credentials remain the same — just log in to access your benefits under this new partner.</p>
  <p>Please find your membership card attached to this email.</p>
  <p style="margin:24px 0">
    <a href="{{ login_url }}" style="background:#0a2257;color:#fff;padding:11px 26px;text-decoration:none;border-radius:6px;font-weight:700;font-size:14px">Log in to EasyClaims</a>
  </p>
  <p style="color:#888;font-size:12px">If you did not expect this enrollment, please contact your administrator.</p>
  <p style="color:#888;font-size:12px;margin-top:24px">— EasyClaims Team</p>
</div>
</body></html>""",
    },
    {
        "slug": "ticket_raised",
        "description": "Sent to member when their claim ticket is created via portal or WhatsApp",
        "subject": "Your Claim Request Has Been Received — Ticket #{{ ticket_id[:8] }}",
        "html_body": """<html><body style="font-family:Arial,sans-serif;color:#222;max-width:600px;margin:0 auto">
<div style="background:#0a2257;padding:20px 28px;border-radius:10px 10px 0 0">
  <span style="color:#fff;font-size:20px;font-weight:800">EasyClaims</span>
  <div style="color:#93c5fd;font-size:12px;margin-top:2px">Claim Assistance</div>
</div>
<div style="background:#fff;border:1px solid #e2e8f0;border-top:none;padding:28px;border-radius:0 0 10px 10px">
  <p>Dear <strong>{{ member_name }}</strong>,</p>
  <p>We have received your claim request. Our team will review it and follow up with you shortly.</p>
  <table style="width:100%;border-collapse:collapse;background:#f0f9ff;border-radius:10px;overflow:hidden;margin:16px 0">
    <tr style="background:#e0f2fe">
      <td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600;width:140px">Ticket ID</td>
      <td style="padding:10px 16px;font-weight:700;font-size:14px;font-family:monospace">{{ ticket_id }}</td>
    </tr>
    <tr>
      <td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Summary</td>
      <td style="padding:10px 16px;font-size:13px">{{ summary }}</td>
    </tr>
    <tr style="background:#e0f2fe">
      <td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Channel</td>
      <td style="padding:10px 16px;font-size:13px">{{ channel }}</td>
    </tr>
  </table>
  <p style="color:#888;font-size:12px;margin-top:24px">— EasyClaims Team</p>
</div>
</body></html>""",
    },
    {
        "slug": "claim_submitted_admin",
        "description": "Sent to every SUPERADMIN when a member submits a policy claim",
        "subject": "New Claim Submitted — {{ claim_number }}",
        "html_body": """<html><body style="font-family:Arial,sans-serif;color:#222;max-width:600px;margin:0 auto">
<div style="background:#0a2257;padding:20px 28px;border-radius:10px 10px 0 0">
  <span style="color:#fff;font-size:20px;font-weight:800">EasyClaims</span>
  <div style="color:#93c5fd;font-size:12px;margin-top:2px">Claim Notification</div>
</div>
<div style="background:#fff;border:1px solid #e2e8f0;border-top:none;padding:28px;border-radius:0 0 10px 10px">
  <p>A new claim has been submitted and {{ agent_name }} has been auto-assigned.</p>
  <table style="width:100%;border-collapse:collapse;background:#f0f9ff;border-radius:10px;overflow:hidden;margin:16px 0">
    <tr style="background:#e0f2fe"><td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600;width:160px">Claim Number</td><td style="padding:10px 16px;font-weight:700;font-family:monospace">{{ claim_number }}</td></tr>
    <tr><td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Member</td><td style="padding:10px 16px;font-size:13px">{{ member_name }}</td></tr>
    <tr style="background:#e0f2fe"><td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Policy</td><td style="padding:10px 16px;font-size:13px">{{ policy_number }}</td></tr>
    <tr><td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Assigned Agent</td><td style="padding:10px 16px;font-size:13px">{{ agent_name }}</td></tr>
  </table>
  <p style="color:#888;font-size:12px;margin-top:24px">— EasyClaims Team</p>
</div>
</body></html>""",
    },
    {
        "slug": "claim_assigned_agent",
        "description": "Sent to a claim agent when a claim is assigned or reassigned to them",
        "subject": "Claim Assigned to You — {{ claim_number }}",
        "html_body": """<html><body style="font-family:Arial,sans-serif;color:#222;max-width:600px;margin:0 auto">
<div style="background:#0a2257;padding:20px 28px;border-radius:10px 10px 0 0">
  <span style="color:#fff;font-size:20px;font-weight:800">EasyClaims</span>
  <div style="color:#93c5fd;font-size:12px;margin-top:2px">Claim Assigned</div>
</div>
<div style="background:#fff;border:1px solid #e2e8f0;border-top:none;padding:28px;border-radius:0 0 10px 10px">
  <p>Dear <strong>{{ agent_name }}</strong>,</p>
  <p>A claim has been assigned to you for processing.</p>
  <table style="width:100%;border-collapse:collapse;background:#f0f9ff;border-radius:10px;overflow:hidden;margin:16px 0">
    <tr style="background:#e0f2fe"><td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600;width:160px">Claim Number</td><td style="padding:10px 16px;font-weight:700;font-family:monospace">{{ claim_number }}</td></tr>
    <tr><td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Member</td><td style="padding:10px 16px;font-size:13px">{{ member_name }}</td></tr>
    <tr style="background:#e0f2fe"><td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Policy</td><td style="padding:10px 16px;font-size:13px">{{ policy_number }}</td></tr>
  </table>
  <p style="color:#888;font-size:12px;margin-top:24px">— EasyClaims Team</p>
</div>
</body></html>""",
    },
    {
        "slug": "claim_status_update_member",
        "description": "Sent to the member whenever their claim's status changes",
        "subject": "Your Claim {{ claim_number }} is now {{ new_status }}",
        "html_body": """<html><body style="font-family:Arial,sans-serif;color:#222;max-width:600px;margin:0 auto">
<div style="background:#0a2257;padding:20px 28px;border-radius:10px 10px 0 0">
  <span style="color:#fff;font-size:20px;font-weight:800">EasyClaims</span>
  <div style="color:#93c5fd;font-size:12px;margin-top:2px">Claim Update</div>
</div>
<div style="background:#fff;border:1px solid #e2e8f0;border-top:none;padding:28px;border-radius:0 0 10px 10px">
  <p>Dear <strong>{{ member_name }}</strong>,</p>
  <p>Your claim <strong>{{ claim_number }}</strong> status has been updated to <strong>{{ new_status }}</strong>.</p>
  {% if remark %}<p style="background:#f8fafc;border-left:3px solid #0a2257;padding:10px 14px;font-size:13px">{{ remark }}</p>{% endif %}
  <p style="color:#888;font-size:12px;margin-top:24px">— EasyClaims Team</p>
</div>
</body></html>""",
    },
    {
        "slug": "membership_card",
        "description": "Membership card email sent after enrollment — PDF card attached, shows partner/plan/benefits",
        "subject": "Your EasyClaims Membership Card — {{ plan_name }}",
        "html_body": """<html><body style="font-family:Arial,sans-serif;color:#222;max-width:600px;margin:0 auto">
<div style="background:#0a2257;padding:20px 28px;border-radius:10px 10px 0 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span style="color:#fff;font-size:22px;font-weight:800;letter-spacing:1px">EasyClaims</span>
      <div style="color:#93c5fd;font-size:12px;margin-top:2px">Your Health Benefits, Simplified</div>
    </div>
    <div style="background:#1e40af;color:#fff;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;letter-spacing:0.5px">MEMBERSHIP CARD</div>
  </div>
</div>
<div style="background:#fff;border:1px solid #e2e8f0;border-top:none;padding:28px;border-radius:0 0 10px 10px">
  <p>Dear <strong>{{ member_name }}</strong>,</p>
  <p>Welcome! Your membership card is attached to this email as a PDF. Here is a summary:</p>
  <table style="width:100%;border-collapse:collapse;background:#f0f4ff;border-radius:10px;overflow:hidden;margin:16px 0">
    <tr style="background:#e8eeff">
      <td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600;width:160px">Member</td>
      <td style="padding:10px 16px;font-weight:700;font-size:15px">{{ member_name }}</td>
    </tr>
    <tr>
      <td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Email</td>
      <td style="padding:10px 16px;font-size:13px">{{ member_email }}</td>
    </tr>
    <tr style="background:#e8eeff">
      <td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Partner</td>
      <td style="padding:10px 16px;font-weight:600">{{ partner_name }} <span style="color:#64748b;font-size:12px;font-weight:400">({{ partner_type }})</span></td>
    </tr>
    <tr>
      <td style="padding:10px 16px;font-size:12px;color:#555;font-weight:600">Plan</td>
      <td style="padding:10px 16px;font-weight:700;color:#0a2257;font-size:15px">{{ plan_name }}</td>
    </tr>
  </table>
  <p style="font-size:13px;font-weight:700;color:#0a2257;margin:20px 0 10px;text-transform:uppercase;letter-spacing:0.5px">Plan Benefits</p>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    <tr><td style="padding:5px 12px 5px 0;color:#555;width:55%">👨‍👩‍👧 Family Members Covered</td><td style="font-weight:600">{{ benefit_family }}</td></tr>
    <tr><td style="padding:5px 12px 5px 0;color:#555">📁 Policy Upload Slots</td><td style="font-weight:600">{{ benefit_slots }}</td></tr>
    <tr><td style="padding:5px 12px 5px 0;color:#555">🛡 Claim Support</td><td style="font-weight:600">{{ benefit_claim }}</td></tr>
    {% if benefit_aiqa %}<tr><td style="padding:5px 12px 5px 0;color:#555">🤖 AI Health Query Assistant</td><td style="font-weight:600;color:#16a34a">✓ Included</td></tr>{% endif %}
    {% if benefit_teleconsult and benefit_teleconsult > 0 %}<tr><td style="padding:5px 12px 5px 0;color:#555">🩺 Tele-consultation</td><td style="font-weight:600">{{ benefit_teleconsult }} sessions</td></tr>{% endif %}
    {% if benefit_wellness and benefit_wellness > 0 %}<tr><td style="padding:5px 12px 5px 0;color:#555">🧘 Wellness Sessions</td><td style="font-weight:600">{{ benefit_wellness }} sessions</td></tr>{% endif %}
    {% if benefit_hospital_cash %}<tr><td style="padding:5px 12px 5px 0;color:#555">🏥 Hospital Cash Benefit</td><td style="font-weight:600;color:#16a34a">✓ Included</td></tr>{% endif %}
    {% if benefit_emergency_assist %}<tr><td style="padding:5px 12px 5px 0;color:#555">🚨 Emergency Assistance</td><td style="font-weight:600;color:#16a34a">✓ Included</td></tr>{% endif %}
  </table>
  <p style="margin:28px 0 8px">
    <a href="{{ login_url }}" style="background:#0a2257;color:#fff;padding:11px 26px;text-decoration:none;border-radius:6px;font-weight:700;font-size:14px">Access My Benefits</a>
  </p>
  <p style="color:#888;font-size:12px;margin-top:20px">Keep the attached PDF as your membership reference. For support, contact your partner or reply to this email.</p>
  <p style="color:#888;font-size:12px">— EasyClaims Team</p>
</div>
</body></html>""",
    },
]


WHATSAPP_TEMPLATES = [
    {
        "slug": "wa_welcome_member",
        "description": "Sent to a new member on first enrollment",
        "html_body": (
            "Welcome to EasyClaims, {{ member_name }}! 🎉\n\n"
            "You have been enrolled under *{{ partner_name }}*.\n\n"
            "To upload your insurance policy document, visit:\n"
            "{{ upload_url }}\n\n"
            "For any queries, just send a message here."
        ),
    },
    {
        "slug": "wa_new_partner",
        "description": "Sent to an existing member when a new partner is added",
        "html_body": (
            "Hi {{ member_name }}! 👋\n\n"
            "You have been enrolled under a new partner on EasyClaims:\n"
            "*{{ partner_name }}*\n\n"
            "Your existing login credentials remain the same.\n"
            "Log in to access your benefits: {{ login_url }}\n\n"
            "— EasyClaims Team"
        ),
    },
    {
        "slug": "wa_membership_card",
        "description": "Sent with the membership card PDF after enrollment",
        "html_body": (
            "🎟 *EasyClaims Membership Card*\n\n"
            "👤 *Member:* {{ member_name }}\n"
            "🏢 *Partner:* {{ partner_name }}\n"
            "📋 *Plan:* {{ plan_name }}\n\n"
            "*Benefits:*\n"
            "• Family: {{ benefit_family }} member(s)\n"
            "• Policy Slots: {{ benefit_slots }}\n"
            "• Claim Support: {{ benefit_claim }}\n"
            "{{ extra_benefits }}\n\n"
            "Your membership card PDF is attached above.\n"
            "Access your benefits: {{ login_url }}\n\n"
            "— EasyClaims"
        ),
    },
    {
        "slug": "wa_policy_uploaded",
        "description": "Sent to member when their policy document is received",
        "html_body": (
            "Hi {{ member_name }}! ✅\n\n"
            "Your {{ policy_type }} policy document has been received.\n\n"
            "We are verifying your document. You will be notified once it is approved."
        ),
    },
    {
        "slug": "wa_policy_rejected",
        "description": "Sent to member when their uploaded document fails verification",
        "html_body": (
            "Hi {{ member_name }}! ❌\n\n"
            "Your uploaded document for policy *{{ policy_number }}* could not be verified.\n\n"
            "Reason: {{ reason }}\n\n"
            "Please upload a valid insurance policy document."
        ),
    },
    {
        "slug": "wa_policy_expired",
        "description": "Sent to member when a policy has expired",
        "html_body": (
            "Hi {{ member_name }}! 🔔\n\n"
            "Your *{{ policy_type }}* policy (*{{ policy_number }}*) has expired.\n\n"
            "Please upload your renewed policy document to maintain continuous coverage:\n"
            "{{ upload_url }}\n\n"
            "Need help? Just reply to this message."
        ),
    },
    {
        "slug": "wa_upload_reminder",
        "description": "Reminder sent to members who haven't uploaded a policy document",
        "html_body": (
            "Hi {{ member_name }}! 👋\n\n"
            "You are enrolled under *{{ partner_name }}* on EasyClaims, "
            "but we haven't received your insurance policy document yet.\n\n"
            "Please upload it here: {{ upload_url }}\n\n"
            "If you need help, just reply to this message."
        ),
    },
    {
        "slug": "wa_policy_expiry_warning",
        "description": "Sent to member when a policy is about to expire",
        "html_body": (
            "Hi {{ member_name }}! ⚠️\n\n"
            "Your *{{ policy_type }}* policy (*{{ policy_number }}*) "
            "is expiring in {{ days_left }} day(s) on *{{ end_date }}*.\n\n"
            "Please renew your policy to avoid a lapse in coverage."
        ),
    },
    {
        "slug": "wa_ticket_raised",
        "description": "Sent to member when their claim ticket is created",
        "html_body": (
            "Hi {{ member_name }}! 🎫\n\n"
            "Your claim request has been received.\n\n"
            "*Ticket ID:* {{ ticket_id }}\n"
            "*Summary:* {{ summary }}\n\n"
            "Our team will follow up with you shortly.\n\n"
            "— EasyClaims Team"
        ),
    },
    {
        "slug": "wa_claim_assigned_agent",
        "description": "Sent to a claim agent via WhatsApp when a claim is assigned or reassigned to them",
        "html_body": (
            "Hi {{ agent_name }}! 📋\n\n"
            "A claim has been assigned to you.\n\n"
            "*Claim Number:* {{ claim_number }}\n"
            "*Member:* {{ member_name }}\n"
            "*Policy:* {{ policy_number }}\n\n"
            "— EasyClaims Team"
        ),
    },
    {
        "slug": "wa_claim_status_update_member",
        "description": "Sent to the member via WhatsApp when their claim's status changes",
        "html_body": (
            "Hi {{ member_name }}! 📋\n\n"
            "Your claim *{{ claim_number }}* is now *{{ new_status }}*.\n\n"
            "{{ remark }}\n\n"
            "— EasyClaims Team"
        ),
    },
    {
        "slug": "wa_claim_submitted_admin",
        "description": "Sent to superadmins via WhatsApp when a new claim is submitted",
        "html_body": (
            "📋 New claim submitted\n\n"
            "*Claim Number:* {{ claim_number }}\n"
            "*Member:* {{ member_name }}\n"
            "*Assigned Agent:* {{ agent_name }}"
        ),
    },
]


def seed_email_templates():
    from app.db.queries.email_template_query import EmailTemplateQuery
    tq = EmailTemplateQuery()
    for tpl in EMAIL_TEMPLATES:
        tq.create_if_not_exists(
            slug=tpl["slug"],
            subject=tpl["subject"],
            html_body=tpl["html_body"],
            description=tpl.get("description", ""),
            channel_type="email",
        )
    for tpl in WHATSAPP_TEMPLATES:
        tq.create_if_not_exists(
            slug=tpl["slug"],
            html_body=tpl["html_body"],
            description=tpl.get("description", ""),
            channel_type="whatsapp",
        )
    logger.info("Email templates seeded: %d entries", len(EMAIL_TEMPLATES))
    logger.info("WhatsApp templates seeded: %d entries", len(WHATSAPP_TEMPLATES))


def run_seed():
    try:
        seed_roles()
        seed_email_templates()
        logger.info("Seeding complete")
    except Exception as exc:
        logger.warning("Seeding failed (DB may not be ready): %s", exc)
