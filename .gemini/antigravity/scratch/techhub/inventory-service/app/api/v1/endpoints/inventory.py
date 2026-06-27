from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user, require_auth, RoleChecker, UserContext
from app.models.inventory import Inventory
from app.models.history import InventoryHistory
from app.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse, StockAdjustment, StockReservation
from app.schemas.history import HistoryResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Role checkers
admin_required = RoleChecker(allowed_roles=["admin"])

def update_status_and_log_event(inv: Inventory):
    old_status = inv.status
    available = inv.available_quantity
    
    if available == 0:
        inv.status = "OUT_OF_STOCK"
    elif available <= inv.low_stock_threshold:
        inv.status = "LOW_STOCK"
    else:
        inv.status = "IN_STOCK"
        
    if old_status != inv.status:
        if inv.status == "OUT_OF_STOCK":
            logger.warning(
                f"[INVENTORY_EVENT] Product {inv.product_id} (SKU: {inv.sku}) is now OUT_OF_STOCK."
            )
        elif inv.status == "LOW_STOCK":
            logger.warning(
                f"[INVENTORY_EVENT] Product {inv.product_id} (SKU: {inv.sku}) is now LOW_STOCK. Available: {available} (Threshold: {inv.low_stock_threshold})."
            )
        elif old_status in ["LOW_STOCK", "OUT_OF_STOCK"] and inv.status == "IN_STOCK":
            logger.info(
                f"[INVENTORY_EVENT] Product {inv.product_id} (SKU: {inv.sku}) stock restored to IN_STOCK. Available: {available}."
            )

def log_history(
    db: Session,
    inv: Inventory,
    action: str,
    qty_changed: int,
    old_avail: int,
    new_avail: int,
    old_res: int,
    new_res: int,
    reason: Optional[str] = None
):
    history = InventoryHistory(
        inventory_id=inv.id,
        action=action,
        quantity_changed=qty_changed,
        old_available=old_avail,
        new_available=new_avail,
        old_reserved=old_res,
        new_reserved=new_res,
        reason=reason
    )
    db.add(history)

@router.get("/", response_model=List[InventoryResponse])
def list_inventory(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all inventory records.
    Publicly accessible.
    """
    return db.query(Inventory).offset(skip).limit(limit).all()

@router.get("/status/low-stock", response_model=List[InventoryResponse])
def list_low_stock(db: Session = Depends(get_db)):
    """
    List all inventory items currently in LOW_STOCK status.
    """
    return db.query(Inventory).filter(Inventory.status == "LOW_STOCK").all()

@router.get("/status/out-of-stock", response_model=List[InventoryResponse])
def list_out_of_stock(db: Session = Depends(get_db)):
    """
    List all inventory items currently in OUT_OF_STOCK status.
    """
    return db.query(Inventory).filter(Inventory.status == "OUT_OF_STOCK").all()

@router.get("/{inventory_id}", response_model=InventoryResponse)
def get_inventory_by_id(inventory_id: int, db: Session = Depends(get_db)):
    """
    Get inventory record by ID.
    """
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    return inv

@router.get("/product/{product_id}", response_model=InventoryResponse)
def get_inventory_by_product_id(product_id: int, db: Session = Depends(get_db)):
    """
    Get inventory record by Product ID.
    """
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found for this product")
    return inv

@router.get("/{inventory_id}/history", response_model=List[HistoryResponse])
def get_inventory_history(inventory_id: int, db: Session = Depends(get_db)):
    """
    Get audit history of stock adjustments for a specific inventory record.
    """
    # Verify inventory exists
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    return db.query(InventoryHistory).filter(InventoryHistory.inventory_id == inventory_id).order_by(InventoryHistory.id.desc()).all()

@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(
    inv_in: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Create a new inventory record for a product.
    [Requires Admin Privileges]
    """
    existing = db.query(Inventory).filter(
        (Inventory.product_id == inv_in.product_id) | (Inventory.sku == inv_in.sku)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Inventory record for this product or SKU already exists"
        )
        
    inv = Inventory(
        product_id=inv_in.product_id,
        warehouse_id=inv_in.warehouse_id,
        sku=inv_in.sku,
        available_quantity=inv_in.initial_quantity,
        reserved_quantity=0,
        low_stock_threshold=inv_in.low_stock_threshold
    )
    update_status_and_log_event(inv)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    
    log_history(
        db, inv, "CREATE",
        inv_in.initial_quantity,
        0, inv.available_quantity,
        0, 0,
        reason="Initial creation"
    )
    db.commit()
    return inv

@router.put("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(
    inventory_id: int,
    inv_in: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Update inventory properties like low stock threshold or warehouse.
    [Requires Admin Privileges]
    """
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
        
    if inv_in.warehouse_id is not None:
        inv.warehouse_id = inv_in.warehouse_id
    if inv_in.low_stock_threshold is not None:
        inv.low_stock_threshold = inv_in.low_stock_threshold
        # Status might change based on new threshold
        update_status_and_log_event(inv)
        
    db.add(inv)
    db.commit()
    db.refresh(inv)
    
    log_history(
        db, inv, "UPDATE",
        0,
        inv.available_quantity, inv.available_quantity,
        inv.reserved_quantity, inv.reserved_quantity,
        reason=f"Properties updated (threshold: {inv.low_stock_threshold})"
    )
    db.commit()
    return inv

@router.post("/{inventory_id}/increase", response_model=InventoryResponse)
def increase_stock(
    inventory_id: int,
    adj: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Increase available stock.
    [Requires Admin Privileges]
    """
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
        
    old_avail = inv.available_quantity
    inv.available_quantity += adj.amount
    update_status_and_log_event(inv)
    db.add(inv)
    
    log_history(
        db, inv, "INCREASE",
        adj.amount,
        old_avail, inv.available_quantity,
        inv.reserved_quantity, inv.reserved_quantity,
        reason=adj.reason
    )
    db.commit()
    db.refresh(inv)
    return inv

@router.post("/{inventory_id}/decrease", response_model=InventoryResponse)
def decrease_stock(
    inventory_id: int,
    adj: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Decrease available stock directly. Prevents negative stock.
    [Requires Admin Privileges]
    """
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
        
    if inv.available_quantity < adj.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decrease by {adj.amount}. Only {inv.available_quantity} available."
        )
        
    old_avail = inv.available_quantity
    inv.available_quantity -= adj.amount
    update_status_and_log_event(inv)
    db.add(inv)
    
    log_history(
        db, inv, "DECREASE",
        -adj.amount,
        old_avail, inv.available_quantity,
        inv.reserved_quantity, inv.reserved_quantity,
        reason=adj.reason
    )
    db.commit()
    db.refresh(inv)
    return inv

@router.post("/{inventory_id}/reserve", response_model=InventoryResponse)
def reserve_stock(
    inventory_id: int,
    res: StockReservation,
    db: Session = Depends(get_db)
):
    """
    Reserve available stock for checkout. Prevents negative stock.
    Accessible to authorized services / users (like Order Service).
    """
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
        
    if inv.available_quantity < res.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reserve {res.amount}. Only {inv.available_quantity} available."
        )
        
    old_avail = inv.available_quantity
    old_res = inv.reserved_quantity
    
    inv.available_quantity -= res.amount
    inv.reserved_quantity += res.amount
    update_status_and_log_event(inv)
    db.add(inv)
    
    log_history(
        db, inv, "RESERVE",
        res.amount,
        old_avail, inv.available_quantity,
        old_res, inv.reserved_quantity,
        reason=res.reason
    )
    db.commit()
    db.refresh(inv)
    return inv

@router.post("/{inventory_id}/release", response_model=InventoryResponse)
def release_stock(
    inventory_id: int,
    res: StockReservation,
    db: Session = Depends(get_db)
):
    """
    Release reserved stock back to available stock. Prevents negative reserved stock.
    """
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
        
    if inv.reserved_quantity < res.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot release {res.amount}. Only {inv.reserved_quantity} reserved."
        )
        
    old_avail = inv.available_quantity
    old_res = inv.reserved_quantity
    
    inv.available_quantity += res.amount
    inv.reserved_quantity -= res.amount
    update_status_and_log_event(inv)
    db.add(inv)
    
    log_history(
        db, inv, "RELEASE",
        res.amount,
        old_avail, inv.available_quantity,
        old_res, inv.reserved_quantity,
        reason=res.reason
    )
    db.commit()
    db.refresh(inv)
    return inv
