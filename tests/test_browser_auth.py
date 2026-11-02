from pathlib import Path

from ytclip.browser_auth import available_browser_ids, load_auth_browser, save_auth_browser
from ytclip.worker import build_options, classify_download_error, parse_args


def test_browser_choice_is_saved_and_loaded(tmp_path: Path) -> None:
    settings = tmp_path / "clipify-settings.json"

    save_auth_browser("chrome", settings)

    assert load_auth_browser(settings) == "chrome"
    assert "chrome" in settings.read_text(encoding="utf-8")


def test_no_sign_in_choice_is_saved(tmp_path: Path) -> None:
    settings = tmp_path / "clipify-settings.json"
    save_auth_browser("edge", settings)

    save_auth_browser(None, settings)

    assert load_auth_browser(settings) is None


def test_platform_browser_lists_do_not_offer_safari_on_windows() -> None:
    assert "safari" not in available_browser_ids(platform="win32", os_name="nt")
    assert "safari" in available_browser_ids(platform="darwin", os_name="posix")


def test_worker_accepts_browser_session() -> None:
    args = parse_args(["--url", "https://youtu.be/example", "--output", ".", "--browser", "firefox"])

    assert args.browser == "firefox"


def test_worker_passes_browser_session_to_downloader(tmp_path: Path, monkeypatch) -> None:
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffmpeg.touch()
    monkeypatch.setattr("ytclip.worker.find_ffmpeg", lambda: ffmpeg)
    monkeypatch.setattr("ytclip.worker.find_deno", lambda: None)
    args = parse_args(
        ["--url", "https://youtu.be/example", "--output", str(tmp_path), "--browser", "edge"]
    )

    options = build_options(args, "testjob")

    assert options["cookiesfrombrowser"] == ("edge", None, None, None)


def test_auth_error_suggests_browser_when_none_is_selected() -> None:
    classified = classify_download_error(
        "Sign in to confirm you’re not a bot. Use --cookies-from-browser for the authentication.",
        None,
    )

    assert classified == ("error.youtube_auth_required", {})


def test_auth_error_names_the_selected_browser() -> None:
    classified = classify_download_error("Sign in to confirm your age", "chrome")

    assert classified == ("error.youtube_session_failed", {"browser": "Chrome"})
