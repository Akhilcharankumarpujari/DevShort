from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import require_auth, UserContext
from app.models.cart import CartItem
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartItemResponse

router = APIRouter()

@router.get("/", response_model=List[CartItemResponse])
def view_cart(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Retrieve all items in the user's shopping cart.
    """
    return db.query(CartItem).filter(CartItem.user_id == current_user.id).all()

@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(
    item_in: CartItemAdd,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Add a product to the user's shopping cart.
    If the product is already in the cart, increments the quantity.
    """
    existing_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item_in.product_id
    ).first()
    
    if existing_item:
        existing_item.quantity += item_in.quantity
        db.add(existing_item)
        db.commit()
        db.refresh(existing_item)
        return existing_item
        
    cart_item = CartItem(
        user_id=current_user.id,
        product_id=item_in.product_id,
        quantity=item_in.quantity
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.put("/{item_id}", response_model=CartItemResponse)
def update_cart_item_quantity(
    item_id: int,
    item_in: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Update the quantity of a specific cart item.
    """
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
        
    cart_item.quantity = item_in.quantity
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
def remove_item_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Remove a product from the user's shopping cart.
    """
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
        
    db.delete(cart_item)
    db.commit()
    return {"message": "Item removed from cart"}

@router.delete("/", status_code=status.HTTP_200_OK)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Clear all items in the user's shopping cart.
    """
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Cart cleared successfully"}
