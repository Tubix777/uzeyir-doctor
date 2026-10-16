#!/usr/bin/env python3
"""Build a Fedora RPM and source RPM without installing them."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_source import ROOT, build
from payload import source_epoch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    destination = args.output.resolve()
    archive = build(destination)
    scratch = ROOT / "work"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rpm-", dir=scratch) as directory:
        top = Path(directory)
        for name in ("SOURCES", "SPECS", "BUILD", "BUILDROOT", "RPMS", "SRPMS"):
            (top / name).mkdir()
        shutil.copy2(archive, top / "SOURCES" / archive.name)
        spec = top / "SPECS" / "uzeyir-doctor.spec"
        shutil.copy2(ROOT / "packaging/uzeyir-doctor.spec", spec)
        subprocess.run(["rpmbuild", "-ba", "--define", f"_topdir {top}", str(spec)],
                       env={**os.environ, "SOURCE_DATE_EPOCH": str(source_epoch())}, check=True)
        packages = sorted(top.glob("RPMS/**/*.rpm")) + sorted(top.glob("SRPMS/*.rpm"))
        if not packages:
            raise RuntimeError("rpmbuild returned no package artifacts")
        for package in packages:
            result = destination / package.name
            shutil.copy2(package, result)
            print(result)


if __name__ == "__main__":
    main()
