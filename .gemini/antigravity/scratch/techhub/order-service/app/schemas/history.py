from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class OrderHistoryResponse(BaseModel):
    id: int
    order_id: int
    status: str
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
