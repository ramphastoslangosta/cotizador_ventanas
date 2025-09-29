"""Authentication Routes

Extracted from main.py as part of TASK-20250929-001
Handles user authentication (login, register, logout) for both web and API
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db, User, DatabaseUserService
from app.dependencies.auth import (
    hash_password,
    verify_password,
    get_current_user_flexible
)
from config import settings
from security.input_validation import SecureUserInput

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router
router = APIRouter()


# === PYDANTIC MODELS FOR API ===
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# === WEB PAGE ROUTES (HTML) ===
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Iniciar Sesión"
    })


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display registration page"""
    return templates.TemplateResponse("register.html", {
        "request": request,
        "title": "Crear Cuenta"
    })


# === WEB FORM ROUTES (POST) ===
@router.post("/web/login")
async def web_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle web login form submission
    Creates session and sets cookie on success
    """
    user_service = DatabaseUserService(db)
    user = user_service.get_user_by_email(email)

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Iniciar Sesión",
            "error": "Email o contraseña incorrectos"
        })

    # Create session
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours)
    user_service.create_session(user.id, token, expires_at)

    # Create response with cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.session_expire_hours * 3600,
        httponly=True,  # Prevent XSS access
        secure=False,   # Set to True in production with HTTPS
        samesite='lax'  # CSRF protection while allowing some cross-site usage
    )

    return response


@router.post("/web/register")
async def web_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle web registration form submission
    Creates user, session, and sets cookie on success
    """
    user_service = DatabaseUserService(db)

    try:
        # Validate input using secure validation
        user_input = SecureUserInput(
            email=email,
            full_name=full_name,
            password=password
        )

        # Use validated data
        validated_email = user_input.email
        validated_name = user_input.full_name
        validated_password = user_input.password

    except ValueError as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "title": "Crear Cuenta",
            "error": str(e)
        })

    # Check if user already exists
    existing_user = user_service.get_user_by_email(validated_email)
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "title": "Crear Cuenta",
            "error": "El email ya está registrado"
        })

    # Create user with validated data
    hashed_password = hash_password(validated_password)
    new_user = user_service.create_user(validated_email, hashed_password, validated_name)

    # Auto-login
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours)
    user_service.create_session(new_user.id, token, expires_at)

    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.session_expire_hours * 3600,
        httponly=True,  # Prevent XSS access
        secure=False,   # Set to True in production with HTTPS
        samesite='lax'  # CSRF protection while allowing some cross-site usage
    )

    return response


@router.post("/web/logout")
async def web_logout(request: Request, db: Session = Depends(get_db)):
    """
    Handle web logout
    Invalidates session and clears cookie
    """
    token = request.cookies.get("access_token")
    if token:
        user_service = DatabaseUserService(db)
        user_service.invalidate_session(token)

    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# === API ROUTES (JSON) ===
@router.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    API endpoint for user registration
    Returns user data on success
    """
    user_service = DatabaseUserService(db)

    try:
        # Validate input using secure validation
        validated_input = SecureUserInput(
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

    if user_service.get_user_by_email(validated_input.email):
        raise HTTPException(
            status_code=400,
            detail=f"El email {validated_input.email} ya está registrado"
        )

    hashed_password = hash_password(validated_input.password)
    new_user = user_service.create_user(
        validated_input.email,
        hashed_password,
        validated_input.full_name
    )

    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name
    )


@router.post("/auth/login", response_model=Token)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    API endpoint for user login
    Returns access token on success
    """
    user_service = DatabaseUserService(db)
    user = user_service.get_user_by_email(login_data.email)

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours)
    user_service.create_session(user.id, token, expires_at)

    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name
    )
    return Token(access_token=token, token_type="bearer", user=user_response)


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user_flexible)
):
    """
    API endpoint to get current user information
    Requires authentication
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name
    )