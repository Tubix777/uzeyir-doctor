"""Short, interruptible page transitions on GTK's frame clock.

Only the outgoing picture is retained. The incoming page stays live, with its
normal focus, input and accessibility tree. No screenshots or GPU readbacks are
made; GTK keeps the immutable paintable on the rendering side.
"""
from __future__ import annotations

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Graphene, Gsk, Gtk


def ease_out(progress):
    return 1 - (1 - min(1.0, max(0.0, progress))) ** 3


class PageTransition(Gtk.Box):
    """Blend from the last displayed frame, including an interrupted transition.

The child is allocated with its transform so pointer picking follows what is
painted. Resizing, unmapping and motion reduction settle synchronously.
"""
    DURATION_US = 300_000
    DISTANCE = 16.0

    def __init__(self, stack, enabled=True):
        super().__init__(hexpand=True, vexpand=True)
        self.set_layout_manager(None)
        self.set_overflow(Gtk.Overflow.HIDDEN)
        self.stack = stack
        self.append(stack)
        stack.set_transition_type(Gtk.StackTransitionType.NONE)
        stack.set_transition_duration(0)
        self.enabled = bool(enabled)
        self._closed = False
        self._picture = None
        self._last_picture = None
        self._tick_id = None
        self._started = None
        self._progress = 1.0
        self._direction = (0, 1)
        self._offset = (0.0, 0.0)
        self._size = None
        self.connect("unmap", self._unmapped)

    def do_get_request_mode(self):
        return self.stack.get_request_mode()

    def do_measure(self, orientation, for_size):
        return self.stack.measure(orientation, for_size)

    def do_size_allocate(self, width, height, baseline):
        if self._size is not None and self._size != (width, height):
            self.settle()
            self._last_picture = None
        self._size = (width, height)
        point = Graphene.Point()
        point.init(*self._offset)
        transform = Gsk.Transform.new().translate(point)
        self.stack.allocate(width, height, baseline, transform)

    def do_snapshot(self, snapshot):
        # Keep the last *painted* frame. A new WidgetPaintable can be empty when
        # sibling style changes have queued an allocation during navigation.
        frame = Gtk.Snapshot()
        if self._picture is None:
            self.snapshot_child(self.stack, frame)
        elif self._progress <= 0:
            self._picture.snapshot(frame, self.get_width(), self.get_height())
        else:
            frame.push_cross_fade(self._progress)
            frame.save()
            point = Graphene.Point()
            drift = -self.DISTANCE * 0.3 * self._progress
            point.init(self._direction[0] * drift, self._direction[1] * drift)
            frame.translate(point)
            self._picture.snapshot(frame, self.get_width(), self.get_height())
            frame.restore()
            frame.pop()
            self.snapshot_child(self.stack, frame)
            frame.pop()
        size = Graphene.Size()
        size.init(self.get_width(), self.get_height())
        self._last_picture = frame.to_paintable(size)
        if self._last_picture is not None:
            self._last_picture.snapshot(snapshot, self.get_width(), self.get_height())

    def navigate(self, name, direction=(0, 1)):
        if self._closed or self.stack.get_child_by_name(name) is None:
            return False
        if self.stack.get_visible_child_name() == name:
            return False
        picture = None
        if self.enabled and self.get_mapped() and self.get_width() > 0:
            picture = self._last_picture
        self.settle()
        self._picture = picture
        self._direction = direction
        self._progress = 0.0 if picture is not None else 1.0
        self._offset = tuple(value * self.DISTANCE * (1 - self._progress) for value in direction)
        self.stack.set_visible_child_name(name)
        if picture is not None:
            self._tick_id = self.add_tick_callback(self._frame)
        self.queue_allocate()
        self.queue_draw()
        return True

    def _frame(self, _widget, clock):
        now = clock.get_frame_time()
        if self._started is None:
            self._started = now
        progress = min(1.0, max(0.0, (now - self._started) / self.DURATION_US))
        self._progress = ease_out(progress)
        self._offset = tuple(value * self.DISTANCE * (1 - self._progress) for value in self._direction)
        if progress >= 1:
            self._tick_id = None
            self.settle()
            return False
        self.queue_allocate()
        self.queue_draw()
        return True

    def settle(self):
        if self._tick_id is not None:
            self.remove_tick_callback(self._tick_id)
            self._tick_id = None
        self._picture = None
        self._started = None
        self._progress = 1.0
        self._offset = (0.0, 0.0)
        self.queue_allocate()
        self.queue_draw()

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        if not self.enabled:
            self.settle()

    def _unmapped(self, *_):
        self.settle()
        self._last_picture = None

    def close(self):
        self._closed = True
        self.settle()
        self._last_picture = None


class SelectionIndicator(Gtk.DrawingArea):
    """A single pill that follows the selected menu row, including rapid clicks."""
    def __init__(self, rows, enabled=True):
        super().__init__(can_target=False, halign=Gtk.Align.START, hexpand=False)
        self.set_content_width(4)
        self.set_accessible_role(Gtk.AccessibleRole.PRESENTATION)
        self.rows = rows
        self.enabled = bool(enabled)
        self.target = None
        self._y = self._from = 0.0
        self._height = 20.0
        self._started = None
        self._tick_id = None
        self.set_draw_func(self._draw)
        self.connect("map", lambda *_: self.select(self.target, animate=False))
        self.connect("unmap", lambda *_: self.settle())

    def _target_y(self):
        if self.target is None:
            return self._y
        okay, bounds = self.target.compute_bounds(self.rows)
        return bounds.get_y() + (bounds.get_height() - self._height) / 2 if okay else self._y

    def select(self, row, *, animate=True):
        self.target = row
        self._from = self._y
        self._started = None
        if self.enabled and animate and self.get_mapped():
            if self._tick_id is None:
                self._tick_id = self.add_tick_callback(self._frame)
        else:
            self.settle()

    def _frame(self, _widget, clock):
        if self._started is None:
            self._started = clock.get_frame_time()
        progress = min(1.0, (clock.get_frame_time() - self._started) / 260_000)
        self._y = self._from + (self._target_y() - self._from) * ease_out(progress)
        self.queue_draw()
        if progress >= 1:
            self._tick_id = None
            return False
        return True

    def _draw(self, _widget, cr, width, height):
        if self.target is None:
            return
        if self._tick_id is None:
            self._y = self._target_y()
        cr.set_source_rgba(0.94, 0.94, 0.94, 0.9)
        cr.set_line_width(3)
        cr.set_line_cap(1)
        cr.move_to(width / 2, self._y + 2)
        cr.line_to(width / 2, self._y + self._height - 2)
        cr.stroke()

    def settle(self):
        if self._tick_id is not None:
            self.remove_tick_callback(self._tick_id)
            self._tick_id = None
        self._started = None
        self._y = self._target_y()
        self.queue_draw()

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        if not self.enabled:
            self.settle()

    def close(self):
        self.settle()
