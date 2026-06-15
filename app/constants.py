from enum import Enum


class UserType(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    CUSTOMER = "CUSTOMER"


class RoleType(str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
