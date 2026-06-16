from enum import Enum


class UserType(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    CUSTOMER = "CUSTOMER"
    PARTNER = "PARTNER"


class RoleType(str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    PARTNER = "PARTNER"
