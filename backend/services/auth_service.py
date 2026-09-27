"""
services/auth_service.py — JWT Authentication & Password Hashing
=================================================================
Provides:
  - Password hashing (bcrypt via passlib)
  - JWT token creation/verification (python-jose)
  - FastAPI dependency for extracting current user from Authorization header
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

logger = logging.getLogger("cad_workbench.auth")

# ─── Configuration ──────────────────────────────────────────────────────────

# In production, set JWT_SECRET_KEY in .env (long random string)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production-please")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h default
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))

import bcrypt

# ─── Daily Generation Quota (free tier) ─────────────────────────────────────

DAILY_GENERATION_QUOTA = 50


async def check_and_bump_quota(user, db=None, cost: int = 1):
    """Enforce free-tier daily quota of 50 generations+modifies per user per UTC day.

    Resets ``generations_today`` to 0 when ``last_generation_date`` != today
    (UTC), raises HTTPException 429 when over limit, else increments + commits.
    Re-fetches the user in the caller's ``db`` session so updates persist even
    when ``user`` was loaded in a different request-scoped session.
    """
    from datetime import timezone as _tz

    today = datetime.now(_tz.utc).date().isoformat()
    target = user
    if db is not None:
        try:
            from models.user import User as _User

            result = await db.execute(select(_User).where(_User.id == user.id))
            db_user = result.scalar_one_or_none()
            if db_user is not None:
                target = db_user
        except Exception:
            target = user
    last = getattr(target, "last_generation_date", None)
    count = getattr(target, "generations_today", 0) or 0
    if last != today:
        count = 0
    if count >= DAILY_GENERATION_QUOTA:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Daily generation quota exceeded (50/day on free tier)",
                "error_code": "quota_exceeded",
                "reset": "midnight UTC",
            },
        )
    target.generations_today = count + int(cost or 0)
    target.last_generation_date = today
    if target is not user:
        try:
            user.generations_today = target.generations_today
            user.last_generation_date = target.last_generation_date
        except Exception:
            pass
    if db is not None:
        try:
            await db.commit()
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
    return target


# ─── Password Hashing ──────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plaintext password using native bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


# ─── JWT Token Management ──────────────────────────────────────────────────

def create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, version: int = 0) -> str:
    """Create a long-lived JWT refresh token with rotation version."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "ver": int(version or 0),
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


# ─── FastAPI Security Dependencies ─────────────────────────────────────────

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency: extracts and validates JWT from Authorization header.
    Returns the User ORM object or raises 401.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type.")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload.")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Import here to avoid circular import
    from models.user import User
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or deactivated.")

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Like get_current_user but returns None instead of raising 401.
    Used for endpoints that work both authenticated and anonymously.
    """
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    from models.user import User
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()
