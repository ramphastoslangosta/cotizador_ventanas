"""Authentication Dependencies

Extracted from main.py as part of TASK-20250929-001
Contains authentication and authorization dependencies for routes
"""

from typing import Optional
from fastapi import Request, Depends
from sqlalchemy.orm import Session

from database import get_db, User, DatabaseUserService
from passlib.context import CryptContext
from error_handling.logging_config import get_logger
from error_handling.error_manager import create_auth_error

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract authentication token from request
    Supports both Bearer token (API) and cookie-based (web) authentication
    """
    # Try Authorization header first (API authentication)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    # Fall back to cookie (web authentication)
    return request.cookies.get("access_token")


async def get_current_user_flexible(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Get current user with comprehensive error handling
    Supports both cookie-based (web) and bearer token (API) authentication

    This is the main authentication dependency used across the application
    """
    logger = get_logger()

    try:
        token = get_token_from_request(request)

        if not token:
            raise create_auth_error("TOKEN_EXPIRED")

        # Use database service with error handling
        user_service = DatabaseUserService(db)
        session = user_service.get_session_by_token(token)

        if not session:
            logger.security_event("invalid_token", "Token validation failed",
                                token_prefix=token[:8] if token else "none",
                                ip_address=request.client.host if request.client else "unknown")
            raise create_auth_error("TOKEN_EXPIRED")

        user = user_service.get_user_by_id(session.user_id)
        if not user:
            logger.security_event("user_not_found", "User not found for valid session",
                                user_id=session.user_id)
            raise create_auth_error("UNAUTHORIZED_ACCESS")

        # Store user ID in request state for logging
        # CRITICAL FIX: Always store user_id as string to prevent UUID serialization errors
        request.state.user_id = str(user.id)

        return user

    except Exception as e:
        logger = get_logger()
        logger.error(f"Authentication error: {str(e)}")
        raise create_auth_error("UNAUTHORIZED_ACCESS")


async def get_current_user_from_cookie(request: Request, db: Session) -> Optional[User]:
    """
    Get current user from cookie (web authentication only)
    Returns None if not authenticated (used for optional authentication)
    """
    token = request.cookies.get("access_token")
    if not token:
        return None

    user_service = DatabaseUserService(db)
    session = user_service.get_session_by_token(token)

    if not session:
        return None

    return user_service.get_user_by_id(session.user_id)