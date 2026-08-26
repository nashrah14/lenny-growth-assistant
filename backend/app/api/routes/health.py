"""
Health & Readiness Routes (/api/v1/health & /api/v1/readiness)
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.rag.qdrant import qdrant_adapter
from backend.app.llm.router import llm_router
from backend.app.api.deps import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse, summary="System Health & Connectivity Check")
async def health_check(db: AsyncSession = Depends(get_db)):
    # 1. Check Database
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {e}"

    # 2. Check Qdrant
    q_health = await qdrant_adapter.health()
    q_status = q_health.get("status", "unknown")

    # 3. Check LLM Providers
    llm_status = await llm_router.get_health_status()

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        qdrant=q_status,
        llm_providers=llm_status
    )


@router.get("/readiness", status_code=status.HTTP_200_OK, summary="Kubernetes / Docker Readiness Probe")
async def readiness_probe():
    return {"status": "ready", "app": settings.APP_NAME}
