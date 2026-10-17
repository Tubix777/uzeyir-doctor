"""Verified GitHub release packages; all network and file work runs in workers."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from urllib.error import URLError

from . import __version__, PACKAGE_NAME, UPDATE_REPOSITORY

MAX_METADATA = 2_000_000
MAX_PACKAGE = 50_000_000
MAX_CHECKSUMS = 100_000
VERSION = re.compile(r"v?(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})\Z")
DIGEST = re.compile(r"sha256:([0-9a-f]{64})\Z")


class UpdateError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class DownloadCancelled(UpdateError):
    def __init__(self):
        super().__init__("cancelled")


def version_key(value):
    match = VERSION.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise UpdateError("metadata")
    return tuple(int(part) for part in match.groups())


@dataclass(frozen=True)
class UpdateAsset:
    name: str
    url: str
    size: int
    sha256: str


@dataclass(frozen=True)
class UpdateOffer:
    version: str
    url: str
    notes: str
    package: UpdateAsset
    checksums: UpdateAsset
    package_format: str


@dataclass(frozen=True)
class VerifiedPackage:
    path: Path
    offer: UpdateOffer


def _asset(data, limit):
    if not isinstance(data, dict):
        raise UpdateError("metadata")
    name, url, size = data.get("name"), data.get("browser_download_url"), data.get("size")
    digest = DIGEST.fullmatch(data.get("digest", "")) if isinstance(data.get("digest"), str) else None
    parsed = urlsplit(url) if isinstance(url, str) else None
    if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,159}", name)
            or parsed is None or parsed.scheme != "https" or parsed.netloc != "github.com"
            or parsed.query or parsed.fragment
            or not url.endswith("/" + name) or type(size) is not int or not 0 < size <= limit or not digest):
        raise UpdateError("metadata")
    return UpdateAsset(name, url, size, digest.group(1))


def parse_updates(data, package_format, current=__version__):
    if package_format not in ("rpm", "deb", "arch"):
        raise UpdateError("unsupported")
    current_key = version_key(current)
    if not isinstance(data, list):
        raise UpdateError("metadata")
    candidates = []
    for release in data[:20]:
        if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
            continue
        try:
            key = version_key(release.get("tag_name"))
        except UpdateError:
            continue
        if key > current_key:
            candidates.append((key, release))
    if not candidates:
        return None
    key, release = max(candidates, key=lambda item: item[0])
    version = ".".join(str(value) for value in key)
    tag = release["tag_name"]
    url = f"https://github.com/{UPDATE_REPOSITORY}/releases/tag/{tag}"
    if release.get("html_url") != url:
        raise UpdateError("metadata")
    stem = re.escape(PACKAGE_NAME)
    v = re.escape(version)
    pattern = {"rpm": rf"{stem}-{v}-\d+\.fc\d+\.noarch\.rpm", "deb": rf"{stem}_{v}-\d+_all\.deb",
               "arch": rf"{stem}-{v}-\d+-any\.pkg\.tar\.zst"}[package_format]
    assets = release.get("assets")
    if not isinstance(assets, list) or len(assets) > 60:
        raise UpdateError("metadata")
    selected = [item for item in assets if isinstance(item, dict) and re.fullmatch(pattern, str(item.get("name", "")))]
    sums = [item for item in assets if isinstance(item, dict) and item.get("name") == "SHA256SUMS"]
    if len(selected) != 1 or len(sums) != 1:
        raise UpdateError("no_package")
    package, checksums = _asset(selected[0], MAX_PACKAGE), _asset(sums[0], MAX_CHECKSUMS)
    prefix = f"https://github.com/{UPDATE_REPOSITORY}/releases/download/{tag}/"
    if package.url != prefix + package.name or checksums.url != prefix + "SHA256SUMS":
        raise UpdateError("metadata")
    notes = release.get("body", "")
    return UpdateOffer(version, url, notes[:12_000] if isinstance(notes, str) else "", package, checksums, package_format)


def _request(url):
    return Request(url, headers={"Accept": "application/vnd.github+json" if "api.github.com" in url else "application/octet-stream",
                                 "User-Agent": f"{PACKAGE_NAME}/{__version__}"})


def check_for_update(package_format, current=__version__, opener=urlopen):
    if package_format not in ("deb", "rpm", "arch"):
        raise UpdateError("unsupported")
    try:
        with opener(_request(f"https://api.github.com/repos/{UPDATE_REPOSITORY}/releases?per_page=20"), timeout=12) as response:
            payload = response.read(MAX_METADATA + 1)
        if len(payload) > MAX_METADATA:
            raise UpdateError("metadata")
        return parse_updates(json.loads(payload), package_format, current)
    except UpdateError:
        raise
    except (OSError, ValueError, TypeError):
        raise UpdateError("network") from None


def _cancelled(cancel):
    if cancel.is_set():
        raise DownloadCancelled()


def checksum_for(payload, filename):
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeError:
        raise UpdateError("checksum") from None
    found = []
    for line in lines:
        match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *](.+)", line)
        if not match:
            raise UpdateError("checksum")
        if match.group(2) == filename:
            found.append(match.group(1).lower())
    if len(found) != 1:
        raise UpdateError("checksum")
    return found[0]


def download_update(offer, cancel=None, progress=lambda done, total: None, cache=None, opener=urlopen):
    cancel = cancel or threading.Event()
    directory = None
    try:
        _cancelled(cancel)
        with opener(_request(offer.checksums.url), timeout=15) as response:
            sums = response.read(MAX_CHECKSUMS + 1)
        if len(sums) != offer.checksums.size or hashlib.sha256(sums).hexdigest() != offer.checksums.sha256:
            raise UpdateError("checksum")
        expected = checksum_for(sums, offer.package.name)
        if expected != offer.package.sha256:
            raise UpdateError("checksum")
        _cancelled(cancel)
        root = Path(cache) if cache else Path(os.environ.get("XDG_CACHE_HOME", Path.home()/".cache"))/PACKAGE_NAME/"updates"
        if root.is_symlink():
            raise UpdateError("storage")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory = Path(tempfile.mkdtemp(prefix="verified-", dir=root))
        path = directory / offer.package.name
        digest, received = hashlib.sha256(), 0
        with opener(_request(offer.package.url), timeout=15) as response, path.open("xb") as target:
            path.chmod(0o600)
            progress(0, offer.package.size)
            while True:
                _cancelled(cancel)
                block = response.read(64 * 1024)
                if not block:
                    break
                received += len(block)
                if received > offer.package.size or received > MAX_PACKAGE:
                    raise UpdateError("checksum")
                target.write(block)
                digest.update(block)
                progress(received, offer.package.size)
        _cancelled(cancel)
        if received != offer.package.size or digest.hexdigest() != expected:
            raise UpdateError("checksum")
        return VerifiedPackage(path, offer)
    except Exception as error:
        if directory is not None:
            shutil.rmtree(directory, ignore_errors=True)
        if isinstance(error, UpdateError):
            raise
        raise UpdateError("network" if isinstance(error, (URLError, TimeoutError, ConnectionError)) else "storage") from None


def verify_download(package):
    path, asset = package.path, package.offer.package
    if path.is_symlink() or not path.is_file() or path.stat().st_size != asset.size:
        raise UpdateError("checksum")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(64 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != asset.sha256:
        raise UpdateError("checksum")
    return path


def installed_version(package_format, runner=subprocess.run):
    commands = {"rpm": ["rpm", "-q", "--qf", "%{VERSION}", PACKAGE_NAME],
                "deb": ["dpkg-query", "-W", "-f=${Version}", PACKAGE_NAME],
                "arch": ["pacman", "-Q", PACKAGE_NAME]}
    if package_format not in commands:
        return None
    try:
        result = runner(commands[package_format], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                        text=True, timeout=10, check=False)
        if result.returncode:
            return None
        value = result.stdout.strip().split()[-1].split(":")[-1].split("-")[0]
        version_key(value)
        return value
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return None


def promote_native_launcher(module_file=None, data_home=None, native_prefix="/usr/bin"):
    """Migrate only this app's marked versioned user launcher after a native update.

    Custom launchers and repository checkouts are left intact. The old version's
    files and a backup desktop entry remain available.
    """
    import shlex
    from . import APPLICATION_ID
    data = Path(data_home) if data_home else Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))
    base = data / PACKAGE_NAME
    versions = base / "versions"
    module = Path(module_file or __file__).resolve()
    try:
        relative = module.relative_to(versions.resolve())
        if len(relative.parts) < 3 or base.is_symlink() or base.stat().st_uid != os.getuid():
            return False
        old_root = versions / relative.parts[0]
        desktop = data / "applications" / (APPLICATION_ID + ".desktop")
        native = Path(native_prefix) / PACKAGE_NAME
        if (desktop.is_symlink() or desktop.stat().st_uid != os.getuid()
                or not native.is_file() or not os.access(native, os.X_OK)):
            return False
        original = desktop.read_text(encoding="utf-8")
        markers = ("X-Linux-Control-UserInstall=true", "X-Uzeyir-Doctor-UserInstall=true")
        if not any(marker in original.splitlines() for marker in markers):
            return False
        lines = original.splitlines()
        commands = [line[5:] for line in lines if line.startswith("Exec=")]
        if len(commands) != 1:
            return False
        argv = shlex.split(commands[0])
        if len(argv) != 1 or not Path(argv[0]).resolve().is_relative_to(old_root.resolve()):
            return False
        updated = "\n".join("Exec=" + str(native) if line.startswith("Exec=") else
                             line.replace("UserInstall=true", "UserInstall=false") for line in lines) + "\n"
        backup = base / "previous-launcher.desktop"
        if not backup.exists():
            with backup.open("x", encoding="utf-8") as stream:
                stream.write(original)
        descriptor, temporary = tempfile.mkstemp(prefix=".update-launcher-", dir=desktop.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(updated)
            os.chmod(temporary, 0o644)
            os.replace(temporary, desktop)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return True
    except (OSError, ValueError, IndexError):
        return False
