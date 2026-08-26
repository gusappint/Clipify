from __future__ import annotations

from ytclip.worker import finalize_unique_result


def test_temporary_marker_is_removed(tmp_path) -> None:
    temporary = tmp_path / "Видео [abc].__clipify_job123.webm"
    temporary.write_bytes(b"new")

    result = finalize_unique_result(temporary, "job123")

    assert result.name == "Видео [abc].webm"
    assert result.read_bytes() == b"new"
    assert not temporary.exists()


def test_existing_download_is_preserved_and_numbered(tmp_path) -> None:
    existing = tmp_path / "Видео [abc].webm"
    second = tmp_path / "Видео [abc] (2).webm"
    existing.write_bytes(b"first")
    second.write_bytes(b"second")
    temporary = tmp_path / "Видео [abc].__clipify_job123.webm"
    temporary.write_bytes(b"third")

    result = finalize_unique_result(temporary, "job123")

    assert existing.read_bytes() == b"first"
    assert second.read_bytes() == b"second"
    assert result.name == "Видео [abc] (3).webm"
    assert result.read_bytes() == b"third"
