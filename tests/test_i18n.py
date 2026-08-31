from __future__ import annotations

from ytclip.i18n import DEFAULT_LOCALE, TEXT, translate
from ytclip.timecode import TimecodeError, parse_timecode


def test_english_is_the_default_locale() -> None:
    assert DEFAULT_LOCALE == "en"
    assert translate(DEFAULT_LOCALE, "action.download") == "Download video"


def test_locales_have_matching_keys() -> None:
    assert set(TEXT["en"]) == set(TEXT["ru"])


def test_russian_copy_is_available() -> None:
    assert translate("ru", "action.download_another") == "Скачать ещё видео"


def test_timecode_errors_are_localizable() -> None:
    try:
        parse_timecode("not-a-time")
    except TimecodeError as exc:
        assert exc.message_key == "error.time_numbers"
        assert translate("en", exc.message_key) == "Time can contain only numbers and colons."
        assert translate("ru", exc.message_key) == "Время может содержать только числа и двоеточия."
    else:
        raise AssertionError("Expected TimecodeError")
