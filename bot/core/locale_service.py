# bot/core/locale_service.py
# ===============================
# locale_service – תמיכה בשפות (כרגע: עברית + אנגלית בסיסית)
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

        en = {
            "start_intro": (
                "Welcome to the Unity Movement.\n\n"
                "This bot helps you join, register as a supporter, or apply as an expert.\n\n"
                "How would you like to join?"
            ),
            "unknown_command": (
                "Unknown command.\n"
                "Try /menu to see available options."
            ),
        }

        if lang == "he":
            return he.get(key, key)
        return en.get(key, key)


locale_service = LocaleService()
