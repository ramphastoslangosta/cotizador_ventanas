"""
Materials and Products Routes
Extracted from main.py as part of TASK-20250929-003

This module contains all material and product catalog routes including:
- Material CRUD operations
- Product CRUD operations
- Material-Color relationships
- CSV import/export for both materials and products
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, File, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from database import (
    get_db,
    User,
    AppMaterial,
    AppProduct,
    DatabaseMaterialService,
    DatabaseColorService,
    DatabaseUserService
)
from services.product_bom_service_db import ProductBOMServiceDB
from services.material_csv_service import MaterialCSVService
from services.product_bom_csv_service import ProductBOMCSVService
from models.enums import WindowType, AluminumLine, GlassType
from models.color_models import MaterialColorCreate, MaterialColorResponse
from config import templates
from error_handling.logging_config import get_logger

router = APIRouter()

# === AUTH HELPER FUNCTIONS ===
# Note: These are temporary until app/dependencies/auth.py is created in TASK-001

async def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Get current user from cookie - returns None if no valid session"""
    logger = get_logger()

    try:
        token = request.cookies.get("access_token")
        if not token:
            return None

        user_service = DatabaseUserService(db)
        session = user_service.get_session_by_token(token)

        if not session:
            return None

        user = user_service.get_user_by_id(session.user_id)
        if user and request.state:
            request.state.user_id = str(user.id)

        return user

    except Exception as e:
        logger.warning(f"Error getting user from cookie: {str(e)}")
        return None

async def get_current_user_flexible(request: Request, db: Session = Depends(get_db)):
    """Get current user from either cookie or bearer token"""
    # Try cookie first
    user = await get_current_user_from_cookie(request, db)
    if user:
        return user

    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.replace("Bearer ", "")
    user_service = DatabaseUserService(db)
    session = user_service.get_session_by_token(token)

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = user_service.get_user_by_id(session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# === MATERIAL CRUD ROUTES ===

@router.get("/api/materials", response_model=List[AppMaterial])
async def get_all_app_materials(current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    """Get all materials from catalog"""
    service = ProductBOMServiceDB(db)
    return service.get_all_materials()

@router.post("/api/materials", response_model=AppMaterial, status_code=status.HTTP_201_CREATED)
async def create_app_material(material: AppMaterial, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    """Create a new material in catalog"""
    service = ProductBOMServiceDB(db)
    return service.create_material(material)

@router.put("/api/materials/{material_id}", response_model=AppMaterial)
async def update_app_material(material_id: int, material: AppMaterial, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    """Update an existing material"""
    service = ProductBOMServiceDB(db)
    updated = service.update_material(material_id, material)
    if not updated:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return updated

@router.delete("/api/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app_material(material_id: int, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    """Delete a material from catalog"""
    service = ProductBOMServiceDB(db)
    if not service.delete_material(material_id):
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# === PRODUCT CRUD ROUTES ===

@router.get("/api/products", response_model=List[AppProduct])
async def get_all_app_products(current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    """Get all products from catalog"""
    service = ProductBOMServiceDB(db)
    return service.get_all_products()

@router.post("/api/products", response_model=AppProduct, status_code=status.HTTP_201_CREATED)
async def create_app_product(product: AppProduct, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    """Create a new product in catalog"""
    service = ProductBOMServiceDB(db)
    # Validar que los material_id en el BOM existan
    for bom_item in product.bom:
        if not service.get_material(bom_item.material_id):
            raise HTTPException(status_code=400, detail=f"Material con ID {bom_item.material_id} no existe en el catálogo.")
    return service.create_product(product)

@router.put("/api/products/{product_id}", response_model=AppProduct)
async def update_app_product(product_id: int, product: AppProduct, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    """Update an existing product"""
    service = ProductBOMServiceDB(db)
    # Validar materiales
    for bom_item in product.bom:
        if not service.get_material(bom_item.material_id):
            raise HTTPException(status_code=400, detail=f"Material con ID {bom_item.material_id} no existe en el catálogo.")
    updated = service.update_product(product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return updated

@router.delete("/api/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app_product(product_id: int, current_user: User = Depends(get_current_user_flexible), db: Session = Depends(get_db)):
    """Delete a product from catalog"""
    service = ProductBOMServiceDB(db)
    if not service.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# === CATALOG HTML PAGES ===

@router.get("/materials_catalog", response_class=HTMLResponse)
async def materials_catalog_page(request: Request, db: Session = Depends(get_db)):
    """Materials catalog management page"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("materials_catalog.html", {
        "request": request,
        "title": "Catálogo de Materiales (BOM)",
        "user": user
    })

@router.get("/products_catalog", response_class=HTMLResponse)
async def products_catalog_page(request: Request, db: Session = Depends(get_db)):
    """Products catalog management page"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Obtener materiales para los selects del BOM
    service = ProductBOMServiceDB(db)
    materials_for_frontend = service.get_all_materials()

    window_types_display = [
        {"value": wt.value, "label": wt.value.replace('_', ' ').title()} for wt in WindowType
    ]
    aluminum_lines_display = [
        {"value": al.value, "label": al.value.replace('_', ' ').title()} for al in AluminumLine
    ]
    glass_types_display = [
        {"value": gt.value, "label": gt.value.replace('_', ' ').title()} for gt in GlassType
    ]

    return templates.TemplateResponse("products_catalog.html", {
        "request": request,
        "title": "Catálogo de Productos (BOM)",
        "user": user,
        "app_materials": [m.model_dump(mode='json') for m in materials_for_frontend],
        "window_types": window_types_display,
        "aluminum_lines": aluminum_lines_display,
        "glass_types": glass_types_display,
    })

# === MATERIAL-COLOR RELATIONSHIP ROUTES ===

@router.get("/api/materials/{material_id}/colors")
async def get_material_colors(
    material_id: int,
    available_only: bool = True,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Obtener colores disponibles para un material"""
    color_service = DatabaseColorService(db)
    material_colors = color_service.get_material_colors(material_id, available_only)

    # Formatear respuesta
    result = []
    for material_color, color in material_colors:
        result.append({
            "id": material_color.id,
            "color_id": color.id,
            "color_name": color.name,
            "color_code": color.code,
            "price_per_unit": material_color.price_per_unit,
            "is_available": material_color.is_available
        })

    return result

@router.post("/api/materials/{material_id}/colors", response_model=MaterialColorResponse, status_code=status.HTTP_201_CREATED)
async def create_material_color(
    material_id: int,
    material_color_data: MaterialColorCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Agregar color a un material con precio específico"""
    color_service = DatabaseColorService(db)

    # Verificar que el material_id coincida
    if material_color_data.material_id != material_id:
        raise HTTPException(status_code=400, detail="Material ID no coincide")

    material_color_dict = material_color_data.model_dump()
    try:
        return color_service.create_material_color(material_color_dict)
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Esta combinación de material y color ya existe")
        raise HTTPException(status_code=500, detail=f"Error creando material-color: {str(e)}")

@router.delete("/api/materials/colors/{material_color_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material_color(
    material_color_id: int,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Eliminar relación material-color"""
    color_service = DatabaseColorService(db)

    success = color_service.delete_material_color(material_color_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relación material-color no encontrada")

    return

@router.get("/api/materials/by-category")
async def get_materials_by_category(
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Obtener materiales agrupados por categoría con sus colores"""
    try:
        material_service = DatabaseMaterialService(db)
        color_service = DatabaseColorService(db)

        # Obtener todos los materiales activos
        try:
            materials = material_service.get_all_materials()
        except Exception as e:
            print(f"Error getting materials: {e}")
            raise HTTPException(status_code=500, detail=f"Error accediendo a materiales: {str(e)}")

        # Verificar si la tabla tiene la columna category
        has_category_column = True
        try:
            # Intentar acceder al primer material para verificar si tiene category
            if materials and hasattr(materials[0], 'category'):
                pass  # Column exists
            else:
                has_category_column = False
        except:
            has_category_column = False

        # Agrupar por categoría
        categories = {}

        for material in materials:
            # Safely get category with fallback
            try:
                category = getattr(material, 'category', 'Otros')
            except AttributeError:
                category = 'Otros'

            if not category:
                category = 'Otros'

            if category not in categories:
                categories[category] = []

            # Get colors for this material
            material_colors = color_service.get_material_colors(material.id, available_only=True)

            # Format material data
            material_data = {
                "id": material.id,
                "product_code": material.product_code,
                "name": material.name,
                "material_type": material.material_type,
                "unit_price": float(material.unit_price) if material.unit_price else 0,
                "selling_unit": material.selling_unit,
                "category": category,
                "colors": []
            }

            # Add colors if available
            for material_color, color in material_colors:
                material_data["colors"].append({
                    "id": material_color.id,
                    "color_id": color.id,
                    "color_name": color.name,
                    "color_code": color.code,
                    "price_per_unit": float(material_color.price_per_unit) if material_color.price_per_unit else 0,
                    "is_available": material_color.is_available
                })

            categories[category].append(material_data)

        return {
            "categories": categories,
            "has_category_column": has_category_column
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_materials_by_category: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error obteniendo materiales: {str(e)}")

# === MATERIAL CSV OPERATIONS ===

@router.get("/api/materials/csv/export")
async def export_materials_csv(
    category: Optional[str] = Query(None, description="Filter by category (Perfiles, Vidrio, Herrajes, Consumibles, Otros) or 'all'"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Export materials to CSV format by category"""
    try:
        csv_service = MaterialCSVService(db)
        csv_content = csv_service.export_materials_to_csv(category)

        # Generate filename
        category_part = f"_{category}" if category and category != "all" else ""
        filename = f"materials{category_part}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting materials: {str(e)}")

@router.post("/api/materials/csv/import")
async def import_materials_csv(
    file: UploadFile = File(..., description="CSV file with materials data"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Import materials from CSV file with bulk CRUD operations"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")

        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')

        # Process CSV
        csv_service = MaterialCSVService(db)
        results = csv_service.import_materials_from_csv(csv_content)

        return {
            "message": "CSV import completed",
            "filename": file.filename,
            "summary": results["summary"],
            "success_count": len(results["success"]),
            "error_count": len(results["errors"]),
            "successes": results["success"],
            "errors": results["errors"]
        }

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please ensure the CSV file is UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing materials: {str(e)}")

@router.get("/api/materials/csv/template")
async def get_materials_csv_template(
    category: Optional[str] = Query(None, description="Generate template for specific category"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get CSV template with sample data for material import"""
    try:
        csv_service = MaterialCSVService(db)
        template_content = csv_service.get_csv_template(category)

        # Generate filename
        category_part = f"_{category}" if category else ""
        filename = f"materials_template{category_part}.csv"

        return Response(
            content=template_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating template: {str(e)}")

# === PRODUCT CSV OPERATIONS ===

@router.get("/api/products/csv/export")
async def export_products_csv(
    window_type: Optional[str] = Query(None, description="Filter by window type (CORREDIZA, FIJA, PROYECTANTE, etc.) or 'all'"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Export products to CSV format by window type"""
    try:
        csv_service = ProductBOMCSVService(db)
        csv_content = csv_service.export_products_to_csv(window_type)

        # Generate filename
        window_type_part = f"_{window_type}" if window_type and window_type != "all" else ""
        filename = f"products{window_type_part}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting products: {str(e)}")

@router.post("/api/products/csv/import")
async def import_products_csv(
    file: UploadFile = File(..., description="CSV file with products data"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Import products from CSV file with bulk CRUD operations"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")

        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')

        # Process CSV
        csv_service = ProductBOMCSVService(db)
        results = csv_service.import_products_from_csv(csv_content)

        return {
            "message": "CSV import completed",
            "filename": file.filename,
            "summary": results["summary"],
            "success_count": len(results["success"]),
            "error_count": len(results["errors"]),
            "successes": results["success"],
            "errors": results["errors"]
        }

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please ensure the CSV file is UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing products: {str(e)}")

@router.get("/api/products/csv/template")
async def get_products_csv_template(
    window_type: Optional[str] = Query(None, description="Generate template for specific window type"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get CSV template with sample data for product import"""
    try:
        csv_service = ProductBOMCSVService(db)
        template_content = csv_service.get_csv_template(window_type)

        # Generate filename
        window_type_part = f"_{window_type}" if window_type else ""
        filename = f"products_template{window_type_part}.csv"

        return Response(
            content=template_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating template: {str(e)}")