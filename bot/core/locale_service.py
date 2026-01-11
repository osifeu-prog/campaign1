# ===============================
# locale_service – תמיכה בשפות (כרגע: עברית)
# ===============================

from typing import Literal


LanguageCode = Literal["he", "en"]


class LocaleService:
    def __init__(self, default_lang: LanguageCode = "he"):
        self.default_lang = default_lang

    def detect_language(self, tg_language_code: str | None) -> LanguageCode:
        if not tg_language_code:
            return self.default_lang
        if tg_language_code.startswith("he"):
            return "he"
        if tg_language_code.startswith("en"):
            return "en"
        return self.default_lang

    def t(self, key: str, lang: LanguageCode = "he") -> str:
        he = {
            "start_intro": (
                "ברוך הבא לתנועת אחדות.\n\n"
                "אני הבוט שדרכו מצטרפים, נרשמים כתומכים ומגישים מועמדות כמומחים.\n\n"
                "איך תרצה להצטרף?"
            ),
            "unknown_command": (
                "הפקודה הזו לא מוכרת.\n"
                "נסה /menu כדי לראות את כל האפשרויות."
            ),
        }

        if lang == "he":
            return he.get(key, key)
        return he.get(key, key)


locale_service = LocaleService()
