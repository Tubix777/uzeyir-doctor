"""PackageKit transaction lifecycle without contacting a system bus."""
import unittest
from gi.repository import GLib,Gio
from uzeyir_doctor.package_install import PackageInstaller,INTERFACE


class Reply:
    def unpack(self):return ('/fake_transaction',)


class Connection:
    def __init__(self):self.calls=[];self.removed=[];self.count=0
    def call(self,*args):self.calls.append(args)
    def call_finish(self,result):return Reply()
    def signal_subscribe(self,*args):self.count+=1;return self.count
    def signal_unsubscribe(self,identity):self.removed.append(identity)


class InstallerTests(unittest.TestCase):
    def test_install_uses_exact_verified_file_and_system_authorization(self):
        connection=Connection();installer=PackageInstaller(lambda status:None)
        installer.connection=connection;installer.package_path='/private/cache/app.deb'
        installer._transaction_ready(connection,None)
        installer._hints_ready(connection,None)
        call=connection.calls[-1]
        self.assertEqual(call[3],'InstallFiles')
        self.assertEqual(call[4].unpack(),(0,['/private/cache/app.deb']))
        self.assertEqual(call[6],Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION)

    def test_error_followed_by_finished_is_not_a_success(self):
        results=[];installer=PackageInstaller(results.append);installer.connection=Connection()
        installer._subscriptions=[1,2]
        installer._signal(None,None,None,None,'ErrorCode',GLib.Variant('(us)',(1,'denied')))
        installer._signal(None,None,None,None,'Finished',GLib.Variant('(uu)',(1,1)))
        installer._signal(None,None,None,None,'Finished',GLib.Variant('(uu)',(1,1)))
        self.assertEqual(results,['install_failed'])
        self.assertEqual(installer.connection.removed,[1,2])

    def test_finished_success_and_actual_percentage_are_reported(self):
        results=[];progress=[];installer=PackageInstaller(results.append,progress.append)
        installer._properties(None,None,None,None,None,GLib.Variant('(sa{sv}as)',(INTERFACE,{'Percentage':GLib.Variant('u',37)},[])))
        installer._signal(None,None,None,None,'Finished',GLib.Variant('(uu)',(1,1)))
        self.assertEqual(progress,[.37]);self.assertEqual(results,['installed'])

    def test_close_releases_signals_without_requesting_mid_commit_cancellation(self):
        results=[];installer=PackageInstaller(results.append);connection=installer.connection=Connection()
        installer._subscriptions=[4,5];installer.path='/fake_transaction';installer.close()
        self.assertEqual(connection.removed,[4,5]);self.assertEqual(connection.calls,[])
        installer._signal(None,None,None,None,'Finished',GLib.Variant('(uu)',(1,1)))
        self.assertEqual(results,[])

    def test_daemon_loss_and_timeout_request_verification_instead_of_success(self):
        results=[];installer=PackageInstaller(results.append)
        installer._owner_changed(None,None,None,None,None,GLib.Variant('(sss)',('org.freedesktop.PackageKit',':1.2','')))
        self.assertEqual(results,['unknown'])
        other=[];installer=PackageInstaller(other.append);installer._timeout()
        self.assertEqual(other,['unknown'])
