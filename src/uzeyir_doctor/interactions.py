"""Shared decorative motion, scheduled only while a transition is running."""
from __future__ import annotations
from contextlib import contextmanager

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


CSS = """
/* Keep geometry fixed while controls respond to pointer and keyboard input. */
.uzeyir-doctor-window button,
.uzeyir-doctor-window dropdown > button,
.uzeyir-doctor-window entry,
.uzeyir-doctor-window searchentry,
.uzeyir-doctor-window spinbutton,
.uzeyir-doctor-window switch,
.uzeyir-doctor-window switch slider,
.uzeyir-doctor-window checkbutton check,
.uzeyir-doctor-window scale slider,
.uzeyir-doctor-window scrollbar slider,
.uzeyir-doctor-window expander title,
.uzeyir-doctor-window listview row,
.uzeyir-doctor-window .card,
.uzeyir-doctor-window .summary {
  transition: background-color 160ms ease-out, border-color 160ms ease-out,
              box-shadow 160ms ease-out, color 160ms ease-out;
}
.uzeyir-doctor-window button:hover:not(:disabled) {
  box-shadow: inset 0 0 0 1px alpha(#ffffff, 0.25);
}
.uzeyir-doctor-window button:active:not(:disabled) {
  box-shadow: inset 0 0 0 2px alpha(#ffffff, 0.35);
}
.uzeyir-doctor-window button image {
  -gtk-icon-transform: scale(1);
  transition: -gtk-icon-transform 160ms ease-out;
}
.uzeyir-doctor-window button:hover:not(:disabled) image {
  -gtk-icon-transform: scale(1.035);
}
.uzeyir-doctor-window button:active:not(:disabled) image {
  -gtk-icon-transform: scale(0.97);
}
.uzeyir-doctor-window entry:focus-within,
.uzeyir-doctor-window searchentry:focus-within,
.uzeyir-doctor-window spinbutton:focus-within {
  border-color: #bdbdbd;
  box-shadow: inset 0 0 0 1px alpha(#ffffff, 0.18);
}
.uzeyir-doctor-window scale:hover:not(:disabled) slider,
.uzeyir-doctor-window scrollbar:hover slider {
  box-shadow: 0 0 0 3px alpha(#ffffff, 0.15);
}
.uzeyir-doctor-window button:focus-visible,
.uzeyir-doctor-window dropdown:focus-visible,
.uzeyir-doctor-window scale:focus-visible,
.uzeyir-doctor-window checkbutton:focus-visible,
.uzeyir-doctor-window switch:focus-visible,
.uzeyir-doctor-window expander:focus-visible {
  outline: 2px solid #cccccc;
  outline-offset: 2px;
}
@keyframes control-menu-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
.uzeyir-doctor-window popover contents {
  animation: control-menu-in 160ms ease-out;
}
.uzeyir-doctor-window .nav-row {
  transition: background-color 260ms ease-out, border-color 260ms ease-out;
}
.uzeyir-doctor-window .nav-download:hover image {
  -gtk-icon-transform: translate(0, 2px);
}
@keyframes control-completion-halo {
  from { box-shadow: 0 0 0 0 alpha(#ffffff, 0.25); }
  to { box-shadow: 0 0 0 6px alpha(#ffffff, 0); }
}
.uzeyir-doctor-window .operation-finished,
.uzeyir-doctor-window .copy-confirmed {
  animation: control-completion-halo 480ms ease-out;
}
.uzeyir-doctor-window.reduce-motion,
.uzeyir-doctor-window.reduce-motion * {
  transition: none;
  animation: none;
}
"""


class MotionController:
    """Own finite card fades and expansion transitions for one window.

    Scan-result cards keep their existing viewport-aware animation owner.
    No input values are interpolated and no periodic background timer is used.
    """
    def __init__(self, window, enabled=True):
        self.window = window
        self.enabled = enabled
        self._closed = False
        self._decorated = set()
        self._reveals = {}
        self._handlers = {}
        self._fades = {}
        self._tick_id = None
        self._order = 0
        self._navigating = False

    @contextmanager
    def navigation(self):
        """One page blend owns the entrance, rather than fading its cards twice."""
        self._navigating = True
        try:
            yield
        finally:
            self._navigating = False

    def decorate(self, root, _inside_entrance=False):
        if self._closed:
            return
        children = []
        child = root.get_first_child()
        while child:
            children.append(child)
            child = child.get_next_sibling()
        entrance = any(root.has_css_class(css) for css in ("card", "summary", "motion-enter"))
        candidate = isinstance(root, Gtk.Expander) or entrance
        if candidate and root not in self._decorated:
            self._decorated.add(root)
            if isinstance(root, Gtk.Expander):
                self._decorate_expander(root)
            if entrance and not _inside_entrance and not root.has_css_class("scan-result"):
                self._connect(root, "map", self._card_mapped)
                self._connect(root, "unmap", self._card_unmapped)
                if root.get_mapped():
                    self._card_mapped(root)
        for child in children:
            self.decorate(child, _inside_entrance or entrance)

    def _decorate_expander(self, expander):
        child = expander.get_child()
        parent = expander.get_parent()
        if child is None or not isinstance(parent, Gtk.Box):
            return
        # Keep the original keyboard-accessible expander header and API.
        # Its content lives in a sibling so closing can animate as well.
        expanded = expander.get_expanded()
        expander.set_child(None)
        reveal = Gtk.Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
            transition_duration=220 if self.enabled else 0,
            reveal_child=expanded,
            visible=expanded,
        )
        reveal.set_child(child)
        expander._motion_reveal = reveal
        parent.insert_child_after(reveal, expander)
        self._reveals[expander] = reveal
        self._connect(expander, "notify::expanded", self._expanded)
        self._connect(reveal, "notify::child-revealed", self._reveal_finished)

    def _connect(self, widget, signal, callback):
        self._handlers.setdefault(widget, []).append(widget.connect(signal, callback))

    def _expanded(self, expander, _param):
        reveal = self._reveals.get(expander)
        if reveal is not None and not self._closed:
            if expander.get_expanded():
                reveal.set_visible(True)
            reveal.set_reveal_child(expander.get_expanded())
            if not self.enabled and not expander.get_expanded():
                reveal.set_visible(False)

    def _reveal_finished(self, reveal, _param):
        if not reveal.get_reveal_child() and not reveal.get_child_revealed():
            reveal.set_visible(False)

    def _card_mapped(self, card):
        if self._closed or not self.enabled or self._navigating:
            self._settle(card)
            return
        if not self._fades:
            self._order = 0
        self._fades[card] = (None, min(self._order * 30000, 90000))
        self._order += 1
        card.set_opacity(0.7)
        if hasattr(card, "set_entrance_offset"):
            card.set_entrance_offset(8)
        if self._tick_id is None:
            self._tick_id = self.window.add_tick_callback(self._frame)

    def _card_unmapped(self, card):
        self._fades.pop(card, None)
        self._settle(card)
        if not self._fades:
            self._stop_tick()

    def _frame(self, _window, clock):
        now = clock.get_frame_time()
        for card, (started, delay) in tuple(self._fades.items()):
            if not self.enabled or self._closed or not card.get_mapped():
                self._settle(card)
                self._fades.pop(card, None)
                continue
            if started is None:
                started = now + delay
                self._fades[card] = (started, delay)
            progress = min(1, max(0, (now - started) / 280000))
            eased = 1 - (1 - progress) ** 3
            card.set_opacity(0.7 + 0.3 * eased)
            if hasattr(card, "set_entrance_offset"):
                card.set_entrance_offset(8 * (1 - eased))
            if progress >= 1:
                self._settle(card)
                self._fades.pop(card, None)
        if not self._fades:
            self._tick_id = None
            return False
        return True

    @staticmethod
    def _settle(widget):
        widget.set_opacity(1)
        if hasattr(widget, "set_entrance_offset"):
            widget.set_entrance_offset(0)

    def _stop_tick(self):
        if self._tick_id is not None:
            self.window.remove_tick_callback(self._tick_id)
            self._tick_id = None

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        for expander, reveal in tuple(self._reveals.items()):
            reveal.set_transition_duration(220 if self.enabled else 0)
            if not self.enabled:
                # A transition already in flight must finish immediately.
                target = expander.get_expanded()
                reveal.set_transition_type(Gtk.RevealerTransitionType.NONE)
                reveal.set_reveal_child(target)
                reveal.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
                if not target:
                    reveal.set_visible(False)
        if not self.enabled:
            self._stop_tick()
            for card in self._fades:
                self._settle(card)
            self._fades.clear()

    def forget(self, root):
        """Release old result widgets before their owner replaces the tree."""
        child = root.get_first_child()
        while child:
            following = child.get_next_sibling()
            self.forget(child)
            child = following
        for handler in self._handlers.pop(root, []):
            root.disconnect(handler)
        self._reveals.pop(root, None)
        self._decorated.discard(root)
        if root in self._fades:
            self._fades.pop(root)
            self._settle(root)
        if hasattr(root, "_motion_reveal"):
            del root._motion_reveal
        if not self._fades:
            self._stop_tick()

    def close(self):
        self.set_enabled(False)
        self._closed = True
        for widget, handlers in tuple(self._handlers.items()):
            for handler in handlers:
                widget.disconnect(handler)
            if hasattr(widget, "_motion_reveal"):
                del widget._motion_reveal
        self._reveals.clear()
        self._handlers.clear()
        self._decorated.clear()
