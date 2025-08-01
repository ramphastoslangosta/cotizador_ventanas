#!/usr/bin/env python3
"""
FastAPI Window Quotation System - No Database Mode
Runs the application with in-memory data for testing without database setup.
"""

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Optional, List
import secrets
import uuid

# Import models (these should work without database)
from models.quote_models import (
    WindowType, AluminumLine, GlassType,
    Client, QuoteRequest, WindowItem, WindowCalculation, QuoteCalculation
)

# === CONFIGURATION ===
app = FastAPI(
    title="Sistema de Cotización de Ventanas - No Database Mode",
    description="Sistema de prueba sin base de datos",
    version="5.0.0-test"
)

# Configure templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === IN-MEMORY DATA STORAGE ===
USERS_DB = {
    "demo@test.com": {
        "id": "user_123",
        "email": "demo@test.com",
        "full_name": "Usuario Demo",
        "hashed_password": "$2b$12$demo_password_hash"  # In real app, this would be properly hashed
    }
}

SESSIONS_DB = {}
QUOTES_DB = []

# === MODELS ===
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

# === MOCK FUNCTIONS ===
def mock_get_current_user_from_cookie(request: Request):
    """Mock user authentication"""
    token = request.cookies.get("access_token")
    if token and token in SESSIONS_DB:
        user_email = SESSIONS_DB[token]["email"]
        return USERS_DB.get(user_email)
    return None

def mock_calculate_quote(quote_request: QuoteRequest) -> QuoteCalculation:
    """Mock quote calculation with sample data"""
    calculated_items = []
    total_cost = Decimal('0')
    
    for item in quote_request.items:
        # Mock calculation
        area_m2 = (item.width_cm / 100) * (item.height_cm / 100)
        perimeter_m = 2 * ((item.width_cm / 100) + (item.height_cm / 100))
        
        # Mock costs
        profiles_cost = area_m2 * Decimal('150') * item.quantity
        glass_cost = area_m2 * Decimal('80') * item.quantity
        hardware_cost = Decimal('50') * item.quantity
        consumables_cost = Decimal('25') * item.quantity
        labor_cost = area_m2 * Decimal('100') * item.quantity
        
        subtotal = profiles_cost + glass_cost + hardware_cost + consumables_cost + labor_cost
        total_cost += subtotal
        
        window_calc = WindowCalculation(
            product_bom_id=item.product_bom_id,
            product_bom_name=f"Ventana Mock #{item.product_bom_id}",
            window_type=WindowType.CORREDIZA,
            aluminum_line=AluminumLine.SERIE_3,
            selected_glass_type=item.selected_glass_type,
            width_cm=item.width_cm,
            height_cm=item.height_cm,
            quantity=item.quantity,
            area_m2=area_m2,
            perimeter_m=perimeter_m,
            total_profiles_cost=profiles_cost,
            total_glass_cost=glass_cost,
            total_hardware_cost=hardware_cost,
            total_consumables_cost=consumables_cost,
            labor_cost=labor_cost,
            subtotal=subtotal
        )
        calculated_items.append(window_calc)
    
    # Mock overhead calculations
    materials_subtotal = total_cost * Decimal('0.7')
    labor_subtotal = total_cost * Decimal('0.3')
    profit_amount = total_cost * Decimal('0.25')
    indirect_costs_amount = total_cost * Decimal('0.15')
    tax_amount = total_cost * Decimal('0.16')
    total_final = total_cost + profit_amount + indirect_costs_amount + tax_amount
    
    return QuoteCalculation(
        client=quote_request.client,
        items=calculated_items,
        materials_subtotal=materials_subtotal,
        labor_subtotal=labor_subtotal,
        subtotal_before_overhead=total_cost,
        profit_amount=profit_amount,
        indirect_costs_amount=indirect_costs_amount,
        subtotal_with_overhead=total_cost + profit_amount + indirect_costs_amount,
        tax_amount=tax_amount,
        total_final=total_final,
        calculated_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        notes=quote_request.notes
    )

# === ROUTES ===
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    user = mock_get_current_user_from_cookie(request)
    if user:
        return RedirectResponse(url="/dashboard")
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Sistema de Cotización de Ventanas - Modo Test"
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Iniciar Sesión - Modo Test"
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    user = mock_get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard - Modo Test",
        "user": user,
        "recent_quotes": QUOTES_DB[-5:] if QUOTES_DB else [],
        "total_quotes": len(QUOTES_DB)
    })

@app.post("/web/login")
async def web_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    # Mock login - in real app, verify password hash
    if email == "demo@test.com" and password == "demo123":
        token = secrets.token_urlsafe(32)
        SESSIONS_DB[token] = {"email": email, "expires": datetime.now() + timedelta(hours=2)}
        
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="access_token",
            value=token,
            max_age=7200,  # 2 hours
            httponly=True,
            secure=False
        )
        return response
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Iniciar Sesión",
        "error": "Email o contraseña incorrectos. Use: demo@test.com / demo123"
    })

@app.post("/web/logout")
async def web_logout(request: Request):
    token = request.cookies.get("access_token")
    if token and token in SESSIONS_DB:
        del SESSIONS_DB[token]
    
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@app.get("/quotes/new", response_class=HTMLResponse)
async def new_quote_page(request: Request):
    user = mock_get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    
    # Mock data for frontend
    mock_products = [
        {
            "id": 1,
            "name": "Ventana Corrediza 2 Hojas",
            "window_type": "corrediza",
            "aluminum_line": "nacional_serie_3",
            "min_width_cm": 80,
            "max_width_cm": 300,
            "min_height_cm": 60,
            "max_height_cm": 250
        },
        {
            "id": 2,
            "name": "Ventana Fija",
            "window_type": "fija",
            "aluminum_line": "nacional_serie_3",
            "min_width_cm": 50,
            "max_width_cm": 200,
            "min_height_cm": 50,
            "max_height_cm": 200
        }
    ]
    
    window_types_display = [
        {"value": wt.value, "label": wt.value.replace('_', ' ').title()} for wt in WindowType
    ]
    aluminum_lines_display = [
        {"value": al.value, "label": al.value.replace('_', ' ').title()} for al in AluminumLine
    ]
    glass_types_display = [
        {"value": gt.value, "label": gt.value.replace('_', ' ').title()} for gt in GlassType
    ]

    return templates.TemplateResponse("new_quote.html", {
        "request": request,
        "title": "Nueva Cotización - Modo Test",
        "user": user,
        "app_materials": [],
        "app_products": mock_products,
        "window_types": window_types_display,
        "aluminum_lines": aluminum_lines_display,
        "glass_types": glass_types_display,
        "business_overhead": {
            "profit_margin": 0.25,
            "indirect_costs": 0.15,
            "tax_rate": 0.16
        }
    })

@app.post("/quotes/calculate", response_model=QuoteCalculation)
async def calculate_quote_main(quote_request: QuoteRequest, request: Request):
    user = mock_get_current_user_from_cookie(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = mock_calculate_quote(quote_request)
        
        # Save to mock database
        quote_data = {
            "id": len(QUOTES_DB) + 1,
            "user_email": user["email"],
            "client_name": result.client.name,
            "total_final": float(result.total_final),
            "created_at": result.calculated_at,
            "quote_data": result.model_dump()
        }
        QUOTES_DB.append(quote_data)
        
        result.quote_id = quote_data["id"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el cálculo: {str(e)}")

@app.get("/quotes", response_class=HTMLResponse)
async def quotes_list_page(request: Request):
    user = mock_get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    
    # Filter quotes for current user
    user_quotes = [q for q in QUOTES_DB if q.get("user_email") == user["email"]]
    
    return templates.TemplateResponse("quotes_list.html", {
        "request": request,
        "title": "Todas las Cotizaciones - Modo Test",
        "user": user,
        "quotes": user_quotes,
        "today": datetime.now().date()
    })

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "no_database",
        "users_count": len(USERS_DB),
        "active_sessions": len(SESSIONS_DB),
        "quotes_count": len(QUOTES_DB)
    }

@app.get("/api/demo-data")
async def get_demo_data():
    """API endpoint to show available demo data"""
    return {
        "demo_login": {
            "email": "demo@test.com",
            "password": "demo123"
        },
        "available_features": [
            "Login/logout",
            "Dashboard",
            "New quote creation",
            "Quote calculation (mock)",
            "Quote listing"
        ],
        "note": "This is running in no-database mode with mock data"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Sistema de Cotización de Ventanas - MODO SIN BASE DE DATOS")
    print("🌐 Web: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📊 Demo Data Info: http://localhost:8000/api/demo-data")
    print("🔐 Demo Login: demo@test.com / demo123")
    print("✨ Funcionalidades disponibles:")
    print("   🔐 Autenticación simulada")
    print("   📊 Dashboard básico")
    print("   📝 Creación de cotizaciones")
    print("   🧮 Cálculos simulados")
    print("   📋 Lista de cotizaciones")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)