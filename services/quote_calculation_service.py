# services/quote_calculation_service.py
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
from datetime import datetime, timedelta
import math

from models.quote_models import (
    QuoteRequest, QuoteCalculation, WindowCalculation, WindowItem,
    Material, Glass, Hardware, LaborCost, BusinessOverhead,
    WindowType, AluminumLine, GlassType
)

class QuoteCalculationService:
    """Servicio para realizar cálculos de cotizaciones"""
    
    def __init__(self):
        # En producción, estos datos vendrían de la base de datos
        self.materials_db = self._load_materials_mock()
        self.glass_db = self._load_glass_mock()
        self.hardware_db = self._load_hardware_mock()
        self.labor_costs_db = self._load_labor_costs_mock()
        self.business_overhead = self._load_business_overhead_mock()
    
    def calculate_quote(self, quote_request: QuoteRequest) -> QuoteCalculation:
        """Calcular cotización completa"""
        
        # Calcular cada ítem
        calculated_items = []
        materials_subtotal = Decimal('0')
        labor_subtotal = Decimal('0')
        
        for item in quote_request.items:
            window_calc = self._calculate_window_item(item)
            calculated_items.append(window_calc)
            materials_subtotal += (window_calc.aluminum_cost + 
                                 window_calc.glass_cost + 
                                 window_calc.hardware_cost)
            labor_subtotal += window_calc.labor_cost
        
        # Subtotal antes de gastos generales
        subtotal_before_overhead = materials_subtotal + labor_subtotal
        
        # Aplicar gastos generales
        overhead = self.business_overhead
        profit_amount = subtotal_before_overhead * overhead.profit_margin
        indirect_costs_amount = subtotal_before_overhead * overhead.indirect_costs
        subtotal_with_overhead = subtotal_before_overhead + profit_amount + indirect_costs_amount
        
        # Calcular impuestos
        tax_amount = subtotal_with_overhead * overhead.tax_rate
        total_final = subtotal_with_overhead + tax_amount
        
        # Crear resultado
        return QuoteCalculation(
            client=quote_request.client,
            items=calculated_items,
            materials_subtotal=self._round_currency(materials_subtotal),
            labor_subtotal=self._round_currency(labor_subtotal),
            subtotal_before_overhead=self._round_currency(subtotal_before_overhead),
            profit_amount=self._round_currency(profit_amount),
            indirect_costs_amount=self._round_currency(indirect_costs_amount),
            subtotal_with_overhead=self._round_currency(subtotal_with_overhead),
            tax_amount=self._round_currency(tax_amount),
            total_final=self._round_currency(total_final),
            calculated_at=datetime.now(),
            valid_until=datetime.now() + timedelta(days=30),
            notes=quote_request.notes
        )
    
    def _calculate_window_item(self, item: WindowItem) -> WindowCalculation:
        """Calcular costos para un ítem de ventana"""
        
        # Conversiones de medidas
        width_m = item.width_cm / Decimal('100')
        height_m = item.height_cm / Decimal('100')
        area_m2 = width_m * height_m
        perimeter_m = 2 * (width_m + height_m)
        
        # Obtener datos de materiales
        material = self._get_material(item.aluminum_line)
        glass = self._get_glass(item.glass_type)
        hardware = self._get_hardware(item.window_type)
        labor_cost_data = self._get_labor_cost(item.window_type)
        
        # Calcular cantidades necesarias (con factores de desperdicio)
        aluminum_length_needed = perimeter_m * material.waste_factor * item.quantity
        glass_area_needed = area_m2 * glass.waste_factor * item.quantity
        
        # Calcular costos
        aluminum_cost = aluminum_length_needed * material.cost_per_meter
        glass_cost = glass_area_needed * glass.cost_per_m2
        hardware_cost = Decimal(str(item.quantity)) * hardware.cost_per_unit
        labor_cost = area_m2 * item.quantity * labor_cost_data.cost_per_m2 * labor_cost_data.complexity_factor
        
        subtotal = aluminum_cost + glass_cost + hardware_cost + labor_cost
        
        return WindowCalculation(
            window_type=item.window_type,
            aluminum_line=item.aluminum_line,
            glass_type=item.glass_type,
            width_cm=item.width_cm,
            height_cm=item.height_cm,
            quantity=item.quantity,
            area_m2=self._round_measurement(area_m2),
            perimeter_m=self._round_measurement(perimeter_m),
            aluminum_length_needed=self._round_measurement(aluminum_length_needed),
            aluminum_cost=self._round_currency(aluminum_cost),
            glass_area_needed=self._round_measurement(glass_area_needed),
            glass_cost=self._round_currency(glass_cost),
            hardware_cost=self._round_currency(hardware_cost),
            labor_cost=self._round_currency(labor_cost),
            subtotal=self._round_currency(subtotal)
        )
    
    def _get_material(self, aluminum_line: AluminumLine) -> Material:
        """Obtener datos del material de aluminio"""
        for material in self.materials_db:
            if material.aluminum_line == aluminum_line:
                return material
        raise ValueError(f"Material no encontrado para línea: {aluminum_line}")
    
    def _get_glass(self, glass_type: GlassType) -> Glass:
        """Obtener datos del tipo de vidrio"""
        for glass in self.glass_db:
            if glass.glass_type == glass_type:
                return glass
        raise ValueError(f"Vidrio no encontrado: {glass_type}")
    
    def _get_hardware(self, window_type: WindowType) -> Hardware:
        """Obtener herrajes compatibles con el tipo de ventana"""
        for hardware in self.hardware_db:
            if window_type in hardware.window_types:
                return hardware
        raise ValueError(f"Herraje no encontrado para tipo de ventana: {window_type}")
    
    def _get_labor_cost(self, window_type: WindowType) -> LaborCost:
        """Obtener costo de mano de obra para el tipo de ventana"""
        for labor in self.labor_costs_db:
            if labor.window_type == window_type:
                return labor
        raise ValueError(f"Costo de mano de obra no encontrado: {window_type}")
    
    def _round_currency(self, amount: Decimal) -> Decimal:
        """Redondear moneda a 2 decimales"""
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _round_measurement(self, measurement: Decimal) -> Decimal:
        """Redondear medidas a 3 decimales"""
        return measurement.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    
    # Datos mock (en producción vendrían de la base de datos)
    def _load_materials_mock(self) -> List[Material]:
        return [
            Material(id=1, name="Perfil Línea 20", aluminum_line=AluminumLine.LINEA_20, 
                    cost_per_meter=Decimal('45.50'), waste_factor=Decimal('1.10')),
            Material(id=2, name="Perfil Línea 25", aluminum_line=AluminumLine.LINEA_25, 
                    cost_per_meter=Decimal('52.75'), waste_factor=Decimal('1.10')),
            Material(id=3, name="Perfil Línea 30", aluminum_line=AluminumLine.LINEA_30, 
                    cost_per_meter=Decimal('68.90'), waste_factor=Decimal('1.08')),
            Material(id=4, name="Perfil Línea 40", aluminum_line=AluminumLine.LINEA_40, 
                    cost_per_meter=Decimal('89.50'), waste_factor=Decimal('1.08')),
            Material(id=5, name="Perfil Europea", aluminum_line=AluminumLine.EUROPEA, 
                    cost_per_meter=Decimal('125.00'), waste_factor=Decimal('1.05')),
        ]
    
    def _load_glass_mock(self) -> List[Glass]:
        return [
            Glass(id=1, name="Vidrio Claro 4mm", glass_type=GlassType.CLARO_4MM, 
                  cost_per_m2=Decimal('85.00'), thickness=4, waste_factor=Decimal('1.05')),
            Glass(id=2, name="Vidrio Claro 6mm", glass_type=GlassType.CLARO_6MM, 
                  cost_per_m2=Decimal('120.00'), thickness=6, waste_factor=Decimal('1.05')),
            Glass(id=3, name="Vidrio Bronce 4mm", glass_type=GlassType.BRONCE_4MM, 
                  cost_per_m2=Decimal('95.00'), thickness=4, waste_factor=Decimal('1.05')),
            Glass(id=4, name="Vidrio Bronce 6mm", glass_type=GlassType.BRONCE_6MM, 
                  cost_per_m2=Decimal('135.00'), thickness=6, waste_factor=Decimal('1.05')),
            Glass(id=5, name="Vidrio Reflectivo 6mm", glass_type=GlassType.REFLECTIVO_6MM, 
                  cost_per_m2=Decimal('180.00'), thickness=6, waste_factor=Decimal('1.08')),
            Glass(id=6, name="Vidrio Laminado 6mm", glass_type=GlassType.LAMINADO_6MM, 
                  cost_per_m2=Decimal('220.00'), thickness=6, waste_factor=Decimal('1.10')),
            Glass(id=7, name="Vidrio Templado 6mm", glass_type=GlassType.TEMPLADO_6MM, 
                  cost_per_m2=Decimal('195.00'), thickness=6, waste_factor=Decimal('1.08')),
        ]
    
    def _load_hardware_mock(self) -> List[Hardware]:
        return [
            Hardware(id=1, name="Herraje Ventana Fija", window_types=[WindowType.FIJA], 
                    cost_per_unit=Decimal('25.00')),
            Hardware(id=2, name="Herraje Corrediza Estándar", window_types=[WindowType.CORREDIZA], 
                    cost_per_unit=Decimal('85.00')),
            Hardware(id=3, name="Herraje Abatible", window_types=[WindowType.ABATIBLE], 
                    cost_per_unit=Decimal('120.00')),
            Hardware(id=4, name="Herraje Oscilobatiente", window_types=[WindowType.OSCILOBATIENTE], 
                    cost_per_unit=Decimal('180.00')),
            Hardware(id=5, name="Herraje Proyectante", window_types=[WindowType.PROYECTANTE], 
                    cost_per_unit=Decimal('95.00')),
        ]
    
    def _load_labor_costs_mock(self) -> List[LaborCost]:
        return [
            LaborCost(id=1, window_type=WindowType.FIJA, cost_per_m2=Decimal('45.00'), 
                     complexity_factor=Decimal('1.0')),
            LaborCost(id=2, window_type=WindowType.CORREDIZA, cost_per_m2=Decimal('65.00'), 
                     complexity_factor=Decimal('1.2')),
            LaborCost(id=3, window_type=WindowType.ABATIBLE, cost_per_m2=Decimal('75.00'), 
                     complexity_factor=Decimal('1.4')),
            LaborCost(id=4, window_type=WindowType.OSCILOBATIENTE, cost_per_m2=Decimal('95.00'), 
                     complexity_factor=Decimal('1.6')),
            LaborCost(id=5, window_type=WindowType.PROYECTANTE, cost_per_m2=Decimal('70.00'), 
                     complexity_factor=Decimal('1.3')),
        ]
    
    def _load_business_overhead_mock(self) -> BusinessOverhead:
        return BusinessOverhead(
            profit_margin=Decimal('0.25'),      # 25% de utilidad
            indirect_costs=Decimal('0.15'),     # 15% de gastos indirectos
            tax_rate=Decimal('0.16')            # 16% de IVA
        )