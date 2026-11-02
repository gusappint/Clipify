from __future__ import annotations

import re

from ytclip.i18n import DEFAULT_LOCALE, TEXT, format_duration, format_size, format_speed, translate
from ytclip.timecode import TimecodeError, describe_range, parse_timecode


def test_english_is_the_default_locale() -> None:
    assert DEFAULT_LOCALE == "en"
    assert translate(DEFAULT_LOCALE, "action.download_video") == "Download video"


def test_locales_have_matching_keys() -> None:
    assert set(TEXT["en"]) == set(TEXT["ru"])


def test_locales_use_the_same_placeholders() -> None:
    for key, english in TEXT["en"].items():
        assert set(re.findall(r"{(\w+)}", english)) == set(re.findall(r"{(\w+)}", TEXT["ru"][key])), key


def test_russian_copy_is_available() -> None:
    assert translate("ru", "action.download_clip") == "Скачать фрагмент"
    assert translate("ru", "action.show_file") == "Показать в папке"


def test_unknown_locale_falls_back_to_english() -> None:
    assert translate("de", "link.paste") == "Paste"


def test_timecode_errors_are_localizable() -> None:
    try:
        parse_timecode("not-a-time")
    except TimecodeError as exc:
        assert exc.message_key == "error.time_numbers"
        assert translate("en", exc.message_key) == "Use digits and colons only, like 1:05."
        assert translate("ru", exc.message_key) == "Только цифры и двоеточия, например 1:05."
    else:
        raise AssertionError("Expected TimecodeError")


def test_range_descriptions_read_naturally() -> None:
    assert describe_range(None, None, "en") == "Whole video"
    assert describe_range(65, 150, "en") == "Clip 1:05–2:30"
    assert describe_range(None, 150, "ru") == "Фрагмент до 2:30"
    assert describe_range(65, None, "ru") == "Фрагмент с 1:05"


def test_sizes_use_local_units_and_decimal_marks() -> None:
    assert format_size(812, "en") == "812 B"
    assert format_size(48.2 * 1024 * 1024, "en") == "48.2 MB"
    assert format_size(48.2 * 1024 * 1024, "ru") == "48,2 МБ"
    assert format_size(3.4 * 1024**3, "en") == "3.40 GB"
    assert format_size(None, "en") == ""
    assert format_speed(3.1 * 1024 * 1024, "ru") == "3,1 МБ/с"
    assert format_speed(0, "en") == ""


def test_durations_stay_short() -> None:
    assert format_duration(37, "en") == "37 s"
    assert format_duration(85, "en") == "1 min 25 s"
    assert format_duration(120, "ru") == "2 мин"
    assert format_duration(725, "en") == "12 min"
    assert format_duration(3725, "ru") == "1 ч 2 мин"
    assert translate("ru", "progress.eta", time=format_duration(37, "ru")) == "осталось 37 с"
