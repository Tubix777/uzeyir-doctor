"""An indeterminate scan signal, driven by the real operation's lifecycle."""
import math
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk


class ScanSignal(Gtk.DrawingArea):
    """A quiet idle diagram, an active sweep and one finite completion halo.

    This is decorative activity, never a progress or health measurement.
    Hidden, closed and reduced-motion views own no frame callback.
    """
    def __init__(self):
        super().__init__(content_width=116, content_height=80)
        self.set_can_target(False)
        self.set_accessible_role(Gtk.AccessibleRole.PRESENTATION)
        self._active = False
        self._running = False
        self._enabled = True
        self._closed = False
        self._tick_id = None
        self._phase = 0.0
        self._finished = None
        self._completion = None
        self._last_frame = 0
        self.set_draw_func(self._draw)
        self.connect("map", self._sync)
        self.connect("unmap", self._sync)

    def set_state(self, *, running=None, active=None, enabled=None):
        if running is not None:
            self._running = bool(running)
            self._finished = self._completion = None
        if active is not None:
            self._active = bool(active)
        if enabled is not None:
            self._enabled = bool(enabled)
        self._sync()

    def finish(self):
        self._running = False
        if self._active and self._enabled and self.get_mapped() and not self._closed:
            self._finished = GLib.get_monotonic_time()
            self._completion = 0.0
        self._sync()

    def _sync(self, *_):
        visible = self._active and self._enabled and self.get_mapped() and not self._closed
        if not visible:
            self._finished = self._completion = None
        needed = visible and (self._running or self._finished is not None)
        if needed and self._tick_id is None:
            self._last_frame = 0
            self._tick_id = self.add_tick_callback(self._frame)
        elif not needed and self._tick_id is not None:
            self.remove_tick_callback(self._tick_id)
            self._tick_id = None
        self.queue_draw()

    def _frame(self, _widget, clock):
        now = clock.get_frame_time()
        if self._last_frame and now - self._last_frame < 33000:
            return True
        self._last_frame = now
        self._phase = (now % 2200000) / 2200000 * math.tau
        if self._finished is not None:
            self._completion = min(1, max(0, (now - self._finished) / 720000))
            if self._completion >= 1:
                self._finished = self._completion = None
                self._tick_id = None
                self.queue_draw()
                return False
        self.queue_draw()
        return True

    def _draw(self, _area, cr, width, height):
        cr.translate(width / 2, height / 2)
        radius = min(width, height) * 0.33
        cr.set_line_width(1)
        for ring in (radius * 0.5, radius):
            cr.set_source_rgba(0.8, 0.8, 0.8, 0.18)
            cr.arc(0, 0, ring, 0, math.tau)
            cr.stroke()
        for index in range(4):
            angle = math.tau * index / 4 + 0.35
            cr.set_source_rgba(0.9, 0.9, 0.9, 0.25)
            cr.move_to(math.cos(angle) * 5, math.sin(angle) * 5)
            cr.line_to(math.cos(angle) * radius, math.sin(angle) * radius)
            cr.stroke()
            cr.arc(math.cos(angle) * radius, math.sin(angle) * radius, 2, 0, math.tau)
            cr.fill()
        cr.set_source_rgba(0.94, 0.94, 0.94, 0.8)
        cr.arc(0, 0, 3, 0, math.tau)
        cr.fill()
        if self._running and self._enabled and self._active:
            cr.set_line_width(2)
            cr.set_source_rgba(0.96, 0.96, 0.96, 0.8)
            cr.arc(0, 0, radius, self._phase, self._phase + 1.1)
            cr.stroke()
            cr.set_source_rgba(0.9, 0.9, 0.9, 0.12)
            cr.move_to(0, 0)
            cr.arc(0, 0, radius, self._phase - 0.6, self._phase + 0.5)
            cr.close_path()
            cr.fill()
        if self._completion is not None:
            cr.set_source_rgba(0.96, 0.96, 0.96, (1 - self._completion) * 0.8)
            cr.arc(0, 0, radius * (0.5 + self._completion * 0.8), 0, math.tau)
            cr.stroke()

    def close(self):
        self._closed = True
        self._running = False
        self._sync()
