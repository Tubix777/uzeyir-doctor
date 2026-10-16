"""Public package payloads, pinned Arch sources and complete release assets."""
import hashlib
import gzip
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packaging"))
import build_arch
import build_deb
import build_source
from collect_release import collect
from payload import source_epoch, stage, version
from publish_release import release_files
from uzeyir_doctor import APP_NAME


class PackageTests(unittest.TestCase):
    def test_shared_source_preserves_compressed_bytes_and_rejects_different_contents(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ):
            os.environ.pop('UZEYIR_SOURCE_ARCHIVE', None)
            root = Path(directory) / 'project'
            root.mkdir()
            (root / 'pyproject.toml').write_text('[project]\nversion = "9.0"\n')
            (root / 'README.md').write_text('Verified public contents')
            with patch.object(build_source, 'ROOT', root):
                canonical = build_source.build(Path(directory) / 'canonical')
                canonical.write_bytes(gzip.compress(gzip.decompress(canonical.read_bytes()), compresslevel=0, mtime=0))
                os.environ['UZEYIR_SOURCE_ARCHIVE'] = str(canonical)
                result = build_source.build(Path(directory) / 'distribution')
                self.assertEqual(result.read_bytes(), canonical.read_bytes())
                (root / 'README.md').write_text('Unverified change')
                with self.assertRaises(ValueError):
                    build_source.build(Path(directory) / 'rejected')

    def test_payload_includes_brand_fonts_licenses_and_no_privileged_installer(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            stage(target)
            self.assertTrue((target / "usr/share/uzeyir-doctor/src/uzeyir_doctor/resources/Manrope.ttf").is_file())
            self.assertTrue((target / "usr/share/licenses/uzeyir-doctor/Manrope-OFL.txt").is_file())
            desktop = (target / "usr/share/applications/io.github.Tubix777.UzeyirDoctor.desktop").read_text()
            self.assertIn("Name=" + APP_NAME, desktop)
            self.assertIn("Exec=uzeyir-doctor", desktop)
            self.assertEqual(APP_NAME, "Uzeyir Doctor")
            self.assertEqual((target / 'usr/share/uzeyir-doctor/src/uzeyir_doctor/__init__.py').stat().st_mtime, source_epoch())
            for name in ("uzeyir-doctor",):
                launcher = target / "usr/bin" / name
                self.assertEqual(launcher.stat().st_mode & 0o777, 0o755)
                self.assertIn('/usr/share/uzeyir-doctor/src', launcher.read_text())
            files = [str(p.relative_to(target)) for p in target.rglob("*") if p.is_file()]
            self.assertFalse(any("__pycache__" in p or p.startswith(("etc/", "usr/libexec/", "usr/lib/udev/")) for p in files))

    def test_arch_bundle_pins_the_included_source_and_can_build_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = build_arch.build(directory, recipe_only=True)
            with tarfile.open(bundle) as archive:
                files = {Path(n).name: archive.extractfile(n).read() for n in archive.getnames()}
            source = files[f"uzeyir-doctor-{version()}.tar.gz"]
            recipe = files["PKGBUILD"].decode()
            self.assertIn(hashlib.sha256(source).hexdigest(), recipe)
            self.assertNotIn("SKIP", recipe)
            self.assertNotIn("@VERSION@", recipe)
            self.assertIn("pkgname=uzeyir-doctor", recipe)
            self.assertNotIn("conflicts=", recipe)
            self.assertIn("packaging/stage_payload.py", recipe)
            self.assertFalse(any(name.endswith(('.pyc', '.rpm', '.deb', '.pkg.tar.zst')) for name in files))

    @unittest.skipUnless(shutil.which("dpkg-deb"), "dpkg-deb is validated in DEB jobs")
    def test_real_deb_ownership_dependencies_payload_and_checksum_list(self):
        with tempfile.TemporaryDirectory() as directory:
            package = build_deb.build(directory)
            self.assertEqual(subprocess.check_output(["dpkg-deb", "-f", str(package), "Architecture"], text=True).strip(), "all")
            depends = subprocess.check_output(["dpkg-deb", "-f", str(package), "Depends"], text=True)
            for dependency in ("python3 (>= 3.11)", "gir1.2-adw-1 (>= 1.5)", "gir1.2-gtk-4.0 (>= 4.12)", "python3-gi-cairo"):
                self.assertIn(dependency, depends)
            listing = subprocess.check_output(["dpkg-deb", "-c", str(package)], text=True)
            self.assertIn("root/root", listing)
            self.assertNotIn("__pycache__", listing)
            extracted = Path(directory) / "extracted"
            subprocess.run(["dpkg-deb", "-R", str(package), str(extracted)], check=True)
            controls = {p.name for p in (extracted / "DEBIAN").iterdir()}
            self.assertEqual(controls, {"control", "md5sums"})
            for line in (extracted / "DEBIAN/md5sums").read_text().splitlines():
                digest, name = line.split(maxsplit=1)
                self.assertEqual(hashlib.md5((extracted / name).read_bytes(), usedforsecurity=False).hexdigest(), digest)

    def test_release_requires_each_distribution_and_rejects_mismatched_sources(self):
        v = version()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                release_files(root, v)
            names = {"fedora": [f"uzeyir-doctor-{v}.tar.gz", f"uzeyir-doctor-{v}-1.fc44.noarch.rpm", f"uzeyir-doctor-{v}-1.fc44.src.rpm"],
                     "ubuntu24": [f"uzeyir-doctor_{v}-1_all.deb"],
                     "arch": [f"uzeyir-doctor-{v}.tar.gz", f"uzeyir-doctor-{v}-1-any.pkg.tar.zst", f"uzeyir-doctor-{v}-arch-build.tar.gz"]}
            for platform, files in names.items():
                folder = root / ("uzeyir-doctor-" + platform)
                folder.mkdir()
                for name in files:
                    (folder / name).write_bytes(b"verified fixture")
            dest = root / "release"
            self.assertEqual(len(collect(root, dest)), 7)
            self.assertEqual(len((dest / "SHA256SUMS").read_text().splitlines()), 6)
            (root / "uzeyir-doctor-arch" / f"uzeyir-doctor-{v}.tar.gz").write_bytes(b"different source")
            with self.assertRaises(ValueError):
                collect(root, dest)

    def test_standalone_identity_and_settings_do_not_overlap_control_center(self):
        project = (ROOT / "pyproject.toml").read_text()
        self.assertIn('name = "uzeyir-doctor"', project)
        self.assertIn('uzeyir-doctor = "uzeyir_doctor.app:main"', project)
        self.assertIn('uzeyir-doctor/preferences.json', (ROOT / 'src/uzeyir_doctor/settings.py').read_text())
        desktop = (ROOT / "share/io.github.Tubix777.UzeyirDoctor.desktop").read_text()
        self.assertIn("Exec=uzeyir-doctor", desktop)
        self.assertNotIn("io.github.Tubix777.LinuxControl", desktop)
        self.assertNotIn("linux-control", project)
        self.assertEqual(set(__import__("uzeyir_doctor.downloads", fromlist=["REPOSITORIES"]).REPOSITORIES), {"doctor"})
