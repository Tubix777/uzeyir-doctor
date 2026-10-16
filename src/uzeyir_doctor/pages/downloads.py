"""Per-module download pages, with explicit external links and no installation."""
from __future__ import annotations

import threading
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk, Pango

from uzeyir_doctor.design import heading, icon, text
from uzeyir_doctor.entrance import MotionBox
from uzeyir_doctor.downloads import APPLICATIONS, REPOSITORIES, bundled_release, fetch_release, size_text

FORMATS = {"rpm": "Fedora · RPM", "deb": "Debian / Ubuntu · DEB", "arch": "Arch · pacman", "portable": "Taşınabilir", "source": "Kaynak paketleri"}
DESCRIPTIONS = {
    "doctor": "Uzeyir Doctor’ün bağımsız uygulamasını ve Linux kurulum paketlerini indir.",
}


class DownloadsPage(Gtk.Box):
    def __init__(self, host, translator, settings, module, loader=fetch_release):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.host, self.tr, self.settings = host, translator, settings
        self.module, self.loader = module, loader
        self._closed, self._active, self._busy = False, False, False
        self._generation = 0
        self.release = bundled_release(module)
        preferred = getattr(host, "package_format", None)
        self._format = (preferred if preferred in self.release.formats else
                        "source" if preferred and "source" in self.release.formats else
                        self.release.formats[0] if self.release.formats else None)
        self._status = "Paket bilgileri bu sürümle birlikte gelir. Güncel sürümü istediğinde kontrol edebilirsin."
        self.asset_buttons = []
        self.commands = []
        self.add_css_class("downloads-page")

        self.scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        clamp = Adw.Clamp(hexpand=True, unit=Adw.LengthUnit.PX, maximum_size=1120, tightening_threshold=950)
        clamp.set_child(self.scroll)
        self.append(clamp)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=22,
                              margin_top=26, margin_bottom=32, margin_start=28, margin_end=28)
        self.scroll.set_child(self.content)
        back = Gtk.Button()
        self.tr.bind(back, "Panele dön")
        back.add_css_class("text-action")
        back.set_halign(Gtk.Align.START)
        back.connect("clicked", lambda *_: host.select_page(module))
        self.content.append(back)

        art = icon("search", 42)
        art.add_css_class("download-hero-icon")
        self.content.append(heading(self.tr, "İNDİRME MERKEZİ", APPLICATIONS[module], DESCRIPTIONS[module], art))
        release_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        release_card.add_css_class("card")
        row = Gtk.Box(spacing=18)
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, hexpand=True)
        info.append(text(self.tr, "Bağımsız uygulama", "eyebrow"))
        self.version_label = Gtk.Label(xalign=0)
        self.version_label.add_css_class("download-version")
        info.append(self.version_label)
        row.append(info)
        self.channel_label = Gtk.Label(valign=Gtk.Align.CENTER)
        self.channel_label.add_css_class("pill")
        self.channel_label.add_css_class("info")
        row.append(self.channel_label)
        release_card.append(row)

        release_actions = Gtk.Box(spacing=10)
        self.release_button = self.button("Sürüm sayfası", lambda *_: self.open_link(self.release.url), "soft")
        release_actions.append(self.release_button)
        self.refresh_button = self.button("Güncel sürümü kontrol et", self.refresh, "soft")
        release_actions.append(self.refresh_button)
        self.spinner = Gtk.Spinner(valign=Gtk.Align.CENTER)
        release_actions.append(self.spinner)
        release_card.append(release_actions)
        self.status = Gtk.Label(xalign=0, wrap=True)
        self.status.add_css_class("download-notice")
        release_card.append(self.status)
        self.content.append(release_card)

        choose = Gtk.Box(spacing=14)
        choose.append(text(self.tr, "Paket seç", "section-title"))
        self.format_model = Gtk.StringList()
        self.format_selector = Gtk.DropDown(model=self.format_model, halign=Gtk.Align.END, hexpand=True)
        self.format_selector.connect("notify::selected", self.format_changed)
        choose.append(self.format_selector)
        self.content.append(choose)
        self.asset_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.asset_box.add_css_class("download-list")
        self.content.append(self.asset_box)

        self.install = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.install.append(text(self.tr, "İndirdikten sonra", "section-title"))
        self.install.append(text(self.tr, "Terminali indirilen dosyanın bulunduğu klasörde aç. Komutu kendin çalıştırabilirsin.", "download-notice"))
        self.command_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.install.append(self.command_box)
        self.content.append(self.install)

        links = Gtk.Box(spacing=20)
        links.add_css_class("download-links")
        links.append(self.button("Kaynak kod", lambda *_: self.open_link(f"https://github.com/{REPOSITORIES[self.module]}"), "text-action"))
        links.append(self.button("Tüm sürümler", lambda *_: self.open_link(f"https://github.com/{REPOSITORIES[self.module]}/releases"), "text-action"))
        links.append(self.button("Sorun bildir", lambda *_: self.open_link(f"https://github.com/{REPOSITORIES[self.module]}/issues"), "text-action"))
        self.content.append(links)
        self.content.append(text(self.tr, "İndirme bağlantıları tarayıcıda açılır. Bu sayfa paket kurmaz veya sistem izinlerini değiştirmez.", "download-notice"))
        self._syncing = False
        self.tr.connect(self.retranslate)
        self.retranslate()

    def button(self, source, callback, css, *, bind=True):
        widget = Gtk.Button()
        if bind:
            self.tr.bind(widget, source)
        else:
            widget.set_label(self.tr(source))
        widget.add_css_class(css)
        widget.connect("clicked", callback)
        return widget

    def retranslate(self):
        if self._closed:
            return
        self.version_label.set_label(self.release.tag)
        self.channel_label.set_label(self.tr("Ön sürüm" if self.release.preview else "Yayımlanan sürüm"))
        self.status.set_label(self.tr(self._status))
        self._syncing = True
        formats = self.release.formats
        self.format_model.splice(0, self.format_model.get_n_items(), [self.tr(FORMATS[kind]) for kind in formats])
        self._format = self._format if self._format in formats else formats[0] if formats else None
        self.format_selector.set_selected(formats.index(self._format) if self._format else Gtk.INVALID_LIST_POSITION)
        self.format_selector.set_sensitive(bool(formats))
        self._syncing = False
        self.render_assets()

    def format_changed(self, selector, *_):
        if self._closed or self._syncing:
            return
        index = selector.get_selected()
        if index < len(self.release.formats):
            self._format = self.release.formats[index]
            self.render_assets()

    def render_assets(self):
        for container in (self.asset_box, self.command_box):
            if hasattr(self.host, "motion"):
                self.host.motion.forget(container)
            child = container.get_first_child()
            while child:
                following = child.get_next_sibling()
                container.remove(child)
                child = following
        self.asset_buttons, self.commands = [], []
        assets = [asset for asset in self.release.assets if asset.kind == self._format]
        if not assets:
            self.asset_box.append(Gtk.Label(label=self.tr("Bu sürümde paket bulunamadı. Tüm sürümler sayfasını açabilirsin."), wrap=True, css_classes=["download-row"]))
        for asset in assets:
            row = MotionBox(spacing=14)
            row.add_css_class("download-row")
            row.append(icon("download", 20))
            copy = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, hexpand=True)
            title = self.tr("Kaynak RPM" if asset.name.endswith(".src.rpm") else FORMATS[asset.kind])
            if size_text(asset.size):
                title += "  ·  " + size_text(asset.size)
            copy.append(Gtk.Label(label=title, xalign=0, css_classes=["download-kind"]))
            filename = Gtk.Label(label=asset.name, xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE)
            filename.set_max_width_chars(40)
            filename.set_tooltip_text(asset.name)
            filename.add_css_class("download-filename")
            copy.append(filename)
            row.append(copy)
            button = self.button("İndir", lambda _button, url=asset.url: self.open_link(url), "primary", bind=False)
            button.set_valign(Gtk.Align.CENTER)
            row.append(button)
            self.asset_buttons.append(button)
            self.asset_box.append(row)
            if asset.install_command:
                command = MotionBox(spacing=12)
                command.add_css_class("command-panel")
                code = Gtk.Label(label=asset.install_command, selectable=True, xalign=0, wrap=True, hexpand=True)
                code.set_wrap_mode(Pango.WrapMode.CHAR)
                code.add_css_class("code-command")
                command.append(code)
                command.append(self.button("Kopyala", lambda _button, value=asset.install_command: self.copy(value), "soft", bind=False))
                self.commands.append(asset.install_command)
                self.command_box.append(command)
        self.install.set_visible(bool(self.commands))
        if hasattr(self.host, "motion"):
            self.host.motion.decorate(self.content)

    def copy(self, value):
        if not self._closed:
            self.get_display().get_clipboard().set(value)
            self.host.toast("Komut kopyalandı")

    def open_link(self, url):
        if self._closed:
            return
        launcher = Gtk.UriLauncher.new(url)
        launcher.launch(self.host, None, self.link_opened)

    def link_opened(self, launcher, result):
        try:
            launcher.launch_finish(result)
        except GLib.Error as error:
            if not self._closed and not error.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                self.host.toast("Bağlantı açılamadı. Varsayılan tarayıcını kontrol et.")

    def refresh(self, *_):
        if self._busy or self._closed:
            return
        self._busy = True
        self._generation += 1
        generation = self._generation
        self.refresh_button.set_sensitive(False)
        self.sync_motion()
        self._status = "GitHub’daki sürüm kontrol ediliyor…"
        self.status.set_label(self.tr(self._status))
        def worker():
            try:
                release = self.loader(self.module)
            except Exception:
                release = None
            GLib.idle_add(self.received, generation, release)
        threading.Thread(target=worker, name="release-check", daemon=True).start()

    def received(self, generation, release):
        if self._closed or generation != self._generation:
            return GLib.SOURCE_REMOVE
        self._busy = False
        self.refresh_button.set_sensitive(True)
        self.spinner.stop()
        if release is None:
            self._status = "Güncel sürüm alınamadı. Kayıtlı bağlantıları kullanabilir veya daha sonra tekrar deneyebilirsin."
        else:
            self.release = release
            self._status = "Sürüm ve paket bağlantıları GitHub’dan güncellendi."
        self.retranslate()
        return GLib.SOURCE_REMOVE

    def set_active(self, active):
        self._active = bool(active) and not self._closed
        self.sync_motion()

    def sync_motion(self):
        enabled = self.host.animations_enabled() if hasattr(self.host, "animations_enabled") else not self.settings.reduced_motion
        self.spinner.set_spinning(self._busy and self._active and enabled and not self._closed)

    def close(self):
        self._closed = True
        self._active = False
        self._generation += 1
        self.spinner.stop()
        self.tr.disconnect(self.retranslate)
