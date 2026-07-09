from enum import Enum


class UserType(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    PARTNER = "PARTNER"


class RoleType(str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    PARTNER = "PARTNER"


# Fixed catalog of admin permission modules (module_key -> human label).
# Every module gets the same 4 actions. SUPERADMIN always bypasses this grid.
PERMISSION_MODULES = {
    "dashboard":       "Dashboard",
    "partners":        "Partners",
    "members":         "Members",
    "plans":           "Membership Plans",
    "policies":        "Policies",
    "policy_types":    "Policy Types",
    "partner_types":   "Partner Types",
    "finance":         "Finance",
    "tickets":         "Tickets",
    "claims":          "Claim Tickets",
    "notifications":   "Notifications",
    "email_templates": "Email Templates",
    "audit_logs":      "Audit Logs",
    "settings":        "Settings",
    "cron":            "Automation (Cron)",
    "ai":              "AI Tools",
    "roles":           "Roles & Permissions",
    "users":           "Admin Users",
}

PERMISSION_ACTIONS = ["view", "add", "edit", "delete"]
