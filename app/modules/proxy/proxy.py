from typing_extensions import Annotated
from fastapi import APIRouter, Depends, Request

from app.common.responses import ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.proxy.translate.translate import translate
from app.modules.proxy.translate.translate_types import Translation, TranslationRequest


router = APIRouter(tags=["Proxy"], prefix="/proxy")


@router.post(
    path="/translate",
    summary="Translate text using DeepL API",
    status_code=200,
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
