# services/product_bom_csv_service.py - CSV Import/Export service for product BOM catalog
import csv
import io
import json
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
from pydantic import ValidationError

from database import DatabaseProductService, AppProduct as DBAppProduct
from models.product_bom_models import AppProduct, BOMItem, MaterialType, WindowType, AluminumLine
from security.input_validation import InputValidator

class ProductBOMCSVService:
    """Service for CSV import/export operations on product BOM catalog with security validation"""
    
    # Valid window types
    VALID_WINDOW_TYPES = [wt.value for wt in WindowType]
    
    # Valid aluminum lines
    VALID_ALUMINUM_LINES = [al.value for al in AluminumLine]
    
    # Valid material types for BOM items
    VALID_MATERIAL_TYPES = [mt.value for mt in MaterialType]
    
    # CSV headers for products
    CSV_HEADERS = [
        "action", "id", "name", "window_type", "aluminum_line", 
        "min_width_cm", "max_width_cm", "min_height_cm", "max_height_cm",
        "bom_json", "description"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.product_service = DatabaseProductService(db)
        self.validator = InputValidator()
    
    def export_products_to_csv(self, window_type: Optional[str] = None) -> str:
        """Export products to CSV format by window type"""
        products = self.product_service.get_all_products()
        
        # Filter by window type if specified
        if window_type and window_type != "all":
            products = [p for p in products if p.window_type == window_type]
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.CSV_HEADERS)
        writer.writeheader()
        
        for product in products:
            # Convert BOM to JSON string for CSV
            bom_json = json.dumps(product.bom) if product.bom else "[]"
            
            writer.writerow({
                "action": "update",  # Default action for existing products
                "id": product.id,
                "name": product.name,
                "window_type": product.window_type,
                "aluminum_line": product.aluminum_line,
                "min_width_cm": str(product.min_width_cm),
                "max_width_cm": str(product.max_width_cm),
                "min_height_cm": str(product.min_height_cm),
                "max_height_cm": str(product.max_height_cm),
                "bom_json": bom_json,
                "description": product.description or ""
            })
        
        return output.getvalue()
    
    def import_products_from_csv(self, csv_content: str) -> Dict[str, Any]:
        """Import products from CSV with validation and bulk operations"""
        results = {
            "success": [],
            "errors": [],
            "summary": {"created": 0, "updated": 0, "deleted": 0, "skipped": 0}
        }
        
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Validate headers
            if not self._validate_csv_headers(csv_reader.fieldnames):
                results["errors"].append({
                    "row": 0,
                    "error": f"Invalid CSV headers. Expected: {', '.join(self.CSV_HEADERS)}"
                })
                return results
            
            # Process each row
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                try:
                    result = self._process_csv_row(row, row_num)
                    if result["success"]:
                        results["success"].append(result)
                        results["summary"][result["action"]] += 1
                    else:
                        results["errors"].append(result)
                        results["summary"]["skipped"] += 1
                        
                except Exception as e:
                    results["errors"].append({
                        "row": row_num,
                        "error": f"Unexpected error: {str(e)}"
                    })
                    results["summary"]["skipped"] += 1
        
        except Exception as e:
            results["errors"].append({
                "row": 0,
                "error": f"CSV parsing error: {str(e)}"
            })
        
        return results
    
    def _validate_csv_headers(self, headers: List[str]) -> bool:
        """Validate that CSV has required headers"""
        if not headers:
            return False
        return set(self.CSV_HEADERS) == set(headers)
    
    def _process_csv_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Process a single CSV row with validation"""
        action = row.get("action", "").strip().lower()
        
        if action not in ["create", "update", "delete"]:
            return {
                "success": False,
                "row": row_num,
                "error": f"Invalid action '{action}'. Must be: create, update, or delete"
            }
        
        try:
            if action == "create":
                return self._create_product_from_row(row, row_num)
            elif action == "update":
                return self._update_product_from_row(row, row_num)
            elif action == "delete":
                return self._delete_product_from_row(row, row_num)
                
        except ValidationError as e:
            return {
                "success": False,
                "row": row_num,
                "error": f"Validation error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "row": row_num,
                "error": f"Processing error: {str(e)}"
            }
    
    def _create_product_from_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Create a new product from CSV row"""
        # Validate and sanitize inputs
        validated_data = self._validate_product_data(row, row_num, require_id=False)
        if not validated_data["valid"]:
            return {
                "success": False,
                "row": row_num,
                "error": validated_data["error"]
            }
        
        data = validated_data["data"]
        
        # Create product
        product = self.product_service.create_product(
            name=data["name"],
            window_type=data["window_type"],
            aluminum_line=data["aluminum_line"],
            min_width_cm=data["min_width_cm"],
            max_width_cm=data["max_width_cm"],
            min_height_cm=data["min_height_cm"],
            max_height_cm=data["max_height_cm"],
            bom=data.get("bom", []),
            description=data.get("description")
        )
        
        return {
            "success": True,
            "action": "created",
            "row": row_num,
            "product_id": product.id,
            "product_name": product.name
        }
    
    def _update_product_from_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Update an existing product from CSV row"""
        # Validate and sanitize inputs
        validated_data = self._validate_product_data(row, row_num, require_id=True)
        if not validated_data["valid"]:
            return {
                "success": False,
                "row": row_num,
                "error": validated_data["error"]
            }
        
        data = validated_data["data"]
        product_id = data["id"]
        
        # Check if product exists
        existing = self.product_service.get_product_by_id(product_id)
        if not existing:
            return {
                "success": False,
                "row": row_num,
                "error": f"Product with ID {product_id} not found"
            }
        
        # Update product
        update_data = {k: v for k, v in data.items() if k != "id" and v is not None}
        product = self.product_service.update_product(product_id, **update_data)
        
        return {
            "success": True,
            "action": "updated",
            "row": row_num,
            "product_id": product.id,
            "product_name": product.name
        }
    
    def _delete_product_from_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Delete a product from CSV row (soft delete)"""
        try:
            product_id = int(row.get("id", "").strip())
            if not product_id:
                return {
                    "success": False,
                    "row": row_num,
                    "error": "Product ID is required for delete action"
                }
        except (ValueError, TypeError):
            return {
                "success": False,
                "row": row_num,
                "error": "Invalid product ID for delete action"
            }
        
        # Check if product exists
        existing = self.product_service.get_product_by_id(product_id)
        if not existing:
            return {
                "success": False,
                "row": row_num,
                "error": f"Product with ID {product_id} not found"
            }
        
        # Soft delete product
        success = self.product_service.delete_product(product_id)
        if not success:
            return {
                "success": False,
                "row": row_num,
                "error": f"Failed to delete product with ID {product_id}"
            }
        
        return {
            "success": True,
            "action": "deleted",
            "row": row_num,
            "product_id": product_id,
            "product_name": existing.name
        }
    
    def _validate_product_data(self, row: Dict[str, str], row_num: int, require_id: bool = False) -> Dict[str, Any]:
        """Validate and sanitize product data from CSV row"""
        try:
            data = {}
            
            # ID validation (for updates/deletes)
            if require_id:
                try:
                    product_id = int(row.get("id", "").strip())
                    if not product_id:
                        return {"valid": False, "error": "Product ID is required"}
                    data["id"] = product_id
                except (ValueError, TypeError):
                    return {"valid": False, "error": "Invalid product ID"}
            
            # Name validation (required for create/update)
            name = row.get("name", "").strip()
            if not require_id or name:  # Required for create, optional for update
                if not name:
                    return {"valid": False, "error": "Product name is required"}
                if len(name) > 100:
                    return {"valid": False, "error": "Invalid product name (max 100 characters)"}
                data["name"] = self.validator.sanitize_text(name, max_length=100)
            
            # Window type validation (required for create)
            window_type = row.get("window_type", "").strip()
            if not require_id or window_type:  # Required for create, optional for update
                if not window_type:
                    return {"valid": False, "error": "Window type is required"}
                if window_type not in self.VALID_WINDOW_TYPES:
                    return {"valid": False, "error": f"Invalid window type. Must be one of: {', '.join(self.VALID_WINDOW_TYPES)}"}
                data["window_type"] = window_type
            
            # Aluminum line validation (required for create)
            aluminum_line = row.get("aluminum_line", "").strip()
            if not require_id or aluminum_line:  # Required for create, optional for update
                if not aluminum_line:
                    return {"valid": False, "error": "Aluminum line is required"}
                if aluminum_line not in self.VALID_ALUMINUM_LINES:
                    return {"valid": False, "error": f"Invalid aluminum line. Must be one of: {', '.join(self.VALID_ALUMINUM_LINES)}"}
                data["aluminum_line"] = aluminum_line
            
            # Dimension validations (required for create)
            dimension_fields = ["min_width_cm", "max_width_cm", "min_height_cm", "max_height_cm"]
            for field in dimension_fields:
                value_str = row.get(field, "").strip()
                if not require_id or value_str:  # Required for create, optional for update
                    if not value_str:
                        return {"valid": False, "error": f"{field.replace('_', ' ').title()} is required"}
                    try:
                        value = Decimal(value_str)
                        if value <= 0:
                            return {"valid": False, "error": f"{field.replace('_', ' ').title()} must be greater than 0"}
                        data[field] = value
                    except (InvalidOperation, ValueError):
                        return {"valid": False, "error": f"Invalid {field.replace('_', ' ')} format"}
            
            # Validate dimension ranges
            if "min_width_cm" in data and "max_width_cm" in data:
                if data["min_width_cm"] >= data["max_width_cm"]:
                    return {"valid": False, "error": "Min width must be less than max width"}
            
            if "min_height_cm" in data and "max_height_cm" in data:
                if data["min_height_cm"] >= data["max_height_cm"]:
                    return {"valid": False, "error": "Min height must be less than max height"}
            
            # BOM validation (optional)
            bom_json_str = row.get("bom_json", "").strip()
            if bom_json_str:
                try:
                    bom_data = json.loads(bom_json_str)
                    if not isinstance(bom_data, list):
                        return {"valid": False, "error": "BOM JSON must be an array"}
                    
                    # Validate each BOM item
                    validated_bom = []
                    for i, bom_item in enumerate(bom_data):
                        if not isinstance(bom_item, dict):
                            return {"valid": False, "error": f"BOM item {i+1} must be an object"}
                        
                        # Validate required BOM item fields
                        required_fields = ["material_id", "material_type", "quantity_formula"]
                        for field in required_fields:
                            if field not in bom_item:
                                return {"valid": False, "error": f"BOM item {i+1} missing required field: {field}"}
                        
                        # Validate material_type
                        if bom_item["material_type"] not in self.VALID_MATERIAL_TYPES:
                            return {"valid": False, "error": f"Invalid material type in BOM item {i+1}. Must be one of: {', '.join(self.VALID_MATERIAL_TYPES)}"}
                        
                        # Validate material_id
                        try:
                            material_id = int(bom_item["material_id"])
                        except (ValueError, TypeError):
                            return {"valid": False, "error": f"Invalid material ID in BOM item {i+1}"}
                        
                        # Validate quantity_formula (basic check - actual formula validation should be done by formula evaluator)
                        formula = str(bom_item["quantity_formula"]).strip()
                        if not formula:
                            return {"valid": False, "error": f"Empty quantity formula in BOM item {i+1}"}
                        
                        # Validate waste_factor (optional, default to 1.05)
                        waste_factor = bom_item.get("waste_factor", "1.05")
                        try:
                            waste_factor = Decimal(str(waste_factor))
                            if waste_factor < Decimal("1.0"):
                                return {"valid": False, "error": f"Waste factor in BOM item {i+1} must be >= 1.0"}
                        except (InvalidOperation, ValueError):
                            return {"valid": False, "error": f"Invalid waste factor in BOM item {i+1}"}
                        
                        validated_bom.append({
                            "material_id": material_id,
                            "material_type": bom_item["material_type"],
                            "quantity_formula": formula,
                            "waste_factor": waste_factor,
                            "description": bom_item.get("description", "")
                        })
                    
                    data["bom"] = validated_bom
                    
                except json.JSONDecodeError as e:
                    return {"valid": False, "error": f"Invalid BOM JSON format: {str(e)}"}
            else:
                data["bom"] = []
            
            # Description validation (optional)
            description = row.get("description", "").strip()
            if description:
                if len(description) > 500:
                    return {"valid": False, "error": "Description too long (max 500 characters)"}
                data["description"] = self.validator.sanitize_text(description, max_length=500)
            
            return {"valid": True, "data": data}
            
        except Exception as e:
            return {"valid": False, "error": f"Data validation error: {str(e)}"}
    
    def get_csv_template(self, window_type: Optional[str] = None) -> str:
        """Generate a CSV template with sample data for the specified window type"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.CSV_HEADERS)
        writer.writeheader()
        
        # Sample BOM for a sliding window
        sample_bom = [
            {
                "material_id": 1,
                "material_type": "PERFIL",
                "quantity_formula": "2 * width_m + 2 * height_m",
                "waste_factor": "1.05",
                "description": "Marco principal"
            },
            {
                "material_id": 2,
                "material_type": "VIDRIO",
                "quantity_formula": "area_m2",
                "waste_factor": "1.10",
                "description": "Vidrio principal"
            },
            {
                "material_id": 3,
                "material_type": "HERRAJE",
                "quantity_formula": "quantity",
                "waste_factor": "1.00",
                "description": "Kit de herrajes"
            }
        ]
        
        # Add sample rows based on window type
        if window_type == "corrediza" or not window_type:
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Ventana Corrediza Serie 3",
                "window_type": "corrediza",
                "aluminum_line": "nacional_serie_3",
                "min_width_cm": "80.0",
                "max_width_cm": "300.0",
                "min_height_cm": "60.0",
                "max_height_cm": "180.0",
                "bom_json": json.dumps(sample_bom),
                "description": "Ventana corrediza estándar de 2 hojas"
            })
        
        if window_type == "fija" or not window_type:
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Ventana Fija Serie 35",
                "window_type": "fija",
                "aluminum_line": "nacional_serie_35",
                "min_width_cm": "40.0",
                "max_width_cm": "250.0",
                "min_height_cm": "40.0",
                "max_height_cm": "200.0",
                "bom_json": json.dumps([item for item in sample_bom if item["material_type"] != "HERRAJE"]),
                "description": "Ventana fija sin herrajes"
            })
        
        if window_type == "proyectante" or not window_type:
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Ventana Proyectante",
                "window_type": "proyectante",
                "aluminum_line": "nacional_serie_3",
                "min_width_cm": "60.0",
                "max_width_cm": "180.0",
                "min_height_cm": "50.0",
                "max_height_cm": "120.0",
                "bom_json": json.dumps(sample_bom + [{
                    "material_id": 4,
                    "material_type": "HERRAJE",
                    "quantity_formula": "1",
                    "waste_factor": "1.00",
                    "description": "Mecanismo proyectante"
                }]),
                "description": "Ventana proyectante con mecanismo especial"
            })
        
        return output.getvalue()