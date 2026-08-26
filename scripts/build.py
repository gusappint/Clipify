from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print(" ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def artifact_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower().replace("amd64", "x86_64")
    return f"Clipify-{system}-{machine}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a native portable Clipify artifact")
    parser.add_argument("--fetch-deno", action="store_true", help="download Deno before building")
    parser.add_argument("--no-zip", action="store_true", help="leave only the executable/app bundle")
    args = parser.parse_args()

    if args.fetch_deno:
        run([sys.executable, str(ROOT / "scripts" / "fetch_deno.py")])
    run([sys.executable, str(ROOT / "scripts" / "fetch_roboto.py")])
    run([sys.executable, str(ROOT / "scripts" / "generate_icon.py")])
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(ROOT / "Clipify.spec")])

    if args.no_zip:
        return

    dist = ROOT / "dist"
    executable = dist / ("Clipify.exe" if platform.system() == "Windows" else "Clipify")
    if platform.system() == "Darwin":
        executable = dist / "Clipify.app"
    if not executable.exists():
        raise FileNotFoundError(f"Build artifact not found: {executable}")

    stage = ROOT / "build" / "portable"
    build_root = (ROOT / "build").resolve()
    resolved_stage = stage.resolve()
    if build_root not in resolved_stage.parents or resolved_stage == build_root:
        raise RuntimeError(f"Refusing to replace an unsafe staging path: {resolved_stage}")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    if executable.is_dir():
        shutil.copytree(executable, stage / executable.name)
    else:
        shutil.copy2(executable, stage / executable.name)
    shutil.copy2(ROOT / "README_PORTABLE.txt", stage / "README.txt")
    shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", stage / "THIRD_PARTY_NOTICES.md")
    licenses = stage / "licenses"
    licenses.mkdir()
    shutil.copy2(ROOT / "assets" / "vendor" / "BOOTSTRAP-ICONS-LICENSE", licenses / "Bootstrap-Icons-MIT.txt")
    shutil.copy2(ROOT / "assets" / "fonts" / "OFL.txt", licenses / "Roboto-OFL.txt")

    archive = dist / f"{artifact_name()}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in stage.rglob("*"):
            if path.is_file():
                package.write(path, path.relative_to(stage))
    print(f"Portable archive: {archive}")


if __name__ == "__main__":
    main()
