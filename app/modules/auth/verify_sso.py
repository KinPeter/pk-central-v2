from logging import Logger
from fastapi import Request

from app.common.aws_cognito import CognitoClientHelper
from app.common.db import DbCollection
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, UnauthorizedException
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import SsoLoginRequest, LoginResponse
from app.modules.auth.auth_utils import get_access_token


async def sso_verify(body: SsoLoginRequest, request: Request) -> LoginResponse:
    """
    Verify the SSO id token issued by AWS Cognito.
    If the token is not valid or expired, it will return an error.
    """
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db
    email = None

    try:
        email = body.email.lower().strip()
        id_token = body.id_token.strip()
        cognito = CognitoClientHelper(env)

        verified_email = cognito.verify_id_token(email, id_token)

        user = await db.get_collection(DbCollection.USERS).find_one(
            {"email": verified_email}
        )

        if not user:
            raise UnauthorizedException("User does not exist")

        token, expires_at = get_access_token(
            user_id=user["id"], secret=env.JWT_SECRET, expires_in_days=env.TOKEN_EXPIRY
        )

        return LoginResponse(
            email=email, id=user["id"], token=token, expires_at=expires_at.isoformat()
        )

    except UnauthorizedException as e:
        raise e
    except Exception as e:
        logger.error(f"Error logging in user {email}: {e}")
        raise InternalServerErrorException(
            "An error occurred while logging in. Please try again later." + str(e)
        )
