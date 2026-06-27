from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user, require_auth, RoleChecker, UserContext
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse

router = APIRouter()

# Role checkers
admin_required = RoleChecker(allowed_roles=["admin"])

@router.get("/", response_model=ProductListResponse)
def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "newest",
    db: Session = Depends(get_db)
):
    """
    Retrieve products with search, pagination, filters, and sorting.
    Publicly accessible to everyone.
    """
    query = db.query(Product).filter(Product.is_active == True)
    
    # 1. Search filter
    if q:
        query = query.filter(
            (Product.name.ilike(f"%{q}%")) | 
            (Product.description.ilike(f"%{q}%"))
        )
        
    # 2. Category filter
    if category:
        query = query.filter(Product.category == category)
        
    # 3. Brand filter
    if brand:
        query = query.filter(Product.brand == brand)
        
    # 4. Price range filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
        
    # Total count
    total = query.count()
    
    # 5. Sorting
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "rating":
        query = query.order_by(Product.average_rating.desc())
    elif sort_by == "newest":
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.created_at.desc())
        
    # 6. Pagination
    items = query.offset(skip).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific product by ID.
    Publicly accessible to everyone.
    """
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Create a new product.
    [Requires Admin Privileges]
    """
    existing_sku = db.query(Product).filter(Product.sku == product_in.sku).first()
    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A product with this SKU already exists"
        )
        
    db_product = Product(
        name=product_in.name,
        description=product_in.description,
        brand=product_in.brand,
        category=product_in.category,
        sku=product_in.sku,
        price=product_in.price,
        discount_percentage=product_in.discount_percentage,
        stock_quantity=product_in.stock_quantity,
        image_urls=product_in.image_urls,
        average_rating=0.0,
        review_count=0,
        is_active=True
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Update an existing product.
    [Requires Admin Privileges]
    """
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
        
    if product_in.sku and product_in.sku != product.sku:
        existing_sku = db.query(Product).filter(Product.sku == product_in.sku).first()
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A product with this SKU already exists"
            )

    # Apply updates
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
        
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Soft delete a product by deactivating it.
    [Requires Admin Privileges]
    """
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
        
    product.is_active = False
    db.add(product)
    db.commit()
    return {"message": "Product successfully deleted (soft-deleted)"}
