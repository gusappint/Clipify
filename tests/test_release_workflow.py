from pathlib import Path


def test_release_builds_all_supported_architectures() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "build-portable.yml").read_text(encoding="utf-8")

    assert "windows-latest" in workflow
    assert "macos-15\n" in workflow
    assert "macos-15-intel" in workflow
    assert "Expected three release archives" in workflow
