"""Small paint-only entrances: layout, focus and live input remain unchanged."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Graphene, Gtk


class MotionBox(Gtk.Box):
    """Translate child painting without resizing or rebuilding its controls."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entrance_offset = 0.0
        self.add_css_class("motion-enter")

    def set_entrance_offset(self, offset):
        self.entrance_offset = float(offset)
        self.queue_draw()

    def do_snapshot(self, snapshot):
        snapshot.save()
        point = Graphene.Point()
        point.init(0, self.entrance_offset)
        snapshot.translate(point)
        Gtk.Box.do_snapshot(self, snapshot)
        snapshot.restore()
