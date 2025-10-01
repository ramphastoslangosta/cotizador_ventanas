"""Quote Routes

Extracted from main.py as part of TASK-20250929-002
Handles quote creation, calculation, viewing, editing, and PDF generation
"""

import math
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db, User, DatabaseQuoteService, DatabaseColorService, DatabaseCompanyService
from services.product_bom_service_db import ProductBOMServiceDB
from services.pdf_service import PDFQuoteService
from app.dependencies.auth import get_current_user_flexible, get_current_user_from_cookie
from security.formula_evaluator import formula_evaluator
from config import settings

# Import models
from models.quote_models import (
    WindowType, AluminumLine, GlassType,
    Client, QuoteRequest, WindowItem, WindowCalculation, QuoteCalculation
)
from models.product_bom_models import MaterialUnit, MaterialType

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router
router = APIRouter()


# === HELPER FUNCTIONS ===
def round_currency(amount: Decimal) -> Decimal:
    """Round currency to 2 decimal places"""
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def round_measurement(measurement: Decimal) -> Decimal:
    """Round measurements to 3 decimal places"""
    return measurement.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


# === CALCULATION FUNCTIONS ===
def calculate_window_item_from_bom(
    item: WindowItem,
    product_bom_service: ProductBOMServiceDB,
    global_labor_rate_per_m2_override: Optional[Decimal] = None
) -> WindowCalculation:
    """
    Calculate window item cost using dynamic BOM from database

    This is a complex calculation function that:
    - Retrieves product BOM from database
    - Evaluates material quantity formulas safely
    - Applies waste factors
    - Handles color-specific pricing for profiles
    - Calculates glass and labor costs
    """

    product = product_bom_service.get_product(item.product_bom_id)
    if not product:
        raise ValueError(f"Producto BOM con ID {item.product_bom_id} no encontrado.")

    # Validate dimensions against product ranges
    if not (product.min_width_cm <= item.width_cm <= product.max_width_cm and
            product.min_height_cm <= item.height_cm <= product.max_height_cm):
        raise ValueError(
            f"Dimensiones ({item.width_cm}x{item.height_cm}cm) fuera del rango permitido para el producto "
            f"'{product.name}' ({product.min_width_cm}-{product.max_width_cm}cm x "
            f"{product.min_height_cm}-{product.max_height_cm}cm)."
        )

    # Calculate base measurements for formulas
    width_m = item.width_cm / Decimal('100')
    height_m = item.height_cm / Decimal('100')
    area_m2 = width_m * height_m
    perimeter_m = 2 * (width_m + height_m)

    # Variables available for formulas
    formula_vars = {
        'width_m': width_m,
        'height_m': height_m,
        'width_cm': item.width_cm,
        'height_cm': item.height_cm,
        'quantity': item.quantity,
        'area_m2': area_m2,
        'perimeter_m': perimeter_m,
    }

    # Initialize detailed costs by material type
    total_profiles_cost = Decimal('0')
    total_glass_cost = Decimal('0')
    total_hardware_cost = Decimal('0')
    total_consumables_cost = Decimal('0')

    # Calculate material costs from BOM
    for bom_item in product.bom:
        material = product_bom_service.get_material(bom_item.material_id)
        if not material:
            raise ValueError(
                f"Material con ID {bom_item.material_id} referenciado en BOM de "
                f"'{product.name}' no encontrado."
            )

        try:
            # Evaluate formula safely to get net quantity for ONE window
            quantity_net_for_one_window = formula_evaluator.evaluate_formula(
                bom_item.quantity_formula, formula_vars
            )
            if quantity_net_for_one_window < 0:
                quantity_net_for_one_window = Decimal('0')
        except Exception as e:
            raise ValueError(
                f"Error al evaluar fórmula '{bom_item.quantity_formula}' para material "
                f"'{material.name}': {e}"
            )

        # Apply waste factor
        quantity_with_waste_for_one_window = quantity_net_for_one_window * bom_item.waste_factor

        # Adjust for selling unit if it's a profile
        final_quantity_to_cost = quantity_with_waste_for_one_window
        if material.selling_unit_length_m and material.unit == MaterialUnit.ML:
            num_selling_units = math.ceil(
                quantity_with_waste_for_one_window / material.selling_unit_length_m
            )
            final_quantity_to_cost = Decimal(str(num_selling_units)) * material.selling_unit_length_m

        # Determine price per unit (considering color for profiles)
        price_per_unit = material.cost_per_unit
        if bom_item.material_type == MaterialType.PERFIL and item.selected_profile_color:
            # Look up color-specific price for this material
            color_service = DatabaseColorService(product_bom_service.db)
            color_price = color_service.get_material_color_price(
                material.id, item.selected_profile_color
            )
            if color_price:
                price_per_unit = color_price

        # Cost of this material for ONE window
        cost_for_this_material_per_product_unit = final_quantity_to_cost * price_per_unit

        # Add to category total, multiplied by quantity of windows in quote item
        total_cost_for_item_quantity = cost_for_this_material_per_product_unit * item.quantity

        if bom_item.material_type == MaterialType.PERFIL:
            total_profiles_cost += total_cost_for_item_quantity
        elif bom_item.material_type == MaterialType.HERRAJE:
            total_hardware_cost += total_cost_for_item_quantity
        elif bom_item.material_type == MaterialType.CONSUMIBLE:
            total_consumables_cost += total_cost_for_item_quantity

    # Calculate glass cost
    glass_cost_per_m2 = product_bom_service.get_glass_cost_per_m2(item.selected_glass_type)
    glass_waste_factor = Decimal('1.05')
    total_glass_cost = area_m2 * glass_cost_per_m2 * glass_waste_factor * item.quantity
    total_glass_cost = round_currency(total_glass_cost)

    # Calculate labor cost
    if global_labor_rate_per_m2_override is not None:
        labor_cost = area_m2 * global_labor_rate_per_m2_override * item.quantity
    else:
        labor_data = product_bom_service.get_labor_cost_data(product.window_type)
        if not labor_data:
            raise ValueError(f"Costo de mano de obra no encontrado para tipo de ventana: {product.window_type}")

        labor_cost_per_m2_effective = labor_data.cost_per_m2 * labor_data.complexity_factor
        labor_cost = area_m2 * labor_cost_per_m2_effective * item.quantity
    labor_cost = round_currency(labor_cost)

    # Subtotal for this item
    subtotal = (total_profiles_cost + total_glass_cost +
                total_hardware_cost + total_consumables_cost + labor_cost)
    subtotal = round_currency(subtotal)

    return WindowCalculation(
        product_bom_id=product.id,
        product_bom_name=product.name,
        window_type=product.window_type,
        aluminum_line=product.aluminum_line,
        selected_glass_type=item.selected_glass_type,
        width_cm=item.width_cm,
        height_cm=item.height_cm,
        quantity=item.quantity,
        area_m2=round_measurement(area_m2),
        perimeter_m=round_measurement(perimeter_m),
        total_profiles_cost=round_currency(total_profiles_cost),
        total_glass_cost=round_currency(total_glass_cost),
        total_hardware_cost=round_currency(total_hardware_cost),
        total_consumables_cost=round_currency(total_consumables_cost),
        labor_cost=labor_cost,
        subtotal=subtotal,
        # Compatibility fields
        aluminum_length_needed=Decimal('0'),
        aluminum_cost=total_profiles_cost + total_hardware_cost + total_consumables_cost,
        glass_area_needed=Decimal('0'),
        hardware_cost=total_hardware_cost
    )


def calculate_complete_quote(quote_request: QuoteRequest, db: Session) -> QuoteCalculation:
    """
    Calculate complete quote using database

    Processes all items in quote request and applies:
    - Material costs per item
    - Labor costs per item
    - Profit margin
    - Indirect costs
    - Taxes
    """

    product_bom_service = ProductBOMServiceDB(db)

    calculated_items = []
    materials_subtotal = Decimal('0')
    labor_subtotal = Decimal('0')

    # Use values from QuoteRequest if provided, otherwise use defaults
    current_profit_margin = (
        quote_request.profit_margin if quote_request.profit_margin is not None
        else Decimal(str(settings.default_profit_margin))
    )
    current_indirect_costs_rate = (
        quote_request.indirect_costs_rate if quote_request.indirect_costs_rate is not None
        else Decimal(str(settings.default_indirect_costs))
    )
    current_tax_rate = (
        quote_request.tax_rate if quote_request.tax_rate is not None
        else Decimal(str(settings.default_tax_rate))
    )
    current_labor_rate_per_m2_override = quote_request.labor_rate_per_m2_override

    for item in quote_request.items:
        window_calc = calculate_window_item_from_bom(
            item, product_bom_service,
            global_labor_rate_per_m2_override=current_labor_rate_per_m2_override
        )
        calculated_items.append(window_calc)

        materials_subtotal += (
            window_calc.total_profiles_cost +
            window_calc.total_glass_cost +
            window_calc.total_hardware_cost +
            window_calc.total_consumables_cost
        )
        labor_subtotal += window_calc.labor_cost

    subtotal_before_overhead = materials_subtotal + labor_subtotal

    profit_amount = subtotal_before_overhead * current_profit_margin
    indirect_costs_amount = subtotal_before_overhead * current_indirect_costs_rate
    subtotal_with_overhead = subtotal_before_overhead + profit_amount + indirect_costs_amount

    tax_amount = subtotal_with_overhead * current_tax_rate
    total_final = subtotal_with_overhead + tax_amount

    result = QuoteCalculation(
        client=quote_request.client,
        items=calculated_items,
        materials_subtotal=round_currency(materials_subtotal),
        labor_subtotal=round_currency(labor_subtotal),
        subtotal_before_overhead=round_currency(subtotal_before_overhead),
        profit_amount=round_currency(profit_amount),
        indirect_costs_amount=round_currency(indirect_costs_amount),
        subtotal_with_overhead=round_currency(subtotal_with_overhead),
        tax_amount=round_currency(tax_amount),
        total_final=round_currency(total_final),
        calculated_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        notes=quote_request.notes
    )

    return result


# === WEB PAGE ROUTES (HTML) ===
@router.get("/quotes/new", response_class=HTMLResponse)
async def new_quote_page(request: Request, db: Session = Depends(get_db)):
    """Display new quote creation page"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Get products and materials from database
    product_bom_service = ProductBOMServiceDB(db)
    materials_for_frontend = product_bom_service.get_all_materials()
    products_for_frontend = product_bom_service.get_all_products()

    # Map enums for frontend
    window_types_display = [
        {"value": wt.value, "label": wt.value.replace('_', ' ').title()} for wt in WindowType
    ]
    aluminum_lines_display = [
        {"value": al.value, "label": al.value.replace('_', ' ').title()} for al in AluminumLine
    ]
    glass_types_display = [
        {"value": gt.value, "label": gt.value.replace('_', ' ').title()} for gt in GlassType
    ]

    # Convert to JSON-compatible format
    app_materials_json_compatible = [m.model_dump(mode='json') for m in materials_for_frontend]
    app_products_json_compatible = [p.model_dump(mode='json') for p in products_for_frontend]

    return templates.TemplateResponse("new_quote.html", {
        "request": request,
        "title": "Nueva Cotización",
        "user": user,
        "app_materials": app_materials_json_compatible,
        "app_products": app_products_json_compatible,
        "window_types": window_types_display,
        "aluminum_lines": aluminum_lines_display,
        "glass_types": glass_types_display,
        "business_overhead": {
            "profit_margin": settings.default_profit_margin,
            "indirect_costs": settings.default_indirect_costs,
            "tax_rate": settings.default_tax_rate
        }
    })


@router.get("/quotes", response_class=HTMLResponse)
async def quotes_list_page(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    per_page: int = 20
):
    """Display list of user's quotes with pagination"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    quote_service = DatabaseQuoteService(db)

    # Get paginated quotes
    offset = (page - 1) * per_page
    user_quotes = quote_service.get_quotes_by_user(user.id, limit=per_page, offset=offset)

    # Get total count for pagination
    all_quotes = quote_service.get_quotes_by_user(user.id, limit=10000)
    total_quotes = len(all_quotes)
    total_pages = (total_quotes + per_page - 1) // per_page

    from datetime import date
    today = date.today()

    return templates.TemplateResponse("quotes_list.html", {
        "request": request,
        "title": "Mis Cotizaciones",
        "user": user,
        "quotes": user_quotes,
        "page": page,
        "per_page": per_page,
        "total_quotes": total_quotes,
        "total_pages": total_pages,
        "today": today
    })


@router.get("/quotes/{quote_id}", response_class=HTMLResponse)
async def view_quote_page(
    quote_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Display specific quote details"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    quote_service = DatabaseQuoteService(db)
    quote = quote_service.get_quote_by_id(quote_id, user.id)

    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    return templates.TemplateResponse("view_quote.html", {
        "request": request,
        "title": f"Cotización #{quote.id}",
        "user": user,
        "quote": quote
    })


@router.get("/quotes/{quote_id}/edit", response_class=HTMLResponse)
async def edit_quote_page(
    quote_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Display quote editing page (QE-001)"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    quote_service = DatabaseQuoteService(db)
    quote = quote_service.get_quote_by_id(quote_id, user.id)

    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # Get products and materials for editing
    product_bom_service = ProductBOMServiceDB(db)
    materials_for_frontend = product_bom_service.get_all_materials()
    products_for_frontend = product_bom_service.get_all_products()

    # Map enums for frontend
    window_types_display = [
        {"value": wt.value, "label": wt.value.replace('_', ' ').title()} for wt in WindowType
    ]
    aluminum_lines_display = [
        {"value": al.value, "label": al.value.replace('_', ' ').title()} for al in AluminumLine
    ]
    glass_types_display = [
        {"value": gt.value, "label": gt.value.replace('_', ' ').title()} for gt in GlassType
    ]

    # Convert to JSON-compatible
    app_materials_json_compatible = [m.model_dump(mode='json') for m in materials_for_frontend]
    app_products_json_compatible = [p.model_dump(mode='json') for p in products_for_frontend]

    return templates.TemplateResponse("edit_quote.html", {
        "request": request,
        "title": f"Editar Cotización #{quote.id}",
        "user": user,
        "quote": quote,
        "app_materials": app_materials_json_compatible,
        "app_products": app_products_json_compatible,
        "window_types": window_types_display,
        "aluminum_lines": aluminum_lines_display,
        "glass_types": glass_types_display,
    })


# === API ROUTES (JSON) ===
@router.post("/quotes/calculate_item", response_model=WindowCalculation)
async def calculate_single_window_item(
    item_request: WindowItem,
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Calculate single window item cost"""
    try:
        # Get labor override if provided
        labor_override_param = request.query_params.get("labor_rate_override")
        labor_override_decimal = Decimal(labor_override_param) if labor_override_param else None

        product_bom_service = ProductBOMServiceDB(db)
        result = calculate_window_item_from_bom(
            item_request, product_bom_service,
            global_labor_rate_per_m2_override=labor_override_decimal
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el cálculo del ítem: {str(e)}")


@router.post("/quotes/calculate", response_model=QuoteCalculation)
async def calculate_quote_main(
    quote_request: QuoteRequest,
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Calculate complete quote and save to database"""
    try:
        result = calculate_complete_quote(quote_request, db)

        # Save quote to database
        quote_service = DatabaseQuoteService(db)
        quote_data_for_db = {
            'client_name': result.client.name,
            'client_email': result.client.email,
            'client_phone': result.client.phone,
            'client_address': result.client.address,
            'total_final': result.total_final,
            'materials_subtotal': result.materials_subtotal,
            'labor_subtotal': result.labor_subtotal,
            'profit_amount': result.profit_amount,
            'indirect_costs_amount': result.indirect_costs_amount,
            'tax_amount': result.tax_amount,
            'items_count': len(result.items),
            'quote_data': result.model_dump(mode='json'),
            'notes': result.notes,
            'valid_until': result.valid_until
        }
        saved_quote = quote_service.create_quote(
            user_id=current_user.id,
            quote_data=quote_data_for_db
        )

        # Assign saved quote ID
        result.quote_id = saved_quote.id

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el cálculo: {str(e)}")


@router.post("/quotes/example")
async def create_example_quote_main(
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Create an example quote for testing"""
    # Implementation can be added if needed
    raise HTTPException(status_code=501, detail="Example quote endpoint not yet implemented")


@router.get("/quotes/{quote_id}/pdf")
async def generate_quote_pdf(
    quote_id: int,
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Generate PDF for a specific quote"""
    try:
        quote_service = DatabaseQuoteService(db)
        company_service = DatabaseCompanyService(db)

        # Get quote
        quote = quote_service.get_quote_by_id(quote_id, current_user.id)
        if not quote:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")

        # Get company information
        company = company_service.get_or_create_company(current_user.id)
        company_info = {
            'name': company.name,
            'address': company.address,
            'phone': company.phone,
            'email': company.email,
            'website': company.website,
            'logo_path': company.logo_path
        }

        # Generate PDF
        pdf_service = PDFQuoteService()
        pdf_bytes = pdf_service.generate_quote_pdf(quote, company_info)

        # Return PDF response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=cotizacion_{quote_id}.pdf"
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")


@router.put("/api/quotes/{quote_id}", response_model=QuoteCalculation)
async def update_quote(
    quote_id: int,
    quote_request: QuoteRequest,
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Update existing quote (QE-001)"""
    try:
        # Verify quote exists and belongs to user
        quote_service = DatabaseQuoteService(db)
        existing_quote = quote_service.get_quote_by_id(quote_id, current_user.id)

        if not existing_quote:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")

        # Recalculate with new data
        result = calculate_complete_quote(quote_request, db)

        # Update quote in database
        quote_data_for_db = {
            'client_name': result.client.name,
            'client_email': result.client.email,
            'client_phone': result.client.phone,
            'client_address': result.client.address,
            'total_final': result.total_final,
            'materials_subtotal': result.materials_subtotal,
            'labor_subtotal': result.labor_subtotal,
            'profit_amount': result.profit_amount,
            'indirect_costs_amount': result.indirect_costs_amount,
            'tax_amount': result.tax_amount,
            'items_count': len(result.items),
            'quote_data': result.model_dump(mode='json'),
            'notes': result.notes,
            'valid_until': result.valid_until
        }

        updated_quote = quote_service.update_quote(quote_id, current_user.id, quote_data_for_db)

        if not updated_quote:
            raise HTTPException(status_code=404, detail="Error actualizando cotización")

        # Return recalculated result with ID
        result.quote_id = quote_id
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error actualizando cotización: {str(e)}")


@router.get("/api/quotes/{quote_id}/edit-data")
async def get_quote_edit_data(
    quote_id: int,
    request: Request,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get quote data formatted for editing (QE-001)"""
    try:
        quote_service = DatabaseQuoteService(db)
        quote = quote_service.get_quote_by_id(quote_id, current_user.id)

        if not quote:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")

        # Return quote data in format suitable for editing
        return {
            "quote_id": quote.id,
            "client": {
                "name": quote.client_name,
                "email": quote.client_email,
                "phone": quote.client_phone,
                "address": quote.client_address
            },
            "quote_data": quote.quote_data,
            "notes": quote.notes
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de cotización: {str(e)}")