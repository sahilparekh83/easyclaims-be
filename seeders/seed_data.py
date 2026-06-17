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
]


def seed_email_templates():
    from app.db.queries.email_template_query import EmailTemplateQuery
    tq = EmailTemplateQuery()
    for tpl in EMAIL_TEMPLATES:
        tq.upsert(
            slug=tpl["slug"],
            subject=tpl["subject"],
            html_body=tpl["html_body"],
            description=tpl.get("description", ""),
        )
    logger.info("Email templates seeded: %d entries", len(EMAIL_TEMPLATES))


def run_seed():
    try:
        seed_roles()
        seed_email_templates()
        logger.info("Seeding complete")
    except Exception as exc:
        logger.warning("Seeding failed (DB may not be ready): %s", exc)
