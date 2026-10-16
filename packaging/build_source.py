#!/usr/bin/env python3
"""Build a deterministic source archive with an explicit public-file allowlist."""
import argparse
import gzip
import io
import os
from pathlib import Path
import shutil
import tarfile
import tomllib
from payload import source_epoch

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = ("src", "tests", "share", "packaging", "docs", ".github", "licenses", "COPYING", "README.md", "ATTRIBUTION.md", "PLAN.md", "AGENTS.md", "pyproject.toml", "run.sh", ".gitignore")


def build(destination: Path) -> Path:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f"uzeyir-doctor-{version}.tar.gz"
    epoch = source_epoch(ROOT)
    files = []
    for name in PUBLIC_FILES:
        path = ROOT / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file() and not any(part == "__pycache__" for part in item.parts) and item.suffix not in (".pyc", ".pyo"))
    # A release builds this archive once, then every distribution reuses those
    # exact bytes. zlib and zlib-ng can compress identical tar data differently.
    canonical = os.environ.get("UZEYIR_SOURCE_ARCHIVE")
    if canonical:
        source = Path(canonical)
        expected = {f"uzeyir-doctor-{version}/{p.relative_to(ROOT)}": p for p in files}
        with tarfile.open(source, "r:gz") as tar:
            members = tar.getmembers()
            if len(members) != len(expected) or {m.name for m in members} != set(expected):
                raise ValueError("Canonical source archive does not match the public file list")
            for member in members:
                path = expected[member.name]
                mode = 0o755 if os.access(path, os.X_OK) else 0o644
                if (not member.isfile() or path.is_symlink() or member.mode != mode
                        or member.mtime != epoch or member.uid != 0 or member.gid != 0
                        or tar.extractfile(member).read() != path.read_bytes()):
                    raise ValueError("Canonical source archive differs: " + member.name)
        if source.resolve() != archive.resolve():
            shutil.copyfile(source, archive)
        return archive
    with archive.open("wb") as output, gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=epoch) as compressed, tarfile.open(fileobj=compressed, mode="w") as tar:
        for path in sorted(files):
            if path.is_symlink():
                raise ValueError(f"Source archive refuses symlinks: {path.relative_to(ROOT)}")
            info = tar.gettarinfo(str(path), arcname=f"uzeyir-doctor-{version}/{path.relative_to(ROOT)}")
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = epoch
            info.mode = 0o755 if os.access(path, os.X_OK) else 0o644
            tar.addfile(info, io.BytesIO(path.read_bytes()))
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    print(build(args.output))
