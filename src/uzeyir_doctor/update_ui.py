"""In-app release checks, verified downloads and explicit native installation."""
from __future__ import annotations
import threading
import time
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk
from . import APP_NAME, PACKAGE_NAME, __version__
from .design import icon
from .package_install import PackageInstaller
from .updates import (UpdateError, check_for_update, download_update, installed_version,
                      verify_download, version_key, promote_native_launcher)

MESSAGES = {
    "network": "GitHub’a ulaşılamadı. Bağlantını kontrol edip tekrar deneyebilirsin.",
    "metadata": "Sürüm bilgileri doğrulanamadı. Kurulum başlatılmadı.",
    "checksum": "Paket doğrulanamadı. Dosya kullanılmadı; tekrar indirebilirsin.",
    "storage": "İndirme klasörüne yazılamadı. Boş alanı ve klasör izinlerini kontrol et.",
    "no_package": "Bu sürümde sistemine uygun doğrulanabilir paket bulunamadı.",
    "unsupported": "Bu sistem için uygulama içi paket kurulumu desteklenmiyor. Sürüm sayfasını açabilirsin.",
    "cancelled": "İndirme iptal edildi. Çalışan sürüm korunuyor.",
    "install_failed": "Paket yöneticisi kurulumu tamamlayamadı. İşlemi kontrol edip yeniden deneyebilirsin.",
}


class UpdateController:
    def __init__(self, host, *, checker=check_for_update, downloader=download_update,
                 installer_factory=PackageInstaller, probe=installed_version, cache=None):
        self.host, self.tr = host, host.tr
        self.checker, self.downloader, self.installer_factory, self.probe = checker, downloader, installer_factory, probe
        self.cache = cache
        self.state, self.message = "idle", "GitHub’da yayımlanan yeni sürümleri buradan kontrol edebilirsin."
        self.offer = self.package = self.installer = self.dialog = None
        self.fraction = None
        self._closed = False
        self._generation = 0
        self._cancel = threading.Event()
        self._listeners = []
        self._startup = None
        self._announced = None
        self._retry = self.check

    @property
    def busy(self):
        return self.state in ("checking", "downloading", "verifying", "installing")

    def schedule_startup(self):
        if getattr(self.host.preferences, "check_updates_on_startup", False):
            def start():
                self._startup = None
                if not self._closed and self.state == "idle":
                    self.check()
                return GLib.SOURCE_REMOVE
            self._startup = GLib.timeout_add_seconds(2, start)

    def changed(self, state, message, fraction=None):
        if self._closed:
            return
        self.state, self.message, self.fraction = state, message, fraction
        for listener in tuple(self._listeners):
            listener()

    def show(self, *_):
        if self._closed:
            return
        if self.dialog is None:
            self.dialog = UpdateDialog(self)
        self.dialog.present(self.host)

    def _work(self, task, completed):
        self._generation += 1
        generation = self._generation
        def worker():
            try:
                result, error = task(), None
            except UpdateError as exc:
                result, error = None, exc.code
            except Exception:
                result, error = None, "network"
            def deliver():
                if not self._closed and generation == self._generation:
                    completed(result, error)
                return GLib.SOURCE_REMOVE
            GLib.idle_add(deliver)
        threading.Thread(target=worker, name="app-update", daemon=True).start()
        return generation

    def check(self, *_):
        if self._closed or self.busy:
            return
        self.changed("checking", "Yeni sürüm kontrol ediliyor…")
        self._retry = self.check
        def done(offer, error):
            if error:
                self.changed("error", MESSAGES.get(error, MESSAGES["network"]))
            elif offer is None:
                self.offer = None
                self.changed("current", "En güncel sürümü kullanıyorsun.")
            else:
                self.offer = offer
                self.changed("available", "Yeni sürüm hazır. Sürüm notlarını inceleyip güncelleyebilirsin.")
                if self.dialog is None and self._announced != offer.version:
                    self.host.toast("Yeni bir uygulama sürümü hazır.")
                self._announced = offer.version
        self._work(lambda: self.checker(self.host.package_format or "source"), done)

    def download(self, *_):
        if self._closed or self.busy or self.offer is None:
            return
        self._cancel = threading.Event()
        self.changed("downloading", "Paket indiriliyor ve SHA-256 ile doğrulanıyor…", 0)
        self._retry = self.download
        generation, last = self._generation + 1, [0.0]
        def progress(received, total):
            now = time.monotonic()
            if received not in (0, total) and now - last[0] < .1:
                return
            last[0] = now
            def apply():
                if not self._closed and generation == self._generation and self.state == "downloading":
                    self.changed("downloading", "Paket indiriliyor ve SHA-256 ile doğrulanıyor…", received / total)
                return GLib.SOURCE_REMOVE
            GLib.idle_add(apply)
        def done(package, error):
            if error:
                self.changed("available" if error == "cancelled" else "error", MESSAGES.get(error, MESSAGES["network"]))
            else:
                self.package = package
                self.changed("ready", "Paket doğrulandı. Hazır olduğunda kurulumu başlat.", 1)
                if self.dialog is None:
                    self.host.toast("Güncelleme indirildi. Kuruluma hazır.")
        self._work(lambda: self.downloader(self.offer, self._cancel, progress, cache=self.cache), done)

    def cancel_download(self, *_):
        if self.state == "downloading":
            self._cancel.set()

    def install(self, *_):
        if self._closed or self.busy or self.package is None:
            return
        if self.offer is None or self.package.offer != self.offer:
            self._retry = self.download
            self.changed("error", MESSAGES["checksum"])
            return
        self.changed("verifying", "Kurulum öncesi paket yeniden doğrulanıyor…")
        self._retry = self.install
        def verified(path, error):
            if error:
                self.package = None
                self._retry = self.download
                self.changed("error", MESSAGES["checksum"])
                return
            self.changed("installing", "Sistem paket yöneticisi kurulumu yürütüyor. Yetkilendirme penceresini tamamla.")
            self.installer = self.installer_factory(self.install_finished, self.install_progress)
            self.installer.install(path)
        self._work(lambda: verify_download(self.package), verified)

    def install_progress(self, fraction):
        if self.state == "installing":
            self.changed(self.state, self.message, fraction)

    def install_finished(self, status):
        if self._closed:
            return
        if status == "unavailable":
            launcher = Gtk.FileLauncher.new(Gio.File.new_for_path(str(self.package.path)))
            launcher.launch(self.host, None, self._launched)
        elif status == "installed":
            self.verify_installed()
        elif status == "unknown":
            self.changed("external", "Kurulum durumu alınamadı. Yeniden kurmadan önce kurulu sürümü doğrula.")
        else:
            self._retry = self.install
            self.changed("error", MESSAGES["install_failed"])

    def _launched(self, launcher, result):
        if self._closed:
            return
        try:
            launcher.launch_finish(result)
            self.changed("external", "Dağıtımın paket kurucusu açıldı. Kurulum bitince buradan doğrula.")
        except GLib.Error:
            self.changed("manual", "Bu sistemde paket kurucusu açılamadı. Doğrulanan dosyanın kurulum komutunu kopyalayabilirsin.")

    def verify_installed(self, *_):
        if self._closed or self.offer is None or self.state == "verifying":
            return
        self.changed("verifying", "Kurulu sürüm kontrol ediliyor…")
        self._retry = self.verify_installed
        def done(version, error):
            if not error and version and version_key(version) >= version_key(self.offer.version):
                self.changed("installed", "Güncelleme kuruldu. Yeni sürümü kullanmak için uygulamayı yeniden başlat.")
            else:
                self.changed("external", "Yeni sürüm henüz doğrulanamadı. Kurulumu tamamlayıp tekrar kontrol et.")
        def probe():
            version = self.probe(self.offer.package_format)
            if version and version_key(version) >= version_key(self.offer.version):
                promote_native_launcher()
            return version
        self._work(probe, done)

    def open_release(self, *_):
        from . import UPDATE_REPOSITORY
        url = self.offer.url if self.offer else f"https://github.com/{UPDATE_REPOSITORY}/releases"
        launcher = Gtk.UriLauncher.new(url)
        launcher.launch(self.host, None, self._link_opened)

    def _link_opened(self, launcher, result):
        try:
            launcher.launch_finish(result)
        except GLib.Error:
            if not self._closed:
                self.host.toast("Bağlantı açılamadı. Varsayılan tarayıcını kontrol et.")

    def copy_command(self, *_):
        if self.package is not None:
            import shlex
            prefix = {"rpm": "sudo dnf install ", "deb": "sudo apt install ", "arch": "sudo pacman -U "}[self.offer.package_format]
            self.host.get_display().get_clipboard().set(prefix + shlex.quote(str(self.package.path)))
            self.host.toast("Komut kopyalandı")

    def restart(self, *_):
        executable = Path("/usr/bin") / PACKAGE_NAME
        if self.state != "installed" or not executable.is_file():
            return
        try:
            Gio.Subprocess.new([str(executable)], Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE)
        except GLib.Error:
            self.host.toast("Uygulamayı menüden yeniden başlatabilirsin.")
            return
        self.host.close()

    def close(self):
        self._closed = True
        self._generation += 1
        self._cancel.set()
        if self._startup is not None:
            GLib.source_remove(self._startup)
            self._startup = None
        if self.installer is not None:
            self.installer.close()
        if self.dialog is not None:
            self.dialog.close()
        self._listeners.clear()


class UpdateDialog(Adw.Dialog):
    def __init__(self, controller):
        super().__init__()
        self.controller, self.host, self.tr = controller, controller.host, controller.tr
        self._opening_tick = None
        self._opening_frames = 0
        self._close_queued = False
        # libadwaita 1.5 opens the sheet on its second map tick. Our map
        # handler can register first, so wait until the following frame before
        # accepting a queued close; otherwise the native reveal reopens it.
        self.set_can_close(False)
        self.connect("close-attempt", self._queue_close)
        self.set_content_width(570)
        self.set_content_height(650)
        self.set_title(self.tr("Güncellemeler"))
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.append(Adw.HeaderBar())
        scroll = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20, margin_start=24, margin_end=24, margin_top=10, margin_bottom=24)
        scroll.set_child(root)
        outer.append(scroll)
        self.set_child(outer)
        hero = Gtk.Box(spacing=16)
        hero.append(icon("brand", 40))
        copy = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, hexpand=True)
        copy.append(Gtk.Label(label=APP_NAME, xalign=0, css_classes=["title-2"]))
        self.version_label = Gtk.Label(xalign=0, css_classes=["muted"])
        copy.append(self.version_label)
        hero.append(copy)
        root.append(hero)
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, css_classes=["card"])
        status_row = Gtk.Box(spacing=12)
        self.spinner = Gtk.Spinner(valign=Gtk.Align.START)
        self.message = Gtk.Label(xalign=0, wrap=True, hexpand=True)
        status_row.append(self.spinner)
        status_row.append(self.message)
        panel.append(status_row)
        self.progress = Gtk.ProgressBar(show_text=True)
        panel.append(self.progress)
        self.primary = Gtk.Button(css_classes=["primary"])
        self.primary.connect("clicked", self.act)
        panel.append(self.primary)
        self.cancel = Gtk.Button(css_classes=["soft"])
        self.cancel.connect("clicked", controller.cancel_download)
        panel.append(self.cancel)
        self.release_button = Gtk.Button(css_classes=["soft"])
        self.release_button.connect("clicked", controller.open_release)
        panel.append(self.release_button)
        root.append(panel)
        self.notes = Gtk.Expander()
        self.notes_text = Gtk.Label(xalign=0, wrap=True, selectable=True)
        self.notes.set_child(self.notes_text)
        root.append(self.notes)
        option = Gtk.Box(spacing=20)
        self.auto_label = Gtk.Label(xalign=0, wrap=True, hexpand=True)
        option.append(self.auto_label)
        self.auto_switch = Gtk.Switch(active=getattr(self.host.preferences,"check_updates_on_startup",False), valign=Gtk.Align.CENTER)
        self.auto_switch.connect("notify::active", self.auto_changed)
        option.append(self.auto_switch)
        root.append(option)
        self.privacy = Gtk.Label(xalign=0, wrap=True, css_classes=["download-notice"])
        root.append(self.privacy)
        controller._listeners.append(self.render)
        self.tr.connect(self.render)
        self.connect("closed", self.closed)
        self.connect("map", self._mapped)
        self.connect("unmap", self._unmapped)
        self._root = root
        self.host.motion.decorate(root)
        self.render()

    def _queue_close(self, *_):
        self._close_queued = True

    def _mapped(self, *_):
        self.render()
        self._opening_frames = 0
        if self._opening_tick is None:
            self._opening_tick = self.add_tick_callback(self._presented_frame)

    def _presented_frame(self, _widget, _clock):
        self._opening_frames += 1
        if self._opening_frames < 3:
            return True
        self._opening_tick = None
        self.set_can_close(True)
        if self._close_queued:
            self._close_queued = False
            self.close()
        return False

    def _unmapped(self, *_):
        self.spinner.stop()
        if self._opening_tick is not None:
            self.remove_tick_callback(self._opening_tick)
            self._opening_tick = None

    def render(self):
        c = self.controller
        self.set_title(self.tr("Güncellemeler"))
        current = self.tr("Mevcut sürüm: {version}", version=__version__)
        if c.offer is not None:
            current += "  →  " + self.tr("Yeni sürüm: {version}", version=c.offer.version)
        self.version_label.set_label(current)
        self.message.set_label(self.tr(c.message))
        animate = self.host.animations_enabled() and self.get_mapped()
        self.spinner.set_visible(c.busy)
        self.spinner.set_spinning(c.busy and animate)
        self.progress.set_visible(c.fraction is not None)
        if c.fraction is not None:
            self.progress.set_fraction(max(0, min(1, c.fraction)))
        labels = {"available":"Güncellemeyi indir", "ready":"Kurulumu başlat", "installed":"Yeniden başlat",
                  "external":"Kurulumu doğrula", "manual":"Kurulum komutunu kopyala", "error":"Tekrar dene"}
        self.primary.set_label(self.tr(labels.get(c.state, "Güncellemeleri kontrol et")))
        self.primary.set_sensitive(not c.busy)
        self.cancel.set_visible(c.state == "downloading")
        self.cancel.set_label(self.tr("İndirmeyi iptal et"))
        self.release_button.set_label(self.tr("GitHub’da sürümleri aç"))
        self.notes.set_label(self.tr("Sürüm notları"))
        self.notes.set_visible(bool(c.offer and c.offer.notes))
        self.notes_text.set_label(c.offer.notes if c.offer else "")
        self.auto_label.set_label(self.tr("Açılışta güncellemeleri kontrol et"))
        self.auto_switch.set_tooltip_text(self.tr("Açılışta güncellemeleri kontrol et"))
        self.privacy.set_label(self.tr("Sürüm kontrolü GitHub’a bağlanır. Kurulum yalnız sen başlatınca yapılır; sistem yetkilendirme isteyebilir."))

    def act(self, *_):
        c = self.controller
        actions = {"available":c.download,"ready":c.install,"installed":c.restart,"external":c.verify_installed,
                   "manual":c.copy_command,"error":c._retry}
        actions.get(c.state,c.check)()

    def auto_changed(self, switch, *_):
        self.host.preferences.check_updates_on_startup = switch.get_active()
        self.host.save_preferences()

    def closed(self, *_):
        self._unmapped()
        self.host.motion.forget(self._root)
        self.tr.disconnect(self.render)
        if self.render in self.controller._listeners:
            self.controller._listeners.remove(self.render)
        self.controller.dialog = None
