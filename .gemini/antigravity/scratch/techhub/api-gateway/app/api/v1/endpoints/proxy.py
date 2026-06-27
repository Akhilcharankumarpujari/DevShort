from fastapi import APIRouter, Request, Response, HTTPException
import httpx
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def proxy_request(service_url: str, path: str, request: Request) -> Response:
    url = f"{service_url}{path}"
    # Filter out Host header to let httpx compute it
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
    
    body = await request.body()
    params = request.query_params
    method = request.method
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                content=body,
                timeout=10.0
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except httpx.RequestError as exc:
            logger.error(f"Error proxying request to {url}: {exc}")
            raise HTTPException(status_code=503, detail="Service unavailable")

@router.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_users(path: str, request: Request):
    return await proxy_request(settings.USER_SERVICE_URL, f"/api/v1/users/{path}", request)

@router.api_route("/products/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_products(path: str, request: Request):
    return await proxy_request(settings.PRODUCT_SERVICE_URL, f"/api/v1/products/{path}", request)

@router.api_route("/orders/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_orders(path: str, request: Request):
    return await proxy_request(settings.ORDER_SERVICE_URL, f"/api/v1/orders/{path}", request)

@router.api_route("/inventory/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_inventory(path: str, request: Request):
    return await proxy_request(settings.INVENTORY_SERVICE_URL, f"/api/v1/inventory/{path}", request)

@router.api_route("/payments/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_payments(path: str, request: Request):
    return await proxy_request(settings.PAYMENT_SERVICE_URL, f"/api/v1/payments/{path}", request)
