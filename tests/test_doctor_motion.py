"""GTK integration checks; run under an isolated virtual display.

All diagnostics are replaced with queued callbacks: these tests never scan the
host or launch another instance of the user's running application.
"""
from __future__ import annotations

import time
import unittest
from unittest.mock import patch

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from doctor.app import CSS
from uzeyir_doctor.pages.doctor import DoctorPage as Window
from uzeyir_doctor.i18n import Translator
from uzeyir_doctor.settings import Settings
from doctor.core import Finding


def findings(count: int) -> list[Finding]:
    return [Finding(f"Test kontrolü {index + 1}", "warning",
                    "Bu, gerçek sistem bilgisi kullanmayan bir test açıklamasıdır.")
            for index in range(count)]


def pump(seconds: float = 0.02) -> None:
    context = GLib.MainContext.default()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for _ in range(100):
            if not context.pending():
                break
            context.iteration(False)
        time.sleep(0.005)


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default() is not None, "GTK display unavailable; use a virtual display")
class ScanMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()
        cls.application = Adw.Application(
            application_id="io.github.fedoradoctor.MotionTests",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        cls.application.register(None)
        cls.provider = Gtk.CssProvider()
        cls.provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), cls.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        cls.settings = Gtk.Settings.get_default()
        cls.original_animations = cls.settings.get_property("gtk-enable-animations")

    @classmethod
    def tearDownClass(cls):
        cls.settings.set_property("gtk-enable-animations", cls.original_animations)
        Gtk.StyleContext.remove_provider_for_display(
            Gdk.Display.get_default(), cls.provider)
        cls.application.quit()

    def setUp(self):
        self.settings.set_property("gtk-enable-animations", True)
        self.jobs = []

        def queue_background(window, task, callback):
            self.jobs.append((task, callback))

        self.background_patch = patch.object(Window, "background", queue_background)
        self.background_patch.start()
        self.host = Adw.ApplicationWindow(application=self.application)
        self.host.set_default_size(1040, 740)
        self.window = Window(self.host, Translator(), Settings(path="/tmp/uzeyir-doctor-unused-test-preferences"))
        self.window.set_active(True)
        self.host.set_content(self.window)
        self.host.present()
        self.window.set_apps([])
        self.wait_for(lambda: self.window.get_height() > 0, "initial window allocation")
        pump(0.08)

    def tearDown(self):
        self.window.close()
        self.host.close()
        pump(0.03)
        self.assertIsNone(self.window._motion_tick_id)
        self.background_patch.stop()
        self.settings.set_property("gtk-enable-animations", self.original_animations)

    def wait_for(self, predicate, description, timeout=4.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            pump()
        self.fail(f"Timed out waiting for {description}")

    def finish_motion(self):
        self.wait_for(lambda: self.window._motion_tick_id is None
                      and not self.window._auto_scroll, "scroll and reveal to settle")

    def visible_cards(self):
        adjustment = self.window.scroll.get_vadjustment()
        top = adjustment.get_value()
        bottom = top + adjustment.get_page_size()
        visible = []
        for index, card in enumerate(self.window._cards):
            success, bounds = card.compute_bounds(self.window.content)
            if (success and bounds.get_y() < bottom - 8
                    and bounds.get_y() + bounds.get_height() > top + 8):
                visible.append((index, card))
        return visible

    def test_scroll_moves_down_within_bounds_and_visible_cards_become_opaque(self):
        adjustment = self.window.scroll.get_vadjustment()
        initial = adjustment.get_value()
        self.window.show_findings(findings(12))
        samples = []
        fade_samples = []
        deadline = time.monotonic() + 4
        while self.window._motion_tick_id is not None and time.monotonic() < deadline:
            pump(0.025)
            value = adjustment.get_value()
            samples.append(value)
            fade_samples.append(self.window._cards[0].get_opacity())
            self.assertGreaterEqual(value, adjustment.get_lower() - 0.01)
            self.assertLessEqual(value, adjustment.get_upper() - adjustment.get_page_size() + 0.01)
        self.assertIsNone(self.window._motion_tick_id)
        self.assertGreater(adjustment.get_value(), initial + 10)
        self.assertGreater(len({round(value, 1) for value in samples}), 3,
                           "scroll should travel through intermediate positions")
        self.assertTrue(any(0 < opacity < 1 for opacity in fade_samples),
                        "visible cards should fade through intermediate opacity")
        self.assertTrue(self.visible_cards())
        allocated, heading = self.window.results_header.compute_bounds(self.window.content)
        self.assertTrue(allocated)
        self.assertGreaterEqual(heading.get_y(), adjustment.get_value())
        self.assertLessEqual(heading.get_y() + heading.get_height(),
                             adjustment.get_value() + adjustment.get_page_size())
        for index, card in self.visible_cards():
            self.assertEqual(card.get_opacity(), 1)
            self.assertIn(index, self.window._revealed)

    def test_scan_signal_tracks_pending_job_and_reduction_without_fake_progress(self):
        signal = self.window.scan_signal
        self.assertIsNone(signal._tick_id)
        self.window.start_scan()
        self.wait_for(lambda: signal._tick_id is not None, "real pending scan signal")
        count = len(self.jobs)
        self.window.start_scan()
        self.assertEqual(len(self.jobs), count)
        self.window.set_active(False)
        self.assertIsNone(signal._tick_id)
        self.window.set_active(True)
        self.window.preferences.reduced_motion = True
        self.window.sync_motion()
        self.assertIsNone(signal._tick_id)
        self.assertFalse(self.window.spinner.get_spinning())
        self.assertTrue(self.window._busy)
        self.window.show_findings(findings(2))
        self.assertFalse(signal._running)
        self.finish_motion()
        self.assertTrue(all(card.entrance_offset == 0 for card in self.window._cards))

    def test_filter_rebuild_does_not_show_operation_completion_animation(self):
        self.window.show_findings(findings(2), auto_scroll=False)
        self.assertIsNone(self.window.scan_signal._tick_id)
        self.window.filter_button.set_active(True)
        self.assertIsNone(self.window.scan_signal._tick_id)

    def test_unseen_cards_reveal_when_user_scrolls_later(self):
        self.window.show_findings(findings(12))
        self.finish_motion()
        unseen = set(range(12)) - self.window._revealed
        self.assertTrue(unseen, "fixture must contain cards below the viewport")
        last = self.window._cards[-1]
        self.assertEqual(last.get_opacity(), 0)
        adjustment = self.window.scroll.get_vadjustment()
        adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
        # GTK quantizes opacity; it can read as 1 shortly before the fade ends.
        self.wait_for(lambda: 11 in self.window._revealed, "last card to reveal")
        self.assertEqual(last.get_opacity(), 1)
        self.assertIn(11, self.window._revealed)

    def test_unseen_cards_reveal_when_the_viewport_grows(self):
        self.window.show_findings(findings(12))
        self.finish_motion()
        old_visible = {index for index, _ in self.visible_cards()}
        self.host.set_default_size(1040, 1200)
        self.wait_for(lambda: self.host.get_height() >= 1100, "viewport to grow")
        pump(0.1)
        newly_visible = {index for index, _ in self.visible_cards()} - old_visible
        self.assertTrue(newly_visible, "fixture must expose more cards after resizing")
        self.wait_for(lambda: newly_visible <= self.window._revealed,
                      "newly visible cards to reveal after resizing")

    def test_manual_cancellation_stops_automatic_drift(self):
        self.window.show_findings(findings(12))
        adjustment = self.window.scroll.get_vadjustment()
        self.wait_for(lambda: adjustment.get_value() > 20, "scroll to begin")
        self.assertTrue(self.window._auto_scroll)
        self.assertFalse(self.window.manual_scroll(None, 0, 1))
        frozen = adjustment.get_value()
        pump(1.15)
        self.assertFalse(self.window._auto_scroll)
        self.assertAlmostEqual(adjustment.get_value(), frozen, delta=0.1)
        for _, card in self.visible_cards():
            self.assertEqual(card.get_opacity(), 1)

    def test_navigation_key_cancels_without_consuming_the_event(self):
        self.window.show_findings(findings(12))
        adjustment = self.window.scroll.get_vadjustment()
        self.wait_for(lambda: adjustment.get_value() > 20, "scroll to begin")
        self.assertFalse(self.window.navigation_key(None, Gdk.KEY_Page_Down, 0, 0))
        frozen = adjustment.get_value()
        pump(0.2)
        self.assertFalse(self.window._auto_scroll)
        self.assertAlmostEqual(adjustment.get_value(), frozen, delta=0.1)

    def test_new_scan_and_replacement_discard_old_animation_effects(self):
        self.window.show_findings(findings(12))
        self.wait_for(lambda: self.window.scroll.get_vadjustment().get_value() > 20,
                      "old animation to begin")
        old_cards = list(self.window._cards)
        self.window.start_scan()
        self.assertTrue(self.window._busy)
        self.assertTrue(self.window.spinner.get_spinning())
        self.assertIsNone(self.window._motion_tick_id)
        self.assertEqual(self.window._cards, [])
        self.assertTrue(all(card.get_opacity() == 1 for card in old_cards))
        _, completion = self.jobs[-1]
        completion(findings(3))
        self.finish_motion()
        self.assertFalse(self.window._busy)
        self.assertFalse(self.window.spinner.get_spinning())
        self.assertEqual(len(self.window._cards), 3)
        self.assertTrue(all(card.get_parent() is None for card in old_cards))
        self.assertTrue(all(card.get_opacity() == 1 for card in self.window._cards))

    def test_reduced_motion_shows_every_card_without_fades(self):
        self.settings.set_property("gtk-enable-animations", False)
        self.window.show_findings(findings(12))
        self.assertTrue(all(card.get_opacity() == 1 for card in self.window._cards))
        self.finish_motion()
        self.assertEqual(self.window._revealed, set(range(12)))
        self.assertFalse(self.window._auto_scroll)

    def test_short_results_do_not_scroll_past_the_available_content(self):
        self.host.set_default_size(1040, 1400)
        self.wait_for(lambda: self.host.get_height() >= 1300, "tall test window")
        self.window.show_findings(findings(1))
        self.finish_motion()
        adjustment = self.window.scroll.get_vadjustment()
        self.assertAlmostEqual(adjustment.get_upper(), adjustment.get_page_size(), delta=1)
        self.assertAlmostEqual(adjustment.get_value(), 0, delta=0.1)
        self.assertEqual(self.window._cards[0].get_opacity(), 1)


if __name__ == "__main__":
    unittest.main()
