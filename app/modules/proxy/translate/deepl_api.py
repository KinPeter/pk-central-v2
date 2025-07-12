import httpx
from logging import Logger

from app.common.environment import PkCentralEnv
from app.modules.proxy.translate.translate_types import (
    DeeplLanguage,
    Translation,
    target_languages,
    source_languages,
)


class DeeplApi:
    """
    A class to interact with the DeepL API for translations.
    """

    def __init__(self, api_key: str, translate_url: str, logger: Logger):
        self.api_key = api_key
        self.translate_url = translate_url
        self.logger = logger

    async def translate_text(
        self,
        text: str,
        target_lang: DeeplLanguage,
        source_lang: DeeplLanguage,
    ) -> Translation:
        """
        Translate text using the DeepL API.
        """
        body = {
            "text": [text],
            "target_lang": target_languages[target_lang],
            "source_lang": source_languages[source_lang],
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url=self.translate_url,
                    headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
                translation = " ".join(
                    str(item["text"]) for item in data.get("translations", [])
                )

            except httpx.HTTPStatusError as e:
                self.logger.error(
                    f"Error during DeepL API call: {e.response.status_code} - {e.response.text}"
                )
                raise e

        return Translation(
            original=text,
            translation=translation,
            source_lang=source_lang,
            target_lang=target_lang,
        )
