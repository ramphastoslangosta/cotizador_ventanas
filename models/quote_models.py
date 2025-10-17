# models/quote_models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum

class WindowType(str, Enum):
    """Tipos de ventana disponibles"""
    FIJA = "fija"
    CORREDIZA = "corrediza"
    PROYECTANTE = "proyectante"
    ABATIBLE = "abatible"
    OSCILOBATIENTE = "oscilobatiente"


class AluminumLine(str, Enum):
    """Líneas de aluminio disponibles"""
    SERIE_3 = "nacional_serie_3" # Para productos que usan Línea Nacional 3 pulgadas
    SERIE_35 = "nacional_serie_35" # Para productos que usan Serie 35


class GlassType(str, Enum):
    """Tipos de vidrio disponibles"""
    CLARO_4MM = "claro_4mm"
    CLARO_6MM = "claro_6mm"
    BRONCE_4MM = "bronce_4mm"
    BRONCE_6MM = "bronce_6mm"
    REFLECTIVO_6MM = "reflectivo_6mm"
    LAMINADO_6MM = "laminado_6mm"
    TEMPLADO_6MM = "templado_6mm"

# Modelos de datos base (se mantienen para compatibilidad si otras partes del código los usan)
class Material(BaseModel):
    id: int
    name: str
    aluminum_line: AluminumLine
    cost_per_meter: Decimal = Field(..., gt=0, description="Costo por metro lineal")
    waste_factor: Decimal = Field(default=Decimal("1.1"), description="Factor de desperdicio (1.1 = 10%)")
    description: Optional[str] = None

class Glass(BaseModel):
    id: int
    name: str
    glass_type: GlassType
    cost_per_m2: Decimal = Field(..., gt=0, description="Costo por metro cuadrado")
    waste_factor: Decimal = Field(default=Decimal("1.05"), description="Factor de desperdicio")
    thickness: int = Field(..., gt=0, description="Espesor en mm")

class Hardware(BaseModel):
    id: int
    name: str
    window_types: List[WindowType] = Field(..., description="Tipos de ventana compatibles")
    cost_per_unit: Decimal = Field(..., gt=0)
    description: Optional[str] = None

class LaborCost(BaseModel):
    id: int
    window_type: WindowType
    cost_per_m2: Decimal = Field(..., gt=0, description="Costo de instalación por m²")
    complexity_factor: Decimal = Field(default=Decimal("1.0"), description="Factor de complejidad")

class BusinessOverhead(BaseModel):
    profit_margin: Decimal = Field(..., ge=0, le=1, description="Margen de utilidad (0.0 a 1.0)")
    indirect_costs: Decimal = Field(..., ge=0, le=1, description="Gastos indirectos (0.0 a 1.0)")
    tax_rate: Decimal = Field(..., ge=0, le=1, description="Tasa de impuestos (0.0 a 1.0)")

# Modelos para requests de cotización
class WindowItem(BaseModel):
    """
    Modelo para un ítem de ventana en la cotización.
    Ahora referencia un `product_bom_id` y permite seleccionar el `glass_type` en la cotización.

    GLASS SELECTION: Supports dual-path approach for backward compatibility
    - NEW PATH: Use selected_glass_material_id (database ID) - preferred
    - OLD PATH: Use selected_glass_type (enum) - deprecated but functional
    """
    product_bom_id: int = Field(..., description="ID del producto definido en el catálogo de BOM (AppProduct).")

    # GLASS SELECTION: Dual-path support
    selected_glass_type: Optional[GlassType] = Field(
        None,
        description="[DEPRECATED] Tipo de vidrio seleccionado (enum). Use selected_glass_material_id instead for database-driven selection."
    )
    selected_glass_material_id: Optional[int] = Field(
        None,
        description="[PREFERRED] ID del material de vidrio desde database. Permite selección dinámica desde Materials Catalog."
    )

    selected_profile_color: Optional[int] = Field(None, description="ID del color seleccionado para los perfiles.")

    width_cm: Decimal = Field(..., gt=0, le=1000, description="Ancho en centímetros")
    height_cm: Decimal = Field(..., gt=0, le=1000, description="Alto en centímetros")
    quantity: int = Field(..., gt=0, le=100, description="Cantidad de ventanas")
    description: Optional[str] = None

    @validator('selected_glass_material_id', 'selected_glass_type')
    def validate_glass_selection(cls, v, values):
        """
        Ensure at least one glass selection method is provided.
        Dual-path validation: must have either material_id (NEW) or glass_type (OLD).
        """
        # On first field validation, can't check the other yet
        if 'selected_glass_type' not in values and 'selected_glass_material_id' not in values:
            return v

        glass_type = values.get('selected_glass_type')
        glass_material_id = values.get('selected_glass_material_id')

        # At least one must be provided
        if glass_type is None and glass_material_id is None:
            raise ValueError(
                'Must provide either selected_glass_type (deprecated) or selected_glass_material_id (preferred) for glass selection'
            )

        return v

    @validator('width_cm', 'height_cm')
    def validate_dimensions(cls, v):
        """Validar que las dimensiones sean razonables"""
        if v < 30:
            raise ValueError('Las dimensiones mínimas son 30cm')
        if v > 500:
            raise ValueError('Las dimensiones máximas son 500cm')
        return v

class Client(BaseModel):
    """Modelo para cliente"""
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class QuoteRequest(BaseModel):
    """Modelo para solicitud de cotización"""
    client: Client
    items: List[WindowItem] = Field(..., min_items=1, max_items=50)
    notes: Optional[str] = None
    # START: Added fields for modifiable overhead variables and labor override
    profit_margin: Optional[Decimal] = Field(None, ge=0, le=1, description="Margen de utilidad para esta cotización (0.0 a 1.0)")
    indirect_costs_rate: Optional[Decimal] = Field(None, ge=0, le=1, description="Tasa de gastos indirectos para esta cotización (0.0 a 1.0)")
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1, description="Tasa de impuestos para esta cotización (0.0 a 1.0)")
    labor_rate_per_m2_override: Optional[Decimal] = Field(None, gt=0, description="Costo de mano de obra por m2 para esta cotización (opcional, anula el cálculo por tipo de ventana)")
    # END: Added fields
    
    @validator('items')
    def validate_items(cls, v):
        if len(v) == 0:
            raise ValueError('Debe incluir al menos un ítem')
        return v

# Modelos para responses de cálculos
class WindowCalculation(BaseModel):
    """
    Resultado del cálculo para una ventana con desglose de costos del BOM dinámico.

    GLASS SELECTION: Supports dual-path approach for backward compatibility
    """
    # Datos originales o del AppProduct
    product_bom_id: int
    product_bom_name: str
    window_type: WindowType
    aluminum_line: AluminumLine

    # GLASS SELECTION: Dual-path support
    selected_glass_type: Optional[GlassType] = Field(
        None,
        description="[DEPRECATED] El tipo de vidrio elegido (enum) - for backward compatibility"
    )
    selected_glass_material_id: Optional[int] = Field(
        None,
        description="[PREFERRED] ID del material de vidrio desde database"
    )

    width_cm: Decimal
    height_cm: Decimal
    quantity: int
    
    # Medidas calculadas
    area_m2: Decimal = Field(..., description="Área en metros cuadrados")
    perimeter_m: Decimal = Field(..., description="Perímetro en metros")
    
    # Costos detallados de materiales del BOM (calculados dinámicamente)
    total_profiles_cost: Decimal = Field(..., description="Costo total de perfiles de aluminio.")
    total_glass_cost: Decimal = Field(..., description="Costo total de vidrio.")
    total_hardware_cost: Decimal = Field(..., description="Costo total de herrajes.")
    total_consumables_cost: Decimal = Field(..., description="Costo total de consumibles (silicona, pijas, etc.).")
    
    labor_cost: Decimal = Field(..., description="Costo de mano de obra.")
    
    # Subtotal por ítem
    subtotal: Decimal = Field(..., description="Subtotal antes de gastos generales.")
    
class QuoteCalculation(BaseModel):
    """Resultado completo del cálculo de cotización"""
    quote_id: Optional[int] = None
    client: Client
    items: List[WindowCalculation]
    
    # Totales
    materials_subtotal: Decimal = Field(..., description="Subtotal de materiales (perfiles + vidrio + herrajes + consumibles)")
    labor_subtotal: Decimal = Field(..., description="Subtotal de mano de obra")
    subtotal_before_overhead: Decimal = Field(..., description="Subtotal antes de gastos generales")
    
    # Gastos generales
    profit_amount: Decimal = Field(..., description="Monto de utilidad")
    indirect_costs_amount: Decimal = Field(..., description="Monto de gastos indirectos")
    subtotal_with_overhead: Decimal = Field(..., description="Subtotal con gastos generales")
    
    # Total final
    tax_amount: Decimal = Field(..., description="Monto de impuestos")
    total_final: Decimal = Field(..., description="Total final con impuestos")
    
    # Metadatos
    calculated_at: datetime = Field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None

class QuoteSummary(BaseModel):
    """Resumen de cotización para listados"""
    id: int
    client_name: str
    total_amount: Decimal
    items_count: int
    created_at: datetime
    status: str = "pending"