from __future__ import annotations

import math

from .i18n import DEFAULT_LOCALE, translate


class TimecodeError(ValueError):
    """Raised when a user-facing timecode cannot be parsed."""

    def __init__(self, message_key: str) -> None:
        self.message_key = message_key
        super().__init__(message_key)


def parse_timecode(value: str | None) -> float | None:
    """Parse SS, MM:SS, or HH:MM:SS into seconds.

    A comma is accepted as a decimal separator for a plain-seconds value or
    for the seconds component. Empty input means that the boundary is unset.
    """

    if value is None:
        return None

    text = value.strip().replace(",", ".")
    if not text:
        return None

    parts = text.split(":")
    if not 1 <= len(parts) <= 3 or any(not part.strip() for part in parts):
        raise TimecodeError("error.time_format")

    try:
        if len(parts) == 1:
            seconds = float(parts[0])
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError
            return seconds

        whole = [int(part) for part in parts[:-1]]
        seconds_part = float(parts[-1])
    except ValueError as exc:
        raise TimecodeError("error.time_numbers") from exc

    if any(component < 0 for component in whole):
        raise TimecodeError("error.time_negative")
    if not math.isfinite(seconds_part) or not 0 <= seconds_part < 60:
        raise TimecodeError("error.seconds_range")

    if len(parts) == 2:
        minutes = whole[0]
        return minutes * 60 + seconds_part

    hours, minutes = whole
    if minutes >= 60:
        raise TimecodeError("error.minutes_range")
    return hours * 3600 + minutes * 60 + seconds_part


def validate_time_range(start: float | None, end: float | None) -> None:
    if start is not None and end is not None and end <= start:
        raise TimecodeError("error.range_order")


def format_timecode(seconds: float | None) -> str:
    if seconds is None:
        return ""

    rounded = round(seconds, 3)
    hours = int(rounded // 3600)
    minutes = int((rounded % 3600) // 60)
    secs = rounded % 60
    seconds_text = f"{secs:06.3f}".rstrip("0").rstrip(".")
    if secs < 10:
        seconds_text = f"0{seconds_text}" if not seconds_text.startswith("0") else seconds_text

    if hours:
        return f"{hours}:{minutes:02d}:{seconds_text}"
    return f"{minutes}:{seconds_text}"


def describe_range(start: float | None, end: float | None, locale: str = DEFAULT_LOCALE) -> str:
    if start is None and end is None:
        return translate(locale, "range.full")
    if start is None:
        return translate(locale, "range.until", end=format_timecode(end))
    if end is None:
        return translate(locale, "range.from", start=format_timecode(start))
    return translate(locale, "range.between", start=format_timecode(start), end=format_timecode(end))
