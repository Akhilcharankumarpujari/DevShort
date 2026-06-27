from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    price_at_purchase: float
    product_name_snapshot: str
    product_sku_snapshot: str

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_price: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)

class OrderStatusUpdate(BaseModel):
    status: str = Field(..., description="Target status for transition")
    notes: Optional[str] = Field(default=None, max_length=255)
