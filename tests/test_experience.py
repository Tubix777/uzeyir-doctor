"""Standalone navigation and feedback regressions on a private GTK display."""
import tempfile
import time
import unittest
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Graphene, Gtk
from uzeyir_doctor.app import CSS, MainWindow
from uzeyir_doctor.settings import Settings


def pump(seconds=.03):
    deadline = time.monotonic() + seconds
    context = GLib.MainContext.default()
    while time.monotonic() < deadline:
        for _ in range(100):
            if not context.pending():
                break
            context.iteration(False)
        time.sleep(.002)


def wait_for(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        pump(.01)
    if not predicate():
        raise AssertionError("Transition did not settle")


class EditablePage(Gtk.Box):
    def __init__(self, host, translator, settings):
        super().__init__()
        self.entry = Gtk.Entry(text="Pending input")
        self.card = Gtk.Box(css_classes=["card"])
        self.card.append(self.entry)
        self.append(self.card)
        self.active = False

    def set_active(self, active):
        self.active = active

    def sync_motion(self):
        pass

    def close(self):
        pass


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default(), "Private display required")
class ExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()
        cls.app = Adw.Application(application_id="io.github.Tubix777.DoctorExperienceTests", flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)
        cls.provider = Gtk.CssProvider()
        cls.provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), cls.provider, 620)

    @classmethod
    def tearDownClass(cls):
        Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(), cls.provider)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.desktop = Gtk.Settings.get_default()
        self.previous = self.desktop.get_property("gtk-enable-animations")
        self.desktop.set_property("gtk-enable-animations", True)
        self.window = MainWindow(self.app, Settings(Path(self.temp.name)/"preferences.json"), {"doctor": EditablePage})
        self.window.present()
        wait_for(lambda: self.window.page_transition.get_width() > 100)
        pump(.6)
        self.deck = self.window.page_transition

    def tearDown(self):
        self.window.on_close()
        self.window.destroy()
        self.desktop.set_property("gtk-enable-animations", self.previous)
        pump()
        self.temp.cleanup()

    def test_visible_blend_has_intermediate_frames_and_releases_picture(self):
        self.window.select_downloads("doctor")
        self.assertIsNotNone(self.deck._picture)
        values = []
        while self.deck._tick_id is not None:
            values.append(self.deck._progress)
            pump(.025)
        self.assertGreater(len(set(round(v,2) for v in values)), 4)
        self.assertIsNone(self.deck._picture)
        self.assertEqual(self.deck._offset, (0,0))
        self.assertIsNone(self.window.motion._tick_id)

    def test_repeated_navigation_keeps_latest_choice_and_unsaved_input(self):
        page = self.window.pages["doctor"]
        for index in range(8):
            self.window.select_page("doctor", "downloads" if index % 2 == 0 else "dashboard")
            pump(.04)
        self.assertIs(self.window.stack.get_visible_child(), page)
        self.assertEqual(page.entry.get_text(), "Pending input")
        self.assertEqual(page.card.get_opacity(), 1)
        wait_for(lambda: self.deck._tick_id is None)
        self.assertIsNone(self.deck._picture)

    def test_motion_reduction_and_desktop_preference_settle_immediately(self):
        self.window.select_downloads("doctor")
        pump(.06)
        self.desktop.set_property("gtk-enable-animations", False)
        self.assertIsNone(self.deck._tick_id)
        self.assertEqual(self.deck._offset, (0,0))
        self.window.select_page("doctor")
        self.assertIsNone(self.deck._tick_id)
        self.desktop.set_property("gtk-enable-animations", True)
        self.window.motion_switch.set_active(True)
        self.window.select_downloads("doctor")
        self.assertIsNone(self.deck._tick_id)

    def test_resize_hide_and_close_release_callbacks(self):
        self.window.select_downloads("doctor")
        self.window.set_default_size(1000,700)
        wait_for(lambda: self.window.get_width() <= 1050)
        self.assertIsNone(self.deck._picture)
        self.window.select_page("doctor")
        self.window.set_visible(False)
        self.assertIsNone(self.deck._tick_id)
        self.window.present()
        pump(.1)
        self.window.select_downloads("doctor")
        self.window.on_close()
        self.assertIsNone(self.deck._tick_id)
        self.assertFalse(self.deck.navigate("doctor"))

    def test_copy_feedback_and_focus_survive_rebuild_without_old_timers(self):
        self.window.select_downloads("doctor")
        pump(.5)
        page = self.window.downloads["doctor"]
        key, button = next((key,button) for key,button in page._action_widgets.items() if key[1]=="copy")
        button.grab_focus()
        button.emit("clicked")
        self.assertEqual(button.get_label(), "Kopyalandı")
        button.emit("clicked")
        self.assertEqual(len(page._copy_feedback),1)
        page.render_assets()
        self.assertEqual(page._copy_feedback,{})
        self.assertIs(self.window.get_focus(),page._action_widgets[key])
        self.window.tr.set_language("en")
        self.assertEqual(page._action_widgets[key].get_label(),"Copy")
        self.assertIs(self.window.get_focus(),page._action_widgets[key])

    def test_stylesheet_parses_without_errors(self):
        errors=[]
        provider=Gtk.CssProvider()
        provider.connect("parsing-error", lambda _p,_s,error: errors.append(str(error)))
        provider.load_from_string(CSS)
        self.assertEqual(errors,[])

    def painted_bytes(self):
        snapshot=Gtk.Snapshot()
        self.deck.do_snapshot(snapshot)
        rect=Graphene.Rect()
        rect.init(0,0,self.deck.get_width(),self.deck.get_height())
        texture=self.window.get_renderer().render_texture(snapshot.to_node(),rect)
        return bytes(texture.save_to_png_bytes().get_data())

    def test_first_frame_and_interruption_preserve_displayed_pixels(self):
        before=self.painted_bytes()
        self.window.select_downloads("doctor")
        self.assertEqual(self.painted_bytes(),before)
        pump(.12)
        middle=self.painted_bytes()
        self.window.select_page("doctor")
        self.assertEqual(self.painted_bytes(),middle)
