# services/material_csv_service.py - CSV Import/Export service for materials
import csv
import io
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
from pydantic import ValidationError

from database import DatabaseMaterialService, AppMaterial as DBAppMaterial, DatabaseColorService
from models.product_bom_models import AppMaterial, MaterialUnit
from security.input_validation import InputValidator

class MaterialCSVService:
    """Service for CSV import/export operations on materials with security validation"""
    
    # Valid categories for materials
    VALID_CATEGORIES = ["Perfiles", "Vidrio", "Herrajes", "Consumibles", "Otros"]
    
    # CSV headers - includes color information for profiles
    CSV_HEADERS = [
        "action", "id", "name", "code", "unit", "category", 
        "cost_per_unit", "selling_unit_length_m", "description",
        "color_name", "color_code", "color_price_per_unit"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.material_service = DatabaseMaterialService(db)
        self.color_service = DatabaseColorService(db)
        self.validator = InputValidator()
    
    def export_materials_to_csv(self, category: Optional[str] = None) -> str:
        """Export materials to CSV format by category, including color information for profiles"""
        materials = self.material_service.get_all_materials()
        
        # Filter by category if specified
        if category and category != "all":
            materials = [m for m in materials if m.category == category]
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.CSV_HEADERS)
        writer.writeheader()
        
        for material in materials:
            # Check if material is a profile with colors
            if material.category == "Perfiles":
                # Get material colors for this profile
                material_colors = self.color_service.get_material_colors(material.id)
                
                if material_colors:
                    # Export one row per color
                    for material_color, color in material_colors:
                        writer.writerow({
                            "action": "update",
                            "id": material.id,
                            "name": material.name,
                            "code": material.code or "",
                            "unit": material.unit,
                            "category": material.category,
                            "cost_per_unit": str(material.cost_per_unit),
                            "selling_unit_length_m": str(material.selling_unit_length_m) if material.selling_unit_length_m else "",
                            "description": material.description or "",
                            "color_name": color.name if color else "",
                            "color_code": color.code if color and color.code else "",
                            "color_price_per_unit": str(material_color.price_per_unit)
                        })
                else:
                    # Export profile without specific colors
                    writer.writerow({
                        "action": "update",
                        "id": material.id,
                        "name": material.name,
                        "code": material.code or "",
                        "unit": material.unit,
                        "category": material.category,
                        "cost_per_unit": str(material.cost_per_unit),
                        "selling_unit_length_m": str(material.selling_unit_length_m) if material.selling_unit_length_m else "",
                        "description": material.description or "",
                        "color_name": "",
                        "color_code": "",
                        "color_price_per_unit": ""
                    })
            else:
                # Export non-profile materials without color information
                writer.writerow({
                    "action": "update",
                    "id": material.id,
                    "name": material.name,
                    "code": material.code or "",
                    "unit": material.unit,
                    "category": material.category,
                    "cost_per_unit": str(material.cost_per_unit),
                    "selling_unit_length_m": str(material.selling_unit_length_m) if material.selling_unit_length_m else "",
                    "description": material.description or "",
                    "color_name": "",
                    "color_code": "",
                    "color_price_per_unit": ""
                })
        
        return output.getvalue()
    
    def import_materials_from_csv(self, csv_content: str) -> Dict[str, Any]:
        """Import materials from CSV with validation and bulk operations"""
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
        """Process a single CSV row with validation, including color information"""
        action = row.get("action", "").strip().lower()
        
        if action not in ["create", "update", "delete"]:
            return {
                "success": False,
                "row": row_num,
                "error": f"Invalid action '{action}'. Must be: create, update, or delete"
            }
        
        try:
            if action == "create":
                return self._create_material_from_row(row, row_num)
            elif action == "update":
                return self._update_material_from_row(row, row_num)
            elif action == "delete":
                return self._delete_material_from_row(row, row_num)
                
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
    
    def _create_material_from_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Create a new material from CSV row, including color information for profiles"""
        # Validate and sanitize inputs
        validated_data = self._validate_material_data(row, row_num, require_id=False)
        if not validated_data["valid"]:
            return {
                "success": False,
                "row": row_num,
                "error": validated_data["error"]
            }
        
        data = validated_data["data"]
        
        # Check if material with same code already exists
        if data.get("code"):
            existing = self.material_service.get_material_by_code(data["code"])
            if existing:
                return {
                    "success": False,
                    "row": row_num,
                    "error": f"Material with code '{data['code']}' already exists"
                }
        
        # Create material
        material = self.material_service.create_material(
            name=data["name"],
            unit=data["unit"],
            category=data["category"],
            code=data.get("code"),
            cost_per_unit=data["cost_per_unit"],
            selling_unit_length_m=data.get("selling_unit_length_m"),
            description=data.get("description")
        )
        
        # Handle color information for profiles
        color_result = self._process_color_data(material, row, row_num)
        if not color_result["success"]:
            return color_result
        
        result = {
            "success": True,
            "action": "created",
            "row": row_num,
            "material_id": material.id,
            "material_name": material.name
        }
        
        if color_result.get("color_message"):
            result["color_info"] = color_result["color_message"]
            
        return result
    
    def _update_material_from_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Update an existing material from CSV row, including color information for profiles"""
        # Validate and sanitize inputs
        validated_data = self._validate_material_data(row, row_num, require_id=True)
        if not validated_data["valid"]:
            return {
                "success": False,
                "row": row_num,
                "error": validated_data["error"]
            }
        
        data = validated_data["data"]
        material_id = data["id"]
        
        # Check if material exists
        existing = self.material_service.get_material_by_id(material_id)
        if not existing:
            return {
                "success": False,
                "row": row_num,
                "error": f"Material with ID {material_id} not found"
            }
        
        # Check for code conflicts (if changing code)
        if data.get("code") and data["code"] != existing.code:
            existing_with_code = self.material_service.get_material_by_code(data["code"])
            if existing_with_code and existing_with_code.id != material_id:
                return {
                    "success": False,
                    "row": row_num,
                    "error": f"Material with code '{data['code']}' already exists"
                }
        
        # Update material
        update_data = {k: v for k, v in data.items() if k != "id" and v is not None}
        material = self.material_service.update_material(material_id, **update_data)
        
        # Handle color information for profiles
        color_result = self._process_color_data(material, row, row_num)
        if not color_result["success"]:
            return color_result
        
        result = {
            "success": True,
            "action": "updated",
            "row": row_num,
            "material_id": material.id,
            "material_name": material.name
        }
        
        if color_result.get("color_message"):
            result["color_info"] = color_result["color_message"]
            
        return result
    
    def _delete_material_from_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Delete a material from CSV row (soft delete)"""
        try:
            material_id = int(row.get("id", "").strip())
            if not material_id:
                return {
                    "success": False,
                    "row": row_num,
                    "error": "Material ID is required for delete action"
                }
        except (ValueError, TypeError):
            return {
                "success": False,
                "row": row_num,
                "error": "Invalid material ID for delete action"
            }
        
        # Check if material exists
        existing = self.material_service.get_material_by_id(material_id)
        if not existing:
            return {
                "success": False,
                "row": row_num,
                "error": f"Material with ID {material_id} not found"
            }
        
        # Soft delete material
        success = self.material_service.delete_material(material_id)
        if not success:
            return {
                "success": False,
                "row": row_num,
                "error": f"Failed to delete material with ID {material_id}"
            }
        
        return {
            "success": True,
            "action": "deleted",
            "row": row_num,
            "material_id": material_id,
            "material_name": existing.name
        }
    
    def _validate_material_data(self, row: Dict[str, str], row_num: int, require_id: bool = False) -> Dict[str, Any]:
        """Validate and sanitize material data from CSV row"""
        try:
            data = {}
            
            # ID validation (for updates/deletes)
            if require_id:
                try:
                    material_id = int(row.get("id", "").strip())
                    if not material_id:
                        return {"valid": False, "error": "Material ID is required"}
                    data["id"] = material_id
                except (ValueError, TypeError):
                    return {"valid": False, "error": "Invalid material ID"}
            
            # Name validation (required for create/update)
            name = row.get("name", "").strip()
            if not require_id or name:  # Required for create, optional for update
                if not name:
                    return {"valid": False, "error": "Material name is required"}
                if not self.validator.validate_text_input(name, min_length=1, max_length=100):
                    return {"valid": False, "error": "Invalid material name"}
                data["name"] = self.validator.sanitize_text_input(name)
            
            # Code validation (optional)
            code = row.get("code", "").strip()
            if code:
                if not self.validator.validate_text_input(code, min_length=1, max_length=50):
                    return {"valid": False, "error": "Invalid material code"}
                data["code"] = self.validator.sanitize_text_input(code)
            
            # Unit validation (required for create)
            unit = row.get("unit", "").strip()
            if not require_id or unit:  # Required for create, optional for update
                if not unit:
                    return {"valid": False, "error": "Material unit is required"}
                try:
                    MaterialUnit(unit)  # Validate enum value
                    data["unit"] = unit
                except ValueError:
                    valid_units = [u.value for u in MaterialUnit]
                    return {"valid": False, "error": f"Invalid unit. Must be one of: {', '.join(valid_units)}"}
            
            # Category validation (required for create)
            category = row.get("category", "").strip()
            if not require_id or category:  # Required for create, optional for update
                if not category:
                    return {"valid": False, "error": "Material category is required"}
                if category not in self.VALID_CATEGORIES:
                    return {"valid": False, "error": f"Invalid category. Must be one of: {', '.join(self.VALID_CATEGORIES)}"}
                data["category"] = category
            
            # Cost per unit validation (required for create)
            cost_str = row.get("cost_per_unit", "").strip()
            if not require_id or cost_str:  # Required for create, optional for update
                if not cost_str:
                    return {"valid": False, "error": "Cost per unit is required"}
                try:
                    cost = Decimal(cost_str)
                    if cost <= 0:
                        return {"valid": False, "error": "Cost per unit must be greater than 0"}
                    data["cost_per_unit"] = cost
                except (InvalidOperation, ValueError):
                    return {"valid": False, "error": "Invalid cost per unit format"}
            
            # Selling unit length validation (optional)
            length_str = row.get("selling_unit_length_m", "").strip()
            if length_str:
                try:
                    length = Decimal(length_str)
                    if length <= 0:
                        return {"valid": False, "error": "Selling unit length must be greater than 0"}
                    data["selling_unit_length_m"] = length
                except (InvalidOperation, ValueError):
                    return {"valid": False, "error": "Invalid selling unit length format"}
            
            # Description validation (optional)
            description = row.get("description", "").strip()
            if description:
                if not self.validator.validate_text_input(description, max_length=500):
                    return {"valid": False, "error": "Description too long (max 500 characters)"}
                data["description"] = self.validator.sanitize_text_input(description)
            
            return {"valid": True, "data": data}
            
        except Exception as e:
            return {"valid": False, "error": f"Data validation error: {str(e)}"}
    
    def _process_color_data(self, material, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Process color information for profiles"""
        # Only process colors for profiles
        if material.category != "Perfiles":
            return {"success": True, "color_message": "No color processing needed for non-profile materials"}
        
        color_name = row.get("color_name", "").strip()
        color_code = row.get("color_code", "").strip()
        color_price_str = row.get("color_price_per_unit", "").strip()
        
        # If no color information provided, skip color processing
        if not color_name and not color_price_str:
            return {"success": True, "color_message": "No color information provided"}
        
        # Validate color information
        if not color_name:
            return {
                "success": False,
                "row": row_num,
                "error": "Color name is required when color price is provided"
            }
        
        if not color_price_str:
            return {
                "success": False,
                "row": row_num,
                "error": "Color price is required when color name is provided"
            }
        
        # Validate color price
        try:
            color_price = Decimal(color_price_str)
            if color_price <= 0:
                return {
                    "success": False,
                    "row": row_num,
                    "error": "Color price must be greater than 0"
                }
        except (InvalidOperation, ValueError):
            return {
                "success": False,
                "row": row_num,
                "error": "Invalid color price format"
            }
        
        # Validate color name
        if not self.validator.validate_text_input(color_name, min_length=1, max_length=100):
            return {
                "success": False,
                "row": row_num,
                "error": "Invalid color name"
            }
        
        # Sanitize inputs
        color_name = self.validator.sanitize_text_input(color_name)
        if color_code:
            if not self.validator.validate_text_input(color_code, min_length=1, max_length=20):
                return {
                    "success": False,
                    "row": row_num,
                    "error": "Invalid color code"
                }
            color_code = self.validator.sanitize_text_input(color_code)
        
        try:
            # Check if color exists, create if not
            existing_color = None
            if color_code:
                # Try to find by code first
                existing_color = self.color_service.get_color_by_code(color_code)
            
            if not existing_color:
                # Try to find by name
                existing_color = self.color_service.get_color_by_name(color_name)
            
            if not existing_color:
                # Create new color
                color = self.color_service.create_color(
                    name=color_name,
                    code=color_code if color_code else None,
                    description=f"Color for {material.name}"
                )
                color_message = f"Created new color: {color_name}"
            else:
                color = existing_color
                color_message = f"Using existing color: {color_name}"
            
            # Create or update material-color relationship
            existing_material_color = self.color_service.get_material_color_by_ids(material.id, color.id)
            
            if existing_material_color:
                # Update existing relationship
                self.color_service.update_material_color(
                    existing_material_color.id,
                    price_per_unit=color_price,
                    is_available=True
                )
                color_message += f" (updated price: {color_price})"
            else:
                # Create new relationship
                self.color_service.create_material_color(
                    material_id=material.id,
                    color_id=color.id,
                    price_per_unit=color_price
                )
                color_message += f" (new price: {color_price})"
            
            return {"success": True, "color_message": color_message}
            
        except Exception as e:
            return {
                "success": False,
                "row": row_num,
                "error": f"Error processing color data: {str(e)}"
            }
    
    def get_csv_template(self, category: Optional[str] = None) -> str:
        """Generate a CSV template with sample data for the specified category"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.CSV_HEADERS)
        writer.writeheader()
        
        # Add sample rows based on category
        if category == "Perfiles" or not category:
            # Profile without color
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Perfil Aluminio Serie 3",
                "code": "PRF-AL-S3-001",
                "unit": "ML",
                "category": "Perfiles",
                "cost_per_unit": "45.50",
                "selling_unit_length_m": "6.0",
                "description": "Perfil de aluminio serie 3 para ventanas",
                "color_name": "",
                "color_code": "",
                "color_price_per_unit": ""
            })
            # Profile with color - White
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Perfil Aluminio Serie 3 Blanco",
                "code": "PRF-AL-S3-002",
                "unit": "ML",
                "category": "Perfiles",
                "cost_per_unit": "45.50",
                "selling_unit_length_m": "6.0",
                "description": "Perfil de aluminio serie 3 en color blanco",
                "color_name": "Blanco",
                "color_code": "WHT",
                "color_price_per_unit": "50.00"
            })
            # Profile with color - Bronze
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Perfil Aluminio Serie 3 Bronze",
                "code": "PRF-AL-S3-003",
                "unit": "ML",
                "category": "Perfiles",
                "cost_per_unit": "45.50",
                "selling_unit_length_m": "6.0",
                "description": "Perfil de aluminio serie 3 en color bronze",
                "color_name": "Bronze",
                "color_code": "BRZ",
                "color_price_per_unit": "55.00"
            })
        
        if category == "Vidrio" or not category:
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Vidrio Claro 6mm",
                "code": "VID-CLR-6MM",
                "unit": "M2",
                "category": "Vidrio",
                "cost_per_unit": "280.00",
                "selling_unit_length_m": "",
                "description": "Vidrio claro templado 6mm",
                "color_name": "",
                "color_code": "",
                "color_price_per_unit": ""
            })
        
        if category == "Herrajes" or not category:
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Cerradura Ventana",
                "code": "HRJ-CER-001",
                "unit": "PZA",
                "category": "Herrajes",
                "cost_per_unit": "85.00",
                "selling_unit_length_m": "",
                "description": "Cerradura para ventana corrediza",
                "color_name": "",
                "color_code": "",
                "color_price_per_unit": ""
            })
        
        if category == "Consumibles" or not category:
            writer.writerow({
                "action": "create",
                "id": "",
                "name": "Silicón Estructural",
                "code": "CON-SIL-EST",
                "unit": "CARTUCHO",
                "category": "Consumibles",
                "cost_per_unit": "45.00",
                "selling_unit_length_m": "",
                "description": "Silicón estructural para sellado",
                "color_name": "",
                "color_code": "",
                "color_price_per_unit": ""
            })
        
        return output.getvalue()