from typing import Optional
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_inventory_by_product_id(product_id: int) -> Optional[dict]:
    """
    Get inventory record for a product.
    """
    url = f"{settings.INVENTORY_SERVICE_URL}{settings.API_V1_STR}/inventory/product/{product_id}"
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            return response.json()
        logger.error(f"Failed to fetch inventory for product {product_id}. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error calling Inventory Service for product {product_id}: {str(e)}")
    return None

def reserve_stock(inventory_id: int, amount: int, reason: str) -> bool:
    """
    Reserve stock for an inventory record.
    """
    url = f"{settings.INVENTORY_SERVICE_URL}{settings.API_V1_STR}/inventory/{inventory_id}/reserve"
    try:
        response = httpx.post(url, json={"amount": amount, "reason": reason}, timeout=5.0)
        if response.status_code == 200:
            return True
        logger.error(f"Failed to reserve stock for inventory {inventory_id}. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error calling Inventory Service reserve for inventory {inventory_id}: {str(e)}")
    return False

def release_stock(inventory_id: int, amount: int, reason: str) -> bool:
    """
    Release reserved stock.
    """
    url = f"{settings.INVENTORY_SERVICE_URL}{settings.API_V1_STR}/inventory/{inventory_id}/release"
    try:
        response = httpx.post(url, json={"amount": amount, "reason": reason}, timeout=5.0)
        if response.status_code == 200:
            return True
        logger.error(f"Failed to release stock for inventory {inventory_id}. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error calling Inventory Service release for inventory {inventory_id}: {str(e)}")
    return False
