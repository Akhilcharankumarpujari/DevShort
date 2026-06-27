from typing import Optional
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_product_metadata(product_id: int) -> Optional[dict]:
    """
    Fetch product information from Product Service.
    """
    url = f"{settings.PRODUCT_SERVICE_URL}{settings.API_V1_STR}/products/{product_id}"
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            return response.json()
        logger.error(f"Failed to fetch product {product_id}. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error calling Product Service for product {product_id}: {str(e)}")
    return None
