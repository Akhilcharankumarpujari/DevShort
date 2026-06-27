from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    brand: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    sku: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0.0)
    discount_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    stock_quantity: int = Field(default=0, ge=0)
    image_urls: List[str] = Field(default_factory=list)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    brand: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    sku: Optional[str] = Field(default=None, min_length=1, max_length=100)
    price: Optional[float] = Field(default=None, gt=0.0)
    discount_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    image_urls: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    average_rating: float
    review_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    skip: int
    limit: int
