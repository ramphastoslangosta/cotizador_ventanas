# security/input_validation.py - Comprehensive input validation
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, ValidationError, validator, Field
import html
import bleach

class InputValidator:
    """
    Secure input validation to prevent injection attacks and ensure data integrity
    """
    
    # Safe HTML tags and attributes for rich text inputs
    ALLOWED_HTML_TAGS = [
        'b', 'i', 'u', 'em', 'strong', 'br', 'p', 'ul', 'ol', 'li'
    ]
    ALLOWED_HTML_ATTRIBUTES = {}
    
    # Regex patterns for common validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]{7,20}$')
    RFC_PATTERN = re.compile(r'^[A-Z&Ññ]{3,4}[0-9]{6}[A-Z0-9]{3}$')
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.]+$')
    SAFE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.áéíóúÁÉÍÓÚñÑ]+$')
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        Sanitize HTML input to prevent XSS attacks
        """
        if not text:
            return ""
        
        # Use bleach to clean HTML
        cleaned = bleach.clean(
            text,
            tags=InputValidator.ALLOWED_HTML_TAGS,
            attributes=InputValidator.ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
        return cleaned.strip()
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """
        Sanitize plain text input
        """
        if not text:
            return ""
        
        # HTML escape the input
        sanitized = html.escape(text.strip())
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate and sanitize email address
        """
        if not email:
            raise ValueError("Email is required")
        
        email = email.strip().lower()
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValueError("Email address is too long")
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            raise ValueError("Invalid email format")
        
        return email
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """
        Validate and sanitize phone number
        """
        if not phone:
            return ""
        
        phone = phone.strip()
        
        if len(phone) > 20:
            raise ValueError("Phone number is too long")
        
        if not InputValidator.PHONE_PATTERN.match(phone):
            raise ValueError("Invalid phone number format")
        
        return phone
    
    @staticmethod
    def validate_rfc(rfc: str) -> str:
        """
        Validate Mexican RFC (tax ID)
        """
        if not rfc:
            return ""
        
        rfc = rfc.strip().upper()
        
        if not InputValidator.RFC_PATTERN.match(rfc):
            raise ValueError("Invalid RFC format")
        
        return rfc
    
    @staticmethod
    def validate_decimal(value: Any, min_value: Optional[Decimal] = None, 
                        max_value: Optional[Decimal] = None) -> Decimal:
        """
        Validate and convert to Decimal with bounds checking
        """
        if value is None:
            raise ValueError("Value is required")
        
        try:
            if isinstance(value, str):
                # Remove any non-numeric characters except decimal point and minus
                cleaned = re.sub(r'[^\d.-]', '', value.strip())
                decimal_value = Decimal(cleaned)
            else:
                decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid numeric value")
        
        if min_value is not None and decimal_value < min_value:
            raise ValueError(f"Value must be at least {min_value}")
        
        if max_value is not None and decimal_value > max_value:
            raise ValueError(f"Value must be at most {max_value}")
        
        return decimal_value
    
    @staticmethod
    def validate_integer(value: Any, min_value: Optional[int] = None, 
                        max_value: Optional[int] = None) -> int:
        """
        Validate and convert to integer with bounds checking
        """
        if value is None:
            raise ValueError("Value is required")
        
        try:
            if isinstance(value, str):
                # Remove any non-numeric characters except minus
                cleaned = re.sub(r'[^\d-]', '', value.strip())
                int_value = int(cleaned)
            else:
                int_value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Invalid integer value")
        
        if min_value is not None and int_value < min_value:
            raise ValueError(f"Value must be at least {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValueError(f"Value must be at most {max_value}")
        
        return int_value
    
    @staticmethod
    def validate_safe_name(name: str, max_length: int = 100) -> str:
        """
        Validate names (supports Spanish characters)
        """
        if not name:
            raise ValueError("Name is required")
        
        name = name.strip()
        
        if len(name) > max_length:
            raise ValueError(f"Name is too long (max {max_length} characters)")
        
        if len(name) < 2:
            raise ValueError("Name is too short")
        
        if not InputValidator.SAFE_NAME_PATTERN.match(name):
            raise ValueError("Name contains invalid characters")
        
        return name
    
    @staticmethod
    def validate_product_code(code: str) -> str:
        """
        Validate product code format (e.g., ALU-PER-NAC3-001)
        """
        if not code:
            return ""
        
        code = code.strip().upper()
        
        if len(code) > 20:
            raise ValueError("Product code is too long")
        
        # Allow alphanumeric characters and hyphens
        if not re.match(r'^[A-Z0-9-]+$', code):
            raise ValueError("Product code contains invalid characters")
        
        return code
    
    @staticmethod
    def validate_formula(formula: str) -> str:
        """
        Validate mathematical formula (used with safe evaluator)
        """
        if not formula:
            raise ValueError("Formula is required")
        
        formula = formula.strip()
        
        if len(formula) > 200:
            raise ValueError("Formula is too long")
        
        # Basic safety check - more detailed validation happens in SafeFormulaEvaluator
        dangerous_patterns = [
            'eval', 'exec', 'import', '__', 'getattr', 'setattr',
            'open', 'file', 'input', 'raw_input', 'compile'
        ]
        
        formula_lower = formula.lower()
        for pattern in dangerous_patterns:
            if pattern in formula_lower:
                raise ValueError(f"Formula contains forbidden pattern: {pattern}")
        
        return formula
    
    @staticmethod
    def validate_enum_value(value: str, allowed_values: List[str], field_name: str = "field") -> str:
        """
        Validate that a value is in the allowed enum values
        """
        if not value:
            raise ValueError(f"{field_name} is required")
        
        if value not in allowed_values:
            raise ValueError(f"Invalid {field_name}. Allowed values: {', '.join(allowed_values)}")
        
        return value

# Pydantic models with enhanced validation
class SecureUserInput(BaseModel):
    """Secure validation for user registration/update"""
    email: str = Field(..., max_length=254)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    
    @validator('email')
    def validate_email_field(cls, v):
        return InputValidator.validate_email(v)
    
    @validator('full_name')
    def validate_name_field(cls, v):
        return InputValidator.validate_safe_name(v)
    
    @validator('password')
    def validate_password_field(cls, v):
        if v and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if v and not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if v and not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

class SecureClientInput(BaseModel):
    """Secure validation for client data"""
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[str] = Field(None, max_length=254)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    
    @validator('name')
    def validate_name_field(cls, v):
        return InputValidator.validate_safe_name(v)
    
    @validator('email')
    def validate_email_field(cls, v):
        if v:
            return InputValidator.validate_email(v)
        return v
    
    @validator('phone')  
    def validate_phone_field(cls, v):
        if v:
            return InputValidator.validate_phone(v)
        return v
    
    @validator('address')
    def validate_address_field(cls, v):
        if v:
            return InputValidator.sanitize_text(v, max_length=500)
        return v

class SecureMaterialInput(BaseModel):
    """Secure validation for material data"""
    name: str = Field(..., min_length=2, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    unit: str = Field(..., min_length=1, max_length=10)
    category: str = Field(..., min_length=1, max_length=50)
    cost_per_unit: Decimal = Field(..., gt=0, le=999999.99)
    selling_unit_length_m: Optional[Decimal] = Field(None, gt=0, le=100)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('name')
    def validate_name_field(cls, v):
        return InputValidator.validate_safe_name(v, max_length=200)
    
    @validator('code')
    def validate_code_field(cls, v):
        if v:
            return InputValidator.validate_product_code(v)
        return v
    
    @validator('description')
    def validate_description_field(cls, v):
        if v:
            return InputValidator.sanitize_text(v, max_length=1000)
        return v

# Global validator instance
input_validator = InputValidator()