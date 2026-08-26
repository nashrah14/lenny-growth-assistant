"""
FastAPI Main Application Entry Point
Configures CORS, Request-ID tracing, Rate Limiting, lifespan handlers, exception handling, and API routing.
"""
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.core.exceptions import AppException
from backend.app.core.limiter import limiter
from backend.app.db.session import init_db
from backend.app.api.routes import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    setup_logging(settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode", extra={"operation": "app_startup"})
    logger.info(
        f"Rate limits — chat: {settings.RATE_LIMIT_CHAT_PER_MINUTE}/min, "
        f"auth: {settings.RATE_LIMIT_AUTH_PER_MINUTE}/min, "
        f"storage: {settings.RATE_LIMIT_STORAGE_URI}",
        extra={"operation": "rate_limit_config"}
    )
    
    # Initialize database tables
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}", extra={"operation": "db_init_warning"})

    yield
    logger.info(f"Shutting down {settings.APP_NAME}", extra={"operation": "app_shutdown"})


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Grounded RAG Assistant & Growth Intelligence Platform for Lenny's Podcast Transcripts",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# Attach limiter to app state (required by slowapi)
app.state.limiter = limiter

# ----------------- Middleware -----------------

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"]
)

# Request ID & Latency Tracing Middleware
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()

    response = await call_next(request)

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    response.headers["X-Request-ID"] = request_id

    # Log non-health requests
    if not request.url.path.endswith("/health") and not request.url.path.endswith("/readiness"):
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({latency_ms}ms)",
            extra={
                "request_id": request_id,
                "route": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms
            }
        )

    return response


# ----------------- Exception Handlers -----------------

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Return a structured JSON 429 with Retry-After information."""
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    retry_after = getattr(exc, "retry_after", 60)
    logger.warning(
        f"Rate limit exceeded: {exc.detail}",
        extra={"request_id": req_id, "route": request.url.path}
    )
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please wait before trying again.",
                "details": {
                    "limit": str(exc.detail),
                    "retry_after_seconds": retry_after,
                    "request_id": req_id
                }
            }
        }
    )
    response.headers["Retry-After"] = str(retry_after)
    return response


@app.exception_handler(AppException)
async def domain_exception_handler(request: Request, exc: AppException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(f"Handled Domain Exception: {exc.message}", extra={"request_id": req_id, "error_code": exc.error_code})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(f"Request validation error: {exc.errors()}", extra={"request_id": req_id})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request payload or query parameters.",
                "details": {"errors": exc.errors()},
                "request_id": req_id
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(f"Unhandled Server Exception: {exc}", exc_info=True, extra={"request_id": req_id})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please check server logs.",
                "details": {},
                "request_id": req_id
            }
        }
    )


# ----------------- Route Registration -----------------

app.include_router(api_v1_router)

@app.get("/", summary="Root Endpoint")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
