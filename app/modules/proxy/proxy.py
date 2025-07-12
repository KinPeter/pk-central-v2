from typing_extensions import Annotated
from fastapi import APIRouter, Depends, Request

from app.common.responses import ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user


router = APIRouter(tags=["Proxy"], prefix="/proxy")


@router.get(
    path="/something",
    summary="Get the list of something",
    status_code=200,
    responses={
        **ResponseDocs.unauthorized_response,
        **ResponseDocs.not_found_response,
    },
)
async def get_get_birthdays(
    request: Request, user: Annotated[CurrentUser, Depends(auth_user)]
) -> ListResponse[dict]:
    """
    Get the list of something from the proxy service.
    """
    return ListResponse(
        entities=[{"name": "John Doe", "date": "2023-01-01"}]
    )  # Placeholder response
