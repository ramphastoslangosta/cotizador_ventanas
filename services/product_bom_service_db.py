# services/product_bom_service_db.py - Versión actualizada para usar base de datos
from typing import List, Dict, Optional
from decimal import Decimal
import math
from sqlalchemy.orm import Session

from models.product_bom_models import AppMaterial, AppProduct, BOMItem, MaterialUnit, MaterialType
from models.quote_models import WindowType, AluminumLine, GlassType, LaborCost, Glass
from database import AppMaterial as DBAppMaterial, AppProduct as DBAppProduct
from database import DatabaseMaterialService, DatabaseProductService, DatabaseColorService, Color, MaterialColor

# Glass type to material code mapping
# Material codes follow pattern: VID-{TYPE}-{THICKNESS}
GLASS_TYPE_TO_MATERIAL_CODE = {
    GlassType.CLARO_4MM: "VID-CLARO-4",
    GlassType.CLARO_6MM: "VID-CLARO-6",
    GlassType.BRONCE_4MM: "VID-BRONCE-4",
    GlassType.BRONCE_6MM: "VID-BRONCE-6",
    GlassType.REFLECTIVO_6MM: "VID-REFLECTIVO-6",
    GlassType.LAMINADO_6MM: "VID-LAMINADO-6",
    GlassType.TEMPLADO_6MM: "VID-TEMP-6",
}

# Hardcoded fallback prices (backward compatibility)
GLASS_FALLBACK_PRICES = {
    GlassType.CLARO_4MM: Decimal('85.00'),
    GlassType.CLARO_6MM: Decimal('120.00'),
    GlassType.BRONCE_4MM: Decimal('95.00'),
    GlassType.BRONCE_6MM: Decimal('135.00'),
    GlassType.REFLECTIVO_6MM: Decimal('180.00'),
    GlassType.LAMINADO_6MM: Decimal('220.00'),
    GlassType.TEMPLADO_6MM: Decimal('195.00'),
}

class ProductBOMServiceDB:
    """Versión de ProductBOMService que usa base de datos en lugar de memoria"""
    
    def __init__(self, db: Session):
        self.db = db
        self.material_service = DatabaseMaterialService(db)
        self.product_service = DatabaseProductService(db)
    
    # === Métodos para Materiales ===
    def get_all_materials(self) -> List[AppMaterial]:
        """Obtiene todos los materiales activos de la base de datos"""
        db_materials = self.material_service.get_all_materials()
        return [self._db_material_to_pydantic(mat) for mat in db_materials]
    
    def get_material(self, material_id: int) -> Optional[AppMaterial]:
        """Obtiene un material específico por ID"""
        db_material = self.material_service.get_material_by_id(material_id)
        if not db_material:
            return None
        return self._db_material_to_pydantic(db_material)
    
    def create_material(self, material: AppMaterial) -> AppMaterial:
        """Crea un nuevo material en la base de datos"""
        db_material = self.material_service.create_material(
            name=material.name,
            unit=material.unit.value,
            category=material.category,
            code=material.code,
            cost_per_unit=material.cost_per_unit,
            selling_unit_length_m=material.selling_unit_length_m,
            description=material.description
        )
        return self._db_material_to_pydantic(db_material)
    
    def update_material(self, material_id: int, updated_material: AppMaterial) -> Optional[AppMaterial]:
        """Actualiza un material existente"""
        db_material = self.material_service.update_material(
            material_id=material_id,
            name=updated_material.name,
            unit=updated_material.unit.value,
            category=updated_material.category,
            code=updated_material.code,
            cost_per_unit=updated_material.cost_per_unit,
            selling_unit_length_m=updated_material.selling_unit_length_m,
            description=updated_material.description
        )
        if not db_material:
            return None
        return self._db_material_to_pydantic(db_material)
    
    def delete_material(self, material_id: int) -> bool:
        """Elimina (desactiva) un material"""
        return self.material_service.delete_material(material_id)
    
    # === Métodos para Productos ===
    def get_all_products(self) -> List[AppProduct]:
        """Obtiene todos los productos activos de la base de datos"""
        db_products = self.product_service.get_all_products()
        return [self._db_product_to_pydantic(prod) for prod in db_products]
    
    def get_product(self, product_id: int) -> Optional[AppProduct]:
        """Obtiene un producto específico por ID"""
        db_product = self.product_service.get_product_by_id(product_id)
        if not db_product:
            return None
        return self._db_product_to_pydantic(db_product)
    
    def create_product(self, product: AppProduct) -> AppProduct:
        """Crea un nuevo producto en la base de datos"""
        # Convertir BOM a formato JSON para la base de datos
        bom_json = [item.model_dump(mode='json') for item in product.bom]
        
        db_product = self.product_service.create_product(
            name=product.name,
            window_type=product.window_type.value,
            aluminum_line=product.aluminum_line.value,
            min_width_cm=product.min_width_cm,
            max_width_cm=product.max_width_cm,
            min_height_cm=product.min_height_cm,
            max_height_cm=product.max_height_cm,
            bom=bom_json,
            description=product.description,
            code=product.code
        )
        return self._db_product_to_pydantic(db_product)
    
    def update_product(self, product_id: int, updated_product: AppProduct) -> Optional[AppProduct]:
        """Actualiza un producto existente"""
        # Convertir BOM a formato JSON
        bom_json = [item.model_dump(mode='json') for item in updated_product.bom]
        
        db_product = self.product_service.update_product(
            product_id=product_id,
            name=updated_product.name,
            window_type=updated_product.window_type.value,
            aluminum_line=updated_product.aluminum_line.value,
            min_width_cm=updated_product.min_width_cm,
            max_width_cm=updated_product.max_width_cm,
            min_height_cm=updated_product.min_height_cm,
            max_height_cm=updated_product.max_height_cm,
            bom=bom_json,
            description=updated_product.description,
            code=updated_product.code
        )
        if not db_product:
            return None
        return self._db_product_to_pydantic(db_product)
    
    def delete_product(self, product_id: int) -> bool:
        """Elimina (desactiva) un producto"""
        return self.product_service.delete_product(product_id)
    
    # === Métodos de Utilidad (mismos que la versión original) ===
    def get_material_cost_per_unit(self, material_id: int) -> Decimal:
        material = self.get_material(material_id)
        if not material:
            raise ValueError(f"Material con ID {material_id} no encontrado.")
        return material.cost_per_unit
    
    def get_product_base_info(self, product_id: int) -> Optional[Dict]:
        product = self.get_product(product_id)
        if product:
            return {
                "name": product.name,
                "window_type": product.window_type,
                "aluminum_line": product.aluminum_line,
                "description": product.description,
                "min_width_cm": product.min_width_cm,
                "max_width_cm": product.max_width_cm,
                "min_height_cm": product.min_height_cm,
                "max_height_cm": product.max_height_cm,
            }
        return None
    
    def get_labor_cost_data(self, window_type: WindowType) -> Optional[LaborCost]:
        """Obtiene el costo de mano de obra para un tipo de ventana."""
        _LABOR_COSTS = [
            LaborCost(id=1, window_type=WindowType.FIJA, cost_per_m2=Decimal('45.00')),
            LaborCost(id=2, window_type=WindowType.CORREDIZA, cost_per_m2=Decimal('65.00'), complexity_factor=Decimal('1.2')),
            LaborCost(id=3, window_type=WindowType.ABATIBLE, cost_per_m2=Decimal('75.00'), complexity_factor=Decimal('1.4')),
            LaborCost(id=4, window_type=WindowType.OSCILOBATIENTE, cost_per_m2=Decimal('95.00'), complexity_factor=Decimal('1.6')),
            LaborCost(id=5, window_type=WindowType.PROYECTANTE, cost_per_m2=Decimal('70.00'), complexity_factor=Decimal('1.3')),
        ]
        for labor in _LABOR_COSTS:
            if labor.window_type == window_type:
                return labor
        return None

    def get_glass_cost_per_m2(self, glass_type: GlassType) -> Decimal:
        """Obtiene el costo por m2 de un tipo de vidrio."""
        _GLASS_CATALOG = [
            Glass(id=1, name="Vidrio Claro 4mm", glass_type=GlassType.CLARO_4MM, cost_per_m2=Decimal('85.00'), thickness=4),
            Glass(id=2, name="Vidrio Claro 6mm", glass_type=GlassType.CLARO_6MM, cost_per_m2=Decimal('120.00'), thickness=6),
            Glass(id=3, name="Vidrio Bronce 4mm", glass_type=GlassType.BRONCE_4MM, cost_per_m2=Decimal('95.00'), thickness=4),
            Glass(id=4, name="Vidrio Bronce 6mm", glass_type=GlassType.BRONCE_6MM, cost_per_m2=Decimal('135.00'), thickness=6),
            Glass(id=5, name="Vidrio Reflectivo 6mm", glass_type=GlassType.REFLECTIVO_6MM, cost_per_m2=Decimal('180.00'), thickness=6),
            Glass(id=6, name="Vidrio Laminado 6mm", glass_type=GlassType.LAMINADO_6MM, cost_per_m2=Decimal('220.00'), thickness=6),
            Glass(id=7, name="Vidrio Templado 6mm", glass_type=GlassType.TEMPLADO_6MM, cost_per_m2=Decimal('195.00'), thickness=6),
        ]
        for glass in _GLASS_CATALOG:
            if glass.glass_type == glass_type:
                return glass.cost_per_m2
        raise ValueError(f"Costo de vidrio no encontrado para tipo: {glass_type}")
    
    # === Métodos de conversión entre modelos DB y Pydantic ===
    def _db_material_to_pydantic(self, db_material: DBAppMaterial) -> AppMaterial:
        """Convierte un modelo de base de datos a Pydantic"""
        return AppMaterial(
            id=db_material.id,
            name=db_material.name,
            unit=MaterialUnit(db_material.unit),
            category=getattr(db_material, 'category', 'Otros'),
            code=db_material.code,
            cost_per_unit=db_material.cost_per_unit,
            selling_unit_length_m=db_material.selling_unit_length_m,
            description=db_material.description
        )
    
    def _db_product_to_pydantic(self, db_product: DBAppProduct) -> AppProduct:
        """Convierte un modelo de producto de base de datos a Pydantic"""
        # Convertir BOM de JSON a objetos Pydantic
        bom_items = []
        for bom_data in db_product.bom:
            bom_item = BOMItem(
                material_id=bom_data['material_id'],
                material_type=MaterialType(bom_data['material_type']),
                quantity_formula=bom_data['quantity_formula'],
                waste_factor=Decimal(str(bom_data['waste_factor'])),
                description=bom_data.get('description')
            )
            bom_items.append(bom_item)
        
        return AppProduct(
            id=db_product.id,
            name=db_product.name,
            code=getattr(db_product, 'code', None),
            window_type=WindowType(db_product.window_type),
            aluminum_line=AluminumLine(db_product.aluminum_line),
            min_width_cm=db_product.min_width_cm,
            max_width_cm=db_product.max_width_cm,
            min_height_cm=db_product.min_height_cm,
            max_height_cm=db_product.max_height_cm,
            bom=bom_items,
            description=db_product.description
        )

# === Función para inicializar datos de ejemplo ===
def initialize_sample_data(db: Session):
    """Inicializa la base de datos con datos de ejemplo si está vacía - VERSIÓN MEJORADA"""
    service = ProductBOMServiceDB(db)
    color_service = DatabaseColorService(db)
    
    # Verificar si ya hay datos
    if len(service.get_all_materials()) > 0:
        return  # Ya hay datos, no inicializar
    
    print("🚀 Inicializando base de datos con catálogo mejorado de materiales...")
    
    # === FASE 1: CREAR COLORES ===
    print("📋 Creando sistema de colores...")
    
    aluminum_colors = [
        {"name": "Natural", "code": "NAT", "description": "Aluminio natural sin pintura"},
        {"name": "Blanco", "code": "BLA", "description": "Blanco texturizado"},
        {"name": "Negro", "code": "NEG", "description": "Negro mate texturizado"},
        {"name": "Bronze", "code": "BRO", "description": "Bronze anodizado"},
        {"name": "Champagne", "code": "CHA", "description": "Champagne anodizado"},
        {"name": "Madera Clara", "code": "MCA", "description": "Imitación madera color claro"},
    ]
    
    # Multiplicadores de precio por color
    color_pricing = {
        "Natural": Decimal("1.00"),    # Precio base
        "Blanco": Decimal("1.15"),     # 15% premium
        "Negro": Decimal("1.20"),      # 20% premium  
        "Bronze": Decimal("1.25"),     # 25% premium
        "Champagne": Decimal("1.25"),  # 25% premium
        "Madera Clara": Decimal("1.40"), # 40% premium
    }
    
    created_colors = {}
    for color_data in aluminum_colors:
        created_color = color_service.create_color(color_data)
        created_colors[color_data["name"]] = created_color
        print(f"  ✓ Color: {created_color.name} ({created_color.code})")
    
    # === FASE 2: CREAR MATERIALES POR CATEGORÍA ===
    print("\n🏗️ Creando catálogo de materiales por categoría...")
    
    # 2.1 PERFILES (Aluminio con colores)
    print("  📦 Categoría: PERFILES")
    perfiles_data = [
        # Línea Nacional 3"
        {"name": "Perfil Riel Superior 3\"", "code": "PER-NAC3-RS", "cost": Decimal("52.00"), "unit": MaterialUnit.ML, "selling_unit_length_m": Decimal("6.0")},
        {"name": "Perfil Jamba 3\"", "code": "PER-NAC3-JA", "cost": Decimal("48.00"), "unit": MaterialUnit.ML, "selling_unit_length_m": Decimal("6.0")},
        {"name": "Perfil Zócalo 3\"", "code": "PER-NAC3-ZO", "cost": Decimal("55.00"), "unit": MaterialUnit.ML, "selling_unit_length_m": Decimal("6.0")},
        {"name": "Perfil Traslape 3\"", "code": "PER-NAC3-TR", "cost": Decimal("60.00"), "unit": MaterialUnit.ML, "selling_unit_length_m": Decimal("6.0")},
        # Serie 35
        {"name": "Perfil Contramarco Serie 35", "code": "PER-S35-CM", "cost": Decimal("65.00"), "unit": MaterialUnit.ML, "selling_unit_length_m": Decimal("6.0")},
        {"name": "Perfil Marco Móvil Serie 35", "code": "PER-S35-MM", "cost": Decimal("70.00"), "unit": MaterialUnit.ML, "selling_unit_length_m": Decimal("6.0")},
        # Fijos
        {"name": "Perfil Fijo Escalonado 3\"", "code": "PER-NAC3-FE", "cost": Decimal("78.90"), "unit": MaterialUnit.ML, "selling_unit_length_m": Decimal("6.0")},
        {"name": "Junquillo Fijo 3\"", "code": "PER-NAC3-JF", "cost": Decimal("28.90"), "unit": MaterialUnit.ML, "selling_unit_length_m": Decimal("6.0")},
    ]
    
    created_profiles = {}
    for perfil_data in perfiles_data:
        # Crear el perfil base
        material = AppMaterial(
            name=perfil_data["name"],
            code=perfil_data["code"],
            unit=perfil_data["unit"],
            category="Perfiles",
            cost_per_unit=perfil_data["cost"],
            selling_unit_length_m=perfil_data.get("selling_unit_length_m"),
            description=f"Perfil de aluminio - {perfil_data['name']}"
        )
        created_material = service.create_material(material)
        created_profiles[perfil_data["name"]] = created_material
        print(f"    ✓ {created_material.name} (ID: {created_material.id})")
        
        # Crear variaciones de color para este perfil
        for color_name, color_multiplier in color_pricing.items():
            color = created_colors[color_name]
            price_per_unit = perfil_data["cost"] * color_multiplier
            
            material_color_data = {
                "material_id": created_material.id,
                "color_id": color.id,
                "price_per_unit": price_per_unit,
                "is_available": True
            }
            color_service.create_material_color(material_color_data)
    
    print(f"    📊 {len(created_profiles)} perfiles con {len(aluminum_colors)} colores = {len(created_profiles) * len(aluminum_colors)} combinaciones")
    
    # 2.2 VIDRIOS
    print("  🪟 Categoría: VIDRIOS")
    vidrios_data = [
        {"name": "Vidrio Flotado 6mm", "code": "VID-FLOT-6", "cost": Decimal("145.00"), "unit": MaterialUnit.M2},
        {"name": "Vidrio Templado 6mm", "code": "VID-TEMP-6", "cost": Decimal("280.00"), "unit": MaterialUnit.M2},
        {"name": "Vidrio Laminado 6mm", "code": "VID-LAM-6", "cost": Decimal("320.00"), "unit": MaterialUnit.M2},
        {"name": "Vidrio Reflectivo Bronze 6mm", "code": "VID-REF-BR6", "cost": Decimal("195.00"), "unit": MaterialUnit.M2},
        {"name": "Vidrio Doble Acristalamiento", "code": "VID-DOBLE-6", "cost": Decimal("450.00"), "unit": MaterialUnit.M2},
    ]
    
    created_glass = {}
    for vidrio_data in vidrios_data:
        material = AppMaterial(
            name=vidrio_data["name"],
            code=vidrio_data["code"],
            unit=vidrio_data["unit"],
            category="Vidrio",
            cost_per_unit=vidrio_data["cost"],
            description=f"Vidrio para ventanas - {vidrio_data['name']}"
        )
        created_material = service.create_material(material)
        created_glass[vidrio_data["name"]] = created_material
        print(f"    ✓ {created_material.name} (ID: {created_material.id})")
    
    # 2.3 HERRAJES
    print("  🔧 Categoría: HERRAJES")
    herrajes_data = [
        {"name": "Rodamiento Doble Línea 3\"", "code": "HER-ROD-3", "cost": Decimal("15.00"), "unit": MaterialUnit.PZA},
        {"name": "Brazo Proyectante 10\"", "code": "HER-BRA-10", "cost": Decimal("70.00"), "unit": MaterialUnit.PZA},
        {"name": "Cremona Serie 35", "code": "HER-CRE-S35", "cost": Decimal("45.00"), "unit": MaterialUnit.PZA},
        {"name": "Cerradura Multipunto", "code": "HER-CER-MP", "cost": Decimal("150.00"), "unit": MaterialUnit.PZA},
        {"name": "Bisagra Reforzada", "code": "HER-BIS-REF", "cost": Decimal("25.00"), "unit": MaterialUnit.PZA},
    ]
    
    created_hardware = {}
    for herraje_data in herrajes_data:
        material = AppMaterial(
            name=herraje_data["name"],
            code=herraje_data["code"],
            unit=herraje_data["unit"],
            category="Herrajes",
            cost_per_unit=herraje_data["cost"],
            description=f"Herraje para ventanas - {herraje_data['name']}"
        )
        created_material = service.create_material(material)
        created_hardware[herraje_data["name"]] = created_material
        print(f"    ✓ {created_material.name} (ID: {created_material.id})")
    
    # 2.4 CONSUMIBLES
    print("  🧰 Categoría: CONSUMIBLES")
    consumibles_data = [
        {"name": "Felpa Negra 1/2\"", "code": "CON-FEL-NEG", "cost": Decimal("2.50"), "unit": MaterialUnit.ML},
        {"name": "Silicona Neutra Transparente", "code": "CON-SIL-NEU", "cost": Decimal("80.00"), "unit": MaterialUnit.CARTUCHO},
        {"name": "Pijas #8 x 1\"", "code": "CON-PIJ-8x1", "cost": Decimal("0.50"), "unit": MaterialUnit.PZA},
        {"name": "Cuñas de Hule", "code": "CON-CUN-HUL", "cost": Decimal("0.80"), "unit": MaterialUnit.PZA},
        {"name": "Tornillo Autoperforante", "code": "CON-TOR-AUTO", "cost": Decimal("1.20"), "unit": MaterialUnit.PZA},
    ]
    
    created_consumables = {}
    for consumible_data in consumibles_data:
        material = AppMaterial(
            name=consumible_data["name"],
            code=consumible_data["code"],
            unit=consumible_data["unit"],
            category="Consumibles",
            cost_per_unit=consumible_data["cost"],
            description=f"Consumible para ventanas - {consumible_data['name']}"
        )
        created_material = service.create_material(material)
        created_consumables[consumible_data["name"]] = created_material
        print(f"    ✓ {created_material.name} (ID: {created_material.id})")
    
    # === FASE 3: CREAR PRODUCTOS CON BOMS MEJORADOS ===
    print("\n🏠 Creando productos con BOMs mejorados...")
    
    # 3.1 VENTANA CORREDIZA 2 HOJAS CON VIDRIO
    corrediza_bom = [
        # Perfiles (con colores disponibles)
        BOMItem(material_id=created_profiles["Perfil Riel Superior 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="width_m", description="Riel Superior"),
        BOMItem(material_id=created_profiles["Perfil Zócalo 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="width_m", description="Zócalo Inferior"),
        BOMItem(material_id=created_profiles["Perfil Jamba 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="2 * height_m", description="Jambas Laterales"),
        BOMItem(material_id=created_profiles["Perfil Jamba 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m / 2)", description="Cabezales de Hojas"),
        BOMItem(material_id=created_profiles["Perfil Zócalo 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m / 2)", description="Zócalos de Hojas"),
        BOMItem(material_id=created_profiles["Perfil Traslape 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="height_m", description="Traslape Vertical"),
        # Vidrio
        BOMItem(material_id=created_glass["Vidrio Flotado 6mm"].id, material_type=MaterialType.VIDRIO, quantity_formula="area_m2 * 0.5", description="Vidrio por paño (50% del área total)"),
        # Herrajes
        BOMItem(material_id=created_hardware["Rodamiento Doble Línea 3\""].id, material_type=MaterialType.HERRAJE, quantity_formula="4", description="Rodamientos (4 por ventana)"),
        # Consumibles
        BOMItem(material_id=created_consumables["Felpa Negra 1/2\""].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4 * (width_m / 2 + height_m)", description="Felpa perimetral"),
        BOMItem(material_id=created_consumables["Silicona Neutra Transparente"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.5", description="Silicona (medio cartucho)"),
        BOMItem(material_id=created_consumables["Pijas #8 x 1\""].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="20", description="Pijas de ensamble"),
        BOMItem(material_id=created_consumables["Cuñas de Hule"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="8", description="Cuñas de hule (4 por paño × 2)"),
    ]
    
    corrediza_product = AppProduct(
        name="Ventana Corrediza 2 Hojas con Vidrio (Línea 3\")",
        window_type=WindowType.CORREDIZA,
        aluminum_line=AluminumLine.SERIE_3,
        min_width_cm=Decimal('80'), max_width_cm=Decimal('300'),
        min_height_cm=Decimal('60'), max_height_cm=Decimal('250'),
        description="Sistema corredizo de 2 hojas con vidrio incluido, disponible en 6 colores.",
        bom=corrediza_bom
    )
    created_corrediza = service.create_product(corrediza_product)
    print(f"  ✓ {created_corrediza.name} (ID: {created_corrediza.id})")
    
    # 3.2 VENTANA FIJA CON VIDRIO
    fija_bom = [
        # Perfiles (con colores disponibles)
        BOMItem(material_id=created_profiles["Perfil Fijo Escalonado 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Marco Perimetral Escalonado"),
        BOMItem(material_id=created_profiles["Junquillo Fijo 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Junquillo de sujeción"),
        # Vidrio
        BOMItem(material_id=created_glass["Vidrio Templado 6mm"].id, material_type=MaterialType.VIDRIO, quantity_formula="area_m2", description="Vidrio templado completo"),
        # Consumibles
        BOMItem(material_id=created_consumables["Silicona Neutra Transparente"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.3", description="Silicona para sellado"),
        BOMItem(material_id=created_consumables["Pijas #8 x 1\""].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="10", description="Pijas de fijación"),
        BOMItem(material_id=created_consumables["Cuñas de Hule"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4", description="Cuñas de asentamiento"),
    ]
    
    fija_product = AppProduct(
        name="Ventana Fija con Vidrio Templado (Línea 3\")",
        window_type=WindowType.FIJA,
        aluminum_line=AluminumLine.SERIE_3,
        min_width_cm=Decimal('50'), max_width_cm=Decimal('200'),
        min_height_cm=Decimal('50'), max_height_cm=Decimal('180'),
        description="Sistema fijo con vidrio templado, disponible en 6 colores.",
        bom=fija_bom
    )
    created_fija = service.create_product(fija_product)
    print(f"  ✓ {created_fija.name} (ID: {created_fija.id})")
    
    # 3.3 VENTANA PROYECTANTE CON VIDRIO
    proyectante_bom = [
        # Perfiles (con colores disponibles)
        BOMItem(material_id=created_profiles["Perfil Contramarco Serie 35"].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Contramarco Fijo"),
        BOMItem(material_id=created_profiles["Perfil Marco Móvil Serie 35"].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Marco Móvil de Hoja"),
        # Vidrio
        BOMItem(material_id=created_glass["Vidrio Laminado 6mm"].id, material_type=MaterialType.VIDRIO, quantity_formula="area_m2", description="Vidrio laminado de seguridad"),
        # Herrajes
        BOMItem(material_id=created_hardware["Brazo Proyectante 10\""].id, material_type=MaterialType.HERRAJE, quantity_formula="2", description="Brazos proyectantes"),
        BOMItem(material_id=created_hardware["Cremona Serie 35"].id, material_type=MaterialType.HERRAJE, quantity_formula="1", description="Cremona de cierre"),
        # Consumibles
        BOMItem(material_id=created_consumables["Silicona Neutra Transparente"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.4", description="Silicona de sellado"),
        BOMItem(material_id=created_consumables["Tornillo Autoperforante"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="15", description="Tornillos de herrajes"),
        BOMItem(material_id=created_consumables["Cuñas de Hule"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4", description="Cuñas de vidrio"),
    ]
    
    proyectante_product = AppProduct(
        name="Ventana Proyectante con Vidrio Laminado (Serie 35)",
        window_type=WindowType.PROYECTANTE,
        aluminum_line=AluminumLine.SERIE_35,
        min_width_cm=Decimal('40'), max_width_cm=Decimal('120'),
        min_height_cm=Decimal('40'), max_height_cm=Decimal('100'),
        description="Sistema proyectante con vidrio laminado, disponible en 6 colores.",
        bom=proyectante_bom
    )
    created_proyectante = service.create_product(proyectante_product)
    print(f"  ✓ {created_proyectante.name} (ID: {created_proyectante.id})")
    
    # === RESUMEN FINAL ===
    print("\n📊 RESUMEN DE INICIALIZACIÓN:")
    print(f"  🎨 Colores: {len(aluminum_colors)} colores estándar")
    print(f"  📦 Perfiles: {len(created_profiles)} con {len(aluminum_colors)} colores = {len(created_profiles) * len(aluminum_colors)} combinaciones")
    print(f"  🪟 Vidrios: {len(created_glass)} tipos diferentes")
    print(f"  🔧 Herrajes: {len(created_hardware)} componentes")
    print(f"  🧰 Consumibles: {len(created_consumables)} materiales")
    print(f"  🏠 Productos: 3 sistemas completos con vidrio incluido")
    print("\n✅ CATÁLOGO PROFESIONAL INICIALIZADO CON ÉXITO!")
    print("🎯 Sistema listo para cotizaciones con colores y especificaciones técnicas")