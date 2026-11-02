from __future__ import annotations

from ytclip.ui import reading_time_ms


def test_notice_reading_time_grows_with_length() -> None:
    short = reading_time_ms("Видео сохранено")
    long = reading_time_ms("Подробное сообщение об ошибке с дополнительными сведениями для пользователя")

    assert 2800 <= short < long <= 15000
