# services/product_bom_service_db.py - Versión actualizada para usar base de datos
from typing import List, Dict, Optional
from decimal import Decimal
import math
from sqlalchemy.orm import Session

from models.product_bom_models import AppMaterial, AppProduct, BOMItem, MaterialUnit, MaterialType
from models.quote_models import WindowType, AluminumLine, GlassType, LaborCost, Glass
from database import AppMaterial as DBAppMaterial, AppProduct as DBAppProduct
from database import DatabaseMaterialService, DatabaseProductService

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
            description=product.description
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
            description=updated_product.description
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
    """Inicializa la base de datos con datos de ejemplo si está vacía"""
    service = ProductBOMServiceDB(db)
    
    # Verificar si ya hay datos
    if len(service.get_all_materials()) > 0:
        return  # Ya hay datos, no inicializar
    
    print("Inicializando base de datos con datos de ejemplo...")
    
    # Crear materiales de ejemplo
    materials_data = [
        {"name": "Perfil L. Nac. 3\" Riel Sup.", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('50.00'), "selling_unit_length_m": Decimal('6.0'), "description": "Riel superior corrediza 3\""},
        {"name": "Perfil L. Nac. 3\" Jamba", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('48.00'), "selling_unit_length_m": Decimal('6.0'), "description": "Jamba vertical corrediza 3\""},
        {"name": "Perfil L. Nac. 3\" Zoclo", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('55.00'), "selling_unit_length_m": Decimal('6.0'), "description": "Zoclo inferior corrediza 3\""},
        {"name": "Perfil L. Nac. 3\" Traslape", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('60.00'), "selling_unit_length_m": Decimal('6.0'), "description": "Traslape central corrediza 3\""},
        {"name": "Rodamiento Doble Línea 3\"", "unit": MaterialUnit.PZA, "cost_per_unit": Decimal('15.00'), "description": "Rodamiento para hojas corredizas"},
        {"name": "Felpa 1/2\"", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('2.50'), "description": "Burlete de felpa para sellado"},
        {"name": "Silicona Neutra", "unit": MaterialUnit.CARTUCHO, "cost_per_unit": Decimal('80.00'), "description": "Sellador de silicona neutra"},
        {"name": "Pijas #8 x 1\"", "unit": MaterialUnit.PZA, "cost_per_unit": Decimal('0.50'), "description": "Tornillos para ensamble"},
        {"name": "Perfil Serie 35 Contramarco", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('65.00'), "selling_unit_length_m": Decimal('6.0'), "description": "Contramarco para proyectante Serie 35"},
        {"name": "Perfil Serie 35 Marco Móvil", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('70.00'), "selling_unit_length_m": Decimal('6.0'), "description": "Marco móvil para proyectante Serie 35"},
        {"name": "Brazo Proyectante 10\"", "unit": MaterialUnit.PZA, "cost_per_unit": Decimal('70.00'), "description": "Brazo para ventana proyectante"},
        {"name": "Cremona Serie 35", "unit": MaterialUnit.PZA, "cost_per_unit": Decimal('45.00'), "description": "Manija con cierre para proyectante"},
        {"name": "Perfil Fijo 3\" Escalonado", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('78.90'), "selling_unit_length_m": Decimal('6.0'), "description": "Marco perimetral escalonado fijo 3\""},
        {"name": "Junquillo Fijo 3\"", "unit": MaterialUnit.ML, "cost_per_unit": Decimal('28.90'), "selling_unit_length_m": Decimal('6.0'), "description": "Junquillo para sujeción de vidrio fijo 3\""},
        {"name": "Cuñas de Hule", "unit": MaterialUnit.PZA, "cost_per_unit": Decimal('0.80'), "description": "Cuñas para asentar vidrio"},
    ]
    
    created_materials = {}
    for mat_data in materials_data:
        material = AppMaterial(**mat_data)
        created_material = service.create_material(material)
        created_materials[mat_data["name"]] = created_material
        print(f"✓ Material creado: {created_material.name} (ID: {created_material.id})")
    
    # Crear productos de ejemplo
    # Ventana Corrediza 2 Hojas
    corrediza_bom = [
        BOMItem(material_id=created_materials["Perfil L. Nac. 3\" Riel Sup."].id, material_type=MaterialType.PERFIL, quantity_formula="width_m", description="Riel Superior"),
        BOMItem(material_id=created_materials["Perfil L. Nac. 3\" Zoclo"].id, material_type=MaterialType.PERFIL, quantity_formula="width_m", description="Zoclo Inferior"),
        BOMItem(material_id=created_materials["Perfil L. Nac. 3\" Jamba"].id, material_type=MaterialType.PERFIL, quantity_formula="2 * height_m", description="Jambas Laterales"),
        BOMItem(material_id=created_materials["Perfil L. Nac. 3\" Jamba"].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m / 2)", description="Cabezales de Hojas"),
        BOMItem(material_id=created_materials["Perfil L. Nac. 3\" Zoclo"].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m / 2)", description="Zoclos de Hojas"),
        BOMItem(material_id=created_materials["Perfil L. Nac. 3\" Traslape"].id, material_type=MaterialType.PERFIL, quantity_formula="height_m", description="Traslape Vertical"),
        BOMItem(material_id=created_materials["Rodamiento Doble Línea 3\""].id, material_type=MaterialType.HERRAJE, quantity_formula="4", description="Rodamientos (4 por ventana)"),
        BOMItem(material_id=created_materials["Felpa 1/2\""].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4 * (width_m / 2 + height_m)", description="Felpa para Hojas"),
        BOMItem(material_id=created_materials["Silicona Neutra"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.5", description="Silicona (medio cartucho)"),
        BOMItem(material_id=created_materials["Pijas #8 x 1\""].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="20", description="Pijas (cantidad fija)"),
        BOMItem(material_id=created_materials["Cuñas de Hule"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4 * 2", description="Cuñas de hule (4 por paño, 2 paños)"),
    ]
    
    corrediza_product = AppProduct(
        name="Ventana Corrediza 2 Hojas (Línea 3\")",
        window_type=WindowType.CORREDIZA,
        aluminum_line=AluminumLine.SERIE_3,
        min_width_cm=Decimal('80'), max_width_cm=Decimal('300'),
        min_height_cm=Decimal('60'), max_height_cm=Decimal('250'),
        description="Sistema corredizo de 2 hojas, adaptable a dimensiones.",
        bom=corrediza_bom
    )
    created_corrediza = service.create_product(corrediza_product)
    print(f"✓ Producto creado: {created_corrediza.name} (ID: {created_corrediza.id})")
    
    # Ventana Fija
    fija_bom = [
        BOMItem(material_id=created_materials["Perfil Fijo 3\" Escalonado"].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Marco Perimetral Escalonado"),
        BOMItem(material_id=created_materials["Junquillo Fijo 3\""].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Junquillo de sujeción de vidrio"),
        BOMItem(material_id=created_materials["Silicona Neutra"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.3", description="Silicona (cantidad fija)"),
        BOMItem(material_id=created_materials["Pijas #8 x 1\""].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="10", description="Pijas (cantidad fija)"),
        BOMItem(material_id=created_materials["Cuñas de Hule"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4", description="Cuñas de hule (4 por paño)"),
    ]
    
    fija_product = AppProduct(
        name="Ventana Fija (Línea 3\")",
        window_type=WindowType.FIJA,
        aluminum_line=AluminumLine.SERIE_3,
        min_width_cm=Decimal('50'), max_width_cm=Decimal('200'),
        min_height_cm=Decimal('50'), max_height_cm=Decimal('180'),
        description="Sistema fijo para iluminación, adaptable a dimensiones.",
        bom=fija_bom
    )
    created_fija = service.create_product(fija_product)
    print(f"✓ Producto creado: {created_fija.name} (ID: {created_fija.id})")
    
    # Ventana Proyectante
    proyectante_bom = [
        BOMItem(material_id=created_materials["Perfil Serie 35 Contramarco"].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Contramarco Fijo"),
        BOMItem(material_id=created_materials["Perfil Serie 35 Marco Móvil"].id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Marco Móvil de Hoja"),
        BOMItem(material_id=created_materials["Brazo Proyectante 10\""].id, material_type=MaterialType.HERRAJE, quantity_formula="2", description="Brazos Proyectantes (2 por ventana)"),
        BOMItem(material_id=created_materials["Cremona Serie 35"].id, material_type=MaterialType.HERRAJE, quantity_formula="1", description="Cremona (1 por ventana)"),
        BOMItem(material_id=created_materials["Silicona Neutra"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.4", description="Silicona (cantidad fija)"),
        BOMItem(material_id=created_materials["Pijas #8 x 1\""].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="15", description="Pijas (cantidad fija)"),
        BOMItem(material_id=created_materials["Cuñas de Hule"].id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4", description="Cuñas de hule (4 por paño)"),
    ]
    
    proyectante_product = AppProduct(
        name="Ventana Proyectada (Serie 35)",
        window_type=WindowType.PROYECTANTE,
        aluminum_line=AluminumLine.SERIE_35,
        min_width_cm=Decimal('40'), max_width_cm=Decimal('120'),
        min_height_cm=Decimal('40'), max_height_cm=Decimal('100'),
        description="Sistema proyectante para ventilación, adaptable a dimensiones.",
        bom=proyectante_bom
    )
    created_proyectante = service.create_product(proyectante_product)
    print(f"✓ Producto creado: {created_proyectante.name} (ID: {created_proyectante.id})")
    
    print("✅ Inicialización completada con éxito!")