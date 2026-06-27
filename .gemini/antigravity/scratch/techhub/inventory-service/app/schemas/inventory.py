from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class InventoryBase(BaseModel):
    product_id: int = Field(..., gt=0)
    warehouse_id: str = Field(..., min_length=1, max_length=50)
    sku: str = Field(..., min_length=1, max_length=100)
    low_stock_threshold: int = Field(default=10, ge=0)

class InventoryCreate(InventoryBase):
    initial_quantity: int = Field(default=0, ge=0)

class InventoryUpdate(BaseModel):
    warehouse_id: Optional[str] = Field(default=None, min_length=1, max_length=50)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0)

class InventoryResponse(InventoryBase):
    id: int
    available_quantity: int
    reserved_quantity: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StockAdjustment(BaseModel):
    amount: int = Field(..., gt=0, description="Amount of stock to change")
    reason: Optional[str] = Field(default=None, max_length=255)

class StockReservation(BaseModel):
    amount: int = Field(..., gt=0, description="Amount of stock to reserve/release")
    reason: Optional[str] = Field(default=None, max_length=255)
