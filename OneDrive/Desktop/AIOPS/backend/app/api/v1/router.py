from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.kubernetes import router as kubernetes_router
from app.api.routes.prometheus import router as prometheus_router
from app.api.routes.loki import router as loki_router
from app.api.routes.alertmanager import router as alertmanager_router
from app.api.routes.ai import router as ai_router
from app.api.routes.jenkins import router as jenkins_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(incidents_router, prefix="/incidents", tags=["incidents"])
api_router.include_router(kubernetes_router, prefix="/k8s", tags=["kubernetes"])
api_router.include_router(prometheus_router, prefix="/metrics", tags=["metrics"])
api_router.include_router(loki_router, prefix="/logs", tags=["logs"])
api_router.include_router(alertmanager_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(jenkins_router, prefix="/jenkins", tags=["jenkins"])
