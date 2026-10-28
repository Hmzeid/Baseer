"""Baseer accounts + roles (production, stdlib only).

Roles mirror the acting-as identity already in the UI: Safety Supervisor,
Site Manager, Contractor — plus Admin for user management. Passwords are
PBKDF2-HMAC-SHA256; API tokens are stateless HMAC-signed
(base64 username:expiry:signature) so no session table is needed.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone

ROLES = ("Safety Supervisor", "Site Manager", "Contractor", "Admin")
TOKEN_TTL_SECONDS = 12 * 3600

_secret = ""


def init(secret: str) -> None:
    global _secret
    _secret = secret


def _get_secret() -> str:
    assert _secret, "auth.init() was not called"
    return _secret


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210_000)
    return digest.hex(), salt


def verify_password(password: str, pw_hash: str, salt: str) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210_000)
    return hmac.compare_digest(digest.hex(), pw_hash)


def mint_token(username: str) -> str:
    exp = str(int(time.time()) + TOKEN_TTL_SECONDS)
    sig = hmac.new(_get_secret().encode(), f"{username}:{exp}".encode(),
                   hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{username}:{exp}:{sig}".encode()).decode()


def check_token(token: str) -> str | None:
    """Return the username for a valid, unexpired token, else None."""
    try:
        username, exp, sig = base64.urlsafe_b64decode(token.encode()).decode().split(":")
        if int(exp) < time.time():
            return None
        want = hmac.new(_get_secret().encode(), f"{username}:{exp}".encode(),
                        hashlib.sha256).hexdigest()
        if not hmac.compare_digest(want, sig):
            return None
        return username
    except Exception:
        return None


def get_user(conn: sqlite3.Connection, username: str) -> dict | None:
    row = conn.execute(
        "SELECT username, pw_hash, salt, role FROM users WHERE username = ?",
        (username,)).fetchone()
    if not row:
        return None
    return {"username": row[0], "pw_hash": row[1], "salt": row[2], "role": row[3]}


def create_user(conn: sqlite3.Connection, username: str, password: str, role: str) -> None:
    username = username.strip()
    if not username or not password:
        raise ValueError("username and password are required")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    if role not in ROLES:
        raise ValueError(f"role must be one of {', '.join(ROLES)}")
    if get_user(conn, username):
        raise ValueError("username already exists")
    pw_hash, salt = hash_password(password)
    conn.execute(
        "INSERT INTO users (username, pw_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, pw_hash, salt, role,
         datetime.now(timezone.utc).isoformat()))
    conn.commit()


def ensure_admin(conn: sqlite3.Connection) -> tuple[str, str] | None:
    """Create the bootstrap admin from env on first boot. Returns (user, password)
    only when it actually created one (so the operator sees it once)."""
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        return None
    user = os.getenv("BASEER_ADMIN_USER", "admin")
    password = os.getenv("BASEER_ADMIN_PASSWORD", "")
    if not password:
        password = secrets.token_urlsafe(16)
        created_default = True
    else:
        created_default = False
    try:
        create_user(conn, user, password, "Admin")
    except ValueError:
        return None
    return (user, password) if created_default else (user, "<from BASEER_ADMIN_PASSWORD>")
