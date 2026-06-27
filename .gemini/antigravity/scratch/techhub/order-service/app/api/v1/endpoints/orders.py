from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import require_auth, RoleChecker, UserContext
from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.history import OrderHistory
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.services import product_service, inventory_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Role checkers
admin_required = RoleChecker(allowed_roles=["admin"])

def log_order_history(db: Session, order_id: int, status: str, notes: Optional[str] = None):
    history = OrderHistory(
        order_id=order_id,
        status=status,
        notes=notes
    )
    db.add(history)

@router.get("/", response_model=List[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Get orders.
    - If Admin: returns all active orders in the system.
    - If Customer: returns only the customer's active orders.
    """
    if current_user.role == "admin":
        return db.query(Order).filter(Order.is_active == True).order_by(Order.created_at.desc()).all()
    else:
        return db.query(Order).filter(Order.user_id == current_user.id, Order.is_active == True).order_by(Order.created_at.desc()).all()

@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Get order details by ID.
    - Admin can view any active order.
    - Customer can only view their own active order.
    """
    order = db.query(Order).filter(Order.id == order_id, Order.is_active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this order")
        
    return order

@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Place an order by checking out all items currently in the user's cart.
    Validates product data, reserves stock, snaps product details, and clears the cart.
    """
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty"
        )
        
    order_items_to_create = []
    reserved_items = []  # Keep track of reservations to rollback on failures
    total_price = 0.0
    
    try:
        for item in cart_items:
            # 1. Validate product
            prod = product_service.get_product_metadata(item.product_id)
            if not prod or not prod.get("is_active"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {item.product_id} is no longer available"
                )
                
            # 2. Get inventory and check stock
            inv = inventory_service.get_inventory_by_product_id(item.product_id)
            if not inv or inv.get("available_quantity", 0) < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product '{prod.get('name')}'"
                )
                
            # 3. Reserve stock in Inventory Service
            success = inventory_service.reserve_stock(
                inv["id"], item.quantity,
                reason=f"Checkout reservation for Order"
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to reserve stock for product '{prod.get('name')}'"
                )
            reserved_items.append((inv["id"], item.quantity))
            
            # 4. Snap values and calculate total
            price = prod.get("price", 0.0)
            discount = prod.get("discount_percentage", 0.0)
            final_price = price * (1.0 - discount / 100.0)
            item_total = final_price * item.quantity
            total_price += item_total
            
            order_items_to_create.append(
                OrderItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_at_purchase=final_price,
                    product_name_snapshot=prod.get("name"),
                    product_sku_snapshot=prod.get("sku")
                )
            )
            
        # Create order record
        order = Order(
            user_id=current_user.id,
            status="Pending",
            total_price=total_price
        )
        db.add(order)
        db.flush() # gets order.id
        
        # Link order items
        for order_item in order_items_to_create:
            order_item.order_id = order.id
            db.add(order_item)
            
        # Log history
        log_order_history(db, order.id, "Pending", "Order placed successfully")
        
        # Clear cart
        db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
        db.commit()
        db.refresh(order)
        return order
        
    except Exception as e:
        # Rollback DB
        db.rollback()
        # Rollback stock reservations in inventory service
        for inv_id, qty in reserved_items:
            inventory_service.release_stock(inv_id, qty, reason="Checkout transaction rollback")
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Checkout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during checkout processing"
        )

def release_order_reserved_stock(order: Order):
    """
    Release reserved stock for all items of an order back to the Inventory Service.
    """
    for item in order.items:
        inv = inventory_service.get_inventory_by_product_id(item.product_id)
        if inv:
            inventory_service.release_stock(
                inv["id"], item.quantity,
                reason=f"Order {order.id} cancelled/refunded - releasing stock"
            )

@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Cancel an order.
    - Customer can cancel their own order only if it's Pending or Confirmed.
    - Admin can cancel any active order.
    - Automatically releases reserved stock back to inventory.
    """
    order = db.query(Order).filter(Order.id == order_id, Order.is_active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if current_user.role != "admin":
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to cancel this order")
        if order.status not in ["Pending", "Confirmed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order in status '{order.status}'. Only Pending/Confirmed can be cancelled."
            )
            
    if order.status in ["Cancelled", "Refunded"]:
        raise HTTPException(status_code=400, detail="Order is already cancelled or refunded")
        
    # Release stock
    release_order_reserved_stock(order)
    
    order.status = "Cancelled"
    log_order_history(db, order.id, "Cancelled", f"Cancelled by {current_user.role}")
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Update order status.
    [Requires Admin Privileges]
    - Automatically releases stock if status is updated to Cancelled.
    """
    order = db.query(Order).filter(Order.id == order_id, Order.is_active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    valid_statuses = ["Pending", "Confirmed", "Processing", "Packed", "Shipped", "Delivered", "Cancelled", "Returned", "Refunded"]
    if status_in.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
    if order.status == status_in.status:
        return order
        
    # If transitioning to Cancelled, release stock
    if status_in.status == "Cancelled":
        release_order_reserved_stock(order)
        
    order.status = status_in.status
    log_order_history(db, order.id, status_in.status, status_in.notes)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/refund", response_model=OrderResponse)
def refund_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Refund an order.
    [Requires Admin Privileges]
    - Changes status to Refunded. Releases reserved stock if it was not already shipped/delivered.
    """
    order = db.query(Order).filter(Order.id == order_id, Order.is_active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status == "Refunded":
        raise HTTPException(status_code=400, detail="Order is already refunded")
        
    # If the order was not shipped or delivered yet, release reserved stock
    if order.status not in ["Shipped", "Delivered", "Cancelled"]:
        release_order_reserved_stock(order)
        
    order.status = "Refunded"
    log_order_history(db, order.id, "Refunded", "Refund issued by admin")
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Soft delete an order.
    [Requires Admin Privileges]
    """
    order = db.query(Order).filter(Order.id == order_id, Order.is_active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.is_active = False
    db.add(order)
    db.commit()
    return {"message": "Order soft-deleted successfully"}
