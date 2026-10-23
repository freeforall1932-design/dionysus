#!/usr/bin/env python3
"""Create deterministic, verified ZIP archive of the root skills/ folder."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
NAMES = ("skills",)
EXCLUDE = {"__pycache__", ".pytest_cache", ".git"}
MANIFEST = "DROPIN_MANIFEST.sha256"


def payload(folder: Path) -> dict[str, bytes]:
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError(f"Expected real directory: {folder}")
    files = {}
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder)
        if any(part in EXCLUDE for part in rel.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink in portable payload: {path}")
        if path.is_file():
            if path.name == MANIFEST:
                raise ValueError(f"Reserved generated manifest name: {path}")
            files[rel.as_posix()] = path.read_bytes()
    if not files:
        raise ValueError(f"Empty drop-in: {folder}")
    return files


def manifest(files: dict[str, bytes]) -> bytes:
    return "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                   for name, data in sorted(files.items())).encode()


def build(source: Path, output: Path) -> list[Path]:
    # Check all inputs before creating output. Never write archives into sources.
    source = source.resolve()
    output = output.resolve()
    for name in NAMES:
        if output == source / name or source / name in output.parents:
            raise ValueError("Output directory must not be inside a drop-in")
    inputs = {name: payload(source / name) for name in NAMES}
    output.mkdir(parents=True, exist_ok=True)
    archives = []
    for name, files in inputs.items():
        archive = output / f"{name}.zip"
        entries = dict(files)
        entries[MANIFEST] = manifest(files)
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for rel, data in sorted(entries.items()):
                info = zipfile.ZipInfo(f"{name}/{rel}", date_time=(2026, 10, 18, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, data)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            with zipfile.ZipFile(archive) as zf:
                if zf.testzip() is not None:
                    raise ValueError(f"Corrupt archive: {archive}")
                zf.extractall(dest)  # entries are generated exclusively from local relative paths
            extracted = {p.relative_to(dest / name).as_posix(): p.read_bytes()
                         for p in (dest / name).rglob("*") if p.is_file()}
            if extracted != entries:
                raise ValueError(f"Extracted bytes differ: {archive}")
            if name == "skills":
                subprocess.run([sys.executable, str(dest / name / "validate_skills.py"),
                                "--root", str(dest), "--layout", "portable", "--quiet"],
                               cwd=dest, check=True)
        archives.append(archive)
        print(f"Verified {archive.name}: {len(files)} files; sha256={hashlib.sha256(archive.read_bytes()).hexdigest()}")
    return archives


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "dropins")
    args = ap.parse_args()
    build(ROOT, args.out)


if __name__ == "__main__":
    main()
