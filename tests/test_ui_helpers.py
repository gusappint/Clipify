from __future__ import annotations

import pytest

from ytclip.ui import fit_end, fit_middle, normalize_youtube_url, youtube_video_id
from ytclip.worker import classify_download_error, job_token_from


class FixedWidthFont:
    """Stands in for a Tk font: every character is 7 px wide."""

    def measure(self, text: str) -> int:
        return len(text) * 7


@pytest.mark.parametrize(
    "value",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://m.youtube.com/shorts/aqz-KE-bpKQ",
        "  https://music.youtube.com/watch?v=dQw4w9WgXcQ  ",
    ],
)
def test_accepts_youtube_links(value: str) -> None:
    assert normalize_youtube_url(value).startswith("https://")


@pytest.mark.parametrize("value", ["vimeo.com/123", "https://notyoutube.com/watch?v=x", "ftp://youtube.com/x", "hello"])
def test_rejects_other_links(value: str) -> None:
    with pytest.raises(ValueError, match="link.error.not_youtube"):
        normalize_youtube_url(value)


@pytest.mark.parametrize(
    ("url", "video_id"),
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42", "dQw4w9WgXcQ"),
        ("https://youtu.be/jNQXAC9IVRw?si=abc", "jNQXAC9IVRw"),
        ("https://www.youtube.com/shorts/aqz-KE-bpKQ", "aqz-KE-bpKQ"),
        ("https://www.youtube.com/live/9bZkp7q19f0", "9bZkp7q19f0"),
        ("https://www.youtube.com/playlist?list=PL123", None),
        ("https://youtu.be/short", None),
    ],
)
def test_reads_video_id_for_thumbnails(url: str, video_id: str | None) -> None:
    assert youtube_video_id(url) == video_id


def test_long_titles_end_with_an_ellipsis() -> None:
    font = FixedWidthFont()
    assert fit_end("Short title", font, 200) == "Short title"
    fitted = fit_end("A very long video title that cannot fit", font, 140)
    assert fitted.endswith("…") and font.measure(fitted) <= 140


def test_long_paths_keep_both_ends() -> None:
    font = FixedWidthFont()
    path = r"C:\Users\someone\Downloads\Clipify-windows-x86_64\clips"
    fitted = fit_middle(path, font, 210)
    assert fitted.startswith("C:\\") and fitted.endswith("clips") and "…" in fitted
    assert font.measure(fitted) <= 210


@pytest.mark.parametrize(
    ("message", "key"),
    [
        ("Sign in to confirm you’re not a bot. This helps protect our community.", "error.youtube_auth_required"),
        ("Private video. Sign in if you've been granted access to this video", "error.video_private"),
        ("Join this channel to get access to members-only content", "error.video_members_only"),
        ("This live event will begin in 3 hours.", "error.video_not_started"),
        ("Video unavailable. This video has been removed by the uploader", "error.video_unavailable"),
        ("Unable to download webpage: <urlopen error [Errno 11001] getaddrinfo failed>", "error.network"),
        ("HTTP Error 429: Too Many Requests", "error.rate_limited"),
        ("unable to write data: [Errno 28] No space left on device", "error.disk_full"),
        ("unable to open for writing: [Errno 13] Permission denied", "error.folder_denied"),
        ("'not a link' is not a valid URL", "error.link_broken"),
    ],
)
def test_common_youtube_failures_get_plain_messages(message: str, key: str) -> None:
    classified = classify_download_error(message, False)
    assert classified == (key, {})


def test_unknown_failures_stay_unclassified() -> None:
    assert classify_download_error("Something odd happened", False) is None


def test_job_token_is_reused_only_when_safe() -> None:
    assert job_token_from("0123456789ab") == "0123456789ab"
    for unsafe in (None, "", "../evil", "ABCDEF123456", "abc"):
        token = job_token_from(unsafe)
        assert token != unsafe and len(token) == 10
