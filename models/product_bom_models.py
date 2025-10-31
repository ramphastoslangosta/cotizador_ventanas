# models/product_bom_models.py
from pydantic import BaseModel, Field, root_validator
from typing import List, Optional
from decimal import Decimal
from enum import Enum

# IMPORTAR ENUMS DE quote_models.py AQUI, FUERA DE CUALQUIER CLASE
from .quote_models import WindowType, AluminumLine, GlassType
from .product_categories import ProductCategory, DoorType

class MaterialUnit(str, Enum):
    ML = "ML" # Metro Lineal
    PZA = "PZA" # Pieza
    M2 = "M2" # Metro Cuadrado
    CARTUCHO = "CARTUCHO" # Cartucho de silicón/pegamento
    LTS = "LTS" # Litros
    KG = "KG" # Kilogramo

class MaterialType(str, Enum):
    PERFIL = "PERFIL"
    VIDRIO = "VIDRIO"
    HERRAJE = "HERRAJE"
    CONSUMIBLE = "CONSUMIBLE" # Silicona, pijas, felpa, etc.
    MANO_DE_OBRA = "MANO_DE_OBRA" # Aunque se calcula aparte, para consistencia del BOM

class BOMItem(BaseModel):
    """Representa un material dentro del Bill of Materials de un producto, con fórmula."""
    material_id: int
    material_type: MaterialType # Tipo de material (Perfil, Vidrio, Herraje, Consumible)
    quantity_formula: str = Field(..., description="Fórmula para calcular la cantidad necesaria (ej: '2 * width_m + 2 * height_m').")
    waste_factor: Decimal = Field(default=Decimal("1.05"), ge=Decimal("1.0"), description="Factor de desperdicio para este material (ej: 1.05 = 5% desperdicio).")
    description: Optional[str] = None # Descripción específica de este uso del material

class AppMaterial(BaseModel):
    """Modelo para materiales genéricos (perfiles, herrajes, vidrios, consumibles) en el contexto del BOM."""
    id: Optional[int] = None # ID es opcional para la creación, se asigna en el servicio
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50, description="Código estándar del producto (ej: ALU-PER-NAC3-001)")
    unit: MaterialUnit
    category: str = Field(default="Otros", description="Categoría del material (Perfiles, Vidrio, Herrajes, Consumibles, Otros)")
    cost_per_unit: Decimal = Field(..., gt=0, description="Costo por la unidad de medida especificada.")
    description: Optional[str] = None # Para añadir más detalles
    # Nuevo: Para perfiles que se venden por tramo fijo (ej. 6m)
    selling_unit_length_m: Optional[Decimal] = Field(None, gt=0, description="Longitud de la unidad de venta para perfiles (en metros), si aplica.")


class AppProduct(BaseModel):
    """Modelo para un producto terminado (ventana) con su Bill of Materials dinámico."""
    id: Optional[int] = None # ID es opcional para la creación
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50, description="Código estándar del producto (ej: WIN-COR-3H-001)")

    # NEW: Category-based flexible system
    product_category: ProductCategory = Field(..., description="Product category")

    # MODIFIED: Make these optional (only used when applicable)
    window_type: Optional[WindowType] = Field(None, description="Window type (required if category=WINDOW)")
    door_type: Optional[DoorType] = Field(None, description="Door type (required if category=DOOR/LOUVER_DOOR)")
    aluminum_line: Optional[AluminumLine] = None
    # glass_type ya NO va aquí, se selecciona en la cotización

    # Nuevos: Rangos de dimensiones permitidas para este tipo de producto
    min_width_cm: Decimal = Field(..., gt=0, description="Ancho mínimo permitido en cm.")
    max_width_cm: Decimal = Field(..., gt=0, description="Ancho máximo permitido en cm.")
    min_height_cm: Decimal = Field(..., gt=0, description="Alto mínimo permitido en cm.")
    max_height_cm: Decimal = Field(..., gt=0, description="Alto máximo permitido en cm.")

    # El BOM es el corazón de este modelo, ahora con fórmulas
    bom: List[BOMItem] = Field(default_factory=list, description="Lista de materiales y fórmulas de cantidad necesarias para este producto.")

    description: Optional[str] = None # Descripción del producto (ej. "Sistema de ventana corrediza de 2 hojas")

    @root_validator(skip_on_failure=True)
    def validate_category_specific_fields(cls, values):
        """Ensure category-specific fields are provided when required"""
        category = values.get('product_category')
        window_type = values.get('window_type')
        door_type = values.get('door_type')

        # Window products must have window_type
        if category == ProductCategory.WINDOW and window_type is None:
            raise ValueError('window_type is required when product_category is WINDOW')

        # Door products must have door_type
        if category in [ProductCategory.DOOR, ProductCategory.LOUVER_DOOR] and door_type is None:
            raise ValueError('door_type is required for door category products')

        # Standalone materials should not have window/door types
        if category == ProductCategory.STANDALONE_MATERIAL:
            if window_type is not None or door_type is not None:
                raise ValueError('Standalone materials cannot have window_type or door_type')

        return values