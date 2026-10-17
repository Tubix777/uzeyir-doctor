"""Standalone local diagnostic application with shared accessible native motion."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Graphene, Gtk
from doctor.app import CSS as DOCTOR_CSS, box, label
from . import APP_NAME, __version__
from .i18n import Translator
from .settings import Settings
from .interactions import CSS as MOTION_CSS, MotionController
from .design import CSS as DESIGN_CSS, icon, load_font
from .navigation import PageTransition, SelectionIndicator
from .update_ui import UpdateController
from .pages.doctor import DoctorPage
from .pages.downloads import DownloadsPage


CSS = DOCTOR_CSS + MOTION_CSS + DESIGN_CSS

MODULES = (("doctor", "Sorun Teşhisi", "Sistem taraması ve çözüm adımları", "search"),)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application, preferences=None, page_factories=None, initial="doctor", initial_view="dashboard", package_format=None):
        super().__init__(application=application, title=APP_NAME)
        load_font()
        self.add_css_class("uzeyir-doctor-window")
        self.set_default_size(1320, 900)
        self.set_size_request(960, 620)
        self.preferences = preferences or Settings()
        self.package_format = package_format
        if self.preferences.reduced_motion:
            self.add_css_class("reduce-motion")
        self.tr = Translator(self.preferences.language)
        self._closed = False
        self.current_page = None
        self.current_view = "dashboard"
        self.pages = {}
        self.downloads = {}
        self.nav_buttons = {}
        self.download_buttons = {}
        self.nav_rows = {}
        self.motion = MotionController(self, self.animations_enabled())
        root = box(0)
        header = Adw.HeaderBar()
        self.page_title = label("", "page-header", False)
        header.set_title_widget(self.page_title)
        tag = label(f"v{__version__}", "module-tag", False)
        header.pack_end(tag)
        help_button = Gtk.Button()
        help_button.set_child(icon("keyboard", 18))
        self.tr.bind(help_button, "Klavye kısayolları", "set_tooltip_text")
        help_button.add_css_class("flat")
        help_button.connect("clicked", self.show_shortcuts)
        header.pack_end(help_button)
        self.update_button = Gtk.Button(css_classes=["flat"])
        self.update_button.set_child(icon("update", 18))
        self.tr.bind(self.update_button, "Güncellemeler", "set_tooltip_text")
        self.update_button.connect("clicked", lambda *_: self.updater.show())
        header.pack_end(self.update_button)
        root.append(header)
        body = box(0, True)
        body.set_vexpand(True)
        sidebar = box(8)
        sidebar.set_size_request(220, -1)
        sidebar.set_hexpand(False)
        sidebar.add_css_class("sidebar")
        brand_row = box(10, True)
        resources = Path(__file__).parent / "resources"
        brand_image = icon("brand", 30)
        brand_row.append(brand_image)
        brand_copy = box(3)
        brand_copy.append(label(APP_NAME, "brand", False))
        brand_copy.append(self.tr.bind(label("Sorunları anlaşılır biçimde gör.", "brand-caption"), "Sorunları anlaşılır biçimde gör."))
        brand_row.append(brand_copy)
        sidebar.append(brand_row)
        section = label("ARAÇLAR", "sidebar-title")
        section.set_margin_top(26)
        section.set_margin_start(8)
        self.tr.bind(section, "ARAÇLAR")
        sidebar.append(section)
        menu = box(8)
        menu_overlay = Gtk.Overlay(child=menu)
        self.selection_indicator = SelectionIndicator(menu, self.animations_enabled())
        menu_overlay.add_overlay(self.selection_indicator)
        sidebar.append(menu_overlay)
        for name, title, caption, _symbolic_icon in MODULES:
            nav_row = box(0, True)
            nav_row.add_css_class("nav-row")
            button = Gtk.Button()
            button.add_css_class("nav-button")
            button.set_hexpand(True)
            content = box(12, True)
            image = icon("search", 20)
            image.set_pixel_size(20)
            image.add_css_class("nav-icon")
            content.append(image)
            texts = box(4)
            texts.set_hexpand(True)
            texts.append(self.tr.bind(label(title, "nav-title", False), title))
            caption = APP_NAME
            caption_label = label(caption, "nav-caption", False)
            caption_label.set_max_width_chars(25)
            texts.append(self.tr.bind(caption_label, caption))
            content.append(texts)
            button.set_child(content)
            self.tr.bind(button, title, "set_tooltip_text")
            button.connect("clicked", lambda _button, target=name: self.select_page(target))
            nav_row.append(button)
            download_button = Gtk.Button()
            download_button.add_css_class("nav-download")
            download_image = icon("download", 17)
            download_image.set_pixel_size(17)
            download_button.set_child(download_image)
            download_button.connect("clicked", lambda _button, target=name: self.select_downloads(target))
            nav_row.append(download_button)
            menu.append(nav_row)
            self.nav_buttons[name] = button
            self.download_buttons[name] = download_button
            self.nav_rows[name] = nav_row
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda _action, _parameter, target=name: self.select_page(target))
            self.add_action(action)
        spacer = Gtk.Box(vexpand=True)
        sidebar.append(spacer)
        preferences_box = box(10)
        preferences_box.add_css_class("sidebar-settings")
        preferences_box.append(self.tr.bind(label("TERCİHLER", "sidebar-title"), "TERCİHLER"))
        self.language = Gtk.DropDown.new_from_strings(["Türkçe", "English"])
        self.language.set_selected(0 if self.preferences.language == "tr" else 1)
        self.language.connect("notify::selected", self.language_changed)
        self.tr.bind(self.language, "Dil", "set_tooltip_text")
        preferences_box.append(self.language)
        motion_row = box(10, True)
        motion_label = label("Hareketi azalt", "sidebar-footer")
        motion_label.set_hexpand(True)
        self.tr.bind(motion_label, "Hareketi azalt")
        motion_row.append(motion_label)
        self.motion_switch = Gtk.Switch(valign=Gtk.Align.CENTER, active=self.preferences.reduced_motion)
        self.tr.bind(self.motion_switch, "Geçiş ve kaydırma animasyonlarını azalt", "set_tooltip_text")
        self.motion_switch.connect("notify::active", self.motion_changed)
        motion_row.append(self.motion_switch)
        preferences_box.append(motion_row)
        sidebar.append(preferences_box)
        footer = label("Yerel ve şeffaf", "sidebar-footer")
        self.tr.bind(footer, "Yerel ve şeffaf")
        footer.set_margin_top(12)
        footer.set_margin_start(8)
        sidebar.append(footer)
        body.append(sidebar)
        body.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self.stack = Gtk.Stack(hexpand=True, vexpand=True)
        self.stack.set_hhomogeneous(False)
        self.stack.set_vhomogeneous(False)
        self.page_transition = PageTransition(self.stack, self.animations_enabled())
        body.append(self.page_transition)
        root.append(body)
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(root)
        self.set_content(self.toast_overlay)
        if page_factories is None:
            page_factories = {"doctor": DoctorPage}
        for name, _, _, _ in MODULES:
            factory = page_factories[name]
            page = factory(self, self.tr, self.preferences)
            self.pages[name] = page
            self.stack.add_named(page, name)
            page.set_active(False)
            self.motion.decorate(page)
            downloads = DownloadsPage(self, self.tr, self.preferences, name)
            self.downloads[name] = downloads
            self.stack.add_named(downloads, name + "-downloads")
            self.motion.decorate(downloads)
        self.tr.connect(self.retranslate)
        self._gtk_settings = Gtk.Settings.get_default()
        self._animation_signal = (
            self._gtk_settings.connect("notify::gtk-enable-animations", self.sync_motion)
            if self._gtk_settings else None
        )
        self.updater = UpdateController(self)
        self.sync_motion()
        self.select_page(initial, initial_view)
        self.updater.schedule_startup()
        self.connect("close-request", self.on_close)
        for index, (name, *_rest) in enumerate(MODULES, 1):
            application.set_accels_for_action("win." + name, [f"<Control>{index}"])
        download_action = Gio.SimpleAction.new("downloads", None)
        download_action.connect("activate", lambda *_: self.select_downloads(self.current_page))
        self.add_action(download_action)
        application.set_accels_for_action("win.downloads", ["<Control>l"])
        update_action = Gio.SimpleAction.new("updates", None)
        update_action.connect("activate", lambda *_: self.updater.show())
        self.add_action(update_action)
        application.set_accels_for_action("win.updates", ["<Control>u"])

    def animations_enabled(self):
        settings = Gtk.Settings.get_default()
        return bool(not self.preferences.reduced_motion and settings and settings.get_property("gtk-enable-animations"))

    def select_page(self, name, view="dashboard"):
        if self._closed or name not in self.pages or view not in ("dashboard", "downloads"):
            return
        if name == self.current_page and view == self.current_view:
            return
        previous_name = self.current_page
        if self.current_page:
            previous = self.downloads if self.current_view == "downloads" else self.pages
            previous[self.current_page].set_active(False)
            self.nav_buttons[self.current_page].remove_css_class("selected")
            self.download_buttons[self.current_page].remove_css_class("selected")
            self.nav_rows[self.current_page].remove_css_class("current")
        self.current_page = name
        self.current_view = view
        self.nav_rows[name].add_css_class("current")
        self.nav_buttons[name].add_css_class("selected")
        if view == "downloads":
            self.download_buttons[name].add_css_class("selected")
        if previous_name == name:
            direction = (1, 0) if view == "downloads" else (-1, 0)
        elif previous_name:
            names = [module[0] for module in MODULES]
            direction = (0, 1) if names.index(name) > names.index(previous_name) else (0, -1)
        else:
            direction = (0, 1)
        self.selection_indicator.select(self.nav_rows[name], animate=previous_name is not None)
        with self.motion.navigation():
            self.page_transition.navigate(name + ("-downloads" if view == "downloads" else ""), direction)
        target = self.downloads if view == "downloads" else self.pages
        target[name].set_active(True)
        self.retranslate()

    def select_downloads(self, name):
        self.select_page(name, "downloads")

    def toast(self, source):
        if not self._closed:
            self.toast_overlay.add_toast(Adw.Toast.new(self.tr(source)))

    def show_shortcuts(self, *_):
        dialog = Adw.Dialog(title=self.tr("Klavye kısayolları"))
        dialog.set_content_width(420)
        root = box(18)
        root.append(Adw.HeaderBar())
        content = box(16)
        for method in (content.set_margin_start, content.set_margin_end, content.set_margin_bottom):
            method(24)
        for keys, source in (("Ctrl + 1", "Sorun Teşhisi"), ("Ctrl + L", "Bu bölümün indirme sayfası"), ("Ctrl + U", "Güncellemeler")):
            row = box(24, True)
            title = label(self.tr(source))
            title.set_hexpand(True)
            row.append(title)
            row.append(label(keys, "shortcut-key", False))
            content.append(row)
        root.append(content)
        dialog.set_child(root)
        dialog.present(self)

    def language_changed(self, dropdown, *_):
        self.preferences.language = "tr" if dropdown.get_selected() == 0 else "en"
        self.tr.set_language(self.preferences.language)
        self.save_preferences()

    def motion_changed(self, switch, *_):
        self.preferences.reduced_motion = switch.get_active()
        self.sync_motion()
        self.save_preferences()

    def sync_motion(self, *_):
        enabled = self.animations_enabled()
        if not enabled:
            self.add_css_class("reduce-motion")
        else:
            self.remove_css_class("reduce-motion")
        self.motion.set_enabled(enabled)
        self.page_transition.set_enabled(enabled)
        self.selection_indicator.set_enabled(enabled)
        if hasattr(self, "updater") and self.updater.dialog is not None:
            self.updater.dialog.render()
        for page in (*self.pages.values(), *self.downloads.values()):
            if hasattr(page, "sync_motion"):
                page.sync_motion()

    def save_preferences(self):
        try:
            self.preferences.save()
        except OSError:
            # A read-only home must not stop navigation or language selection.
            pass

    def retranslate(self):
        title = next((title for name, title, *_ in MODULES if name == self.current_page), APP_NAME)
        self.page_title.set_label(self.tr(title))
        if self.current_view == "downloads":
            self.page_title.set_label(self.tr(title) + "  /  " + self.tr("İndirmeler"))
        for name, button in self.download_buttons.items():
            from .downloads import APPLICATIONS
            description = self.tr("{app} indirme sayfası", app=APPLICATIONS[name])
            button.set_tooltip_text(description)
            button.update_property([Gtk.AccessibleProperty.LABEL], [description])

    def on_close(self, *_):
        if not self._closed:
            self._closed = True
            self.updater.close()
            self.page_transition.close()
            self.selection_indicator.close()
            self.motion.close()
            if self._animation_signal is not None:
                self._gtk_settings.disconnect(self._animation_signal)
                self._animation_signal = None
            for page in (*self.pages.values(), *self.downloads.values()):
                page.close()
        return False


def save_screenshot(window, destination):
    paintable = Gtk.WidgetPaintable.new(window)
    snapshot = Gtk.Snapshot()
    paintable.snapshot(snapshot, window.get_width(), window.get_height())
    node = snapshot.to_node()
    if node is None:
        return False
    rectangle = Graphene.Rect()
    rectangle.init(0, 0, window.get_width(), window.get_height())
    texture = window.get_native().get_renderer().render_texture(node, rectangle)
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    return texture.save_to_png(str(destination))


def main():
    parser = argparse.ArgumentParser(description=APP_NAME + " native desktop application")
    parser.add_argument("--page", choices=[name for name, *_ in MODULES], default="doctor")
    parser.add_argument("--language", choices=("tr", "en"))
    parser.add_argument("--downloads", action="store_true", help="Open the selected module's download page")
    parser.add_argument("--screenshot", help="Render the selected page to a PNG, then exit")
    arguments = parser.parse_args()
    # Resolve the OS before GTK's event loop starts; navigation does no file IO.
    from .downloads import system_format
    package_format = system_format()
    application = Adw.Application(application_id="io.github.Tubix777.UzeyirDoctor", flags=Gio.ApplicationFlags.NON_UNIQUE)

    def activate(app):
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 20)
        preferences = Settings()
        if arguments.language:
            preferences.language = arguments.language
        window = MainWindow(app, preferences=preferences, initial=arguments.page, 
                            initial_view="downloads" if arguments.downloads else "dashboard", package_format=package_format)
        window.present()
        if arguments.screenshot:
            if arguments.page == "doctor" and not arguments.downloads:
                window.pages["doctor"].start_scan()
            started = GLib.get_monotonic_time()

            def render_ready():
                elapsed = (GLib.get_monotonic_time() - started) / 1_000_000
                page = (window.downloads if arguments.downloads else window.pages)[arguments.page]
                pending = getattr(page, "_busy", False) or getattr(page, "_polling", False) or getattr(page, "_scan_running", False)
                if elapsed < 3 or (pending and elapsed < 45):
                    return True
                if arguments.page == "doctor" and not arguments.downloads and getattr(page, "_motion_tick_id", None) is not None and elapsed < 47:
                    return True
                okay = save_screenshot(window, arguments.screenshot)
                window.on_close()
                app.quit()
                if not okay:
                    print("UI rendering did not produce an image", file=sys.stderr)
                return False
            GLib.timeout_add(100, render_ready)
    application.connect("activate", activate)
    return application.run([])


if __name__ == "__main__":
    raise SystemExit(main())
