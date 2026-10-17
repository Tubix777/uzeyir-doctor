"""Update UI state, async lifecycle and authorization boundaries without installs."""
import tempfile
import threading
import time
import unittest
from pathlib import Path
import gi
gi.require_version("Gtk","4.0")
gi.require_version("Adw","1")
from gi.repository import Adw,Gdk,Gio,GLib,Gtk
from uzeyir_doctor.app import CSS,MainWindow
from uzeyir_doctor.settings import Settings
from uzeyir_doctor.update_ui import UpdateController
from uzeyir_doctor.updates import UpdateError,download_update,parse_updates
from test_updates import fixture


def pump(seconds=.03):
    context=GLib.MainContext.default();deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        for _ in range(100):
            if not context.pending():break
            context.iteration(False)
        time.sleep(.002)


def wait_for(predicate,timeout=3):
    end=time.monotonic()+timeout
    while not predicate() and time.monotonic()<end:pump(.01)
    if not predicate():raise AssertionError("Update callback did not arrive")


class Page(Gtk.Box):
    def __init__(self,*args):super().__init__()
    def set_active(self,*args):pass
    def sync_motion(self):pass
    def close(self):pass


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default(),"Private display required")
class UpdateUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()
        cls.app=Adw.Application(application_id="io.github.Tubix777.UpdateUITests",flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)
        cls.provider=Gtk.CssProvider();cls.provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),cls.provider,620)

    @classmethod
    def tearDownClass(cls):
        Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(),cls.provider)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)
        self.host=MainWindow(self.app,Settings(self.path/'preferences.json'),{name:Page for name in ('hardware','wheel','doctor')},package_format='deb')
        self.host.updater.close()
        data,self.bodies=fixture();self.offer=parse_updates([data],'deb','1.0.0');self.installs=[]
        outer=self
        class Installer:
            def __init__(self,finished,progress):self.finished,self.progress=finished,progress;self.closed=False
            def install(self,path):outer.installs.append((self,path))
            def close(self):self.closed=True
        def downloader(offer,cancel,progress,cache=None):
            import io
            return download_update(offer,cancel,progress,cache=cache,opener=lambda request,**kwargs:io.BytesIO(outer.bodies[request.full_url]))
        self.c=self.host.updater=UpdateController(self.host,checker=lambda kind:self.offer,downloader=downloader,
                        installer_factory=Installer,probe=lambda kind:self.offer.version,cache=self.path/'cache')
        self.host.present();wait_for(lambda:self.host.get_mapped())

    def tearDown(self):
        self.host.on_close();self.host.destroy();pump();self.temp.cleanup()

    def ready(self):
        self.c.check();wait_for(lambda:self.c.state=='available');self.c.download();wait_for(lambda:self.c.state=='ready')

    def test_no_install_until_explicit_request_and_verified_version_before_restart(self):
        self.ready();self.assertEqual(self.installs,[])
        self.c.install();wait_for(lambda:bool(self.installs))
        self.assertEqual(self.c.state,'installing')
        self.installs[0][0].finished('installed');wait_for(lambda:self.c.state=='installed')
        self.assertEqual(self.installs[0][1],self.c.package.path)

    def test_package_tampering_blocks_native_installer(self):
        self.ready();self.c.package.path.write_bytes(b'changed')
        self.c.install();wait_for(lambda:self.c.state=='error')
        self.assertEqual(self.installs,[]);self.assertIn('doğrulanamadı',self.c.message)

    def test_old_installed_version_is_never_reported_as_update_success(self):
        self.ready();self.c.probe=lambda kind:'1.0.0'
        self.c.install();wait_for(lambda:bool(self.installs));self.installs[0][0].finished('installed')
        wait_for(lambda:self.c.state=='external')
        self.assertIn('henüz doğrulanamadı',self.c.message)

    def test_denied_or_failed_install_does_not_claim_success(self):
        self.ready();self.c.install();wait_for(lambda:bool(self.installs));self.installs[0][0].finished('install_failed')
        self.assertEqual(self.c.state,'error')
        self.assertIsNotNone(self.c.package)

    def test_offline_retry_can_recover_without_installing(self):
        def failed(kind):raise UpdateError('network')
        self.c.checker=failed;self.c.check();wait_for(lambda:self.c.state=='error')
        self.c.checker=lambda kind:self.offer;self.c.check();wait_for(lambda:self.c.state=='available')
        self.assertEqual(self.installs,[])

    def test_pending_check_does_not_block_navigation_or_duplicate_requests(self):
        gate=threading.Event();entered=threading.Event();calls=[]
        def check(kind):calls.append(kind);entered.set();gate.wait(2);return self.offer
        self.c.checker=check
        try:
            self.c.check();self.assertTrue(entered.wait(.3));self.c.check()
            self.host.select_downloads('doctor');pump(.05)
            self.assertEqual(self.host.current_view,'downloads');self.assertEqual(calls,['deb'])
        finally:
            gate.set();wait_for(lambda:self.c.state=='available')

    def test_close_discards_pending_completion_and_startup_timer(self):
        gate=threading.Event();entered=threading.Event()
        def check(kind):entered.set();gate.wait(2);return self.offer
        self.c.checker=check;self.c.check();self.assertTrue(entered.wait(.3))
        self.host.preferences.check_updates_on_startup=True;self.c.schedule_startup();self.assertIsNotNone(self.c._startup)
        self.c.close();gate.set();pump(.1)
        self.assertIsNone(self.c._startup);self.assertIsNone(self.c.offer);self.assertEqual(self.c._listeners,[])

    def test_cancel_download_is_explicit_and_preserves_available_offer(self):
        entered=threading.Event()
        def downloader(offer,cancel,progress,cache=None):
            from uzeyir_doctor.updates import DownloadCancelled
            entered.set();cancel.wait(2);raise DownloadCancelled()
        self.c.downloader=downloader;self.c.check();wait_for(lambda:self.c.state=='available');self.c.download()
        self.assertTrue(entered.wait(.3));self.c.cancel_download();wait_for(lambda:self.c.state=='available')
        self.assertIs(self.c.offer,self.offer);self.assertIsNone(self.c.package);self.assertEqual(self.installs,[])

    def test_dialog_language_auto_preference_and_cleanup(self):
        baseline=len(self.host.motion._handlers)
        self.c.show();wait_for(lambda:self.c.dialog.get_mapped());dialog=self.c.dialog
        self.host.tr.set_language('en');self.assertEqual(dialog.primary.get_label(),'Check for updates')
        dialog.auto_switch.set_active(True)
        self.assertTrue(Settings(self.path/'preferences.json').check_updates_on_startup)
        dialog.close();wait_for(lambda:self.c.dialog is None)
        self.assertEqual(len(self.host.motion._handlers),baseline)
        self.assertFalse(dialog.spinner.get_spinning())

    def test_reduced_motion_stops_dialog_spinner_without_cancelling_check(self):
        gate=threading.Event();entered=threading.Event()
        def check(kind):entered.set();gate.wait(2);return None
        self.c.checker=check
        try:
            self.c.show();wait_for(lambda:self.c.dialog.get_mapped());self.c.check();self.assertTrue(entered.wait(.3))
            self.host.motion_switch.set_active(True)
            self.assertFalse(self.c.dialog.spinner.get_spinning());self.assertEqual(self.c.state,'checking')
        finally:
            gate.set();wait_for(lambda:self.c.state=='current')
