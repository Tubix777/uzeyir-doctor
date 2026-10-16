"""Diagnostics use fixed read-only commands; no shell or privilege escalation."""
from __future__ import annotations

from dataclasses import dataclass, field
import configparser
import os
from pathlib import Path
import re
import shutil
import subprocess


@dataclass
class Finding:
    title: str
    status: str
    explanation: str
    evidence: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    certainty: str = "Doğrudan gözlem"
    metric: float | None = None
    metric_label: str = ""


@dataclass
class Result:
    code: int
    output: str = ""
    error: str = ""


def run(args: list[str], timeout: int = 8) -> Result:
    """Only internally constructed argument arrays are accepted by callers."""
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=timeout, check=False,
                                env={**os.environ, "LC_ALL": "C", "LANG": "C"})
        return Result(result.returncode, result.stdout[:24000], result.stderr[:4000])
    except FileNotFoundError:
        return Result(127, error="Gerekli araç kurulu değil.")
    except subprocess.TimeoutExpired:
        return Result(124, error="Kontrol zaman aşımına uğradı.")
    except (OSError, UnicodeError):
        return Result(125, error="Kontrol tamamlanamadı.")


def disk_finding(total: int, free: int, label: str) -> Finding:
    if total <= 0:
        return Finding(label, "unknown", "Disk kapasitesi okunamadı.")
    percent = 100 * (total - free) / total
    status = "critical" if percent >= 97 else "warning" if percent >= 90 else "ok"
    return Finding(label, status,
        "Diskteki boş alan çok az; kurulum ve güncellemeler etkilenebilir." if status != "ok"
        else "Bu dosya sisteminde yeterli boş alan görünüyor.",
        [f"Kullanım: %{percent:.1f}", f"Boş alan: {free / (1024 ** 3):.1f} GB"],
        ["Büyük dosyaları dosya yöneticisinden incele.",
         "Gereksiz olduğundan emin olduğun dosyaları kaldır; ardından tekrar tara."] if status != "ok" else [],
        metric=round(percent, 1), metric_label="Disk doluluğu")


def services_finding(result: Result, user: bool) -> Finding:
    title = "Kullanıcı servisleri" if user else "Sistem servisleri"
    if result.code:
        return Finding(title, "unknown", "Servis durumu okunamadı; sağlıklı olduğu varsayılmadı.")
    units = []
    for line in result.output.splitlines():
        unit = line.strip().split(maxsplit=1)[0] if line.strip() else ""
        if unit.endswith(".service"):
            units.append(unit)
    if not units:
        return Finding(title, "ok", "Başarısız durumda servis bulunmadı.")
    return Finding(title, "warning", f"Başarısız durumda {len(units)} servis bulundu. Bu bulgu tek başına uygulama hatasının nedenini kanıtlamaz.",
                   units[:8], ["İlgili servisin durumunu ve hata kaydını incele.",
                               "Servisin görevini anlamadan yeniden başlatma veya devre dışı bırakma."])


def scan() -> list[Finding]:
    findings = []
    try:
        release = {}
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                release[key] = value.strip('"')
        name = release.get("PRETTY_NAME", "Linux")
        findings.append(Finding("İşletim sistemi", "info", name,
                                ["Kontroller yerel bilgisayarda çalışır.", "Yönetici yetkisi istenmez."]))
    except OSError:
        findings.append(Finding("İşletim sistemi", "unknown", "Sistem bilgisi okunamadı."))
    devices = set()
    for path, label in [(Path("/"), "Sistem diski"), (Path.home(), "Kişisel dosyaların diski")]:
        try:
            device = path.stat().st_dev
            if device in devices:
                continue
            devices.add(device)
            usage = shutil.disk_usage(path)
            findings.append(disk_finding(usage.total, usage.free, label))
        except OSError:
            findings.append(Finding(label, "unknown", "Disk bilgisi okunamadı."))
    if shutil.which("systemctl"):
        for user in (False, True):
            args = ["systemctl"] + (["--user"] if user else [])
            args += ["--failed", "--type=service", "--no-legend", "--plain", "--no-pager"]
            findings.append(services_finding(run(args), user))
    else:
        findings.append(Finding("Servisler", "unknown", "Bu sistemde systemctl bulunamadı."))
    if shutil.which("nmcli"):
        state = run(["nmcli", "-t", "-f", "STATE", "general"])
        value = state.output.strip()
        if state.code or not value:
            findings.append(Finding("Ağ bağlantısı", "unknown", "NetworkManager durumu okunamadı."))
        elif value.startswith("connected"):
            findings.append(Finding("Ağ bağlantısı", "ok", "NetworkManager bir ağ bağlantısı bildiriyor. İnternet erişimi ayrıca test edilmedi."))
        else:
            findings.append(Finding("Ağ bağlantısı", "warning", "NetworkManager bağlı bir ağ bildirmiyor.",
                                    steps=["Masaüstünün ağ menüsünde Wi-Fi veya kablo bağlantısını kontrol et."]))
    else:
        findings.append(Finding("Ağ bağlantısı", "unknown", "NetworkManager aracı bulunamadı; ağ testi yapılmadı."))
    findings.extend(repository_findings())
    findings.extend(ssd_health_findings())
    return findings


def ssd_health_findings() -> list[Finding]:
    try:
        from .hardware import read_ssd_health
        return read_ssd_health()
    except Exception:
        # Optional hardware support must not erase the other scan results.
        return [Finding("SSD sağlığı", "unknown", "SSD sağlık verisi okunamadı; diğer kontroller tamamlandı.")]


def repository_findings(directory: Path = Path("/etc/yum.repos.d")) -> list[Finding]:
    if not directory.exists():
        return [Finding("RPM depoları", "info", "Bu sistemde Fedora tarzı RPM depo dizini bulunmuyor.")]
    enabled, broken = 0, []
    for path in sorted(directory.glob("*.repo")):
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read_string(path.read_text())
            for section in parser.sections():
                if section != "main" and parser.getboolean(section, "enabled", fallback=True):
                    enabled += 1
        except (OSError, UnicodeError, configparser.Error, ValueError):
            broken.append(path.name)
    if broken:
        return [Finding("Depo yapılandırması", "warning", "Bazı depo dosyaları okunamadı veya geçerli biçimde değil.",
                        broken, ["İlgili depo dosyasını incele. Bu uygulama dosyada değişiklik yapmaz."])]
    if not enabled:
        return [Finding("RPM depoları", "warning", "Etkin RPM deposu bulunamadı. Atomik Fedora sürümlerinde güncelleme yolu farklı olabilir.")]
    return [Finding("RPM depoları", "info", f"{enabled} etkin depo tanımı bulundu. Depoların erişilebilirliği ve güncelleme işlemi test edilmedi.")]


APP_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\.[A-Za-z_][A-Za-z0-9_-]*$")


def scope_arg(scope: str) -> str:
    if scope in ("user", "system"):
        return "--" + scope
    if re.fullmatch(r"[A-Za-z0-9_-]+", scope):
        return "--installation=" + scope
    raise ValueError("Geçersiz Flatpak kurulum adı.")


def list_flatpaks() -> list[tuple[str, str, str]]:
    result = run(["flatpak", "list", "--app", "--columns=application,name,installation"])
    apps = []
    if result.code:
        return apps
    for line in result.output.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and APP_ID.fullmatch(parts[0]):
            try:
                scope_arg(parts[2])
                apps.append((parts[0], parts[1], parts[2]))
            except ValueError:
                continue
    return sorted(apps, key=lambda item: (item[1].casefold(), item[2]))


def access_finding(result: Result) -> Finding:
    if result.code:
        return Finding("Klasöre erişim", "unknown", "Flatpak dosya erişimi sorgusu tamamlanamadı.")
    value = result.output.strip().lower()
    if value == "hidden":
        return Finding("Klasöre erişim", "warning", "Flatpak bu klasöre doğrudan erişim olmadığını bildiriyor. Dosya seçme penceresi üzerinden verilen erişim farklı olabilir.",
                       ["Doğrudan erişim: yok"], ["Önce uygulamanın Dosya aç menüsünden dosyayı seçmeyi dene.",
                       "Kalıcı klasör erişimi gerekiyorsa uygulamanın izinlerini incele; yalnız gerekli klasöre izin ver."],
                       "İzin durumu doğrulandı; hata nedeni henüz kesin değil")
    if value in ("read-only", "read-write"):
        text = "Yalnız okuma" if value == "read-only" else "Okuma ve yazma"
        return Finding("Klasöre erişim", "info", f"Flatpak doğrudan erişim bildiriyor: {text.lower()}. Bu, uygulamanın dosyayı başarıyla açtığını kanıtlamaz.",
                       [f"Doğrudan erişim: {text}"], ["Sorun sürüyorsa dosyanın biçimini ve normal dosya izinlerini kontrol et."])
    return Finding("Klasöre erişim", "unknown", "Flatpak beklenen erişim yanıtını vermedi; sonuç tahmin edilmedi.")


def check_app(app_id: str, scope: str, folder: str | None = None) -> list[Finding]:
    if not APP_ID.fullmatch(app_id):
        raise ValueError("Geçersiz uygulama kimliği.")
    scope_option = scope_arg(scope)
    info = run(["flatpak", "info", scope_option, "--show-runtime", app_id])
    if info.code:
        return [Finding("Uygulama kurulumu", "unknown", "Seçilen kurulumdaki uygulama bilgisi okunamadı.")]
    runtime = info.output.strip()
    findings = [Finding("Uygulama kurulumu", "ok", "Seçilen Flatpak kurulumu okunabildi.", [app_id])]
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", runtime):
        check = run(["flatpak", "info", scope_option, runtime])
        findings.append(Finding("Çalışma ortamı", "ok" if check.code == 0 else "unknown",
                                "Gerekli Flatpak çalışma ortamı kurulu görünüyor." if check.code == 0
                                else "Gerekli çalışma ortamı doğrulanamadı.", [runtime]))
    else:
        findings.append(Finding("Çalışma ortamı", "unknown", "Uygulamanın çalışma ortamı bilgisi doğrulanamadı."))
    if folder:
        path = Path(folder).expanduser().resolve()
        if not path.is_dir():
            findings.append(Finding("Seçilen klasör", "unknown", "Klasör mevcut değil veya okunamıyor."))
        else:
            findings.append(access_finding(run(["flatpak", "info", scope_option,
                                                "--file-access=" + str(path), app_id])))
    findings.append(Finding("Açılış testi", "info", "Uygulama çalıştırılmadı. Kurulum ve izin bulguları, açılış hatasının nedenini tek başına kanıtlamaz.",
                            steps=["Uygulamayı normal şekilde açıp sonucu gözlemle."]))
    return findings
