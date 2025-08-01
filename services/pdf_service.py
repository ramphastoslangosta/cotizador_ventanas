# services/pdf_service.py - Servicio para generación de PDFs de cotizaciones
from typing import Dict, List
from decimal import Decimal
from datetime import datetime
import io
import os
import base64
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from models.quote_models import QuoteCalculation

class PDFQuoteService:
    """Servicio para generar PDFs profesionales de cotizaciones"""
    
    def __init__(self):
        # Configurar Jinja2 para templates de PDF
        self.env = Environment(loader=FileSystemLoader('templates'))
    
    def get_logo_base64(self, logo_path: str) -> str:
        """Convierte una imagen a base64 para uso en PDF"""
        try:
            if not logo_path or not os.path.exists(logo_path):
                return None
                
            with open(logo_path, "rb") as image_file:
                base64_data = base64.b64encode(image_file.read()).decode('utf-8')
                
                # Detectar tipo de imagen por extensión
                file_extension = os.path.splitext(logo_path)[1].lower()
                if file_extension in ['.png']:
                    mime_type = 'image/png'
                elif file_extension in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif file_extension in ['.svg']:
                    mime_type = 'image/svg+xml'
                else:
                    mime_type = 'image/png'  # default
                
                return f"data:{mime_type};base64,{base64_data}"
        except Exception as e:
            print(f"Error cargando logo: {e}")
            return None
    
    def calculate_unit_selling_prices(self, quote: QuoteCalculation) -> List[Dict]:
        """
        Calcula los precios unitarios de venta para cada producto.
        
        Lógica:
        1. Toma el subtotal_with_overhead (precio sin IVA)
        2. Lo distribuye proporcionalmente entre los productos según su costo relativo
        3. Calcula el precio unitario de venta dividiendo entre la cantidad
        
        Args:
            quote: QuoteCalculation con los datos de la cotización
            
        Returns:
            List[Dict]: Lista con información de productos y precios de venta
        """
        products_info = []
        
        # Calcular el costo total de todos los productos (sin overhead)
        total_cost_before_overhead = sum(item.subtotal for item in quote.items)
        
        # El precio total de venta es el subtotal con overhead (sin IVA)
        total_selling_price = quote.subtotal_with_overhead
        
        for item in quote.items:
            # Calcular la proporción de este producto respecto al costo total
            cost_proportion = item.subtotal / total_cost_before_overhead if total_cost_before_overhead > 0 else 0
            
            # Asignar proporcionalmente el precio de venta sin IVA
            item_selling_price_total = total_selling_price * cost_proportion
            
            # Calcular precio unitario de venta
            unit_selling_price = item_selling_price_total / item.quantity if item.quantity > 0 else Decimal('0')
            
            product_info = {
                'product_bom_name': item.product_bom_name,
                'description': f"{item.window_type.value.title()} - {item.aluminum_line.value.replace('_', ' ').title()}",
                'dimensions': f"{item.width_cm} × {item.height_cm} cm",
                'glass_type': item.selected_glass_type.value.replace('_', ' ').title(),
                'quantity': item.quantity,
                'area_m2': item.area_m2,
                'unit_cost': item.subtotal / item.quantity if item.quantity > 0 else Decimal('0'),  # Costo unitario
                'unit_selling_price': unit_selling_price,  # Precio unitario de venta
                'total_selling_price': item_selling_price_total,  # Precio total de venta de este item
                'cost_proportion': cost_proportion
            }
            products_info.append(product_info)
        
        return products_info
    
    def generate_quote_pdf(self, quote_data, company_info: Dict = None) -> bytes:
        """
        Genera un PDF profesional de la cotización
        
        Args:
            quote_data: Datos de la cotización (dict o QuoteCalculation)
            company_info: Información de la empresa (opcional)
            
        Returns:
            bytes: Contenido del PDF generado
        """
        # Convertir quote_data a QuoteCalculation si es necesario
        if isinstance(quote_data, dict):
            quote = QuoteCalculation(**quote_data)
        else:
            quote = quote_data
        
        # Información por defecto de la empresa (si no se proporciona)
        if company_info is None:
            company_info = {
                'name': 'Mi Empresa',
                'address': 'Dirección de mi empresa',
                'phone': '+52 999 123 4567',
                'email': 'contacto@miempresa.com',
                'website': 'www.miempresa.com',
                'rfc': 'RFC123456789'
            }
        
        # Calcular precios unitarios de venta
        products_info = self.calculate_unit_selling_prices(quote)
        
        # Convertir logo a base64 si existe
        logo_base64 = None
        if company_info.get('logo_path'):
            logo_base64 = self.get_logo_base64(company_info['logo_path'])
        
        # Preparar datos para el template
        template_data = {
            'quote': quote,
            'products': products_info,
            'company': company_info,
            'company_logo_base64': logo_base64,
            'generated_date': datetime.now(),
            'quote_number': f"COT-{quote.quote_id:05d}" if quote.quote_id else "COT-DRAFT",
            # Totales formateados
            'subtotal_before_overhead_formatted': f"${quote.subtotal_before_overhead:,.2f}",
            'profit_amount_formatted': f"${quote.profit_amount:,.2f}",
            'indirect_costs_amount_formatted': f"${quote.indirect_costs_amount:,.2f}",
            'subtotal_with_overhead_formatted': f"${quote.subtotal_with_overhead:,.2f}",
            'tax_amount_formatted': f"${quote.tax_amount:,.2f}",
            'total_final_formatted': f"${quote.total_final:,.2f}",
            # Cálculos adicionales
            'total_area': sum(p['area_m2'] for p in products_info),
            'total_windows': sum(p['quantity'] for p in products_info)
        }
        
        # Renderizar template HTML
        template = self.env.get_template('quote_pdf.html')
        html_content = template.render(**template_data)
        
        # CSS para el PDF
        css_content = """
        @page {
            size: A4;
            margin: 1cm;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #333;
        }
        
        .header {
            border-bottom: 2px solid #007bff;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        
        .header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .logo-section {
            flex: 0 0 auto;
            margin-right: 20px;
        }
        
        .company-logo {
            max-height: 80px;
            max-width: 150px;
            object-fit: contain;
        }
        
        .company-details {
            flex: 1;
            text-align: center;
        }
        
        .company-name {
            font-size: 24pt;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }
        
        .quote-title {
            font-size: 18pt;
            font-weight: bold;
            margin: 15px 0;
            text-align: center;
            color: #495057;
        }
        
        .info-section {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        
        .info-box {
            border: 1px solid #dee2e6;
            padding: 10px;
            border-radius: 5px;
            background-color: #f8f9fa;
        }
        
        .products-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 9pt;
        }
        
        .products-table th,
        .products-table td {
            border: 1px solid #dee2e6;
            padding: 8px;
            text-align: left;
        }
        
        .products-table th {
            background-color: #007bff;
            color: white;
            font-weight: bold;
            text-align: center;
        }
        
        .products-table td.number {
            text-align: right;
        }
        
        .products-table td.center {
            text-align: center;
        }
        
        .totals-section {
            margin-top: 20px;
            page-break-inside: avoid;
        }
        
        .totals-table {
            width: 50%;
            margin-left: auto;
            border-collapse: collapse;
        }
        
        .totals-table td {
            padding: 5px 10px;
            border: 1px solid #dee2e6;
        }
        
        .totals-table .label {
            background-color: #f8f9fa;
            font-weight: bold;
            text-align: right;
        }
        
        .totals-table .amount {
            text-align: right;
            background-color: white;
        }
        
        .total-final {
            background-color: #f8f9fa !important;
            color: black !important;
            font-weight: bold;
            font-size: 12pt;
            border: 2px solid #007bff;
        }
        
        .footer {
            margin-top: 30px;
            border-top: 1px solid #dee2e6;
            padding-top: 15px;
            font-size: 8pt;
            color: #6c757d;
            text-align: center;
        }
        
        .validity-note {
            margin-top: 20px;
            padding: 10px;
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            font-style: italic;
        }
        """
        
        # Generar PDF
        html_doc = HTML(string=html_content)
        css_doc = CSS(string=css_content)
        
        pdf_buffer = io.BytesIO()
        html_doc.write_pdf(pdf_buffer, stylesheets=[css_doc])
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue()
    
    def format_currency(self, amount: Decimal) -> str:
        """Formatea una cantidad como moneda"""
        return f"${amount:,.2f}"
    
    def format_percentage(self, rate: Decimal) -> str:
        """Formatea una tasa como porcentaje"""
        return f"{(rate * 100):.1f}%"