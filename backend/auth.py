"""Supabase-backed authentication for EcoVision AI."""
from __future__ import annotations

import os
import hashlib
import binascii
import re
import logging
from datetime import datetime, timedelta, timezone

from database.db import get_one, select, insert, update
from config import settings

logger = logging.getLogger("ecovision.auth")

PBKDF2_ITERATIONS = 260_000
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or binascii.hexlify(os.urandom(16)).decode()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return binascii.hexlify(dk).decode(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    check, _ = hash_password(password, salt)
    return check == password_hash


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must include at least one number."
    return True, ""


def _audit(user_id, action, details=""):
    try:
        insert("audit_log", {"user_id": user_id, "action": action, "details": details})
    except Exception:
        logger.warning("Audit log write failed", exc_info=True)


def register_user(full_name, email, phone, password, ward="", address="",
                  role="citizen", security_question="", security_answer=""):
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    ok, msg = validate_password_strength(password)
    if not ok:
        return False, msg
    if get_one("users", {"email": email}):
        return False, "An account with this email already exists."

    pw_hash, salt = hash_password(password)
    ans_hash, _ = hash_password(security_answer.strip().lower(), salt) if security_answer else (None, salt)
    try:
        row = insert("users", {
            "full_name": full_name.strip(),
            "email": email,
            "phone": phone.strip(),
            "password_hash": pw_hash,
            "salt": salt,
            "role": role,
            "ward": ward.strip(),
            "address": address.strip(),
            "security_question": security_question,
            "security_answer_hash": ans_hash,
            "auth_provider": "email",
            "is_active": True,
        })
        if not row:
            return False, "Registration failed: Supabase did not return the new account."
        _audit(row["id"], "register", f"role={role}")
        return True, row["id"]
    except Exception as exc:
        logger.exception("Registration failed")
        return False, f"Registration failed: {exc}"


def _recent_failed_attempts(email: str) -> int:
    since = (datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)).isoformat()
    rows = select("login_attempts", "id", {"email": email, "success": False}, limit=100)
    return sum(1 for r in rows if r.get("created_at", "") >= since)


def login_user(email: str, password: str):
    email = email.strip().lower()
    if _recent_failed_attempts(email) >= MAX_FAILED_ATTEMPTS:
        return False, f"Too many failed attempts. Please try again in {LOCKOUT_WINDOW_MINUTES} minutes."

    user = get_one("users", {"email": email})
    if not user or not user.get("is_active", True):
        insert("login_attempts", {"email": email, "success": False})
        return False, "Invalid email or password."

    if user.get("auth_provider") == "google" and user.get("password_hash") == "OIDC_ONLY":
        return False, "This account uses Google sign-in. Please choose Continue with Google."

    if not verify_password(password, user.get("password_hash", ""), user.get("salt", "")):
        insert("login_attempts", {"email": email, "success": False})
        return False, "Invalid email or password."

    insert("login_attempts", {"email": email, "success": True})
    update("users", {"id": user["id"]}, {"last_login": datetime.now(timezone.utc).isoformat()})
    _audit(user["id"], "login")
    user.pop("password_hash", None)
    user.pop("salt", None)
    user.pop("security_answer_hash", None)
    return True, user


def get_security_question(email: str):
    user = get_one("users", {"email": email.strip().lower()}, "security_question")
    return user.get("security_question") if user else None


def reset_password(email: str, security_answer: str, new_password: str):
    email = email.strip().lower()
    user = get_one("users", {"email": email})
    if not user:
        return False, "No account found with this email."

    ans_hash, _ = hash_password(security_answer.strip().lower(), user["salt"])
    if ans_hash != user.get("security_answer_hash"):
        return False, "Security answer is incorrect."

    ok, msg = validate_password_strength(new_password)
    if not ok:
        return False, msg

    pw_hash, salt = hash_password(new_password)
    update("users", {"id": user["id"]}, {
        "password_hash": pw_hash, "salt": salt, "auth_provider": "email"
    })
    _audit(user["id"], "password_reset")
    return True, "Password reset successfully. You can now log in."


def upsert_google_user(claims: dict):
    """Create/update a user from Streamlit's Google OIDC claims."""
    email = str(claims.get("email") or "").strip().lower()
    if not email or not EMAIL_RE.match(email):
        raise ValueError("Google did not return a valid email address.")
    sub = str(claims.get("sub") or "")
    name = str(claims.get("name") or "").strip()
    given = str(claims.get("given_name") or "").strip()
    family = str(claims.get("family_name") or "").strip()
    if not given and name:
        parts = name.split()
        given, family = parts[0], " ".join(parts[1:])
    given = given or "Google"
    family = family or "User"

    user = get_one("users", {"email": email})
    if user:
        if not user.get("oauth_subject") and sub:
            data = {"oauth_subject": sub}
            if user.get("password_hash") == "OIDC_ONLY":
                data["auth_provider"] = "google"
            update("users", {"id": user["id"]}, data)
        user.update({"password_hash": None, "salt": None, "security_answer_hash": None})
        return user

    row = insert("users", {
        "full_name": f"{given} {family}".strip(),
        "email": email,
        "phone": "",
        "password_hash": "OIDC_ONLY",
        "salt": "OIDC_ONLY",
        "role": "citizen",
        "ward": "",
        "address": "",
        "security_question": "",
        "security_answer_hash": None,
        "auth_provider": "google",
        "oauth_subject": sub,
        "is_active": True,
    })
    if not row:
        raise RuntimeError("Could not create Google account in Supabase.")
    _audit(row["id"], "google_login")
    row.update({"password_hash": None, "salt": None, "security_answer_hash": None})
    return row
