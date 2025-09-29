"""
Work Order Routes - QTO-001 System
Extracted from main.py as part of TASK-20250929-003

This module contains all work order related routes for the Quote-to-Order system.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import (
    get_db,
    User,
    WorkOrder,
    DatabaseUserService,
    DatabaseQuoteService,
    DatabaseWorkOrderService
)
from models.work_order_models import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
    WorkOrderListResponse,
    WorkOrderStatusUpdate,
    WorkOrderStatus,
    WorkOrderPriority
)
from config import templates
from error_handling.logging_config import get_logger

router = APIRouter()

# === AUTH HELPER FUNCTIONS ===
# Note: These are temporary until app/dependencies/auth.py is created in TASK-001

async def get_current_user_from_cookie(request: Request, db: Session):
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

async def get_current_user_flexible(request: Request, db: Session):
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

# === HTML ROUTES (User Interface) ===

@router.get("/work-orders", response_class=HTMLResponse)
async def work_orders_list_page(request: Request, db: Session = Depends(get_db)):
    """Work orders list page - QTO-001"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("work_orders_list.html", {
        "request": request,
        "title": "Órdenes de Trabajo",
        "user": user
    })

@router.get("/work-orders/{work_order_id}", response_class=HTMLResponse)
async def work_order_detail_page(request: Request, work_order_id: int, db: Session = Depends(get_db)):
    """Work order detail page - QTO-001"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Get work order details
    work_order_service = DatabaseWorkOrderService(db)
    work_order = work_order_service.get_work_order_by_id(work_order_id, user.id)

    if not work_order:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")

    return templates.TemplateResponse("work_order_detail.html", {
        "request": request,
        "title": f"Orden de Trabajo {work_order.order_number}",
        "user": user,
        "work_order": work_order
    })

# === API ROUTES (REST Endpoints) ===

@router.post("/api/work-orders/from-quote", response_model=WorkOrderResponse)
async def create_work_order_from_quote(
    work_order_request: WorkOrderCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Convert a quote to a work order - QTO-001"""
    try:
        logger = get_logger()
        logger.info(f"Creating work order from quote {work_order_request.quote_id} for user {current_user.id}")

        # Get the quote service and work order service
        quote_service = DatabaseQuoteService(db)
        work_order_service = DatabaseWorkOrderService(db)

        # Verify the quote exists and belongs to the user
        quote = quote_service.get_quote_by_id(work_order_request.quote_id, current_user.id)
        if not quote:
            raise HTTPException(
                status_code=404,
                detail="Quote not found or access denied"
            )

        # Create work order from quote
        work_order = work_order_service.create_work_order_from_quote(quote)

        # Update additional fields if provided
        if work_order_request.production_notes:
            work_order_data = work_order.work_order_data.copy()
            work_order_data['production_notes'] = work_order_request.production_notes
            work_order.work_order_data = work_order_data

        if work_order_request.delivery_instructions:
            work_order_data = work_order.work_order_data.copy()
            work_order_data['delivery_instructions'] = work_order_request.delivery_instructions
            work_order.work_order_data = work_order_data

        if work_order_request.priority != WorkOrderPriority.NORMAL:
            work_order.priority = work_order_request.priority

        if work_order_request.estimated_delivery:
            work_order.estimated_delivery = work_order_request.estimated_delivery

        # Commit changes if any updates were made
        if (work_order_request.production_notes or work_order_request.delivery_instructions or
            work_order_request.priority != WorkOrderPriority.NORMAL or work_order_request.estimated_delivery):
            db.commit()
            db.refresh(work_order)

        logger.info(f"Work order {work_order.order_number} created successfully")
        return work_order

    except HTTPException:
        raise
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error creating work order from quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating work order: {str(e)}")

@router.get("/api/work-orders", response_model=List[WorkOrderListResponse])
async def get_work_orders(
    limit: int = Query(50, ge=1, le=100, description="Number of work orders to retrieve"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get list of work orders for current user"""
    try:
        work_order_service = DatabaseWorkOrderService(db)
        work_orders = work_order_service.get_work_orders_by_user(current_user.id, limit)
        return work_orders

    except Exception as e:
        logger = get_logger()
        logger.error(f"Error retrieving work orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving work orders: {str(e)}")

@router.get("/api/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: int,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get specific work order by ID"""
    try:
        work_order_service = DatabaseWorkOrderService(db)
        work_order = work_order_service.get_work_order_by_id(work_order_id, current_user.id)

        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found or access denied")

        return work_order

    except HTTPException:
        raise
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error retrieving work order {work_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving work order: {str(e)}")

@router.put("/api/work-orders/{work_order_id}/status", response_model=WorkOrderResponse)
async def update_work_order_status(
    work_order_id: int,
    status_update: WorkOrderStatusUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Update work order status"""
    try:
        logger = get_logger()
        work_order_service = DatabaseWorkOrderService(db)

        # Update the work order status
        work_order = work_order_service.update_work_order_status(
            work_order_id,
            current_user.id,
            status_update.status,
            status_update.notes
        )

        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found or access denied")

        logger.info(f"Work order {work_order.order_number} status updated to {status_update.status}")
        return work_order

    except HTTPException:
        raise
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error updating work order status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating work order status: {str(e)}")

@router.put("/api/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(
    work_order_id: int,
    work_order_update: WorkOrderUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Update work order details"""
    try:
        logger = get_logger()
        work_order_service = DatabaseWorkOrderService(db)

        # Get the work order first
        work_order = work_order_service.get_work_order_by_id(work_order_id, current_user.id)
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found or access denied")

        # Update fields if provided
        updated = False

        if work_order_update.status is not None:
            work_order = work_order_service.update_work_order_status(
                work_order_id, current_user.id, work_order_update.status, work_order_update.notes
            )
            updated = True

        if work_order_update.priority is not None:
            work_order.priority = work_order_update.priority
            updated = True

        if work_order_update.production_notes is not None:
            work_order_data = work_order.work_order_data.copy()
            work_order_data['production_notes'] = work_order_update.production_notes
            work_order.work_order_data = work_order_data
            updated = True

        if work_order_update.delivery_instructions is not None:
            work_order_data = work_order.work_order_data.copy()
            work_order_data['delivery_instructions'] = work_order_update.delivery_instructions
            work_order.work_order_data = work_order_data
            updated = True

        if work_order_update.estimated_delivery is not None:
            work_order.estimated_delivery = work_order_update.estimated_delivery
            updated = True

        if work_order_update.notes is not None and work_order_update.status is None:
            # Add notes without status change
            current_notes = work_order.notes or ""
            work_order.notes = f"{current_notes}\n{work_order_update.notes}".strip()
            updated = True

        # Commit if any updates were made
        if updated:
            db.commit()
            db.refresh(work_order)
            logger.info(f"Work order {work_order.order_number} updated successfully")

        return work_order

    except HTTPException:
        raise
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error updating work order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating work order: {str(e)}")

@router.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(
    work_order_id: int,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Delete a work order"""
    try:
        logger = get_logger()
        work_order_service = DatabaseWorkOrderService(db)

        # Get the work order first to verify ownership
        work_order = work_order_service.get_work_order_by_id(work_order_id, current_user.id)
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found or access denied")

        # Delete the work order
        success = work_order_service.delete_work_order(work_order_id, current_user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete work order")

        logger.info(f"Work order {work_order.order_number} deleted successfully")
        return {"message": "Work order deleted successfully", "work_order_id": work_order_id}

    except HTTPException:
        raise
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error deleting work order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting work order: {str(e)}")