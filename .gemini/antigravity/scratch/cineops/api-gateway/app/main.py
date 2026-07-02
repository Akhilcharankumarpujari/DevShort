import httpx
from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.config import settings
from app.middleware import setup_logging, LoggingAndMetricsMiddleware

# Initialize logging
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(LoggingAndMetricsMiddleware, service_name="api-gateway")

# Persistent httpx client for reuse
client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()

import json

@app.get("/health")
async def health():
    health_status = {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0",
        "database": "N/A",
        "dependencies": {}
    }
    
    # Check each dependency
    for name, url in SERVICE_MAP.items():
        try:
            async with httpx.AsyncClient() as async_client:
                res = await async_client.get(f"{url}/health", timeout=2.0)
                if res.status_code == 200:
                    health_status["dependencies"][name] = "connected"
                else:
                    health_status["dependencies"][name] = f"unhealthy (status {res.status_code})"
                    health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["dependencies"][name] = f"disconnected: {str(e)}"
            health_status["status"] = "unhealthy"
            
    status_code = 200 if health_status["status"] == "healthy" else 500
    return Response(
        status_code=status_code,
        content=json.dumps(health_status),
        media_type="application/json"
    )

from prometheus_fastapi_instrumentator import Instrumentator

# Initialize Prometheus Instrumentator
Instrumentator().instrument(app).expose(app)

# Map service names to their base URLs
SERVICE_MAP = {
    "users": settings.USER_SERVICE_URL,
    "movies": settings.MOVIE_SERVICE_URL,
    "bookings": settings.BOOKING_SERVICE_URL,
    "payments": settings.PAYMENT_SERVICE_URL,
    "notifications": settings.NOTIFICATION_SERVICE_URL,
}

@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def route_gateway(service: str, path: str, request: Request):
    if service not in SERVICE_MAP:
        return Response(status_code=404, content=f"Service '{service}' not found")
    
    target_url = f"{SERVICE_MAP[service]}/api/v1/{service}/{path}"
    
    # Forward query parameters
    query_params = dict(request.query_params)
    
    # Forward headers, modifying Host
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Read body
    body = await request.body()
    
    try:
        # Proxy the request
        async_response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=query_params,
            content=body,
            timeout=10.0
        )
        return Response(
            content=async_response.content,
            status_code=async_response.status_code,
            headers=dict(async_response.headers)
        )
    except httpx.RequestError as exc:
        return Response(
            status_code=502,
            content=f"Gateway Error: Unable to reach downstream service. Exception: {exc}"
        )
