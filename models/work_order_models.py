# models/work_order_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum
import uuid

# Import WorkOrder enums from database module
class WorkOrderStatus(str, Enum):
    PENDING = "pending"
    MATERIALS_ORDERED = "materials_ordered"
    MATERIALS_RECEIVED = "materials_received"
    IN_PRODUCTION = "in_production"
    QUALITY_CHECK = "quality_check"
    READY_FOR_DELIVERY = "ready_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class WorkOrderPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class MaterialBreakdownItem(BaseModel):
    """Material breakdown for a work order item"""
    item_description: str = Field(..., description="Description of the work order item")
    quantity: int = Field(..., ge=1, description="Quantity of items")
    profiles_cost: str = Field(..., description="Cost of profiles for this item")
    glass_cost: str = Field(..., description="Cost of glass for this item")
    hardware_cost: str = Field(..., description="Cost of hardware for this item")
    consumables_cost: str = Field(..., description="Cost of consumables for this item")
    labor_cost: str = Field(..., description="Labor cost for this item")
    product_bom_id: Optional[int] = Field(None, description="Product BOM ID reference")
    product_bom_name: str = Field(..., description="Product BOM name")

class QuoteReference(BaseModel):
    """Reference to the original quote"""
    quote_id: int = Field(..., description="Original quote ID")
    quote_created_at: Optional[str] = Field(None, description="Original quote creation date")
    original_total: str = Field(..., description="Original quote total amount")

class WorkOrderData(BaseModel):
    """Complete work order data structure"""
    quote_reference: QuoteReference = Field(..., description="Reference to original quote")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Original quote items")
    material_breakdown: List[MaterialBreakdownItem] = Field(default_factory=list, description="Material breakdown for production")
    production_notes: str = Field(default="", description="Notes for production team")
    delivery_instructions: str = Field(default="", description="Special delivery instructions")

class WorkOrderCreate(BaseModel):
    """Request model for creating work order from quote"""
    quote_id: int = Field(..., description="Quote ID to convert to work order")
    priority: WorkOrderPriority = Field(default=WorkOrderPriority.NORMAL, description="Work order priority")
    production_notes: Optional[str] = Field(None, description="Initial production notes")
    delivery_instructions: Optional[str] = Field(None, description="Special delivery instructions")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")

class WorkOrderUpdate(BaseModel):
    """Request model for updating work order"""
    status: Optional[WorkOrderStatus] = Field(None, description="New status")
    priority: Optional[WorkOrderPriority] = Field(None, description="New priority")
    production_notes: Optional[str] = Field(None, description="Updated production notes")
    delivery_instructions: Optional[str] = Field(None, description="Updated delivery instructions")
    estimated_delivery: Optional[datetime] = Field(None, description="Updated estimated delivery")
    notes: Optional[str] = Field(None, description="Additional notes")

class WorkOrderResponse(BaseModel):
    """Response model for work order"""
    id: int = Field(..., description="Work order ID")
    order_number: str = Field(..., description="Work order number (WO-YYYY-XXX)")
    quote_id: int = Field(..., description="Related quote ID")
    user_id: uuid.UUID = Field(..., description="User ID who owns this work order")
    
    # Client information
    client_name: str = Field(..., description="Client name")
    client_email: Optional[str] = Field(None, description="Client email")
    client_phone: Optional[str] = Field(None, description="Client phone")
    client_address: Optional[str] = Field(None, description="Client address")
    
    # Financial summary
    total_amount: Decimal = Field(..., description="Total work order amount")
    materials_cost: Decimal = Field(..., description="Total materials cost")
    labor_cost: Decimal = Field(..., description="Total labor cost")
    
    # Work order specific data
    work_order_data: WorkOrderData = Field(..., description="Complete work order data")
    
    # Status and priority
    status: WorkOrderStatus = Field(..., description="Current work order status")
    priority: WorkOrderPriority = Field(..., description="Work order priority")
    
    # Dates
    created_at: datetime = Field(..., description="Work order creation date")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    completed_at: Optional[datetime] = Field(None, description="Completion date")
    
    # Notes
    notes: Optional[str] = Field(None, description="Additional notes and status updates")

    class Config:
        from_attributes = True

class WorkOrderListResponse(BaseModel):
    """Response model for work order list"""
    id: int
    order_number: str
    client_name: str
    total_amount: Decimal
    status: WorkOrderStatus
    priority: WorkOrderPriority
    created_at: datetime
    estimated_delivery: Optional[datetime]

    class Config:
        from_attributes = True

class WorkOrderStatusUpdate(BaseModel):
    """Request model for status updates"""
    status: WorkOrderStatus = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Notes about the status change")