"""
Authentication API Routes (/api/v1/auth)
Implements Signup, Login, Logout, and Current User profile with HttpOnly cookie session management.
"""
from fastapi import APIRouter, Depends, Response, status
from backend.app.core.config import settings
from backend.app.db.models.user import User
from backend.app.services.auth_service import AuthService
from backend.app.api.deps import (
    get_auth_service,
    get_current_user,
    SignupRequest,
    LoginRequest,
    UserResponse,
    AuthResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_auth_cookie(response: Response, token: str) -> None:
    """Set secure HttpOnly authentication cookie (OWASP compliant)."""
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=max_age,
        path="/"
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear authentication session cookie on logout."""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
async def signup(
    payload: SignupRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    user, token = await auth_service.signup(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        confirm_password=payload.confirm_password
    )
    set_auth_cookie(response, token)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        message="Account created successfully"
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password"
)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    user, token = await auth_service.login(
        email=payload.email,
        password=payload.password
    )
    set_auth_cookie(response, token)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        message="Logged in successfully"
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Invalidate session and log out"
)
async def logout(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get currently authenticated user"
)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
