from fastapi import Request

from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException
from app.modules.proxy.translate.deepl_api import DeeplApi
from app.modules.proxy.translate.translate_types import Translation, TranslationRequest


async def translate(request: Request, body: TranslationRequest) -> Translation:
    """
    Translate text using the DeepL API.
    """
    env: PkCentralEnv = request.app.state.env
    logger = request.app.state.logger

    try:
        deepl = DeeplApi(
            api_key=env.DEEPL_API_KEY,
            translate_url=env.PROXY_DEEPL_TRANSLATE_URL,
            logger=logger,
        )

        return await deepl.translate_text(
            text=body.text,
            target_lang=body.target_lang,
            source_lang=body.source_lang,
        )

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise InternalServerErrorException(
            detail="Translation failed due to error:" + str(e)
        )
