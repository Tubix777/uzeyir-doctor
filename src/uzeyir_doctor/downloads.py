"""Official distribution links; network requests happen only after Refresh."""
from __future__ import annotations

from dataclasses import dataclass
import json
import platform
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from . import APP_NAME, __version__

REPOSITORIES = {
    "doctor": "Tubix777/uzeyir-doctor",
}
APPLICATIONS = {"doctor": APP_NAME}
MAX_RESPONSE = 2_000_000
SAFE_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+\-]{0,159}\Z")


def format_for(release):
    family = {release.get("ID", ""), *release.get("ID_LIKE", "").split()}
    if family & {"debian", "ubuntu", "deepin", "zorin"}:
        return "deb"
    if "arch" in family:
        return "arch"
    if "fedora" in family:
        return "rpm"
    return "source"


def system_format():
    try:
        return format_for(platform.freedesktop_os_release())
    except OSError:
        return "source"


def official_url(url, repository, *, asset=False):
    """Do not turn remote metadata into links outside the selected repository."""
    if repository not in REPOSITORIES.values() or not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
        path = unquote(parsed.path)
        prefix = f"/{repository}/releases/" + ("download/" if asset else "tag/")
        return bool(parsed.scheme == "https" and parsed.netloc == "github.com"
                    and not parsed.query and not parsed.fragment
                    and path.startswith(prefix) and len(path) > len(prefix)
                    and "\\" not in path and not any(part in (".", "..") for part in path.split("/")))
    except ValueError:
        return False


@dataclass(frozen=True)
class Asset:
    name: str
    url: str
    size: int = 0

    @property
    def kind(self):
        if self.name.endswith(".src.rpm"):
            return "source"
        if self.name.endswith(".pkg.tar.zst"):
            return "arch"
        if self.name.endswith(".rpm"):
            return "rpm"
        if self.name.endswith(".deb"):
            return "deb"
        if self.name.endswith(".tar.gz") and re.search(r"-linux-(?:x86_64|aarch64|arm64|i686|amd64)(?:[-.]|$)", self.name):
            return "portable"
        if self.name.endswith((".tar.gz", ".whl", ".zip")):
            return "source"
        return None

    @property
    def install_command(self):
        # This string is displayed/copied, never passed to a shell by the app.
        if not SAFE_FILENAME.fullmatch(self.name):
            return None
        if self.kind == "rpm":
            return f"sudo dnf install ./{self.name}"
        if self.kind == "arch":
            return f"sudo pacman -U ./{self.name}"
        if self.kind == "deb":
            return f"sudo apt install ./{self.name}"
        return None


@dataclass(frozen=True)
class Release:
    repository: str
    tag: str
    url: str
    preview: bool
    assets: tuple[Asset, ...]

    @property
    def formats(self):
        return tuple(kind for kind in ("rpm", "deb", "arch", "portable", "source")
                     if any(asset.kind == kind for asset in self.assets))


class ReleaseError(ValueError):
    pass


def parse_release(data, repository):
    if not isinstance(data, dict) or data.get("draft") is True:
        raise ReleaseError("No public release")
    tag, url = data.get("tag_name"), data.get("html_url")
    if not isinstance(tag, str) or not tag or len(tag) > 100 or not official_url(url, repository):
        raise ReleaseError("Invalid release metadata")
    raw_assets = data.get("assets", [])
    if not isinstance(raw_assets, list):
        raise ReleaseError("Invalid release assets")
    assets = []
    seen = set()
    for item in raw_assets[:60]:
        if not isinstance(item, dict):
            continue
        name, asset_url = item.get("name"), item.get("browser_download_url")
        if not isinstance(name, str) or not SAFE_FILENAME.fullmatch(name) or name in seen:
            continue
        if not official_url(asset_url, repository, asset=True) or not unquote(urlsplit(asset_url).path).endswith("/" + name):
            continue
        size = item.get("size", 0)
        size = size if type(size) is int and size >= 0 else 0
        assets.append(Asset(name, asset_url, size))
        seen.add(name)
    preview = data.get("prerelease") is True or bool(re.search(r"(?:alpha|beta|(?:^|[-.])rc)", tag, re.I))
    return Release(repository, tag, url, preview, tuple(assets))


def bundled_release(module):
    repository = REPOSITORIES[module]
    if module == "doctor":
        tag = "v" + __version__
        names = (f"uzeyir-doctor-{__version__}-1.fc44.noarch.rpm",
                 f"uzeyir-doctor_{__version__}-1_all.deb",
                 f"uzeyir-doctor-{__version__}-1-any.pkg.tar.zst",
                 f"uzeyir-doctor-{__version__}.tar.gz",
                 f"uzeyir-doctor-{__version__}-arch-build.tar.gz",
                 f"uzeyir-doctor-{__version__}-1.fc44.src.rpm")
        return parse_release({"tag_name": tag, "html_url": f"https://github.com/{repository}/releases/tag/{tag}",
                              "prerelease": True, "assets": [
                                  {"name": name, "browser_download_url": f"https://github.com/{repository}/releases/download/{tag}/{name}"}
                                  for name in names]}, repository)
    path = Path(__file__).parent / "resources" / "downloads.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return parse_release(data[module], repository)


def fetch_release(module, opener=urlopen):
    repository = REPOSITORIES[module]
    request = Request(f"https://api.github.com/repos/{repository}/releases?per_page=10",
                      headers={"Accept": "application/vnd.github+json", "User-Agent": f"Uzeyir-Doctor/{__version__}"})
    with opener(request, timeout=8) as response:
        payload = response.read(MAX_RESPONSE + 1)
    if len(payload) > MAX_RESPONSE:
        raise ReleaseError("Release response is too large")
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ReleaseError("Unexpected release response")
    for entry in data[:10]:
        if isinstance(entry, dict) and entry.get("draft") is not True:
            return parse_release(entry, repository)
    raise ReleaseError("No published releases")


def size_text(size):
    if not size:
        return ""
    return f"{size / 1_048_576:.1f} MiB" if size >= 1_048_576 else f"{size / 1024:.0f} KiB"
