from pathlib import Path

import pytest
from yt_dlp import YoutubeDL

from ytclip.browser_auth import BrowserAuthError, has_authenticated_youtube_session, save_youtube_cookies
from ytclip.worker import build_options, classify_download_error, parse_args


def _youtube_cookie(name: str, value: str = "secret") -> dict[str, object]:
    return {
        "domain": ".youtube.com",
        "path": "/",
        "secure": True,
        "httpOnly": True,
        "expires": 2_000_000_000,
        "name": name,
        "value": value,
    }


def test_authenticated_session_requires_youtube_login_cookie() -> None:
    assert has_authenticated_youtube_session([_youtube_cookie("SAPISID")])
    assert not has_authenticated_youtube_session([_youtube_cookie("PREF")])
    assert not has_authenticated_youtube_session([{**_youtube_cookie("SAPISID"), "domain": ".example.com"}])


def test_saves_only_youtube_cookies_in_netscape_format(tmp_path: Path) -> None:
    target = tmp_path / "cookies.txt"
    cookies = [
        _youtube_cookie("SAPISID"),
        _youtube_cookie("PREF", "language=ru"),
        {**_youtube_cookie("SID"), "domain": ".google.com"},
    ]

    save_youtube_cookies(cookies, target)

    text = target.read_text(encoding="utf-8")
    assert text.startswith("# Netscape HTTP Cookie File")
    assert "#HttpOnly_.youtube.com\tTRUE\t/\tTRUE\t2000000000\tSAPISID\tsecret" in text
    assert "language=ru" in text
    assert ".google.com" not in text

    with YoutubeDL({"cookiefile": str(target), "quiet": True}) as downloader:
        header = downloader.cookiejar.get_cookie_header("https://www.youtube.com/watch?v=example")
    assert header is not None and "SAPISID=secret" in header


def test_refuses_to_save_anonymous_session(tmp_path: Path) -> None:
    with pytest.raises(BrowserAuthError) as error:
        save_youtube_cookies([_youtube_cookie("PREF")], tmp_path / "cookies.txt")

    assert error.value.message_key == "error.auth_not_signed_in"


def test_worker_accepts_saved_cookie_file(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    args = parse_args(
        ["--url", "https://youtu.be/example", "--output", ".", "--cookies-file", str(cookie_file)]
    )

    assert args.cookies_file == str(cookie_file)


def test_worker_passes_cookie_file_to_downloader(tmp_path: Path, monkeypatch) -> None:
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffmpeg.touch()
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.touch()
    monkeypatch.setattr("ytclip.worker.find_ffmpeg", lambda: ffmpeg)
    monkeypatch.setattr("ytclip.worker.find_deno", lambda: None)
    args = parse_args(
        [
            "--url",
            "https://youtu.be/example",
            "--output",
            str(tmp_path),
            "--cookies-file",
            str(cookie_file),
        ]
    )

    options = build_options(args, "testjob")

    assert options["cookiefile"] == str(cookie_file.resolve())
    assert "cookiesfrombrowser" not in options


def test_auth_error_requests_sign_in_without_saved_session() -> None:
    classified = classify_download_error(
        "Sign in to confirm you’re not a bot. Use --cookies-from-browser for the authentication.",
        False,
    )

    assert classified == ("error.youtube_auth_required", {})


def test_auth_error_marks_saved_session_as_expired() -> None:
    classified = classify_download_error("Sign in to confirm your age", True)

    assert classified == ("error.youtube_session_expired", {})
