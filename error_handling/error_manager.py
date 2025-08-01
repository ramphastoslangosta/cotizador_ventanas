# error_handling/error_manager.py
"""
Comprehensive Error Management System for Window Quotation System
Milestone 1.2: Error Handling & Resilience

Features:
- Comprehensive error hierarchy
- Spanish error messages for Mexico SME market
- Standardized error responses
- Error logging and reporting
- Graceful degradation support
"""

import logging
import traceback
from typing import Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
from fastapi import HTTPException, status
from pydantic import BaseModel


# === ERROR CATEGORIES ===
class ErrorCategory(str, Enum):
    """Error categories for better organization and handling"""
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    NETWORK = "network"
    SECURITY = "security"


class ErrorSeverity(str, Enum):
    """Error severity levels for monitoring and alerts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# === ERROR MODELS ===
class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    message_es: str  # Spanish message for users
    message_en: str  # English message for developers
    technical_details: Optional[str] = None
    user_action: Optional[str] = None  # What user can do
    timestamp: datetime
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response format"""
    success: bool = False
    error: ErrorDetail
    data: Optional[Dict[str, Any]] = None


# === CUSTOM EXCEPTION CLASSES ===
class BaseApplicationError(Exception):
    """Base exception class for all application errors"""
    
    def __init__(
        self,
        code: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        message_es: str,
        message_en: str,
        technical_details: Optional[str] = None,
        user_action: Optional[str] = None,
        http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.code = code
        self.category = category
        self.severity = severity
        self.message_es = message_es
        self.message_en = message_en
        self.technical_details = technical_details
        self.user_action = user_action
        self.http_status = http_status
        self.timestamp = datetime.now()
        
        super().__init__(message_en)


class DatabaseError(BaseApplicationError):
    """Database-related errors"""
    
    def __init__(self, message_es: str, message_en: str, technical_details: str = None):
        super().__init__(
            code="DB_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            message_es=message_es,
            message_en=message_en,
            technical_details=technical_details,
            user_action="Por favor, inténtelo de nuevo en unos momentos.",
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ValidationError(BaseApplicationError):
    """Input validation errors"""
    
    def __init__(self, message_es: str, message_en: str, field: str = None):
        super().__init__(
            code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message_es=message_es,
            message_en=message_en,
            technical_details=f"Field: {field}" if field else None,
            user_action="Por favor, revise los datos ingresados y corríjalos.",
            http_status=status.HTTP_400_BAD_REQUEST
        )


class AuthenticationError(BaseApplicationError):
    """Authentication and authorization errors"""
    
    def __init__(self, message_es: str, message_en: str):
        super().__init__(
            code="AUTH_ERROR",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            message_es=message_es,
            message_en=message_en,
            user_action="Por favor, inicie sesión nuevamente.",
            http_status=status.HTTP_401_UNAUTHORIZED
        )


class BusinessLogicError(BaseApplicationError):
    """Business logic validation errors"""
    
    def __init__(self, message_es: str, message_en: str, details: str = None):
        super().__init__(
            code="BUSINESS_ERROR",
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            message_es=message_es,
            message_en=message_en,
            technical_details=details,
            user_action="Por favor, revise los datos y las reglas de negocio.",
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class SecurityError(BaseApplicationError):
    """Security-related errors"""
    
    def __init__(self, message_es: str, message_en: str, details: str = None):
        super().__init__(
            code="SECURITY_ERROR",
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            message_es=message_es,
            message_en=message_en,
            technical_details=details,
            user_action="Si el problema persiste, contacte al administrador.",
            http_status=status.HTTP_403_FORBIDDEN
        )


# === ERROR MANAGER CLASS ===
class ErrorManager:
    """Central error management system"""
    
    def __init__(self):
        self.logger = logging.getLogger("error_manager")
    
    def handle_error(
        self,
        error: Union[Exception, BaseApplicationError],
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorResponse:
        """
        Handle any error and return standardized response
        
        Args:
            error: Exception or BaseApplicationError instance
            request_id: Optional request identifier for tracking
            context: Additional context information
            
        Returns:
            ErrorResponse: Standardized error response
        """
        
        if isinstance(error, BaseApplicationError):
            # Handle custom application errors
            error_detail = ErrorDetail(
                code=error.code,
                category=error.category,
                severity=error.severity,
                message_es=error.message_es,
                message_en=error.message_en,
                technical_details=error.technical_details,
                user_action=error.user_action,
                timestamp=error.timestamp,
                request_id=request_id
            )
            
            # Log the error
            self._log_error(error_detail, context)
            
        else:
            # Handle unexpected errors
            error_detail = self._handle_unexpected_error(error, request_id, context)
        
        return ErrorResponse(error=error_detail)
    
    def _handle_unexpected_error(
        self,
        error: Exception,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorDetail:
        """Handle unexpected errors"""
        
        error_type = type(error).__name__
        error_message = str(error)
        
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        error_detail = ErrorDetail(
            code="UNEXPECTED_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message_es="Ha ocurrido un error interno. Por favor, inténtelo de nuevo.",
            message_en=f"Unexpected error: {error_type}",
            technical_details=f"{error_message}\n\nStack trace:\n{stack_trace}",
            user_action="Si el problema persiste, contacte al soporte técnico.",
            timestamp=datetime.now(),
            request_id=request_id
        )
        
        # Log critical error
        self._log_error(error_detail, context)
        
        return error_detail
    
    def _log_error(self, error_detail: ErrorDetail, context: Optional[Dict[str, Any]] = None):
        """Log error with appropriate level"""
        
        log_data = {
            "error_code": error_detail.code,
            "category": error_detail.category,
            "severity": error_detail.severity,
            "message": error_detail.message_en,
            "timestamp": error_detail.timestamp.isoformat(),
            "request_id": error_detail.request_id,
            "technical_details": error_detail.technical_details
        }
        
        if context:
            log_data["context"] = context
        
        # Log with appropriate level based on severity
        if error_detail.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {log_data}")
        elif error_detail.severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY ERROR: {log_data}")
        elif error_detail.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY ERROR: {log_data}")
        else:
            self.logger.info(f"LOW SEVERITY ERROR: {log_data}")
    
    def create_http_exception(self, error: BaseApplicationError) -> HTTPException:
        """Convert BaseApplicationError to HTTPException"""
        
        return HTTPException(
            status_code=error.http_status,
            detail={
                "code": error.code,
                "message": error.message_es,  # Spanish message for users
                "user_action": error.user_action,
                "timestamp": error.timestamp.isoformat()
            }
        )


# === GLOBAL ERROR MANAGER INSTANCE ===
error_manager = ErrorManager()


# === PREDEFINED ERROR MESSAGES ===
class ErrorMessages:
    """Predefined error messages in Spanish for common scenarios"""
    
    # Database errors
    DB_CONNECTION_FAILED = {
        "es": "No se pudo conectar a la base de datos. Por favor, inténtelo de nuevo.",
        "en": "Database connection failed"
    }
    
    DB_QUERY_FAILED = {
        "es": "Error al consultar la base de datos. Verifique los datos e inténtelo de nuevo.",
        "en": "Database query failed"
    }
    
    DB_TRANSACTION_FAILED = {
        "es": "Error al procesar la transacción. Los cambios no se guardaron.",
        "en": "Database transaction failed"
    }
    
    # Authentication errors
    INVALID_CREDENTIALS = {
        "es": "Email o contraseña incorrectos. Por favor, verifique sus datos.",
        "en": "Invalid email or password"
    }
    
    TOKEN_EXPIRED = {
        "es": "Su sesión ha expirado. Por favor, inicie sesión nuevamente.",
        "en": "Authentication token expired"
    }
    
    UNAUTHORIZED_ACCESS = {
        "es": "No tiene permisos para acceder a este recurso.",
        "en": "Unauthorized access attempt"
    }
    
    # Validation errors
    INVALID_EMAIL = {
        "es": "El formato del email no es válido. Ejemplo: usuario@dominio.com",
        "en": "Invalid email format"
    }
    
    PASSWORD_TOO_WEAK = {
        "es": "La contraseña debe tener al menos 8 caracteres con letras y números.",
        "en": "Password does not meet security requirements"
    }
    
    REQUIRED_FIELD_MISSING = {
        "es": "Este campo es requerido y no puede estar vacío.",
        "en": "Required field is missing"
    }
    
    # Business logic errors
    INVALID_DIMENSIONS = {
        "es": "Las dimensiones de la ventana están fuera del rango permitido.",
        "en": "Window dimensions are out of allowed range"
    }
    
    PRODUCT_NOT_FOUND = {
        "es": "El producto seleccionado no existe o no está disponible.",
        "en": "Product not found or unavailable"
    }
    
    CALCULATION_ERROR = {
        "es": "Error al calcular la cotización. Verifique los datos ingresados.",
        "en": "Quote calculation error"
    }
    
    # System errors
    SERVICE_UNAVAILABLE = {
        "es": "El servicio no está disponible temporalmente. Inténtelo de nuevo.",
        "en": "Service temporarily unavailable"
    }
    
    RATE_LIMIT_EXCEEDED = {
        "es": "Ha excedido el límite de solicitudes. Espere un momento antes de intentar de nuevo.",
        "en": "Rate limit exceeded"
    }


# === UTILITY FUNCTIONS ===
def create_database_error(message_key: str, technical_details: str = None) -> DatabaseError:
    """Create a database error with predefined messages"""
    messages = getattr(ErrorMessages, message_key, ErrorMessages.DB_QUERY_FAILED)
    return DatabaseError(
        message_es=messages["es"],
        message_en=messages["en"],
        technical_details=technical_details
    )


def create_validation_error(message_key: str, field: str = None) -> ValidationError:
    """Create a validation error with predefined messages"""
    messages = getattr(ErrorMessages, message_key, ErrorMessages.REQUIRED_FIELD_MISSING)
    return ValidationError(
        message_es=messages["es"],
        message_en=messages["en"],
        field=field
    )


def create_auth_error(message_key: str) -> AuthenticationError:
    """Create an authentication error with predefined messages"""
    messages = getattr(ErrorMessages, message_key, ErrorMessages.UNAUTHORIZED_ACCESS)
    return AuthenticationError(
        message_es=messages["es"],
        message_en=messages["en"]
    )


def create_business_error(message_key: str, details: str = None) -> BusinessLogicError:
    """Create a business logic error with predefined messages"""
    messages = getattr(ErrorMessages, message_key, ErrorMessages.CALCULATION_ERROR)
    return BusinessLogicError(
        message_es=messages["es"],
        message_en=messages["en"],
        details=details
    )