# models/company_models.py - Modelos para configuración de empresa

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class CompanyBase(BaseModel):
    """Modelo base para información de empresa"""
    name: str = Field(..., min_length=1, max_length=200, description="Nombre de la empresa")
    address: Optional[str] = Field(None, max_length=500, description="Dirección de la empresa")
    phone: Optional[str] = Field(None, max_length=50, description="Teléfono de la empresa")
    email: Optional[str] = Field(None, description="Email de la empresa")
    website: Optional[str] = Field(None, max_length=200, description="Sitio web de la empresa")
    rfc: Optional[str] = Field(None, max_length=20, description="RFC de la empresa")

class CompanyCreate(CompanyBase):
    """Modelo para crear empresa"""
    pass

class CompanyUpdate(BaseModel):
    """Modelo para actualizar empresa (todos los campos opcionales)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None)
    website: Optional[str] = Field(None, max_length=200)
    rfc: Optional[str] = Field(None, max_length=20)

class CompanyResponse(CompanyBase):
    """Modelo de respuesta para información de empresa"""
    id: int
    logo_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CompanyForPDF(BaseModel):
    """Modelo simplificado para uso en PDFs"""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    rfc: Optional[str] = None
    logo_path: Optional[str] = None  # Ruta completa al archivo de logo