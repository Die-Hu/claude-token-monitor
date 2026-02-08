"""Internationalization support for Claude Token Monitor."""

import locale
import os
from typing import Optional

from claude_token_monitor.i18n import en, zh

_current_lang: str = "en"
_strings: dict[str, str] = {}


def init(lang: Optional[str] = None) -> None:
    """Initialize i18n with the given or auto-detected language."""
    global _current_lang, _strings

    if lang is None:
        lang = os.environ.get("CTM_LANG", "").strip().lower()

    if not lang:
        try:
            system_locale = locale.getdefaultlocale()[0] or ""
        except Exception:
            system_locale = ""
        if system_locale.startswith("zh"):
            lang = "zh"
        else:
            lang = "en"

    _current_lang = lang
    if lang == "zh":
        _strings = zh.STRINGS
    else:
        _strings = en.STRINGS


def T(key: str) -> str:
    """Get a translated string by key."""
    if not _strings:
        init()
    return _strings.get(key, key)


def get_lang() -> str:
    """Get the current language code."""
    return _current_lang
