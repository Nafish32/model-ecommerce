"""Auth + RBAC, stdlib only. Password = pbkdf2; session = HMAC-signed cookie (stateless).
ponytail: single dev SECRET below — set ADMIN_SECRET env in prod. Roles: 'admin', 'customer'."""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import HTTPException, Request

SECRET = os.environ.get("ADMIN_SECRET", "dev-secret-change-me").encode()
COOKIE = "admin_session"
TTL = 86400  # 1 day


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, dk_b64 = stored.split("$")
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), 100_000)
        return hmac.compare_digest(base64.b64decode(dk_b64), test)
    except Exception:
        return False


def make_token(user_id: int, role: str, email: str = "") -> str:
    body = base64.urlsafe_b64encode(
        json.dumps({"uid": user_id, "role": role, "email": email, "exp": int(time.time()) + TTL}).encode()
    ).decode()
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def read_token(token: str) -> dict | None:
    try:
        body, sig = token.split(".")
        if not hmac.compare_digest(sig, hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body))
        return payload if payload["exp"] >= time.time() else None
    except Exception:
        return None


def require_admin(request: Request) -> dict:
    """FastAPI dependency: 401 unless a valid admin session cookie is present."""
    token = request.cookies.get(COOKIE)
    payload = read_token(token) if token else None
    if not payload or payload.get("role") != "admin":
        raise HTTPException(401, "Admin login required")
    return payload


def require_user(request: Request) -> dict:
    """FastAPI dependency: 401 unless any valid session (customer or admin) is present."""
    token = request.cookies.get(COOKIE)
    payload = read_token(token) if token else None
    if not payload:
        raise HTTPException(401, "Login required")
    return payload


def demo():
    h = hash_password("hunter2")
    assert verify_password("hunter2", h) and not verify_password("wrong", h)
    t = make_token(1, "admin")
    assert read_token(t)["role"] == "admin"
    assert read_token(t + "x") is None  # tampered sig rejected
    print("auth demo OK")


if __name__ == "__main__":
    demo()
