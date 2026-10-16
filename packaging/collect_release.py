"""Collect only verified distro artifacts; require identical source archives."""
import argparse
import hashlib
from pathlib import Path
import shutil
from payload import version
from publish_release import release_files


def collect(artifacts, destination):
    artifacts, destination = Path(artifacts), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    v = version()
    source_name = f"uzeyir-doctor-{v}.tar.gz"
    fedora = artifacts / "uzeyir-doctor-fedora"
    arch = artifacts / "uzeyir-doctor-arch"
    if (fedora / source_name).read_bytes() != (arch / source_name).read_bytes():
        raise ValueError("Arch and Fedora must use the same source archive")
    choices = ((fedora, (f"uzeyir-doctor-{v}-1.fc44.noarch.rpm", f"uzeyir-doctor-{v}-1.fc44.src.rpm", source_name)),
               (artifacts / "uzeyir-doctor-ubuntu24", (f"uzeyir-doctor_{v}-1_all.deb",)),
               (arch, (f"uzeyir-doctor-{v}-1-any.pkg.tar.zst", f"uzeyir-doctor-{v}-arch-build.tar.gz")))
    sums = []
    for folder, names in choices:
        for name in names:
            source = folder / name
            if not source.is_file() or not source.stat().st_size:
                raise ValueError("Missing release artifact: " + name)
            shutil.copyfile(source, destination / name)
            sums.append(hashlib.sha256(source.read_bytes()).hexdigest() + "  " + name)
    (destination / "SHA256SUMS").write_text("\n".join(sorted(sums)) + "\n")
    return release_files(destination, v)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    for file in collect(args.artifacts, args.output):
        print(file)
