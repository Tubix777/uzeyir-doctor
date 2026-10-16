#!/usr/bin/env python3
"""Generate a pinned offline Arch build bundle, optionally build with makepkg."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from build_source import build as build_source
from payload import ROOT, source_epoch, version


def recipe(archive):
    digest = hashlib.sha256(Path(archive).read_bytes()).hexdigest()
    return (ROOT / "packaging/arch/PKGBUILD.in").read_text().replace("@VERSION@", version()).replace("@SHA256@", digest)


def build(destination, *, recipe_only=False):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    archive = build_source(destination)
    scratch = ROOT / "work"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="arch-", dir=scratch) as directory:
        staging = Path(directory)
        shutil.copyfile(archive, staging / archive.name)
        (staging / "PKGBUILD").write_text(recipe(archive))
        (staging / "README.txt").write_text(
            "Arch Linux: extract this directory, review PKGBUILD, then run makepkg -si as a normal user.\n"
            "Install base-devel first with sudo pacman -Syu --needed base-devel.\n"
            "The matching source archive is included and its SHA-256 is pinned.\n"
            "Do not run makepkg as root. This is an upstream recipe, not an AUR package.\n")
        bundle = destination / f"uzeyir-doctor-{version()}-arch-build.tar.gz"
        epoch = source_epoch()
        with bundle.open("wb") as output, gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=epoch) as compressed, tarfile.open(fileobj=compressed, mode="w") as tar:
            for file in sorted(staging.iterdir()):
                info = tar.gettarinfo(str(file), arcname=f"uzeyir-doctor-{version()}-arch-build/{file.name}")
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mode, info.mtime = 0o644, epoch
                tar.addfile(info, io.BytesIO(file.read_bytes()))
        if not recipe_only:
            subprocess.run(["makepkg", "--cleanbuild", "--force", "--noconfirm"], cwd=staging, check=True)
            packages = list(staging.glob(f"uzeyir-doctor-{version()}-1-any.pkg.tar.zst"))
            if len(packages) != 1:
                raise RuntimeError("makepkg did not produce the expected package")
            shutil.copyfile(packages[0], destination / packages[0].name)
        return bundle


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--recipe-only", action="store_true", help="Create the offline build bundle without invoking makepkg")
    args = parser.parse_args()
    print(build(args.output, recipe_only=args.recipe_only))
