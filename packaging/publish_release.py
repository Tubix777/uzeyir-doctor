#!/usr/bin/env python3
"""Publish verified tag assets with GitHub CLI; retries preserve existing assets."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tomllib


def release_files(directory, version):
    """A release is incomplete if any distribution artifact is missing."""
    names = (f"uzeyir-doctor-{version}-1.fc44.noarch.rpm",
             f"uzeyir-doctor-{version}-1.fc44.src.rpm",
             f"uzeyir-doctor_{version}-1_all.deb",
             f"uzeyir-doctor-{version}-1-any.pkg.tar.zst",
             f"uzeyir-doctor-{version}.tar.gz",
             f"uzeyir-doctor-{version}-arch-build.tar.gz", "SHA256SUMS")
    files = [Path(directory) / name for name in names]
    if not all(file.is_file() and file.stat().st_size for file in files):
        raise ValueError("Fedora, DEB, Arch, source/build archives and checksums are required")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--assets", type=Path, default=Path("dist"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    if args.tag != "v" + version and not args.tag.startswith("v" + version + "-"):
        raise SystemExit("Release tag does not match the package version")
    repository = os.environ.get("GITHUB_REPOSITORY", "Tubix777/uzeyir-doctor")
    def command(*arguments):
        return ["gh", "release", *arguments, "--repo", repository]
    files = release_files(args.assets, version)
    view = subprocess.run(command("view", args.tag, "--json", "assets,isDraft"), capture_output=True, text=True)
    if view.returncode:
        subprocess.run(command("create", args.tag, "--verify-tag", "--draft", "--prerelease", "--title", f"Uzeyir Doctor {args.tag}", "--notes-file", str(root / "docs/release-notes.md")), check=True)
        existing = set()
        is_draft = True
    else:
        data = json.loads(view.stdout)
        existing = {asset["name"] for asset in data["assets"]}
        is_draft = data["isDraft"]
    for file in files:
        if file.name not in existing:
            subprocess.run(command("upload", args.tag, str(file)), check=True)
    if is_draft:
        subprocess.run(command("edit", args.tag, "--draft=false"), check=True)


if __name__ == "__main__":
    main()
