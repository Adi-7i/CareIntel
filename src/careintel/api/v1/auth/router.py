"""
Auth API router.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from careintel.api.deps import CurrentUserDep, RawTokenDep, get_auth_service
from careintel.application.auth.auth_service import AuthService
from careintel.api.v1.auth.schemas import LoginRequest, TokenResponse, UserProfileResponse
from careintel.core.correlation import get_correlation_id

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login for an access token",
)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Authenticate user with email and password to receive a JWT access token.
    """
    token, _ = await auth_service.login(
        email=request.email,
        password=request.password,
        correlation_id=get_correlation_id(),
    )
    return TokenResponse(access_token=token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke current session",
)
async def logout(
    raw_token: RawTokenDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """
    Revoke the current user's access token session.
    """
    await auth_service.logout(
        token=raw_token,
        correlation_id=get_correlation_id(),
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: CurrentUserDep,
) -> UserProfileResponse:
    """
    Get the profile, roles, and permissions of the currently authenticated user.
    """
    return UserProfileResponse(
        id=current_user.id,
        is_active=current_user.is_active,
        roles=list(current_user.roles),
        permissions=list(current_user.permissions),
    )
