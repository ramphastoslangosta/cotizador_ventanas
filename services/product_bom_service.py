# services/product_bom_service.py
from typing import List, Dict, Optional
from decimal import Decimal
import math # Necesario para math.ceil

from models.product_bom_models import AppMaterial, AppProduct, BOMItem, MaterialUnit, MaterialType
from models.quote_models import WindowType, AluminumLine, GlassType, LaborCost, Glass # <--- AÑADIDO 'Glass' AQUÍ

class ProductBOMService:
    def __init__(self):
        self.materials_db: Dict[int, AppMaterial] = {}
        self.products_db: Dict[int, AppProduct] = {}
        self._next_material_id = 1
        self._next_product_id = 1
        self._initialize_mock_data()

    def _initialize_mock_data(self):
        # Materiales de ejemplo (con selling_unit_length_m para perfiles)
        mat1 = self.create_material(AppMaterial(name="Perfil L. Nac. 3\" Riel Sup.", unit=MaterialUnit.ML, cost_per_unit=Decimal('50.00'), description="Riel superior corrediza 3\"", selling_unit_length_m=Decimal('6.0')))
        mat2 = self.create_material(AppMaterial(name="Perfil L. Nac. 3\" Jamba", unit=MaterialUnit.ML, cost_per_unit=Decimal('48.00'), description="Jamba vertical corrediza 3\"", selling_unit_length_m=Decimal('6.0')))
        mat3 = self.create_material(AppMaterial(name="Perfil L. Nac. 3\" Zoclo", unit=MaterialUnit.ML, cost_per_unit=Decimal('55.00'), description="Zoclo inferior corrediza 3\"", selling_unit_length_m=Decimal('6.0')))
        mat4 = self.create_material(AppMaterial(name="Perfil L. Nac. 3\" Traslape", unit=MaterialUnit.ML, cost_per_unit=Decimal('60.00'), description="Traslape central corrediza 3\"", selling_unit_length_m=Decimal('6.0')))
        mat5 = self.create_material(AppMaterial(name="Rodamiento Doble Línea 3\"", unit=MaterialUnit.PZA, cost_per_unit=Decimal('15.00'), description="Rodamiento para hojas corredizas"))
        mat6 = self.create_material(AppMaterial(name="Felpa 1/2\"", unit=MaterialUnit.ML, cost_per_unit=Decimal('2.50'), description="Burlete de felpa para sellado"))
        mat7 = self.create_material(AppMaterial(name="Silicona Neutra", unit=MaterialUnit.CARTUCHO, cost_per_unit=Decimal('80.00'), description="Sellador de silicona neutra"))
        mat8 = self.create_material(AppMaterial(name="Pijas #8 x 1\"", unit=MaterialUnit.PZA, cost_per_unit=Decimal('0.50'), description="Tornillos para ensamble"))
        mat9 = self.create_material(AppMaterial(name="Perfil Serie 35 Contramarco", unit=MaterialUnit.ML, cost_per_unit=Decimal('65.00'), description="Contramarco para proyectante Serie 35", selling_unit_length_m=Decimal('6.0')))
        mat10 = self.create_material(AppMaterial(name="Perfil Serie 35 Marco Móvil", unit=MaterialUnit.ML, cost_per_unit=Decimal('70.00'), description="Marco móvil para proyectante Serie 35", selling_unit_length_m=Decimal('6.0')))
        mat11 = self.create_material(AppMaterial(name="Brazo Proyectante 10\"", unit=MaterialUnit.PZA, cost_per_unit=Decimal('70.00'), description="Brazo para ventana proyectante"))
        mat12 = self.create_material(AppMaterial(name="Cremona Serie 35", unit=MaterialUnit.PZA, cost_per_unit=Decimal('45.00'), description="Manija con cierre para proyectante"))
        mat13 = self.create_material(AppMaterial(name="Perfil Fijo 3\" Escalonado", unit=MaterialUnit.ML, cost_per_unit=Decimal('78.90'), description="Marco perimetral escalonado fijo 3\"", selling_unit_length_m=Decimal('6.0')))
        mat14 = self.create_material(AppMaterial(name="Junquillo Fijo 3\"", unit=MaterialUnit.ML, cost_per_unit=Decimal('28.90'), description="Junquillo para sujeción de vidrio fijo 3\"", selling_unit_length_m=Decimal('6.0')))
        mat15 = self.create_material(AppMaterial(name="Cuñas de Hule", unit=MaterialUnit.PZA, cost_per_unit=Decimal('0.80'), description="Cuñas para asentar vidrio"))


        # Productos de ejemplo con BOM dinámico (fórmulas)
        self.create_product(AppProduct(
            name="Ventana Corrediza 2 Hojas (Línea 3\")",
            window_type=WindowType.CORREDIZA,
            aluminum_line=AluminumLine.SERIE_3,
            min_width_cm=Decimal('80'), max_width_cm=Decimal('300'),
            min_height_cm=Decimal('60'), max_height_cm=Decimal('250'),
            description="Sistema corredizo de 2 hojas, adaptable a dimensiones.",
            bom=[
                BOMItem(material_id=mat1.id, material_type=MaterialType.PERFIL, quantity_formula="width_m", description="Riel Superior"),
                BOMItem(material_id=mat3.id, material_type=MaterialType.PERFIL, quantity_formula="width_m", description="Zoclo Inferior"),
                BOMItem(material_id=mat2.id, material_type=MaterialType.PERFIL, quantity_formula="2 * height_m", description="Jambas Laterales"),
                BOMItem(material_id=mat2.id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m / 2)", description="Cabezales de Hojas"), # Ancho de hoja * 2
                BOMItem(material_id=mat3.id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m / 2)", description="Zoclos de Hojas"), # Ancho de hoja * 2
                BOMItem(material_id=mat4.id, material_type=MaterialType.PERFIL, quantity_formula="height_m", description="Traslape Vertical"),
                BOMItem(material_id=mat5.id, material_type=MaterialType.HERRAJE, quantity_formula="4", description="Rodamientos (4 por ventana)"),
                BOMItem(material_id=mat6.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4 * (width_m / 2 + height_m)", description="Felpa para Hojas (perímetro de 2 hojas)"),
                BOMItem(material_id=mat7.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.5", description="Silicona (medio cartucho)"),
                BOMItem(material_id=mat8.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="20", description="Pijas (cantidad fija)"),
                BOMItem(material_id=mat15.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4 * 2", description="Cuñas de hule (4 por paño, 2 paños)"),
            ]
        ))

        self.create_product(AppProduct(
            name="Ventana Fija (Línea 3\")",
            window_type=WindowType.FIJA,
            aluminum_line=AluminumLine.SERIE_3,
            min_width_cm=Decimal('50'), max_width_cm=Decimal('200'),
            min_height_cm=Decimal('50'), max_height_cm=Decimal('180'),
            description="Sistema fijo para iluminación, adaptable a dimensiones.",
            bom=[
                BOMItem(material_id=mat13.id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Marco Perimetral Escalonado"),
                BOMItem(material_id=mat14.id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Junquillo de sujeción de vidrio"),
                BOMItem(material_id=mat7.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.3", description="Silicona (cantidad fija)"),
                BOMItem(material_id=mat8.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="10", description="Pijas (cantidad fija)"),
                BOMItem(material_id=mat15.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4", description="Cuñas de hule (4 por paño)"),
            ]
        ))

        self.create_product(AppProduct(
            name="Ventana Proyectada (Serie 35)",
            window_type=WindowType.PROYECTANTE,
            aluminum_line=AluminumLine.SERIE_35,
            min_width_cm=Decimal('40'), max_width_cm=Decimal('120'),
            min_height_cm=Decimal('40'), max_height_cm=Decimal('100'),
            description="Sistema proyectante para ventilación, adaptable a dimensiones.",
            bom=[
                BOMItem(material_id=mat9.id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Contramarco Fijo"),
                BOMItem(material_id=mat10.id, material_type=MaterialType.PERFIL, quantity_formula="2 * (width_m + height_m)", description="Marco Móvil de Hoja"),
                BOMItem(material_id=mat11.id, material_type=MaterialType.HERRAJE, quantity_formula="2", description="Brazos Proyectantes (2 por ventana)"),
                BOMItem(material_id=mat12.id, material_type=MaterialType.HERRAJE, quantity_formula="1", description="Cremona (1 por ventana)"),
                BOMItem(material_id=mat7.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="0.4", description="Silicona (cantidad fija)"),
                BOMItem(material_id=mat8.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="15", description="Pijas (cantidad fija)"),
                BOMItem(material_id=mat15.id, material_type=MaterialType.CONSUMIBLE, quantity_formula="4", description="Cuñas de hule (4 por paño)"),
            ]
        ))


    # --- Métodos para Materiales ---
    def get_all_materials(self) -> List[AppMaterial]:
        return list(self.materials_db.values())

    def get_material(self, material_id: int) -> Optional[AppMaterial]:
        return self.materials_db.get(material_id)

    def create_material(self, material: AppMaterial) -> AppMaterial:
        material.id = self._next_material_id
        self.materials_db[self._next_material_id] = material
        self._next_material_id += 1
        return material

    def update_material(self, material_id: int, updated_material: AppMaterial) -> Optional[AppMaterial]:
        if material_id not in self.materials_db:
            return None
        updated_material.id = material_id
        self.materials_db[material_id] = updated_material
        return updated_material

    def delete_material(self, material_id: int) -> bool:
        if material_id in self.materials_db:
            del self.materials_db[material_id]
            # También eliminar el material de cualquier BOM que lo contenga
            for product_id in list(self.products_db.keys()):
                product = self.products_db[product_id]
                product.bom = [item for item in product.bom if item.material_id != material_id]
            return True
        return False

    # --- Métodos para Productos (Ventanas con BOM) ---
    def get_all_products(self) -> List[AppProduct]:
        return list(self.products_db.values())

    def get_product(self, product_id: int) -> Optional[AppProduct]:
        return self.products_db.get(product_id)

    def create_product(self, product: AppProduct) -> AppProduct:
        product.id = self._next_product_id
        self.products_db[self._next_product_id] = product
        self._next_product_id += 1
        return product

    def update_product(self, product_id: int, updated_product: AppProduct) -> Optional[AppProduct]:
        if product_id not in self.products_db:
            return None
        updated_product.id = product_id
        self.products_db[product_id] = updated_product
        return updated_product

    def delete_product(self, product_id: int) -> bool:
        if product_id in self.products_db:
            del self.products_db[product_id]
            return True
        return False

    # --- Métodos de Utilidad para cálculos ---
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