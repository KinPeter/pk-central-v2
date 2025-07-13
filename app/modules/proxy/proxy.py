from typing_extensions import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.responses import ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.proxy.location.get_city import get_city
from app.modules.proxy.location.location_types import CityLocation
from app.modules.proxy.translate.translate import translate
from app.modules.proxy.translate.translate_types import Translation, TranslationRequest


router = APIRouter(tags=["Proxy"], prefix="/proxy")


@router.post(
    path="/translate",
    summary="Translate text using DeepL API",
    status_code=status.HTTP_200_OK,
    responses={
        **ResponseDocs.unauthorized_response,
    },
)
async def post_translate(
    request: Request,
    body: TranslationRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Translation:
    """
    Translate text using the DeepL API.
    """
    return await translate(request, body)


@router.get(
    path="/location/city",
    summary="Get city information based on latitude and longitude",
    status_code=status.HTTP_200_OK,
    responses={
        **ResponseDocs.unauthorized_response,
        **ResponseDocs.not_found_response,
    },
)
async def get_get_city(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
    lat: float,
    lng: float,
) -> CityLocation:
    """
    Get city information based on latitude and longitude.
    """
    return await get_city(request, lat, lng)
