from __future__ import annotations

import pytest

from ytclip.timecode import TimecodeError, describe_range, format_timecode, parse_timecode, validate_time_range
from ytclip.worker import safe_title_budget


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", None),
        ("90", 90),
        ("90.5", 90.5),
        ("90,5", 90.5),
        ("01:30", 90),
        ("90:00", 5400),
        ("1:02:03", 3723),
        ("  2:03  ", 123),
    ],
)
def test_parse_timecode(raw: str, expected: float | None) -> None:
    assert parse_timecode(raw) == expected


@pytest.mark.parametrize("raw", ["-1", "1:60", "1:60:00", "1::2", "abc", "1:2:3:4"])
def test_invalid_timecodes(raw: str) -> None:
    with pytest.raises(TimecodeError):
        parse_timecode(raw)


def test_range_must_move_forward() -> None:
    with pytest.raises(TimecodeError):
        validate_time_range(20, 20)
    with pytest.raises(TimecodeError):
        validate_time_range(20, 10)


def test_format_and_describe() -> None:
    assert format_timecode(3723) == "1:02:03"
    assert describe_range(None, None) == "Full video"
    assert describe_range(90, 120) == "1:30 — 2:00"
    assert describe_range(None, None, "ru") == "Видео целиком"
    assert describe_range(90, None, "ru") == "С 1:30 до конца"


def test_filename_budget_is_portable(tmp_path) -> None:
    assert safe_title_budget(tmp_path, windows=False) == 180
    assert 40 <= safe_title_budget(tmp_path, windows=True) <= 160


def test_excessively_long_windows_output_path_is_rejected(tmp_path) -> None:
    long_path = tmp_path.joinpath(*(["x" * 30] * 8))
    with pytest.raises(ValueError, match="error.output_path_too_long"):
        safe_title_budget(long_path, windows=True)
