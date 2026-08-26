"""
Rate Limiter Singleton
Extracted into its own module to break the circular import between main.py and routes.

Import from here in any route file:
  from backend.app.core.limiter import limiter
"""
from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_key(request) -> str:
    """
    Rate-limit key function.

    Prefers authenticated user ID extracted from JWT cookie or Authorization header.
    Falls back to client IP address.

    This approach:
    - Prevents one user from consuming another user's quota
    - Still protects unauthenticated endpoints by IP
    - Is imported lazily to avoid circular dependency with security module
    """
    try:
        from backend.app.core.config import settings
        from backend.app.core.security import decode_access_token

        token = request.cookies.get(settings.COOKIE_NAME)
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
        if token:
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                return f"user:{payload['sub']}"
    except Exception:
        pass
    return get_remote_address(request)


def _get_storage_uri() -> str:
    """Read storage URI from settings lazily."""
    try:
        from backend.app.core.config import settings
        return settings.RATE_LIMIT_STORAGE_URI
    except Exception:
        return "memory://"


limiter = Limiter(
    key_func=_rate_limit_key,
    storage_uri=_get_storage_uri(),
    default_limits=[]  # No global default — applied per-endpoint only
)
