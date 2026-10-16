"""Read cached SSD SMART information without authorization prompts or mutation.

NVMe ``percent_used`` is the vendor's endurance estimate, not a universal health
score. The parser intentionally distinguishes that estimate from critical SMART
warnings and refuses to present missing or stale data as a current percentage.
"""
from __future__ import annotations

from collections.abc import Mapping
import time

from .core import Finding


UDISKS_SERVICE = "org.freedesktop.UDisks2"
UDISKS_ROOT = "/org/freedesktop/UDisks2"
OBJECT_MANAGER = "org.freedesktop.DBus.ObjectManager"
DRIVE_INTERFACE = "org.freedesktop.UDisks2.Drive"
ATA_INTERFACE = "org.freedesktop.UDisks2.Drive.Ata"
NVME_INTERFACE = "org.freedesktop.UDisks2.NVMe.Controller"
DBUS_TIMEOUT_MS = 4000
SMART_MAX_AGE_SECONDS = 24 * 60 * 60
METRIC_LABEL = "Tahmini kalan ömür"

WARNING_LABELS = {
    "spare": "Yedek kapasite eşik altında",
    "temperature": "Sıcaklık güvenli aralığın dışında",
    "degraded": "Denetleyici güvenilirlik kaybı bildiriyor",
    "readonly": "Depolama salt okunur duruma geçmiş",
    "volatile_mem": "Geçici bellek yedekleme sorunu",
    "pmr_readonly": "Kalıcı bellek bölgesi salt okunur veya güvenilir değil",
}


def _model_text(model: object) -> str:
    """Only the model property is displayable; never substitute a device ID."""
    if not isinstance(model, str):
        return "Model bilinmiyor"
    cleaned = " ".join("".join(character for character in model if character.isprintable()).split())
    return cleaned[:100] or "Model bilinmiyor"


def _cached_age(properties: Mapping, now: float) -> float | None:
    updated = properties.get("SmartUpdated")
    if type(updated) is not int or updated <= 0 or updated > now:
        return None
    return now - updated


def _critical_warnings(properties: Mapping) -> list[str] | None:
    warnings = properties.get("SmartCriticalWarning")
    if not isinstance(warnings, (list, tuple)) or any(not isinstance(value, str) for value in warnings):
        return None
    return warnings


def parse_nvme_health(
    model: object,
    attributes: Mapping | None,
    properties: Mapping,
    *,
    now: float,
) -> Finding:
    """Interpret one cached NVMe snapshot with an explicit reference time.

    SMART properties are not meaningful when SmartUpdated is zero. Cached
    readings older than one day retain any recorded warning, with an explicit
    age qualifier, but never receive a current endurance percentage.
    """
    if not isinstance(properties, Mapping):
        properties = {}
    title = "SSD · " + _model_text(model)
    age = _cached_age(properties, now)
    if age is None:
        return Finding(
            title, "unknown",
            "Geçerli bir SMART kayıt zamanı yok; SSD’nin güncel kalan ömür yüzdesi doğrulanamadı.",
            ["SMART bilgisi henüz kaydedilmemiş veya kayıt zamanı geçersiz."],
            certainty="SMART kaydı doğrulanamadı",
            metric_label=METRIC_LABEL,
        )

    warnings = _critical_warnings(properties)
    evidence = ["Kaynak: UDisks2 önbelleğindeki NVMe SMART kaydı"]
    warning_evidence = [WARNING_LABELS.get(value, "Tanınmayan bir kritik SMART uyarısı bildirildi")
                        for value in (warnings or [])]
    if age > SMART_MAX_AGE_SECONDS:
        evidence.append(f"SMART kaydı: {int(age // 3600)} saat önce; güncel kabul edilmedi.")
        evidence.extend(warning_evidence)
        return Finding(
            title, "critical" if warnings else "unknown",
            "SMART kaydı 24 saatten eski; güncel bir kalan ömür yüzdesi gösterilemiyor."
            + (" Önceki kayıtta kritik SMART uyarısı var; güncel durumu ayrıca doğrula." if warnings else ""),
            evidence,
            ["Önemli dosyalarının yedeğini kontrol et; kayıtlı uyarıyı güncel bir SMART raporuyla doğrula."]
            if warnings else [],
            "Eski SMART kaydı; güncel durum doğrulanmadı",
            metric_label=METRIC_LABEL,
        )

    evidence.append("SMART kaydı: son 24 saat içinde")
    evidence.extend(warning_evidence)
    value = attributes.get("percent_used") if isinstance(attributes, Mapping) else None
    # UDisks exposes this NVMe field as a byte. Booleans/floats/text are not
    # accepted as percentages; 101..255 are valid values, not parse failures.
    valid_percentage = type(value) is int and 0 <= value <= 255
    remaining = float(max(0, 100 - value)) if valid_percentage else None
    status = "critical" if warnings else "unknown" if warnings is None or not valid_percentage else "info"
    explanation = (
        "Bu yüzde, üreticinin tahmini dayanıklılığından kalan payı gösterir; "
        "genel sağlık garantisi veya arıza olasılığı değildir."
        if valid_percentage else
        "NVMe dayanıklılık yüzdesi alınamadı veya desteklenmiyor; kalan ömür tahmin edilmedi."
    )
    if valid_percentage:
        evidence.append(f"Üreticinin bildirdiği tahmini ömür kullanımı: %{value}")
        if value >= 100:
            if status == "info":
                status = "warning"
            explanation += " Üreticinin dayanıklılık tahmini dolmuş görünüyor; bu tek başına SSD arızası anlamına gelmez."
    if warnings:
        explanation += " SMART kaydında ayrıca kritik uyarı bulunuyor; kalan ömür yüzdesinden bağımsız değerlendirilmelidir."
    elif warnings is None:
        explanation += " Kritik SMART uyarılarının durumu doğrulanamadı."

    steps = ["Önemli dosyalarının yedeğini kontrol et ve kritik SMART uyarısını incele."] if warnings else []
    if valid_percentage and value >= 100:
        steps.append("Yedeklerini kontrol et; yoğun yazma kullanımını ve olası disk değişimini planla.")
    return Finding(
        title, status, explanation, evidence, steps,
        "Üreticinin dayanıklılık tahmini; arıza tahmini değil",
        metric=remaining,
        metric_label=METRIC_LABEL,
    )


def _load_dbus():
    """Keep pure parser tests usable even on systems without PyGObject."""
    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
        return Gio, GLib
    except (ImportError, ValueError):
        return None


def _unknown_ssd(explanation: str) -> Finding:
    return Finding("SSD sağlığı", "unknown", explanation, metric_label=METRIC_LABEL)


def _unpack_reply(reply, expected_type: type):
    unpacked = reply.unpack()
    if not isinstance(unpacked, tuple) or len(unpacked) != 1 or not isinstance(unpacked[0], expected_type):
        return None
    return unpacked[0]


def read_ssd_health() -> list[Finding]:
    """Read UDisks2's existing cached data; never refresh SMART or run tests.

    NO_AUTO_START keeps absent services absent. Attribute requests explicitly
    disable interactive authorization; failures produce no invented percentage
    and no raw D-Bus errors or serial-bearing object paths are returned.
    """
    modules = _load_dbus()
    if modules is None:
        return [_unknown_ssd("SSD SMART bilgisi için gerekli yerel D-Bus bağlantısı kullanılamıyor.")]
    Gio, GLib = modules
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        reply = bus.call_sync(
            UDISKS_SERVICE, UDISKS_ROOT, OBJECT_MANAGER, "GetManagedObjects",
            None, GLib.VariantType.new("(a{oa{sa{sv}}})"),
            Gio.DBusCallFlags.NO_AUTO_START, DBUS_TIMEOUT_MS, None,
        )
        objects = _unpack_reply(reply, dict)
    except (GLib.Error, TypeError, ValueError):
        return [_unknown_ssd("SSD SMART bilgisine erişilemedi; UDisks2 hizmeti veya erişim izni kullanılamıyor.")]
    if objects is None:
        return [_unknown_ssd("SSD donanım bilgisi beklenen biçimde alınamadı.")]

    findings = []
    now = time.time()
    for object_path, interfaces in objects.items():
        if not isinstance(interfaces, Mapping):
            continue
        drive = interfaces.get(DRIVE_INTERFACE)
        if not isinstance(drive, Mapping) or drive.get("Optical") is True:
            continue
        model = drive.get("Model")
        properties = interfaces.get(NVME_INTERFACE)
        if isinstance(properties, Mapping):
            attributes = None
            age = _cached_age(properties, now)
            if age is not None and age <= SMART_MAX_AGE_SECONDS:
                try:
                    reply = bus.call_sync(
                        UDISKS_SERVICE, object_path, NVME_INTERFACE, "SmartGetAttributes",
                        GLib.Variant("(a{sv})", ({
                            "auth.no_user_interaction": GLib.Variant("b", True),
                        },)),
                        GLib.VariantType.new("(a{sv})"),
                        Gio.DBusCallFlags.NO_AUTO_START, DBUS_TIMEOUT_MS, None,
                    )
                    attributes = _unpack_reply(reply, dict)
                except (GLib.Error, TypeError, ValueError):
                    pass
            findings.append(parse_nvme_health(model, attributes, properties, now=now))
        elif type(drive.get("RotationRate")) is int and drive["RotationRate"] == 0:
            explanation = (
                "SATA SSD saptandı. Kalan ömür yüzdesi üreticiye özgü SMART değerlerine bağlı; "
                "bu sürümde doğrulanamıyor."
                if ATA_INTERFACE in interfaces else
                "Katı hal depolama saptandı; bu cihaz için desteklenen bir kalan ömür yüzdesi alınamadı."
            )
            findings.append(Finding("SSD · " + _model_text(model), "unknown", explanation,
                                    metric_label=METRIC_LABEL))
    return findings or [_unknown_ssd("Yüzde sağlayan desteklenen bir SSD saptanamadı; sağlık yüzdesi tahmin edilmedi.")]
