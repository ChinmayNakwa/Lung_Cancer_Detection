import hmac
import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import ADMIN_USERNAME, ADMIN_PASSWORD, JWT_SECRET, JWT_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


def _auth_configured():
    return bool(ADMIN_USERNAME and ADMIN_PASSWORD and JWT_SECRET)


def verify_credentials(username: str, password: str) -> bool:
    """Check login credentials against the configured admin account."""
    if not _auth_configured():
        logger.error("Auth is not configured: set ADMIN_USERNAME, ADMIN_PASSWORD and JWT_SECRET")
        return False
    # Constant-time comparisons to avoid leaking credentials via timing
    user_ok = hmac.compare_digest(username.encode(), ADMIN_USERNAME.encode())
    password_ok = hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode())
    return user_ok and password_ok


def create_access_token(username: str):
    """Return (token, expiry datetime) for the given user."""
    expires = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token = jwt.encode({"sub": username, "exp": expires}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """FastAPI dependency: reject requests without a valid admin token."""
    unauthorized = HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not _auth_configured():
        raise unauthorized
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        raise unauthorized
    return payload["sub"]
