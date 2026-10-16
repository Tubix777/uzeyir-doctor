"""Embedded diagnostics; all system probes run off the GTK thread."""
from __future__ import annotations
import threading
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk
from doctor import __version__
from doctor.core import Finding, check_app, list_flatpaks, scan
from doctor.app import STATUS, box, label as make_label
from uzeyir_doctor.design import heading
from uzeyir_doctor.entrance import MotionBox
from uzeyir_doctor.activity import ScanSignal


class DoctorPage(Gtk.Box):
    def __init__(self, host, translator, settings):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.host, self.tr, self.preferences = host, translator, settings
        self.add_css_class("doctor-page")
        self._closed = False
        self._active = False
        self._findings = None
        self._summary_source = "Henüz tarama yapılmadı. İlk kontrol birkaç saniye sürer."
        def label(text, css="", wrap=True):
            return self.tr.bind(make_label(text, css, wrap), text)
        self.apps = []
        self.folder = None
        self.screenshot = None
        self._busy = False
        self._motion_tick_id = None
        self._auto_scroll = False
        self._scroll_started = None
        self._scroll_from = 0.0
        self._cards = []
        self._fade_started = {}
        self._revealed = set()
        scroll = self.scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        content = self.content = box(22)
        scroll.get_vadjustment().connect("value-changed", self.viewport_changed)
        scroll.get_vadjustment().connect("changed", self.viewport_changed)
        wheel = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        wheel.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        wheel.connect("scroll", self.manual_scroll)
        scroll.add_controller(wheel)
        pointer = Gtk.GestureClick.new()
        pointer.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        pointer.connect("pressed", lambda *_: self.interrupt_auto_scroll())
        scroll.add_controller(pointer)
        keys = Gtk.EventControllerKey.new()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.navigation_key)
        scroll.add_controller(keys)
        for method in (content.set_margin_top, content.set_margin_bottom,
                       content.set_margin_start, content.set_margin_end):
            method(28)
        scroll.set_child(content)
        clamp = Adw.Clamp(hexpand=True, unit=Adw.LengthUnit.PX, maximum_size=1120, tightening_threshold=950)
        clamp.set_child(scroll)
        self.append(clamp)
        self.scan_signal = ScanSignal()
        content.append(heading(self.tr, "UZEYIR DOCTOR", "Sorunu gör. Çözümü bul.",
                              "Sistemini tara; ne olduğunu ve sonraki adımı açıkça gör.", self.scan_signal))
        actions = box(12, True)
        self.scan_button = Gtk.Button(label="Sistemi tara")
        self.tr.bind(self.scan_button, "Sistemi tara")
        self.scan_button.add_css_class("primary")
        self.scan_button.connect("clicked", lambda *_: self.start_scan())
        actions.append(self.scan_button)
        self.spinner = Gtk.Spinner(visible=False)
        actions.append(self.spinner)
        actions.append(label("Yerel çalışır · Sistem ayarlarını değiştirmez", "muted"))
        content.append(actions)
        overview = box(16)
        overview.add_css_class("card")
        overview.add_css_class("scan-overview")
        stats = box(24, True)
        self.scan_counts = {}
        for key, title in (("checks", "Tamamlanan kontrol"), ("alerts", "Dikkat gerektiren"), ("unknown", "Doğrulanamayan")):
            column = box(5)
            column.set_hexpand(True)
            number = Gtk.Label(label="—", xalign=0)
            number.add_css_class("scan-count")
            column.append(number)
            column.append(label(title, "muted"))
            stats.append(column)
            self.scan_counts[key] = number
        overview.append(stats)
        self.summary = label("Henüz tarama yapılmadı. İlk kontrol birkaç saniye sürer.", "muted")
        overview.append(self.summary)
        content.append(overview)
        app_panel = box(10)
        app_panel.add_css_class("card")
        app_panel.append(label("Bir uygulamada sorun mu var?", "card-title"))
        app_panel.append(label("Kurulu Flatpak uygulamasını seç. İstersen erişemediği klasörü de kontrol et.", "muted"))
        app_controls = box(10, True)
        self.app_model = Gtk.StringList.new(["Uygulamalar yükleniyor…"])
        self.dropdown = Gtk.DropDown(model=self.app_model, hexpand=True)
        self.dropdown.set_tooltip_text("Kontrol edilecek Flatpak uygulaması")
        app_controls.append(self.dropdown)
        self.folder_button = Gtk.Button(label="Klasör seç")
        self.tr.bind(self.folder_button, "Klasör seç")
        self.folder_button.add_css_class("soft")
        self.folder_button.connect("clicked", self.choose_folder)
        app_controls.append(self.folder_button)
        self.app_button = Gtk.Button(label="Uygulamayı kontrol et")
        self.tr.bind(self.app_button, "Uygulamayı kontrol et")
        self.app_button.add_css_class("soft")
        self.app_button.set_sensitive(False)
        self.app_button.connect("clicked", self.start_app)
        app_controls.append(self.app_button)
        app_panel.append(app_controls)
        self.folder_label = label("Klasör seçimi isteğe bağlıdır.", "muted")
        app_panel.append(self.folder_label)
        content.append(app_panel)
        results_header = self.results_header = box(16, True)
        title = label("Tarama sonuçları", "section-title")
        title.set_hexpand(True)
        results_header.append(title)
        self.filter_button = Gtk.ToggleButton(sensitive=False)
        self.tr.bind(self.filter_button, "Dikkat gerektirenler")
        self.filter_button.add_css_class("soft")
        self.filter_button.connect("toggled", self.filter_changed)
        results_header.append(self.filter_button)
        content.append(results_header)
        self.results = box(14)
        content.append(self.results)
        empty = box(8)
        empty.add_css_class("doctor-empty")
        empty.append(label("İlk kontrolü başlat.", "card-title"))
        empty.append(label("Disk, SSD, servisler, ağ ve depolar için bulgular burada görünecek.", "muted"))
        self.results.append(empty)
        content.append(label("Kontroller bu bilgisayarda çalışır. Sonuçlar dışarı gönderilmez.", "download-notice"))
        self.tr.connect(self.retranslate)
        self.background(list_flatpaks, self.set_apps)

    def background(self, task, callback):
        def worker():
            try:
                value = task()
            except Exception:
                value = None
            def deliver():
                if not self._closed:
                    callback(value)
                return False
            GLib.idle_add(deliver)
        threading.Thread(target=worker, daemon=True).start()

    def set_apps(self, apps):
        index = self.dropdown.get_selected()
        previous = self.apps[index] if index < len(self.apps) else None
        self.apps = apps or []
        self.app_model.splice(0, self.app_model.get_n_items(),
            [f"{name} · {self.tr('kişisel') if scope == 'user' else self.tr('sistem') if scope == 'system' else scope}" for _, name, scope in self.apps]
            or [self.tr("Kurulu Flatpak uygulaması bulunamadı")])
        if previous:
            selected = next((i for i, item in enumerate(self.apps)
                             if (item[0], item[2]) == (previous[0], previous[2])), 0)
            self.dropdown.set_selected(selected)
        self.dropdown.set_sensitive(bool(self.apps) and not self._busy)
        self.app_button.set_sensitive(bool(self.apps) and not self._busy)
        return False

    def choose_folder(self, *_):
        dialog = Gtk.FileDialog(title=self.tr("Kontrol edilecek klasör"))
        dialog.select_folder(self.host, None, self.folder_chosen)

    def folder_chosen(self, dialog, result):
        try:
            selected = dialog.select_folder_finish(result)
            path = selected.get_path()
            if not path:
                self.folder_label.set_label(self.tr("Yalnız yerel klasörler kontrol edilebilir."))
                return
            self.folder = path
            self.folder_button.set_label(self.tr("Klasörü değiştir"))
            self.folder_label.set_label(self.tr("Seçilen klasör: {name}", name=selected.get_basename()))
        except GLib.Error:
            pass

    def busy(self, value):
        self._busy = value
        self.scan_button.set_sensitive(not value)
        self.app_button.set_sensitive(not value and bool(self.apps))
        self.dropdown.set_sensitive(not value and bool(self.apps))
        self.folder_button.set_sensitive(not value)
        self.filter_button.set_sensitive(not value and self._findings is not None)
        self.spinner.set_visible(value)
        self.scan_signal.set_state(running=value)
        self.sync_motion()

    def start_scan(self):
        if self._closed or self._busy:
            return
        self.cancel_motion()
        self.busy(True)
        self._summary_source = "Sistem kontrol ediliyor…"
        self.summary.set_label(self.tr(self._summary_source))
        self.background(scan, self.show_findings)

    def start_app(self, *_):
        if self._closed or self._busy:
            return
        index = self.dropdown.get_selected()
        if index >= len(self.apps):
            return
        app_id, name, scope = self.apps[index]
        folder = self.folder
        self.cancel_motion()
        self.busy(True)
        self._summary_source = name + " kontrol ediliyor…"
        self.summary.set_label(self.tr.dynamic(self._summary_source))
        self.background(lambda: check_app(app_id, scope, folder), self.show_findings)

    def show_findings(self, findings, *, auto_scroll=True):
        completed = self._busy and findings is not None
        self.cancel_motion()
        if hasattr(self.host, "motion"):
            self.host.motion.forget(self.results)
        self.busy(False)
        if completed:
            self.scan_signal.finish()
        while self.results.get_first_child():
            self.results.remove(self.results.get_first_child())
        if findings is None:
            findings = [Finding("Tarama tamamlanamadı", "unknown", "Bir kontrol sırasında hata oluştu. Tekrar taramayı deneyebilirsin.")]
        alerts = sum(item.status in ("warning", "critical") for item in findings)
        unknown = sum(item.status == "unknown" for item in findings)
        self._findings = list(findings)
        for key, value in (("checks", len(findings)), ("alerts", alerts), ("unknown", unknown)):
            self.scan_counts[key].set_label(str(value))
        self.filter_button.set_sensitive(True)
        self._summary_source = f"{len(findings)} kontrol tamamlandı · {alerts} dikkat gerektiren bulgu · {unknown} kontrol edilemeyen alan"
        self.summary.set_label(self.tr.dynamic(self._summary_source))
        order = {"critical": 0, "warning": 1, "unknown": 2, "ok": 3, "info": 4}
        def finding_order(item):
            priority = 0 if item.status in ("critical", "warning") else 1 if item.metric is not None else 2
            return priority, order[item.status]
        def label(text, css="", wrap=True):
            return make_label(self.tr.dynamic(text), css, wrap)
        visible_findings = [item for item in findings if not self.filter_button.get_active()
                            or item.status in ("warning", "critical", "unknown")]
        if not visible_findings:
            empty = MotionBox(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            empty.add_css_class("doctor-empty")
            empty.add_css_class("scan-result")
            empty.append(label("Dikkat gerektiren bulgu yok.", "card-title"))
            empty.append(label("Diğer kontrolleri görmek için filtreyi kapatabilirsin.", "muted"))
            self.results.append(empty)
            self._cards.append(empty)
        for item in sorted(visible_findings, key=finding_order):
            card = MotionBox(orientation=Gtk.Orientation.VERTICAL, spacing=9)
            card.add_css_class("card")
            card.add_css_class("scan-result")
            heading = box(10, True)
            title = label(item.title, "card-title")
            title.set_hexpand(True)
            heading.append(title)
            pill = label(STATUS[item.status], "pill")
            pill.add_css_class(item.status)
            heading.append(pill)
            card.append(heading)
            if item.metric is not None:
                metric_row = box(12, True)
                percentage = f"{item.metric:g}%" if self.tr.language == "en" else f"%{item.metric:g}"
                metric_row.append(label(percentage, "metric"))
                metric_caption = label(item.metric_label, "muted")
                metric_caption.set_hexpand(True)
                metric_caption.set_wrap(False)
                metric_row.append(metric_caption)
                card.append(metric_row)
                meter = Gtk.ProgressBar(fraction=max(0.0, min(1.0, item.metric / 100)))
                meter.add_css_class("metric-bar")
                card.append(meter)
            card.append(label(item.explanation))
            details = box(8)
            details.append(label(item.certainty, "muted"))
            for evidence in item.evidence:
                details.append(label(evidence, "evidence"))
            if item.steps:
                details.append(label("Ne yapabilirsin?", "card-title"))
                for index, step in enumerate(item.steps, 1):
                    details.append(label(f"{index}. {step}"))
            expander = Gtk.Expander(label=self.tr("Kanıt ve çözüm adımları"))
            expander.set_child(details)
            card.append(expander)
            self.results.append(card)
            self._cards.append(card)
        if hasattr(self.host, "motion"):
            self.host.motion.decorate(self.results)
        if self.animations_enabled():
            for card in self._cards:
                card.set_opacity(0)
                card.set_entrance_offset(18)
        self._auto_scroll = self._active and auto_scroll
        if self._active:
            self.queue_motion()
        else:
            for index, card in enumerate(self._cards):
                card.set_opacity(1)
                card.set_entrance_offset(0)
                self._revealed.add(index)
        return False

    def filter_changed(self, *_):
        if self._closed or self._busy or self._findings is None:
            return
        self.show_findings(self._findings, auto_scroll=False)

    def animations_enabled(self):
        settings = Gtk.Settings.get_default()
        return bool(not self.preferences.reduced_motion and settings and settings.get_property("gtk-enable-animations"))

    def queue_motion(self, *_):
        if self._motion_tick_id is None and self._cards:
            self._motion_tick_id = self.add_tick_callback(self.motion_frame)

    def viewport_changed(self, *_):
        if len(self._revealed) < len(self._cards):
            self.queue_motion()

    def interrupt_auto_scroll(self):
        self._auto_scroll = False
        self._scroll_started = None

    def manual_scroll(self, *_):
        self.interrupt_auto_scroll()
        return False

    def navigation_key(self, _controller, key, _code, _state):
        if key in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Page_Up, Gdk.KEY_Page_Down,
                   Gdk.KEY_Home, Gdk.KEY_End, Gdk.KEY_space):
            self.interrupt_auto_scroll()
        return False

    def cancel_motion(self):
        if self._motion_tick_id is not None:
            self.remove_tick_callback(self._motion_tick_id)
            self._motion_tick_id = None
        for card in self._cards:
            card.set_opacity(1)
            card.set_entrance_offset(0)
        self._cards = []
        self._fade_started = {}
        self._revealed = set()
        self._auto_scroll = False
        self._scroll_started = None

    def close_motion(self, *_):
        self.cancel_motion()
        return False

    def motion_frame(self, _widget, clock):
        adjustment = self.scroll.get_vadjustment()
        allocated, bounds = self.results_header.compute_bounds(self.content)
        # Tick callbacks precede layout. Wait for the new result cards to allocate.
        if not allocated or not self._cards or self._cards[0].get_height() <= 0:
            return True
        now = clock.get_frame_time()
        target = max(adjustment.get_lower(), min(bounds.get_y() - 24,
                     adjustment.get_upper() - adjustment.get_page_size()))
        if not self.animations_enabled():
            if self._auto_scroll:
                adjustment.set_value(target)
            for index, card in enumerate(self._cards):
                card.set_opacity(1)
                card.set_entrance_offset(0)
                self._revealed.add(index)
            self._auto_scroll = False
            self._motion_tick_id = None
            return False
        if self._auto_scroll:
            if self._scroll_started is None:
                self._scroll_started = now
                self._scroll_from = adjustment.get_value()
            progress = min(1.0, max(0.0, (now - self._scroll_started) / 1050000))
            eased = 1 - (1 - progress) ** 3
            adjustment.set_value(self._scroll_from + (target - self._scroll_from) * eased)
            if progress >= 1:
                self._auto_scroll = False
        top = adjustment.get_value()
        bottom = top + adjustment.get_page_size()
        visible_order = 0
        fading = False
        for index, card in enumerate(self._cards):
            if index in self._revealed:
                continue
            found, card_bounds = card.compute_bounds(self.content)
            visible = found and card_bounds.get_y() < bottom - 8 and card_bounds.get_y() + card_bounds.get_height() > top + 8
            if visible and index not in self._fade_started:
                self._fade_started[index] = now + min(visible_order * 70000, 210000)
                visible_order += 1
            if index in self._fade_started:
                progress = min(1.0, max(0.0, (now - self._fade_started[index]) / 420000))
                card.set_opacity(1 - (1 - progress) ** 3)
                card.set_entrance_offset(18 * (1 - progress) ** 3)
                if progress >= 1:
                    self._revealed.add(index)
                else:
                    fading = True
        if self._auto_scroll or fading:
            return True
        self._motion_tick_id = None
        return False

    def set_active(self, active):
        self._active = active
        self.sync_motion()
        if not active:
            if self._motion_tick_id is not None:
                self.remove_tick_callback(self._motion_tick_id)
                self._motion_tick_id = None
            self.interrupt_auto_scroll()
            for index, card in enumerate(self._cards):
                card.set_opacity(1)
                card.set_entrance_offset(0)
                self._revealed.add(index)

    def retranslate(self):
        self.set_apps(self.apps)
        self.folder_button.set_label(self.tr("Klasörü değiştir" if self.folder else "Klasör seç"))
        if self.folder:
            from pathlib import Path
            self.folder_label.set_label(self.tr("Seçilen klasör: {name}", name=Path(self.folder).name))
        self.summary.set_label(self.tr.dynamic(self._summary_source))
        if self._findings is not None and not self._busy:
            scroll_value = self.scroll.get_vadjustment().get_value()
            self.show_findings(self._findings, auto_scroll=False)
            self.interrupt_auto_scroll()
            self.scroll.get_vadjustment().set_value(scroll_value)

    def sync_motion(self):
        enabled = self.animations_enabled()
        self.scan_signal.set_state(active=self._active, enabled=enabled)
        self.spinner.set_spinning(self._busy and self._active and enabled and not self._closed)
        if not self.animations_enabled() and self._active:
            self.queue_motion()

    def close(self):
        self._closed = True
        self.scan_signal.close()
        self.spinner.stop()
        self.cancel_motion()
        self.tr.disconnect(self.retranslate)
