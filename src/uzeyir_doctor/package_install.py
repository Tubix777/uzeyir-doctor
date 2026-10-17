"""Optional existing PackageKit service; no helper, shell or policy is installed."""
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

SERVICE = "org.freedesktop.PackageKit"
INTERFACE = SERVICE + ".Transaction"


class PackageInstaller:
    """One user-requested transaction, authorized by the desktop's normal agent."""
    def __init__(self, finished, progress=lambda value: None):
        self.finished = finished
        self.progress = progress
        self.connection = None
        self.path = None
        self._subscriptions = []
        self._closed = False
        self._done = False
        self._error = None
        self._timeout_id = None
        self.cancellable = Gio.Cancellable()

    def install(self, path):
        if self._closed:
            return
        self.package_path = str(path)
        self._timeout_id = GLib.timeout_add_seconds(600, self._timeout)
        Gio.bus_get(Gio.BusType.SYSTEM, self.cancellable, self._bus_ready)

    def _bus_ready(self, _source, result):
        if self._closed:
            return
        try:
            self.connection = Gio.bus_get_finish(result)
        except GLib.Error:
            self._finish("unavailable")
            return
        self.connection.call(SERVICE, "/org/freedesktop/PackageKit", SERVICE, "CreateTransaction",
                             None, GLib.VariantType.new("(o)"), Gio.DBusCallFlags.NONE, 15_000,
                             self.cancellable, self._transaction_ready)

    def _transaction_ready(self, connection, result):
        if self._closed:
            return
        try:
            self.path = connection.call_finish(result).unpack()[0]
        except GLib.Error:
            self._finish("unavailable")
            return
        self._subscriptions.append(connection.signal_subscribe(SERVICE, INTERFACE, None, self.path, None,
                                    Gio.DBusSignalFlags.NONE, self._signal))
        self._subscriptions.append(connection.signal_subscribe(SERVICE, "org.freedesktop.DBus.Properties",
                                    "PropertiesChanged", self.path, None, Gio.DBusSignalFlags.NONE, self._properties))
        self._subscriptions.append(connection.signal_subscribe("org.freedesktop.DBus", "org.freedesktop.DBus",
                                    "NameOwnerChanged", "/org/freedesktop/DBus", SERVICE,
                                    Gio.DBusSignalFlags.NONE, self._owner_changed))
        connection.call(SERVICE, self.path, INTERFACE, "SetHints", GLib.Variant("(as)", (["interactive=true"],)),
                        None, Gio.DBusCallFlags.NONE, 10_000, self.cancellable, self._hints_ready)

    def _hints_ready(self, connection, result):
        if self._closed:
            return
        try:
            connection.call_finish(result)
        except GLib.Error:
            self._finish("install_failed")
            return
        # No global signature setting is changed. These exact release bytes were
        # already verified against both the asset digest and SHA256SUMS. Local
        # unsigned-package installation still requires PackageKit authorization.
        connection.call(SERVICE, self.path, INTERFACE, "InstallFiles",
                        GLib.Variant("(tas)", (0, [self.package_path])), None,
                        Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, 120_000,
                        self.cancellable, self._accepted)

    def _accepted(self, connection, result):
        if self._closed or self._done:
            return
        try:
            connection.call_finish(result)
        except GLib.Error:
            self._finish("install_failed")

    def _signal(self, _connection, _sender, _path, _interface, signal, parameters):
        if self._closed or self._done:
            return
        values = parameters.unpack()
        if signal == "ErrorCode":
            self._error = "install_failed"
        elif signal == "Finished":
            self._finish("installed" if values[0] == 1 and self._error is None else "install_failed")

    def _properties(self, _connection, _sender, _path, _interface, _signal, parameters):
        if self._closed or self._done:
            return
        interface, changed, _invalid = parameters.unpack()
        value = changed.get("Percentage") if interface == INTERFACE else None
        if type(value) is int and 0 <= value <= 100:
            self.progress(value / 100)

    def _owner_changed(self, _connection, _sender, _path, _interface, _signal, parameters):
        _name, previous, current = parameters.unpack()
        if previous and not current:
            self._finish("unknown")

    def _timeout(self):
        self._timeout_id = None
        self._finish("unknown")
        return GLib.SOURCE_REMOVE

    def _finish(self, status):
        if self._done or self._closed:
            return
        self._done = True
        self._unsubscribe()
        self.finished(status)

    def _unsubscribe(self):
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
        if self.connection is not None:
            for identity in self._subscriptions:
                self.connection.signal_unsubscribe(identity)
        self._subscriptions.clear()

    def close(self):
        self._closed = True
        self._unsubscribe()
        # Do not request cancellation during a package manager's commit phase.
        # An already-running system transaction can complete independently.
