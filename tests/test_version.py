from pathlib import Path

from ytclip import __version__


def test_release_version_is_consistent() -> None:
    root = Path(__file__).resolve().parents[1]
    assert __version__ == "1.0.0"
    assert f"Current version: {__version__}" in (root / "README.md").read_text(encoding="utf-8")
    version_resource = (root / "assets" / "version_info.txt").read_text(encoding="utf-8")
    assert f'StringStruct("ProductVersion", "{__version__}")' in version_resource
