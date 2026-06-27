from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class HistoryResponse(BaseModel):
    id: int
    inventory_id: int
    action: str
    quantity_changed: int
    old_available: int
    new_available: int
    old_reserved: int
    new_reserved: int
    reason: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
