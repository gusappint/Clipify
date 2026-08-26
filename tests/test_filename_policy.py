from __future__ import annotations

from pathlib import Path

from yt_dlp import YoutubeDL

from ytclip.worker import safe_title_budget


def test_yt_dlp_generates_a_safe_unicode_filename(tmp_path: Path) -> None:
    budget = safe_title_budget(tmp_path, windows=True)
    template = str(tmp_path / f"%(title).{budget}B [%(id)s].%(ext)s")
    unsafe_title = 'CON / demo: *question? "quote" <tag> | pipe ' + "я" * 300
    with YoutubeDL(
        {
            "quiet": True,
            "outtmpl": template,
            "windowsfilenames": True,
            "trim_file_name": 210,
        }
    ) as ydl:
        filename = Path(
            ydl.prepare_filename(
                {
                    "id": "abc123xyz00",
                    "title": unsafe_title,
                    "ext": "webm",
                    "extractor": "youtube",
                    "webpage_url": "https://www.youtube.com/watch?v=abc123xyz00",
                }
            )
        )

    assert filename.suffix == ".webm"
    assert "[abc123xyz00]" in filename.name
    assert "я" in filename.name
    assert not any(character in filename.name for character in '<>:"/\\|?*')
    assert len(filename.name.encode("utf-8")) < 220
