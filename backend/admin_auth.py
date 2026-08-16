"""Separate Supabase-backed Admin authentication.

Regular citizen/officer sessions and admin sessions are intentionally separate,
following the LearnMate AI architecture.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import bcrypt
from database.db import get_client, get_one, insert, update
from config import settings


class AdminAuthError(ValueError):
    pass


@dataclass
class AdminUser:
    id: int
    email: str
    first_name: str
    last_name: str
    is_super_admin: bool
    is_active: bool

    def to_dict(self):
        return self.__dict__.copy()


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise AdminAuthError("Admin password must be at least 8 characters.")
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def get_admin_by_email(email: str):
    return get_one("admin_users", {"email": (email or "").strip().lower()})


def ensure_bootstrap_admin():
    """Create an initial admin only when explicit ADMIN_* settings are supplied."""
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD):
        return False
    if get_admin_by_email(settings.ADMIN_EMAIL):
        return True
    try:
        create_admin_user(
            settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD,
            settings.ADMIN_FIRST_NAME, settings.ADMIN_LAST_NAME, True
        )
        return True
    except Exception:
        return False


def create_admin_user(email, password, first_name, last_name, is_super_admin=False):
    email = email.strip().lower()
    if get_admin_by_email(email):
        raise AdminAuthError("An admin with this email already exists.")
    row = insert("admin_users", {
        "email": email,
        "password_hash": hash_password(password),
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "is_super_admin": bool(is_super_admin),
        "is_active": True,
    })
    if not row:
        raise AdminAuthError("Could not create the admin account in Supabase.")
    return AdminUser(row["id"], row["email"], row["first_name"], row["last_name"],
                     bool(row.get("is_super_admin")), bool(row.get("is_active", True)))


def verify_admin_login(email, password):
    row = get_admin_by_email(email)
    if not row or not row.get("is_active", True) or not verify_password(password, row.get("password_hash","")):
        raise AdminAuthError("Invalid admin email or password.")
    update("admin_users", {"id": row["id"]}, {"last_login_at": datetime.now(timezone.utc).isoformat()})
    return AdminUser(row["id"], row["email"], row.get("first_name",""), row.get("last_name",""),
                     bool(row.get("is_super_admin")), bool(row.get("is_active", True)))
