"""Unprivileged staging shared by non-RPM packages. No installer side effects."""
from pathlib import Path
import os
import shutil
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def version():
    return tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]


def source_epoch(root=ROOT):
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    return int(os.environ.get('SOURCE_DATE_EPOCH', metadata.get('tool', {}).get('uzeyir-doctor', {}).get('source-date-epoch', 0)))


def stage(destination):
    destination = Path(destination)
    library = destination / "usr/share/uzeyir-doctor/src"
    for source in sorted((ROOT / "src").rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts or source.suffix in (".pyc", ".pyo"):
            continue
        if source.is_symlink():
            raise ValueError("Package payload refuses symlinks")
        target = library / source.relative_to(ROOT / "src")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    pairs = [(ROOT / "packaging/uzeyir-doctor", "usr/bin/uzeyir-doctor"),
             (ROOT / "share/io.github.Tubix777.UzeyirDoctor.desktop", "usr/share/applications/io.github.Tubix777.UzeyirDoctor.desktop"),
             (ROOT / "share/io.github.Tubix777.UzeyirDoctor.svg", "usr/share/icons/hicolor/scalable/apps/io.github.Tubix777.UzeyirDoctor.svg")]
    pairs += [(p, "usr/share/licenses/uzeyir-doctor/" + p.name)
              for p in [ROOT / "COPYING", *sorted((ROOT / "licenses").glob("*.txt"))]]
    pairs += [(ROOT / name, "usr/share/doc/uzeyir-doctor/" + Path(name).name)
              for name in ("README.md", "ATTRIBUTION.md", "docs/install.md", "docs/permissions.md", "docs/validation.md")]
    for source, name in pairs:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o755 if name.startswith("usr/bin/") else 0o644)
    epoch = source_epoch()
    for directory in destination.rglob("*"):
        if directory.is_dir():
            directory.chmod(0o755)
        else:
            os.utime(directory, (epoch, epoch))
