from __future__ import annotations

from ytclip.ui import toast_duration_ms


def test_toast_duration_grows_with_reading_length() -> None:
    short = toast_duration_ms("Видео готово")
    long = toast_duration_ms("Подробное сообщение об ошибке с дополнительными сведениями для пользователя")

    assert 2800 <= short < long <= 15000
