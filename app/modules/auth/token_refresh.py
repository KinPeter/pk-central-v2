from logging import Logger
from fastapi import Request
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException
from app.modules.auth.auth_types import CurrentUser, LoginResponse
from app.modules.auth.auth_utils import get_access_token


async def token_refresh(request: Request, user: CurrentUser) -> LoginResponse:
    """
    Refresh the authentication token.
    """
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger

    try:
        token, expires_at = get_access_token(
            user_id=user.id,
            secret=env.JWT_SECRET,
            expires_in_days=env.TOKEN_EXPIRY,
        )

        return LoginResponse(
            email=user.email,
            id=user.id,
            token=token,
            expires_at=expires_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise InternalServerErrorException(
            "An error occurred while refreshing the token. Please try again later."
        ) from e
