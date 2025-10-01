"""Quote presentation layer - transforms ORM objects for templates

HOTFIX-20251001-001: Extracted from main.py lines 932-989
This presenter handles data processing for quotes_list.html template
"""

from typing import Dict, Any, List
from database import Quote
from services.product_bom_service_db import ProductBOMServiceDB
from sqlalchemy.orm import Session


class QuoteListPresenter:
    """Transforms Quote objects for quotes_list.html template

    This class extracts the 85-line data processing logic that was in main.py,
    providing template-compatible dictionaries with calculated fields.
    """

    def __init__(self, db: Session):
        self.db = db
        self.product_bom_service = ProductBOMServiceDB(db)

    def present(self, quote: Quote) -> Dict[str, Any]:
        """Convert Quote ORM object to template-compatible dictionary

        Args:
            quote: SQLAlchemy Quote object from database

        Returns:
            Dictionary with all fields required by quotes_list.html template:
            - Basic quote info (id, dates, client info, totals)
            - Calculated fields (total_area, price_per_m2)
            - Extracted data (sample_items, remaining_items)
        """
        try:
            # Extract quote data JSON (line 934 from main.py)
            quote_data = quote.quote_data or {}
            items = quote_data.get("items", [])
            items_count = len(items)

            # Calculate total area from items (lines 938-945 from main.py)
            total_area = 0
            for item in items:
                try:
                    area_value = item.get("area_m2", 0)
                    if area_value is not None:
                        total_area += float(area_value)
                except (ValueError, TypeError):
                    continue  # Skip invalid area values

            # Calculate price per m² (line 956 from main.py)
            price_per_m2 = (
                float(quote.total_final) / total_area
                if total_area > 0 and quote.total_final
                else 0
            )

            # Extract sample items with product info (lines 961-986 from main.py)
            sample_items = self._extract_sample_items(quote_data, items_count)

            # Build template-compatible dictionary (lines 947-958 from main.py)
            return {
                "id": quote.id,
                "created_at": quote.created_at,
                "client_name": quote.client_name or "Cliente Desconocido",
                "client_email": quote.client_email or "",
                "client_phone": quote.client_phone or "",
                "total_final": float(quote.total_final) if quote.total_final else 0,
                "items_count": items_count,
                "total_area": total_area,
                "price_per_m2": price_per_m2,
                "sample_items": sample_items,
                "remaining_items": max(0, items_count - 3)  # line 988 from main.py
            }

        except Exception as quote_error:
            # Graceful degradation - return minimal data (lines 991-994 from main.py)
            print(f"Error processing quote {quote.id}: {quote_error}")
            return {
                "id": quote.id,
                "created_at": quote.created_at,
                "client_name": quote.client_name or "Cliente Desconocido",
                "client_email": "",
                "client_phone": "",
                "total_final": float(quote.total_final) if quote.total_final else 0,
                "items_count": 0,
                "total_area": 0,
                "price_per_m2": 0,
                "sample_items": [],
                "remaining_items": 0
            }

    def _extract_sample_items(self, quote_data: dict, items_count: int) -> List[Dict[str, Any]]:
        """Extract first 3 items with product information

        Extracted from main.py lines 961-986

        Args:
            quote_data: Quote's JSONB data containing items array
            items_count: Total number of items in quote

        Returns:
            List of up to 3 items with window_type, name, width_cm, height_cm
        """
        sample_items = []
        items = quote_data.get("items", [])

        # Process first 3 items (line 962 from main.py)
        for i, item in enumerate(items[:3]):
            try:
                # Get product info from database (line 964 from main.py)
                product_info = self.product_bom_service.get_product_base_info(
                    item.get("product_bom_id")
                )

                if product_info:
                    item_name = product_info["name"]
                    # Safe access to window_type enum value (lines 969-972 from main.py)
                    try:
                        item_type = product_info["window_type"].value
                    except AttributeError:
                        item_type = str(product_info["window_type"])
                else:
                    # Fallback if product not found (lines 974-975 from main.py)
                    item_name = f"Producto #{item.get('product_bom_id', 'N/A')}"
                    item_type = str(item.get("window_type", "Desconocido"))

                # Build sample item dictionary (lines 977-982 from main.py)
                sample_items.append({
                    "window_type": item_type,
                    "name": item_name,
                    "width_cm": int(float(item.get("width_cm", 0))),
                    "height_cm": int(float(item.get("height_cm", 0)))
                })

            except Exception as item_error:
                # Skip problematic items but continue processing (lines 983-986 from main.py)
                print(f"Error processing item {i} for quote {quote.id if hasattr(self, 'quote') else 'unknown'}: {item_error}")
                continue

        return sample_items
