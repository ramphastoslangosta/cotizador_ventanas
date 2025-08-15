# main.py - Sistema de Cotización de Ventanas v5.0.0-RESILIENT
# Milestone 1.2: Error Handling & Resilience - Comprehensive error handling integrated

from fastapi import FastAPI, HTTPException, Depends, status, Request, Form, Response, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, List
from enum import Enum
import secrets
import uuid
import os
import shutil
import time
import math
import json

# Importaciones de base de datos
from sqlalchemy.orm import Session
from database import get_db, User, UserSession, Quote, Company, Color, MaterialColor, WorkOrder
from database import DatabaseUserService, DatabaseQuoteService, DatabaseCompanyService, DatabaseColorService, DatabaseMaterialService, DatabaseWorkOrderService
from services.product_bom_service_db import ProductBOMServiceDB, initialize_sample_data
from services.material_csv_service import MaterialCSVService
from services.product_bom_csv_service import ProductBOMCSVService
from security.formula_evaluator import formula_evaluator
from security.middleware import SecurityMiddleware, SecureCookieMiddleware
from security.input_validation import input_validator
from config import settings

# Importar para hashing de contraseñas
from passlib.context import CryptContext

# Importar para generación de PDFs
from services.pdf_service import PDFQuoteService

# Importar modelos de empresa
from models.company_models import CompanyResponse, CompanyCreate, CompanyUpdate

# Importar modelos de colores
from models.color_models import ColorResponse, ColorCreate, ColorUpdate, MaterialColorResponse, MaterialColorCreate, MaterialColorUpdate

# Importar modelos de work orders - QTO-001
from models.work_order_models import (
    WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse, WorkOrderListResponse, 
    WorkOrderStatusUpdate, WorkOrderStatus, WorkOrderPriority
)

# === MILESTONE 1.2: ERROR HANDLING & RESILIENCE IMPORTS ===
from error_handling.error_manager import (
    error_manager, BaseApplicationError, DatabaseError, ValidationError, 
    AuthenticationError, BusinessLogicError, SecurityError, ErrorResponse, ErrorDetail,
    create_database_error, create_validation_error, create_auth_error, create_business_error
)
from error_handling.logging_config import initialize_logging, get_logger
from error_handling.database_resilience import (
    initialize_database_resilience, get_resilient_db_session, execute_with_fallback,
    fallback_provider
)
from error_handling.health_checks import router as health_router
from error_handling.error_monitoring import error_monitor, record_error_for_monitoring

# === EVENTOS DE APLICACIÓN ===
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejador de eventos de ciclo de vida de la aplicación con error handling robusto"""
    
    # === STARTUP - MILESTONE 1.2: Error Handling & Resilience ===
    logger = None
    
    try:
        # Initialize logging system first
        logger = initialize_logging()
        logger.info("🚀 Starting Window Quotation System v5.0.0-RESILIENT")
        
        # Initialize database resilience system
        from config import settings
        db_manager = initialize_database_resilience(settings.database_url)
        logger.info("✅ Database resilience system initialized")
        
        # Initialize sample data with error handling
        from database import SessionLocal
        from services.product_bom_service_db import initialize_sample_data
        
        try:
            with get_resilient_db_session() as db:
                logger.info("🔄 Initializing sample data with resilient connection...")
                initialize_sample_data(db)
                logger.info("✅ Sample data initialization completed successfully")
                
        except DatabaseError as e:
            logger.error(f"Database initialization failed: {e.message_en}")
            # Try with fallback data if needed
            logger.info("Attempting to continue with fallback configuration...")
            
        except Exception as e:
            logger.critical(f"Critical error during sample data initialization: {str(e)}")
            # Log but don't crash the application
        
        # Log successful startup
        logger.info("✅ Application startup completed successfully")
        logger.audit_event("system_startup", "application", result="success")
        
    except Exception as e:
        if logger:
            logger.critical(f"❌ Critical startup error: {str(e)}")
        else:
            print(f"❌ Critical startup error (logger not available): {str(e)}")
        
        # Don't crash the application - log and continue with degraded functionality
        if logger:
            logger.error("Application starting with degraded functionality due to startup errors")
    
    yield
    
    # === SHUTDOWN ===
    try:
        if logger:
            logger.info("🔄 Gracefully shutting down application...")
            logger.audit_event("system_shutdown", "application", result="success")
        else:
            print("🔄 Shutting down application...")
            
    except Exception as e:
        if logger:
            logger.error(f"Error during shutdown: {str(e)}")
        else:
            print(f"Error during shutdown: {str(e)}")

# === CONFIGURACIÓN ===
app = FastAPI(
    title="Sistema de Cotización de Ventanas - Con Base de Datos",
    description="Sistema completo con API + Frontend + PostgreSQL + Error Handling & Resilience",
    version="5.0.0-RESILIENT",
    lifespan=lifespan
)

# Configurar templates y archivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# === MILESTONE 1.2: Add Health Check Router ===
app.include_router(health_router, prefix="/api")

# === MILESTONE 1.2: Global Error Handler ===
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware with monitoring integration"""
    
    logger = get_logger()
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    # Extract request info for logging
    method = request.method
    url = str(request.url)
    user_agent = request.headers.get("user-agent", "unknown")
    ip_address = request.client.host if request.client else "unknown"
    
    # Add request ID to request state for downstream use
    request.state.request_id = request_id
    
    try:
        # Log request start
        logger.info(
            f"Request started: {method} {url}",
            request_id=request_id,
            method=method,
            endpoint=url,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Log successful response
        logger.info(
            f"Request completed: {method} {url} - {response.status_code} ({response_time:.2f}ms)",
            request_id=request_id,
            method=method,
            endpoint=url,
            status_code=response.status_code,
            response_time=response_time,
            ip_address=ip_address
        )
        
        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except BaseApplicationError as e:
        # Handle our custom application errors
        response_time = (time.time() - start_time) * 1000
        
        # Log the error
        logger.error(
            f"Application error: {method} {url} - {e.code}",
            request_id=request_id,
            method=method,
            endpoint=url,
            error_code=e.code,
            error_category=e.category,
            error_severity=e.severity,
            response_time=response_time,
            ip_address=ip_address
        )
        
        # Record for monitoring with safe serialization
        user_id = getattr(request.state, 'user_id', None)
        # Convert UUID to string for JSON serialization
        user_id_str = str(user_id) if user_id is not None else None
        
        # Safely serialize error details to prevent UUID serialization errors
        safe_error_detail = safe_serialize_for_json(ErrorDetail(
            code=e.code,
            category=e.category,
            severity=e.severity,
            message_es=e.message_es,
            message_en=e.message_en,
            technical_details=safe_serialize_for_json(e.technical_details),
            user_action=e.user_action,
            timestamp=e.timestamp,
            request_id=request_id
        ))
        
        # Temporarily disable error monitoring to isolate UUID serialization issue
        # try:
        #     record_error_for_monitoring(
        #         error_detail=safe_error_detail,
        #         endpoint=url,
        #         user_id=user_id_str,
        #         ip_address=ip_address
        #     )
        # except Exception as monitor_error:
        #     # If error monitoring fails, just log it without breaking the app
        #     logger.warning(f"Error monitoring failed: {str(monitor_error)}")
        
        # Return HTTP error response
        raise error_manager.create_http_exception(e)
        
    except HTTPException as e:
        # Handle FastAPI HTTP exceptions
        response_time = (time.time() - start_time) * 1000
        
        logger.warning(
            f"HTTP exception: {method} {url} - {e.status_code}",
            request_id=request_id,
            method=method,
            endpoint=url,
            status_code=e.status_code,
            error_detail=str(e.detail),
            response_time=response_time,
            ip_address=ip_address
        )
        
        # Re-raise HTTP exceptions
        raise e
        
    except Exception as e:
        # Handle unexpected errors
        response_time = (time.time() - start_time) * 1000
        
        # Create error detail for unexpected errors
        error_detail = error_manager.handle_error(
            error=e,
            request_id=request_id,
            context={
                "method": method,
                "url": url,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "response_time": response_time
            }
        )
        
        # Log critical error
        logger.critical(
            f"Unexpected error: {method} {url} - {type(e).__name__}",
            request_id=request_id,
            method=method,
            endpoint=url,
            error_type=type(e).__name__,
            error_message=str(e),
            response_time=response_time,
            ip_address=ip_address
        )
        
        # Record for monitoring with safe serialization
        user_id = getattr(request.state, 'user_id', None)
        # Convert UUID to string for JSON serialization
        user_id_str = str(user_id) if user_id is not None else None
        
        # Temporarily disable error monitoring to isolate UUID serialization issue
        # try:
        #     # Safely serialize error details to prevent UUID serialization errors
        #     safe_error_detail = safe_serialize_for_json(error_detail.error)
        #     record_error_for_monitoring(
        #         error_detail=safe_error_detail,
        #         endpoint=url,
        #         user_id=user_id_str,
        #         ip_address=ip_address
        #     )
        # except Exception as monitor_error:
        #     # If error monitoring fails, just log it without breaking the app
        #     logger.warning(f"Error monitoring failed: {str(monitor_error)}")
        
        # Return internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Ha ocurrido un error interno. Por favor, inténtelo de nuevo.",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        )

# Add security middleware (order matters - add in reverse order of execution)
app.add_middleware(SecureCookieMiddleware, secure=False)  # Set secure=True in production with HTTPS
app.add_middleware(SecurityMiddleware, rate_limit_requests=100, rate_limit_window=60)

# Secure CORS configuration - restrict origins in production
allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",  # For development frontend
    # Add your production domains here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Restricted origins for security
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods only
    allow_headers=["Accept", "Accept-Language", "Content-Language", "Content-Type", "Authorization", "X-CSRF-Token"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# === ENUMS ===
from models.quote_models import WindowType, AluminumLine, GlassType
from models.product_bom_models import AppMaterial, AppProduct, BOMItem, MaterialUnit, MaterialType

# === MODELOS ===
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

# Importar modelos de quote_models.py
from models.quote_models import (
    Client,
    QuoteRequest,
    WindowItem,
    WindowCalculation,
    QuoteCalculation,
)

# === FUNCIONES AUXILIARES ===
def safe_serialize_for_json(obj):
    """
    Recursively convert UUID objects to strings for JSON serialization
    This prevents UUID serialization errors in error monitoring and logging
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: safe_serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [safe_serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Handle objects with attributes
        result = {}
        for k, v in obj.__dict__.items():
            if not k.startswith('_'):  # Skip private attributes
                result[k] = safe_serialize_for_json(v)
        return result
    else:
        return obj

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_token_from_request(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return request.cookies.get("access_token")

async def get_current_user_flexible(request: Request, db: Session = Depends(get_db)):
    """Get current user with comprehensive error handling"""
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
        request.state.user_id = user.id
        
        return user
        
    except (DatabaseError, AuthenticationError):
        # Re-raise our custom errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error in authentication: {str(e)}")
        raise create_auth_error("UNAUTHORIZED_ACCESS")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from Bearer token with error handling"""
    logger = get_logger()
    
    try:
        token = credentials.credentials
        
        user_service = DatabaseUserService(db)
        session = user_service.get_session_by_token(token)
        
        if not session:
            logger.security_event("invalid_bearer_token", "Bearer token validation failed",
                                token_prefix=token[:8] if token else "none")
            raise create_auth_error("TOKEN_EXPIRED")
        
        user = user_service.get_user_by_id(session.user_id)
        if not user:
            logger.security_event("user_not_found", "User not found for bearer token session",
                                user_id=session.user_id)
            raise create_auth_error("UNAUTHORIZED_ACCESS")
        return user
        
    except (DatabaseError, AuthenticationError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Bearer token authentication: {str(e)}")
        raise create_auth_error("UNAUTHORIZED_ACCESS")

async def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Get current user from cookie - returns None if no valid session"""
    logger = get_logger()
    
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None
        
        user_service = DatabaseUserService(db)
        session = user_service.get_session_by_token(token)
        
        if not session:
            return None
        
        user = user_service.get_user_by_id(session.user_id)
        if user and request.state:
            request.state.user_id = user.id
            
        return user
        
    except Exception as e:
        logger.warning(f"Error getting user from cookie: {str(e)}")
        return None

def round_currency(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def round_measurement(measurement: Decimal) -> Decimal:
    return measurement.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

# === FUNCIONES DE CÁLCULO (ADAPTADAS PARA BD) ===
def calculate_window_item_from_bom(item: WindowItem, product_bom_service: ProductBOMServiceDB, global_labor_rate_per_m2_override: Optional[Decimal] = None) -> WindowCalculation:
    """Calcula el costo de un ítem de ventana utilizando su BOM dinámico con base de datos"""
    
    product = product_bom_service.get_product(item.product_bom_id)
    if not product:
        raise ValueError(f"Producto BOM con ID {item.product_bom_id} no encontrado.")

    # Validar dimensiones contra los rangos del producto
    if not (product.min_width_cm <= item.width_cm <= product.max_width_cm and
            product.min_height_cm <= item.height_cm <= product.max_height_cm):
        raise ValueError(f"Dimensiones ({item.width_cm}x{item.height_cm}cm) fuera del rango permitido para el producto '{product.name}' ({product.min_width_cm}-{product.max_width_cm}cm x {product.min_height_cm}-{product.max_height_cm}cm).")

    # Calcular medidas base para fórmulas
    width_m = item.width_cm / Decimal('100')
    height_m = item.height_cm / Decimal('100')
    area_m2 = width_m * height_m
    perimeter_m = 2 * (width_m + height_m)

    # Variables disponibles para las fórmulas
    formula_vars = {
        'width_m': width_m,
        'height_m': height_m,
        'width_cm': item.width_cm,
        'height_cm': item.height_cm,
        'quantity': item.quantity,
        'area_m2': area_m2,
        'perimeter_m': perimeter_m,
    }

    # Inicializar costos detallados por tipo de material
    total_profiles_cost = Decimal('0')
    total_glass_cost = Decimal('0')
    total_hardware_cost = Decimal('0')
    total_consumables_cost = Decimal('0')

    # Calcular costos de materiales del BOM
    for bom_item in product.bom:
        material = product_bom_service.get_material(bom_item.material_id)
        if not material:
            raise ValueError(f"Material con ID {bom_item.material_id} referenciado en BOM de '{product.name}' no encontrado.")

        try:
            # Evaluar la fórmula de forma segura para obtener la cantidad "neta" para UNA ventana
            quantity_net_for_one_window = formula_evaluator.evaluate_formula(bom_item.quantity_formula, formula_vars)
            if quantity_net_for_one_window < 0:
                quantity_net_for_one_window = Decimal('0')
        except Exception as e:
            raise ValueError(f"Error al evaluar fórmula '{bom_item.quantity_formula}' para material '{material.name}': {e}")

        # Aplicar factor de desperdicio
        quantity_with_waste_for_one_window = quantity_net_for_one_window * bom_item.waste_factor

        # Ajustar por unidad de venta si es un perfil
        final_quantity_to_cost = quantity_with_waste_for_one_window
        if material.selling_unit_length_m and material.unit == MaterialUnit.ML:
            num_selling_units = math.ceil(quantity_with_waste_for_one_window / material.selling_unit_length_m)
            final_quantity_to_cost = Decimal(str(num_selling_units)) * material.selling_unit_length_m

        # Determinar el precio por unidad (considerando color para perfiles)
        price_per_unit = material.cost_per_unit
        if bom_item.material_type == MaterialType.PERFIL and item.selected_profile_color:
            # Buscar el precio del color específico para este material
            color_service = DatabaseColorService(product_bom_service.db)
            color_price = color_service.get_material_color_price(material.id, item.selected_profile_color)
            if color_price:
                price_per_unit = color_price

        # Costo de este material para UNA ventana del tipo AppProduct
        cost_for_this_material_per_product_unit = final_quantity_to_cost * price_per_unit

        # Sumar al costo total de la categoría, multiplicado por la cantidad de ventanas en el item de cotización
        total_cost_for_item_quantity = cost_for_this_material_per_product_unit * item.quantity

        if bom_item.material_type == MaterialType.PERFIL:
            total_profiles_cost += total_cost_for_item_quantity
        elif bom_item.material_type == MaterialType.HERRAJE:
            total_hardware_cost += total_cost_for_item_quantity
        elif bom_item.material_type == MaterialType.CONSUMIBLE:
            total_consumables_cost += total_cost_for_item_quantity

    # Calcular costo del vidrio
    glass_cost_per_m2 = product_bom_service.get_glass_cost_per_m2(item.selected_glass_type)
    glass_waste_factor = Decimal('1.05') 
    total_glass_cost = area_m2 * glass_cost_per_m2 * glass_waste_factor * item.quantity
    total_glass_cost = round_currency(total_glass_cost)

    # Calcular costo de mano de obra
    if global_labor_rate_per_m2_override is not None:
        labor_cost = area_m2 * global_labor_rate_per_m2_override * item.quantity
    else:
        labor_data = product_bom_service.get_labor_cost_data(product.window_type)
        if not labor_data:
             raise ValueError(f"Costo de mano de obra no encontrado para tipo de ventana: {product.window_type}")
        
        labor_cost_per_m2_effective = labor_data.cost_per_m2 * labor_data.complexity_factor
        labor_cost = area_m2 * labor_cost_per_m2_effective * item.quantity
    labor_cost = round_currency(labor_cost)

    # Subtotal de este ítem
    subtotal = total_profiles_cost + total_glass_cost + total_hardware_cost + total_consumables_cost + labor_cost
    subtotal = round_currency(subtotal)

    return WindowCalculation(
        product_bom_id=product.id,
        product_bom_name=product.name,
        window_type=product.window_type,
        aluminum_line=product.aluminum_line,
        selected_glass_type=item.selected_glass_type,
        width_cm=item.width_cm,
        height_cm=item.height_cm,
        quantity=item.quantity,
        area_m2=round_measurement(area_m2),
        perimeter_m=round_measurement(perimeter_m),
        total_profiles_cost=round_currency(total_profiles_cost),
        total_glass_cost=round_currency(total_glass_cost),
        total_hardware_cost=round_currency(total_hardware_cost),
        total_consumables_cost=round_currency(total_consumables_cost),
        labor_cost=labor_cost,
        subtotal=subtotal,
        # Campos de compatibilidad
        aluminum_length_needed=Decimal('0'),
        aluminum_cost=total_profiles_cost + total_hardware_cost + total_consumables_cost,
        glass_area_needed=Decimal('0'),
        hardware_cost=total_hardware_cost
    )

def calculate_complete_quote(quote_request: QuoteRequest, db: Session) -> QuoteCalculation:
    """Calcula cotización completa usando base de datos"""
    
    product_bom_service = ProductBOMServiceDB(db)
    
    calculated_items = []
    materials_subtotal = Decimal('0')
    labor_subtotal = Decimal('0')

    # Usar valores de QuoteRequest si se proporcionan, de lo contrario usar defaults
    current_profit_margin = quote_request.profit_margin if quote_request.profit_margin is not None else Decimal(str(settings.default_profit_margin))
    current_indirect_costs_rate = quote_request.indirect_costs_rate if quote_request.indirect_costs_rate is not None else Decimal(str(settings.default_indirect_costs))
    current_tax_rate = quote_request.tax_rate if quote_request.tax_rate is not None else Decimal(str(settings.default_tax_rate))
    current_labor_rate_per_m2_override = quote_request.labor_rate_per_m2_override

    for item in quote_request.items:
        window_calc = calculate_window_item_from_bom(item, product_bom_service, global_labor_rate_per_m2_override=current_labor_rate_per_m2_override)
        calculated_items.append(window_calc)
        
        materials_subtotal += (window_calc.total_profiles_cost + 
                               window_calc.total_glass_cost + 
                               window_calc.total_hardware_cost + 
                               window_calc.total_consumables_cost)
        labor_subtotal += window_calc.labor_cost
    
    subtotal_before_overhead = materials_subtotal + labor_subtotal
    
    profit_amount = subtotal_before_overhead * current_profit_margin
    indirect_costs_amount = subtotal_before_overhead * current_indirect_costs_rate
    subtotal_with_overhead = subtotal_before_overhead + profit_amount + indirect_costs_amount
    
    tax_amount = subtotal_with_overhead * current_tax_rate
    total_final = subtotal_with_overhead + tax_amount
    
    result = QuoteCalculation(
        client=quote_request.client,
        items=calculated_items,
        materials_subtotal=round_currency(materials_subtotal),
        labor_subtotal=round_currency(labor_subtotal),
        subtotal_before_overhead=round_currency(subtotal_before_overhead),
        profit_amount=round_currency(profit_amount),
        indirect_costs_amount=round_currency(indirect_costs_amount),
        subtotal_with_overhead=round_currency(subtotal_with_overhead),
        tax_amount=round_currency(tax_amount),
        total_final=round_currency(total_final),
        calculated_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        notes=quote_request.notes
    )
    
    return result


# === RUTAS WEB ===
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/dashboard")
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Sistema de Cotización de Ventanas"
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Iniciar Sesión"
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "title": "Crear Cuenta"
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    try:
        user = await get_current_user_from_cookie(request, db)
        if not user:
            return RedirectResponse(url="/login")
        
        # Store user ID as string for error monitoring
        request.state.user_id = str(user.id)
        
        # Obtener estadísticas de cotizaciones del usuario
        quote_service = DatabaseQuoteService(db)
        stats = quote_service.get_quote_statistics(user.id)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "title": "Dashboard",
            "user": user,
            "recent_quotes": stats["recent_quotes"],
            "total_quotes": stats["total_quotes"]
        })
    except Exception as e:
        # Log the specific dashboard error without causing serialization issues
        logger = get_logger()
        logger.error(f"Dashboard error: {str(e)}", 
                    user_id=str(getattr(request.state, 'user_id', 'unknown')),
                    endpoint="/dashboard")
        # Return a simple error page instead of raising
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Error de Sesión",
            "error": "Error interno. Por favor, inicia sesión nuevamente."
        })

# === RUTAS DE FORMULARIOS ===
@app.post("/web/login")
async def web_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user_service = DatabaseUserService(db)
    user = user_service.get_user_by_email(email)
    
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Iniciar Sesión",
            "error": "Email o contraseña incorrectos"
        })
    
    # Crear sesión
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours)
    user_service.create_session(user.id, token, expires_at)
    
    # Crear respuesta con cookie
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

@app.post("/web/register")
async def web_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    db: Session = Depends(get_db)
):
    user_service = DatabaseUserService(db)
    
    try:
        # Validate input using secure validation
        from security.input_validation import SecureUserInput
        
        # Create validation model
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
    
    # Verificar si el usuario ya existe
    existing_user = user_service.get_user_by_email(validated_email)
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "title": "Crear Cuenta",
            "error": "El email ya está registrado"
        })
    
    # Crear usuario con datos validados
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

@app.post("/web/logout")
async def web_logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        user_service = DatabaseUserService(db)
        user_service.invalidate_session(token)
    
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

# === RUTAS PARA NUEVAS COTIZACIONES ===
@app.get("/quotes/new", response_class=HTMLResponse)
async def new_quote_page(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    # Obtener productos y materiales de la base de datos
    product_bom_service = ProductBOMServiceDB(db)
    materials_for_frontend = product_bom_service.get_all_materials()
    products_for_frontend = product_bom_service.get_all_products()

    # Mapear los enums para el frontend
    window_types_display = [
        {"value": wt.value, "label": wt.value.replace('_', ' ').title()} for wt in WindowType
    ]
    aluminum_lines_display = [
        {"value": al.value, "label": al.value.replace('_', ' ').title()} for al in AluminumLine
    ]
    glass_types_display = [
        {"value": gt.value, "label": gt.value.replace('_', ' ').title()} for gt in GlassType
    ]

    # Convertir a JSON-compatible
    app_materials_json_compatible = [m.model_dump(mode='json') for m in materials_for_frontend]
    app_products_json_compatible = [p.model_dump(mode='json') for p in products_for_frontend]

    return templates.TemplateResponse("new_quote.html", {
        "request": request,
        "title": "Nueva Cotización",
        "user": user,
        "app_materials": app_materials_json_compatible,
        "app_products": app_products_json_compatible,
        "window_types": window_types_display,
        "aluminum_lines": aluminum_lines_display,
        "glass_types": glass_types_display,
        "business_overhead": {
            "profit_margin": settings.default_profit_margin,
            "indirect_costs": settings.default_indirect_costs,
            "tax_rate": settings.default_tax_rate
        }
    })

@app.post("/quotes/calculate_item", response_model=WindowCalculation)
async def calculate_single_window_item(
    item_request: WindowItem,
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    try:
        # Obtener override de labor si se proporciona
        labor_override_param = request.query_params.get("labor_rate_override")
        labor_override_decimal = Decimal(labor_override_param) if labor_override_param else None

        product_bom_service = ProductBOMServiceDB(db)
        result = calculate_window_item_from_bom(item_request, product_bom_service, global_labor_rate_per_m2_override=labor_override_decimal)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el cálculo del ítem: {str(e)}")

@app.post("/quotes/calculate", response_model=QuoteCalculation)
async def calculate_quote_main(
    quote_request: QuoteRequest, 
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    try:
        result = calculate_complete_quote(quote_request, db)
        
        # Guardar cotización en la base de datos
        quote_service = DatabaseQuoteService(db)
        saved_quote = quote_service.create_quote(
            user_id=current_user.id,
            client_name=result.client.name,
            client_email=result.client.email,
            client_phone=result.client.phone,
            client_address=result.client.address,
            total_final=result.total_final,
            materials_subtotal=result.materials_subtotal,
            labor_subtotal=result.labor_subtotal,
            profit_amount=result.profit_amount,
            indirect_costs_amount=result.indirect_costs_amount,
            tax_amount=result.tax_amount,
            items_count=len(result.items),
            quote_data=result.model_dump(mode='json'),
            notes=result.notes,
            valid_until=result.valid_until
        )
        
        # Asignar el ID de la cotización guardada
        result.quote_id = saved_quote.id
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el cálculo: {str(e)}")

@app.post("/quotes/example")
async def create_example_quote_main(
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    try:
        product_bom_service = ProductBOMServiceDB(db)
        example_products = product_bom_service.get_all_products()
        
        if not example_products:
            raise HTTPException(status_code=400, detail="No hay productos definidos en el catálogo de BOM para generar un ejemplo.")
        
        # Seleccionar productos de ejemplo
        prod1 = example_products[0]
        prod2 = example_products[1] if len(example_products) > 1 else example_products[0]
        prod3 = example_products[2] if len(example_products) > 2 else example_products[0]

        example_request = QuoteRequest(
            client=Client(
                name="Juan Pérez (Ejemplo BOM)",
                email="juan.perez@example.com",
                phone="+52 998 123 4567",
                address="Av. Ejemplo #123, Mérida, Yuc."
            ),
            items=[
                WindowItem(
                    product_bom_id=prod1.id,
                    selected_glass_type=GlassType.CLARO_6MM,
                    width_cm=Decimal('150'),
                    height_cm=Decimal('120'),
                    quantity=1,
                    description=f"{prod1.name} para sala principal"
                ),
                WindowItem(
                    product_bom_id=prod2.id,
                    selected_glass_type=GlassType.BRONCE_4MM,
                    width_cm=Decimal('80'),
                    height_cm=Decimal('100'),
                    quantity=2,
                    description=f"{prod2.name} para baño y cocina"
                ),
                WindowItem(
                    product_bom_id=prod3.id,
                    selected_glass_type=GlassType.TEMPLADO_6MM,
                    width_cm=Decimal('60'),
                    height_cm=Decimal('60'),
                    quantity=1,
                    description=f"{prod3.name} para oficina"
                )
            ],
            notes="Proyecto residencial - Demostración de cotización con BOM dinámico"
        )
        
        result = calculate_complete_quote(example_request, db)
        
        # Guardar en base de datos
        quote_service = DatabaseQuoteService(db)
        saved_quote = quote_service.create_quote(
            user_id=current_user.id,
            client_name=result.client.name,
            client_email=result.client.email,
            client_phone=result.client.phone,
            client_address=result.client.address,
            total_final=result.total_final,
            materials_subtotal=result.materials_subtotal,
            labor_subtotal=result.labor_subtotal,
            profit_amount=result.profit_amount,
            indirect_costs_amount=result.indirect_costs_amount,
            tax_amount=result.tax_amount,
            items_count=len(result.items),
            quote_data=result.model_dump(mode='json'),
            notes=result.notes,
            valid_until=result.valid_until
        )
        
        result.quote_id = saved_quote.id
        
        return {"message": "✅ Cotización de ejemplo generada", "quote": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# === RUTAS PARA LISTADO Y VISUALIZACIÓN ===
@app.get("/quotes", response_class=HTMLResponse)
async def quotes_list_page(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    # Obtener cotizaciones del usuario
    quote_service = DatabaseQuoteService(db)
    user_quotes = quote_service.get_quotes_by_user(user.id)
    
    all_quotes = []
    for quote in user_quotes:
        try:
            # Cargar datos JSON de la cotización
            quote_data = quote.quote_data or {}
            items_count = len(quote_data.get("items", []))
            
            # Calcular área y perímetro total con manejo de errores
            total_area = 0
            for item in quote_data.get("items", []):
                try:
                    area_value = item.get("area_m2", 0)
                    if area_value is not None:
                        total_area += float(area_value)
                except (ValueError, TypeError):
                    continue  # Skip invalid area values
            
            simple_quote = {
                "id": quote.id,
                "created_at": quote.created_at,
                "client_name": quote.client_name or "Cliente Desconocido",
                "client_email": quote.client_email or "",
                "client_phone": quote.client_phone or "",
                "total_final": float(quote.total_final) if quote.total_final else 0,
                "items_count": items_count,
                "total_area": total_area,
                "price_per_m2": float(quote.total_final) / total_area if total_area > 0 and quote.total_final else 0,
                "sample_items": []
            }
            
            # Obtener items de muestra con manejo de errores
            product_bom_service = ProductBOMServiceDB(db)
            for i, item in enumerate(quote_data.get("items", [])[:3]):
                try:
                    product_info = product_bom_service.get_product_base_info(item.get("product_bom_id"))
                    
                    if product_info:
                        item_name = product_info["name"]
                        # Safe access to window_type enum value
                        try:
                            item_type = product_info["window_type"].value
                        except AttributeError:
                            item_type = str(product_info["window_type"])
                    else:
                        item_name = f"Producto #{item.get('product_bom_id', 'N/A')}"
                        item_type = str(item.get("window_type", "Desconocido"))
                    
                    simple_quote["sample_items"].append({
                        "window_type": item_type,
                        "name": item_name,
                        "width_cm": int(float(item.get("width_cm", 0))),
                        "height_cm": int(float(item.get("height_cm", 0)))
                    })
                except Exception as item_error:
                    # Skip problematic items but continue processing
                    print(f"Error processing item {i} for quote {quote.id}: {item_error}")
                    continue
            
            simple_quote["remaining_items"] = max(0, items_count - 3)
            all_quotes.append(simple_quote)
            
        except Exception as quote_error:
            # Skip problematic quotes but continue processing others
            print(f"Error processing quote {quote.id}: {quote_error}")
            continue
    
    from datetime import date
    today = date.today()
    
    return templates.TemplateResponse("quotes_list.html", {
        "request": request,
        "title": "Todas las Cotizaciones",
        "user": user,
        "quotes": all_quotes,
        "today": today
    })

@app.get("/quotes/{quote_id}", response_class=HTMLResponse)
async def view_quote_page(request: Request, quote_id: int, db: Session = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    # Obtener cotización específica del usuario
    quote_service = DatabaseQuoteService(db)
    quote = quote_service.get_quote_by_id(quote_id, user.id)
    
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    quote_data = quote.quote_data
    
    return templates.TemplateResponse("view_quote.html", {
        "request": request,
        "title": f"Cotización #{quote.id}",
        "user": user,
        "quote_id": quote.id,
        "created_at": quote.created_at,
        "client": {
            "name": quote.client_name,
            "email": quote.client_email,
            "phone": quote.client_phone,
            "address": quote.client_address
        },
        "items": quote_data.get("items", []),
        "total_final": quote_data.get("total_final"),
        "materials_subtotal": quote_data.get("materials_subtotal"),
        "labor_subtotal": quote_data.get("labor_subtotal"),
        "indirect_costs_amount": quote_data.get("indirect_costs_amount"),
        "profit_amount": quote_data.get("profit_amount"),
        "tax_amount": quote_data.get("tax_amount"),
        "notes": quote.notes
    })

# === RUTAS API PARA MATERIALES Y PRODUCTOS ===
@app.get("/api/materials", response_model=List[AppMaterial])
async def get_all_app_materials(current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    service = ProductBOMServiceDB(db)
    return service.get_all_materials()

@app.post("/api/materials", response_model=AppMaterial, status_code=status.HTTP_201_CREATED)
async def create_app_material(material: AppMaterial, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    service = ProductBOMServiceDB(db)
    return service.create_material(material)

@app.put("/api/materials/{material_id}", response_model=AppMaterial)
async def update_app_material(material_id: int, material: AppMaterial, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    service = ProductBOMServiceDB(db)
    updated = service.update_material(material_id, material)
    if not updated:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return updated

@app.delete("/api/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app_material(material_id: int, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    service = ProductBOMServiceDB(db)
    if not service.delete_material(material_id):
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/api/products", response_model=List[AppProduct])
async def get_all_app_products(current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    service = ProductBOMServiceDB(db)
    return service.get_all_products()

@app.post("/api/products", response_model=AppProduct, status_code=status.HTTP_201_CREATED)
async def create_app_product(product: AppProduct, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    service = ProductBOMServiceDB(db)
    # Validar que los material_id en el BOM existan
    for bom_item in product.bom:
        if not service.get_material(bom_item.material_id):
            raise HTTPException(status_code=400, detail=f"Material con ID {bom_item.material_id} no existe en el catálogo.")
    return service.create_product(product)

@app.put("/api/products/{product_id}", response_model=AppProduct)
async def update_app_product(product_id: int, product: AppProduct, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    service = ProductBOMServiceDB(db)
    # Validar materiales
    for bom_item in product.bom:
        if not service.get_material(bom_item.material_id):
            raise HTTPException(status_code=400, detail=f"Material con ID {bom_item.material_id} no existe en el catálogo.")
    updated = service.update_product(product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return updated

@app.delete("/api/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app_product(product_id: int, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    service = ProductBOMServiceDB(db)
    if not service.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# === RUTAS PARA CATÁLOGOS ===
@app.get("/materials_catalog", response_class=HTMLResponse)
async def materials_catalog_page(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse("materials_catalog.html", {
        "request": request,
        "title": "Catálogo de Materiales (BOM)",
        "user": user
    })

@app.get("/products_catalog", response_class=HTMLResponse)
async def products_catalog_page(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    # Obtener materiales para los selects del BOM
    service = ProductBOMServiceDB(db)
    materials_for_frontend = service.get_all_materials()
    
    window_types_display = [
        {"value": wt.value, "label": wt.value.replace('_', ' ').title()} for wt in WindowType
    ]
    aluminum_lines_display = [
        {"value": al.value, "label": al.value.replace('_', ' ').title()} for al in AluminumLine
    ]
    glass_types_display = [
        {"value": gt.value, "label": gt.value.replace('_', ' ').title()} for gt in GlassType
    ]

    return templates.TemplateResponse("products_catalog.html", {
        "request": request,
        "title": "Catálogo de Productos (BOM)",
        "user": user,
        "app_materials": [m.model_dump(mode='json') for m in materials_for_frontend],
        "window_types": window_types_display,
        "aluminum_lines": aluminum_lines_display,
        "glass_types": glass_types_display,
    })

# === RUTAS API COMPATIBILITY ===
@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    user_service = DatabaseUserService(db)
    
    try:
        # Validate input using secure validation
        from security.input_validation import SecureUserInput
        
        validated_input = SecureUserInput(
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    
    if user_service.get_user_by_email(validated_input.email):
        raise HTTPException(status_code=400, detail=f"El email {validated_input.email} ya está registrado")
    
    hashed_password = hash_password(validated_input.password)
    new_user = user_service.create_user(validated_input.email, hashed_password, validated_input.full_name)
    
    return UserResponse(id=str(new_user.id), email=new_user.email, full_name=new_user.full_name)

@app.post("/auth/login", response_model=Token)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    user_service = DatabaseUserService(db)
    user = user_service.get_user_by_email(login_data.email)
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours)
    user_service.create_session(user.id, token, expires_at)
    
    user_response = UserResponse(id=str(user.id), email=user.email, full_name=user.full_name)
    return Token(access_token=token, token_type="bearer", user=user_response)

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user_flexible)
):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name
    )

@app.get("/quotes/{quote_id}/pdf")
async def generate_quote_pdf(
    quote_id: int,
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Generar PDF de una cotización específica"""
    try:
        quote_service = DatabaseQuoteService(db)
        company_service = DatabaseCompanyService(db)
        
        # Obtener la cotización
        quote = quote_service.get_quote_by_id(quote_id, current_user.id)
        if not quote:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        
        # Obtener información de la empresa del usuario
        company = company_service.get_or_create_company(current_user.id)
        company_info = {
            'name': company.name,
            'address': company.address,
            'phone': company.phone,
            'email': company.email,
            'website': company.website,
            'rfc': company.rfc,
            'logo_path': f"static/logos/{company.logo_filename}" if company.logo_filename else None
        }
        
        # Crear servicio de PDF
        pdf_service = PDFQuoteService()
        
        # Generar PDF con información personalizada de la empresa
        pdf_content = pdf_service.generate_quote_pdf(quote.quote_data, company_info)
        
        # Definir nombre del archivo
        filename = f"cotizacion_{quote_id:05d}.pdf"
        
        # Retornar PDF como respuesta
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error generando PDF: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

# === RUTAS PARA CONFIGURACIÓN DE EMPRESA ===

@app.get("/api/company", response_model=CompanyResponse)
async def get_company_info(
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Obtener información de la empresa del usuario"""
    company_service = DatabaseCompanyService(db)
    company = company_service.get_or_create_company(current_user.id)
    return company

@app.put("/api/company", response_model=CompanyResponse)
async def update_company_info(
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Actualizar información de la empresa"""
    company_service = DatabaseCompanyService(db)
    
    # Convertir a dict, excluyendo valores None
    update_data = company_data.model_dump(exclude_none=True)
    
    company = company_service.update_company(current_user.id, update_data)
    if not company:
        raise HTTPException(status_code=404, detail="Error actualizando información de empresa")
    
    return company

@app.get("/company/settings")
async def company_settings_page(
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Página de configuración de empresa"""
    company_service = DatabaseCompanyService(db)
    company = company_service.get_or_create_company(current_user.id)
    
    return templates.TemplateResponse("company_settings.html", {
        "request": request,
        "title": "Configuración de Empresa",
        "user": current_user,
        "company": company
    })

@app.post("/api/company/upload-logo")
async def upload_company_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Subir logo de la empresa"""
    # Validar tipo de archivo
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")
    
    # Validar tamaño (2MB máximo)
    if file.size and file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo no puede ser mayor a 2MB")
    
    # Obtener extensión del archivo
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.png', '.jpg', '.jpeg', '.svg']:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PNG, JPG, JPEG o SVG")
    
    try:
        company_service = DatabaseCompanyService(db)
        
        # Crear nombre único para el archivo
        unique_filename = f"logo_{current_user.id}{file_extension}"
        file_path = f"static/logos/{unique_filename}"
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Actualizar registro en base de datos
        company_service.update_company(current_user.id, {"logo_filename": unique_filename})
        
        return {"message": "Logo subido exitosamente", "filename": unique_filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo logo: {str(e)}")

# === RUTAS PARA GESTIÓN DE COLORES ===

@app.get("/api/colors", response_model=List[ColorResponse])
async def get_all_colors(
    active_only: bool = True,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Obtener todos los colores"""
    color_service = DatabaseColorService(db)
    return color_service.get_all_colors(active_only=active_only)

@app.post("/api/colors", response_model=ColorResponse, status_code=status.HTTP_201_CREATED)
async def create_color(
    color_data: ColorCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Crear nuevo color"""
    color_service = DatabaseColorService(db)
    color_dict = color_data.model_dump()
    return color_service.create_color(color_dict)

@app.get("/api/materials/{material_id}/colors")
async def get_material_colors(
    material_id: int,
    available_only: bool = True,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Obtener colores disponibles para un material"""
    color_service = DatabaseColorService(db)
    material_colors = color_service.get_material_colors(material_id, available_only)
    
    # Formatear respuesta
    result = []
    for material_color, color in material_colors:
        result.append({
            "id": material_color.id,
            "color_id": color.id,
            "color_name": color.name,
            "color_code": color.code,
            "price_per_unit": material_color.price_per_unit,
            "is_available": material_color.is_available
        })
    
    return result

@app.post("/api/materials/{material_id}/colors", response_model=MaterialColorResponse, status_code=status.HTTP_201_CREATED)
async def create_material_color(
    material_id: int,
    material_color_data: MaterialColorCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Agregar color a un material con precio específico"""
    color_service = DatabaseColorService(db)
    
    # Verificar que el material_id coincida
    if material_color_data.material_id != material_id:
        raise HTTPException(status_code=400, detail="Material ID no coincide")
    
    material_color_dict = material_color_data.model_dump()
    try:
        return color_service.create_material_color(material_color_dict)
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Esta combinación de material y color ya existe")
        raise HTTPException(status_code=500, detail=f"Error creando material-color: {str(e)}")

@app.delete("/api/materials/colors/{material_color_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material_color(
    material_color_id: int,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Eliminar relación material-color"""
    color_service = DatabaseColorService(db)
    
    success = color_service.delete_material_color(material_color_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relación material-color no encontrada")
    
    return

@app.get("/api/materials/by-category")
async def get_materials_by_category(
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Obtener materiales agrupados por categoría con sus colores"""
    try:
        material_service = DatabaseMaterialService(db)
        color_service = DatabaseColorService(db)
        
        # Obtener todos los materiales activos
        try:
            materials = material_service.get_all_materials()
        except Exception as e:
            print(f"Error getting materials: {e}")
            raise HTTPException(status_code=500, detail=f"Error accediendo a materiales: {str(e)}")
        
        # Verificar si la tabla tiene la columna category
        has_category_column = True
        try:
            # Intentar acceder al primer material para verificar si tiene category
            if materials and hasattr(materials[0], 'category'):
                pass  # Column exists
            else:
                has_category_column = False
        except:
            has_category_column = False
        
        # Agrupar por categoría
        categories = {}
        
        for material in materials:
            # Safely get category with fallback
            try:
                category = getattr(material, 'category', 'Otros')
            except AttributeError:
                category = 'Otros'
            
            if not category:
                category = 'Otros'
            
            if category not in categories:
                categories[category] = []
            
            # Obtener colores para el material
            try:
                material_colors = color_service.get_material_colors(material.id, available_only=True)
            except Exception as e:
                print(f"Error getting colors for material {material.id}: {e}")
                material_colors = []
            
            colors_data = []
            for material_color, color in material_colors:
                colors_data.append({
                    "id": material_color.id,
                    "color_id": color.id,
                    "color_name": color.name,
                    "color_code": color.code,
                    "price_per_unit": float(material_color.price_per_unit),
                    "is_available": material_color.is_available
                })
            
            # Safely convert data with error handling
            try:
                cost_per_unit = float(material.cost_per_unit) if material.cost_per_unit else 0.0
                selling_unit_length_m = float(material.selling_unit_length_m) if material.selling_unit_length_m else None
            except (ValueError, TypeError) as e:
                print(f"Error converting numeric values for material {material.id}: {e}")
                cost_per_unit = 0.0
                selling_unit_length_m = None
            
            material_data = {
                "id": material.id,
                "name": material.name or "Sin nombre",
                "code": material.code or "",
                "unit": material.unit or "PZA",
                "category": category,
                "cost_per_unit": cost_per_unit,
                "selling_unit_length_m": selling_unit_length_m,
                "description": material.description or "",
                "colors": colors_data,
                "has_colors": len(colors_data) > 0
            }
            
            categories[category].append(material_data)
        
        return {
            "categories": categories,
            "total_materials": len(materials),
            "has_category_column": has_category_column
        }
    except Exception as e:
        print(f"Error in get_materials_by_category: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error obteniendo materiales por categoría: {str(e)}")

@app.get("/api/debug/materials")
async def debug_materials(
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Debug endpoint para verificar estructura de materiales"""
    try:
        material_service = DatabaseMaterialService(db)
        materials = material_service.get_all_materials()
        
        if not materials:
            return {"message": "No materials found", "count": 0}
        
        first_material = materials[0]
        material_attrs = [attr for attr in dir(first_material) if not attr.startswith('_')]
        
        return {
            "total_materials": len(materials),
            "first_material_id": first_material.id,
            "first_material_name": first_material.name,
            "available_attributes": material_attrs,
            "has_category": hasattr(first_material, 'category'),
            "category_value": getattr(first_material, 'category', 'NOT_FOUND')
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

# === CSV IMPORT/EXPORT ENDPOINTS ===

@app.get("/api/materials/csv/export")
async def export_materials_csv(
    category: Optional[str] = Query(None, description="Filter by category (Perfiles, Vidrio, Herrajes, Consumibles, Otros) or 'all'"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Export materials to CSV format by category"""
    try:
        csv_service = MaterialCSVService(db)
        csv_content = csv_service.export_materials_to_csv(category)
        
        # Generate filename
        category_part = f"_{category}" if category and category != "all" else ""
        filename = f"materials{category_part}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting materials: {str(e)}")

@app.post("/api/materials/csv/import")
async def import_materials_csv(
    file: UploadFile = File(..., description="CSV file with materials data"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Import materials from CSV file with bulk CRUD operations"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Process CSV
        csv_service = MaterialCSVService(db)
        results = csv_service.import_materials_from_csv(csv_content)
        
        return {
            "message": "CSV import completed",
            "filename": file.filename,
            "summary": results["summary"],
            "success_count": len(results["success"]),
            "error_count": len(results["errors"]),
            "successes": results["success"],
            "errors": results["errors"]
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please ensure the CSV file is UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing materials: {str(e)}")

@app.get("/api/materials/csv/template")
async def get_materials_csv_template(
    category: Optional[str] = Query(None, description="Generate template for specific category"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get CSV template with sample data for material import"""
    try:
        csv_service = MaterialCSVService(db)
        template_content = csv_service.get_csv_template(category)
        
        # Generate filename
        category_part = f"_{category}" if category else ""
        filename = f"materials_template{category_part}.csv"
        
        return Response(
            content=template_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating template: {str(e)}")

# === ADMIN: Product BOM CSV Operations ===

@app.get("/api/products/csv/export")
async def export_products_csv(
    window_type: Optional[str] = Query(None, description="Filter by window type (CORREDIZA, FIJA, PROYECTANTE, etc.) or 'all'"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Export products to CSV format by window type"""
    try:
        csv_service = ProductBOMCSVService(db)
        csv_content = csv_service.export_products_to_csv(window_type)
        
        # Generate filename
        window_type_part = f"_{window_type}" if window_type and window_type != "all" else ""
        filename = f"products{window_type_part}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting products: {str(e)}")

@app.post("/api/products/csv/import")
async def import_products_csv(
    file: UploadFile = File(..., description="CSV file with products data"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Import products from CSV file with bulk CRUD operations"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Process CSV
        csv_service = ProductBOMCSVService(db)
        results = csv_service.import_products_from_csv(csv_content)
        
        return {
            "message": "CSV import completed",
            "filename": file.filename,
            "summary": results["summary"],
            "success_count": len(results["success"]),
            "error_count": len(results["errors"]),
            "successes": results["success"],
            "errors": results["errors"]
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please ensure the CSV file is UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing products: {str(e)}")

@app.get("/api/products/csv/template")
async def get_products_csv_template(
    window_type: Optional[str] = Query(None, description="Generate template for specific window type"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get CSV template with sample data for product import"""
    try:
        csv_service = ProductBOMCSVService(db)
        template_content = csv_service.get_csv_template(window_type)
        
        # Generate filename
        window_type_part = f"_{window_type}" if window_type else ""
        filename = f"products_template{window_type_part}.csv"
        
        return Response(
            content=template_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating template: {str(e)}")

# ============================================================================
# QTO-001: WORK ORDER MANAGEMENT API ENDPOINTS
# ============================================================================

@app.post("/api/work-orders/from-quote", response_model=WorkOrderResponse)
async def create_work_order_from_quote(
    work_order_request: WorkOrderCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Convert a quote to a work order - QTO-001"""
    try:
        logger = get_logger()
        logger.info(f"Creating work order from quote {work_order_request.quote_id} for user {current_user.id}")
        
        # Get the quote service and work order service
        quote_service = DatabaseQuoteService(db)
        work_order_service = DatabaseWorkOrderService(db)
        
        # Verify the quote exists and belongs to the user
        quote = quote_service.get_quote_by_id(work_order_request.quote_id, current_user.id)
        if not quote:
            raise HTTPException(
                status_code=404, 
                detail="Quote not found or access denied"
            )
        
        # Create work order from quote
        work_order = work_order_service.create_work_order_from_quote(quote)
        
        # Update additional fields if provided
        if work_order_request.production_notes:
            work_order_data = work_order.work_order_data.copy()
            work_order_data['production_notes'] = work_order_request.production_notes
            work_order.work_order_data = work_order_data
        
        if work_order_request.delivery_instructions:
            work_order_data = work_order.work_order_data.copy()
            work_order_data['delivery_instructions'] = work_order_request.delivery_instructions
            work_order.work_order_data = work_order_data
        
        if work_order_request.priority != WorkOrderPriority.NORMAL:
            work_order.priority = work_order_request.priority
        
        if work_order_request.estimated_delivery:
            work_order.estimated_delivery = work_order_request.estimated_delivery
        
        # Commit changes if any updates were made
        if (work_order_request.production_notes or work_order_request.delivery_instructions or 
            work_order_request.priority != WorkOrderPriority.NORMAL or work_order_request.estimated_delivery):
            db.commit()
            db.refresh(work_order)
        
        logger.info(f"Work order {work_order.order_number} created successfully")
        return work_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating work order from quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating work order: {str(e)}")

@app.get("/api/work-orders", response_model=List[WorkOrderListResponse])
async def get_work_orders(
    limit: int = Query(50, ge=1, le=100, description="Number of work orders to retrieve"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get list of work orders for current user"""
    try:
        work_order_service = DatabaseWorkOrderService(db)
        work_orders = work_order_service.get_work_orders_by_user(current_user.id, limit)
        return work_orders
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error retrieving work orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving work orders: {str(e)}")

@app.get("/api/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: int,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get specific work order by ID"""
    try:
        work_order_service = DatabaseWorkOrderService(db)
        work_order = work_order_service.get_work_order_by_id(work_order_id, current_user.id)
        
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found or access denied")
        
        return work_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error retrieving work order {work_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving work order: {str(e)}")

@app.put("/api/work-orders/{work_order_id}/status", response_model=WorkOrderResponse)
async def update_work_order_status(
    work_order_id: int,
    status_update: WorkOrderStatusUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Update work order status"""
    try:
        logger = get_logger()
        work_order_service = DatabaseWorkOrderService(db)
        
        # Update the work order status
        work_order = work_order_service.update_work_order_status(
            work_order_id, 
            current_user.id, 
            status_update.status, 
            status_update.notes
        )
        
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found or access denied")
        
        logger.info(f"Work order {work_order.order_number} status updated to {status_update.status}")
        return work_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error updating work order status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating work order status: {str(e)}")

@app.put("/api/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(
    work_order_id: int,
    work_order_update: WorkOrderUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Update work order details"""
    try:
        logger = get_logger()
        work_order_service = DatabaseWorkOrderService(db)
        
        # Get the work order first
        work_order = work_order_service.get_work_order_by_id(work_order_id, current_user.id)
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found or access denied")
        
        # Update fields if provided
        updated = False
        
        if work_order_update.status is not None:
            work_order = work_order_service.update_work_order_status(
                work_order_id, current_user.id, work_order_update.status, work_order_update.notes
            )
            updated = True
        
        if work_order_update.priority is not None:
            work_order.priority = work_order_update.priority
            updated = True
        
        if work_order_update.production_notes is not None:
            work_order_data = work_order.work_order_data.copy()
            work_order_data['production_notes'] = work_order_update.production_notes
            work_order.work_order_data = work_order_data
            updated = True
        
        if work_order_update.delivery_instructions is not None:
            work_order_data = work_order.work_order_data.copy()
            work_order_data['delivery_instructions'] = work_order_update.delivery_instructions
            work_order.work_order_data = work_order_data
            updated = True
        
        if work_order_update.estimated_delivery is not None:
            work_order.estimated_delivery = work_order_update.estimated_delivery
            updated = True
        
        if work_order_update.notes is not None and work_order_update.status is None:
            # Add notes without status change
            current_notes = work_order.notes or ""
            work_order.notes = f"{current_notes}\n{work_order_update.notes}".strip()
            updated = True
        
        # Commit changes if any updates were made
        if updated:
            db.commit()
            db.refresh(work_order)
            logger.info(f"Work order {work_order.order_number} updated successfully")
        
        return work_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error updating work order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating work order: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Sistema con Base de Datos PostgreSQL Iniciado")
    print("🌐 Web: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("💾 Base de Datos: PostgreSQL/Supabase")
    print("✨ Funcionalidades:")
    print("   🔐 Autenticación persistente")
    print("   📊 Dashboard con datos reales")
    print("   📝 Cotizaciones guardadas")
    print("   📋 Catálogos BOM persistentes")
    uvicorn.run(app, host="0.0.0.0", port=8000)