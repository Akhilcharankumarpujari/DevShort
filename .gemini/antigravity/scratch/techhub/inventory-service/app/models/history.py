from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base

class InventoryHistory(Base):
    __tablename__ = "inventory_history"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False) # e.g. "CREATE", "UPDATE", "INCREASE", "DECREASE", "RESERVE", "RELEASE"
    quantity_changed = Column(Integer, nullable=False)
    old_available = Column(Integer, nullable=False)
    new_available = Column(Integer, nullable=False)
    old_reserved = Column(Integer, nullable=False)
    new_reserved = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
