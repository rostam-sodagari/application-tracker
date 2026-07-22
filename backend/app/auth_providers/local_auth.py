"""Local authentication: email and password accounts stored in the local SQLite database, with a
signed bearer token issued on registration or login. No external service is involved.

The token is deliberately the same shape (an Authorization: Bearer header) that Appwrite mode
uses, so the frontend's request layer does not need to know which backend issued it. Unlike
Appwrite's short-lived tokens, there is no forced refresh here; a token is valid for 30 days from
issue, since there is no equivalent of Appwrite's own session revocation to defer to.
"""

import logging
import smtplib
import time
from collections import defaultdict

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel

from .. import config, email_sender
from ..stores import local_store

TOKEN_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 days
VERIFICATION_TOKEN_MAX_AGE_SECONDS = 48 * 60 * 60  # 48 hours
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 15 * 60

logger = logging.getLogger(__name__)

_login_attempts: dict[str, list[float]] = defaultdict(list)


def _serializer() -> URLSafeTimedSerializer:
    if not config.LOCAL_SESSION_SECRET:
        raise RuntimeError("LOCAL_SESSION_SECRET is not set - see .env.example")
    return URLSafeTimedSerializer(config.LOCAL_SESSION_SECRET, salt="local-auth-token")


def _verification_serializer() -> URLSafeTimedSerializer:
    if not config.LOCAL_SESSION_SECRET:
        raise RuntimeError("LOCAL_SESSION_SECRET is not set - see .env.example")
    return URLSafeTimedSerializer(config.LOCAL_SESSION_SECRET, salt="email-verification")


def _send_verification_email(user_id: str, email: str):
    token = _verification_serializer().dumps(user_id)
    verify_url = f"{config.APP_BASE_URL}/verify-email?token={token}"
    try:
        email_sender.send_verification_email(email, verify_url)
    except (OSError, smtplib.SMTPException):
        logger.exception("failed to send verification email to %s", email)


def _check_rate_limit(client_ip: str):
    now = time.time()
    attempts = [t for t in _login_attempts.get(client_ip, []) if now - t < LOGIN_WINDOW_SECONDS]
    if attempts:
        _login_attempts[client_ip] = attempts
    else:
        # Every login attempt reaches this function, including successful ones, so without this
        # an entry would accumulate here permanently for every distinct client IP ever seen, even
        # once its attempts have all expired out of the window.
        _login_attempts.pop(client_ip, None)
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        retry_after = int(LOGIN_WINDOW_SECONDS - (now - attempts[0]))
        raise HTTPException(status_code=429, detail=f"Too many login attempts. Try again in {retry_after}s.")


def _record_failed_attempt(client_ip: str):
    _login_attempts[client_ip].append(time.time())


def require_auth(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency returning the calling user's id."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = _serializer().loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="session invalid or expired")
    return user_id


router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(payload: RegisterRequest):
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="enter a valid email address")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="password must be at least 8 characters")
    if local_store.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="an account with this email already exists")

    password_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    needs_verification = email_sender.smtp_configured()
    user_id = local_store.create_user(email, password_hash, email_verified=not needs_verification)
    if needs_verification:
        _send_verification_email(user_id, email)

    token = _serializer().dumps(user_id)
    return {"token": token, "email": email, "email_verified": not needs_verification}


@router.post("/login")
def login(payload: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    email = payload.email.strip().lower()
    user = local_store.get_user_by_email(email)
    valid = user is not None and bcrypt.checkpw(payload.password.encode(), user["password_hash"].encode())
    if not valid:
        _record_failed_attempt(client_ip)
        raise HTTPException(status_code=401, detail="invalid email or password")

    token = _serializer().dumps(user["id"])
    return {"token": token, "email": email}


@router.post("/logout")
def logout():
    # Tokens are stateless and not stored server-side, so there is nothing to revoke here; the
    # frontend simply discards the token. Kept as a real endpoint for symmetry with Appwrite mode
    # and in case a revocation list is added later.
    return {"ok": True}


@router.get("/whoami")
def whoami(current_user_id: str = Depends(require_auth)):
    user = local_store.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="account no longer exists")
    return {"email": user["email"], "email_verified": bool(user["email_verified"])}


@router.get("/verify-email")
def verify_email(token: str):
    try:
        user_id = _verification_serializer().loads(token, max_age=VERIFICATION_TOKEN_MAX_AGE_SECONDS)
    except SignatureExpired:
        raise HTTPException(status_code=400, detail="this verification link has expired, request a new one")
    except BadSignature:
        raise HTTPException(status_code=400, detail="this verification link is invalid")

    user = local_store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="account no longer exists")
    local_store.mark_user_verified(user_id)
    return {"ok": True, "email": user["email"]}


@router.post("/resend-verification")
def resend_verification(current_user_id: str = Depends(require_auth)):
    user = local_store.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="account no longer exists")
    if user["email_verified"]:
        return {"ok": True, "already_verified": True}
    if not email_sender.smtp_configured():
        raise HTTPException(status_code=400, detail="this server has no email provider configured")
    _send_verification_email(user["id"], user["email"])
    return {"ok": True, "already_verified": False}
