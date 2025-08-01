# models/color_models.py - Modelos para gestión de colores y precios por color

from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class ColorBase(BaseModel):
    """Modelo base para colores"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del color")
    code: Optional[str] = Field(None, max_length=20, description="Código del color")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del color")
    is_active: bool = Field(True, description="Si el color está activo")

class ColorCreate(ColorBase):
    """Modelo para crear color"""
    pass

class ColorUpdate(BaseModel):
    """Modelo para actualizar color"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class ColorResponse(ColorBase):
    """Modelo de respuesta para color"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Modelos para MaterialColor (relación material-color con precio)

class MaterialColorBase(BaseModel):
    """Modelo base para relación material-color"""
    material_id: int = Field(..., description="ID del material")
    color_id: int = Field(..., description="ID del color")
    price_per_unit: Decimal = Field(..., gt=0, description="Precio por unidad para este color")
    is_available: bool = Field(True, description="Si esta combinación está disponible")

class MaterialColorCreate(MaterialColorBase):
    """Modelo para crear relación material-color"""
    pass

class MaterialColorUpdate(BaseModel):
    """Modelo para actualizar relación material-color"""
    price_per_unit: Optional[Decimal] = Field(None, gt=0)
    is_available: Optional[bool] = None

class MaterialColorResponse(MaterialColorBase):
    """Modelo de respuesta para relación material-color"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MaterialColorWithDetails(BaseModel):
    """Modelo con detalles completos de material-color"""
    id: int
    material_id: int
    color_id: int
    color_name: str
    color_code: Optional[str]
    price_per_unit: Decimal
    is_available: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MaterialWithColors(BaseModel):
    """Modelo de material con sus colores y precios"""
    id: int
    name: str
    code: Optional[str]
    category: str
    unit: str
    base_price: Optional[Decimal]  # Precio base si no tiene colores específicos
    selling_unit_length_m: Optional[Decimal]
    description: Optional[str]
    colors: List[MaterialColorWithDetails] = []
    
    class Config:
        from_attributes = True