"""
API Routes Package Exports
"""
from fastapi import APIRouter
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.sessions import router as sessions_router
from backend.app.api.routes.messages import router as messages_router
from backend.app.api.routes.artifacts import router as artifacts_router
from backend.app.api.routes.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(messages_router)
api_v1_router.include_router(artifacts_router)
api_v1_router.include_router(health_router)

__all__ = ["api_v1_router"]
