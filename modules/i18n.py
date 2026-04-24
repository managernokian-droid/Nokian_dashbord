"""
Internationalization (i18n) module for multi-language support.
Manages translations from JSON files in locales/ folder.
"""

import json
from pathlib import Path
from typing import Any, Optional
import streamlit as st

LOCALES_DIR = Path("locales")
SUPPORTED_LANGUAGES = {
    "Русский": "ru",
    "English": "en",
    "Українська": "uk",
}

# Cache translations in memory
_translations_cache = {}


def _load_translation(lang_code: str) -> dict:
    """Load translation file for given language code."""
    if lang_code in _translations_cache:
        return _translations_cache[lang_code]

    file_path = LOCALES_DIR / f"{lang_code}.json"
    if not file_path.exists():
        st.error(f"Translation file not found: {file_path}")
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        translations = json.load(f)
        _translations_cache[lang_code] = translations
        return translations


def get_language() -> str:
    """Get current language code from session state."""
    if "language" not in st.session_state:
        st.session_state["language"] = "ru"  # Default language
    return st.session_state["language"]


def set_language(lang_code: str) -> None:
    """Set current language code in session state."""
    if lang_code in SUPPORTED_LANGUAGES.values():
        st.session_state["language"] = lang_code


def t(key: str, default: str = "") -> str:
    """
    Translate a key using dot notation.

    Usage:
        t("tabs.position")  # Returns "📍 Позиция модели" (in Russian)
        t("tabs.position", "Unknown")  # With fallback
    """
    lang_code = get_language()
    translations = _load_translation(lang_code)

    keys = key.split(".")
    value = translations

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default if default else f"[{key}]"

    return str(value) if value is not None else (default if default else f"[{key}]")


def t_format(key: str, **kwargs) -> str:
    """
    Translate a key and format with variables.

    Usage:
        t_format("tab2.caption", count=40, comps=5)
    """
    text = t(key)
    return text.format(**kwargs)


def render_language_selector() -> None:
    """Render language selector widget in sidebar."""
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center;'>
            <div style='color: white; font-weight: bold; font-size: 14px; margin-bottom: 8px;'>
                🌍 Выберите язык
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_lang_name = None
    for name, code in SUPPORTED_LANGUAGES.items():
        if code == get_language():
            current_lang_name = name
            break

    selected_lang_name = st.selectbox(
        label="",  # Скрываем лейбл (он уже в HTML выше)
        options=list(SUPPORTED_LANGUAGES.keys()),
        index=list(SUPPORTED_LANGUAGES.keys()).index(current_lang_name) if current_lang_name else 0,
        key="lang_selector",
        label_visibility="collapsed",
    )

    selected_lang_code = SUPPORTED_LANGUAGES[selected_lang_name]

    if selected_lang_code != get_language():
        set_language(selected_lang_code)
        st.rerun()
