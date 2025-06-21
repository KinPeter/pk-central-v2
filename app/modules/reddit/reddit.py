from typing import Annotated
from fastapi import APIRouter, Request, status
from fastapi.params import Depends

from app.common.responses import ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.reddit.get_reddit_config import get_reddit_config
from app.modules.reddit.reddit_types import RedditConfig, RedditConfigRequest
from app.modules.reddit.update_reddit_config import update_reddit_config


router = APIRouter(tags=["Reddit"], prefix="/reddit")


@router.get(
    path="/config",
    summary="Get Reddit configuration for the current user",
    status_code=status.HTTP_200_OK,
    responses={
        **ResponseDocs.unauthorized_response,
        **ResponseDocs.not_found_response,
    },
)
async def get_get_reddit_config(
    request: Request, user: Annotated[CurrentUser, Depends(auth_user)]
) -> RedditConfig:
    """
    Get the Reddit configuration for the current user.
    This includes favorite subreddits and usernames.
    """
    return await get_reddit_config(request, user)


@router.put(
    path="/config",
    summary="Update Reddit configuration for the current user",
    status_code=status.HTTP_200_OK,
    responses={
        **ResponseDocs.unauthorized_response,
        **ResponseDocs.not_found_response,
    },
)
async def put_update_reddit_config(
    request: Request,
    body: RedditConfigRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> RedditConfig:
    """
    Update the Reddit configuration for the current user.
    """
    return await update_reddit_config(request, body, user)
