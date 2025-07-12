from enum import Enum

from pydantic import Field

from app.common.responses import OkResponse
from app.common.types import PkBaseModel


class DeeplLanguage(str, Enum):
    DA = "da"
    DE = "de"
    EL = "el"
    EN = "en"
    ES = "es"
    FR = "fr"
    HU = "hu"
    IT = "it"
    JA = "ja"
    KO = "ko"
    NL = "nl"
    PL = "pl"
    PT = "pt"
    RU = "ru"
    ZH = "zh"


source_languages = {
    DeeplLanguage.DA: "DA",
    DeeplLanguage.DE: "DE",
    DeeplLanguage.EL: "EL",
    DeeplLanguage.EN: "EN",
    DeeplLanguage.ES: "ES",
    DeeplLanguage.FR: "FR",
    DeeplLanguage.HU: "HU",
    DeeplLanguage.IT: "IT",
    DeeplLanguage.JA: "JA",
    DeeplLanguage.KO: "KO",
    DeeplLanguage.NL: "NL",
    DeeplLanguage.PL: "PL",
    DeeplLanguage.PT: "PT",
    DeeplLanguage.RU: "RU",
    DeeplLanguage.ZH: "ZH",
}

target_languages = {
    DeeplLanguage.DA: "DA",
    DeeplLanguage.DE: "DE",
    DeeplLanguage.EL: "EL",
    DeeplLanguage.EN: "EN-US",
    DeeplLanguage.ES: "ES",
    DeeplLanguage.FR: "FR",
    DeeplLanguage.HU: "HU",
    DeeplLanguage.IT: "IT",
    DeeplLanguage.JA: "JA",
    DeeplLanguage.KO: "KO",
    DeeplLanguage.NL: "NL",
    DeeplLanguage.PL: "PL",
    DeeplLanguage.PT: "PT-PT",
    DeeplLanguage.RU: "RU",
    DeeplLanguage.ZH: "ZH-HANS",
}


class TranslationRequest(PkBaseModel):
    text: str = Field(..., min_length=1)
    source_lang: DeeplLanguage
    target_lang: DeeplLanguage


class Translation(OkResponse):
    original: str
    translation: str
    source_lang: DeeplLanguage
    target_lang: DeeplLanguage
