"""Local typography and shared native page components."""
from __future__ import annotations

import ctypes
from ctypes.util import find_library
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gio, Gtk, PangoCairo
from .entrance import MotionBox

RESOURCES = Path(__file__).parent / "resources"
CSS = (RESOURCES / "theme.css").read_text(encoding="utf-8")
_font_loaded = False


def load_font():
    """Register the bundled OFL font in this process only; keep system fonts intact."""
    global _font_loaded
    if _font_loaded:
        return True
    try:
        library = find_library("fontconfig")
        if not library:
            return False
        config = ctypes.CDLL(library)
        config.FcConfigGetCurrent.restype = ctypes.c_void_p
        config.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        config.FcConfigAppFontAddFile.restype = ctypes.c_int
        current = config.FcConfigGetCurrent()
        if not current or not config.FcConfigAppFontAddFile(current, bytes(RESOURCES / "Manrope.ttf")):
            return False
        PangoCairo.FontMap.get_default().changed()
        _font_loaded = True
        return True
    except (OSError, AttributeError):
        return False


def icon(name, size=20):
    image = Gtk.Image()
    file = Gio.File.new_for_path(str(RESOURCES / (name + ".svg")))
    def refresh(widget, *_):
        widget.set_from_paintable(Gtk.IconPaintable.new_for_file(file, size, widget.get_scale_factor()))
    refresh(image)
    image.connect("notify::scale-factor", refresh)
    image.set_pixel_size(size)
    return image


def text(tr, source, css="", wrap=True):
    widget = Gtk.Label(xalign=0, wrap=wrap)
    if css:
        widget.add_css_class(css)
    tr.bind(widget, source)
    return widget


def heading(tr, eyebrow, title, description, illustration=None):
    hero = MotionBox(spacing=24)
    hero.add_css_class("module-hero")
    copy = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, hexpand=True)
    copy.append(text(tr, eyebrow, "eyebrow"))
    copy.append(text(tr, title, "hero"))
    copy.append(text(tr, description, "hero-description"))
    hero.append(copy)
    if illustration is not None:
        illustration.set_valign(Gtk.Align.CENTER)
        hero.append(illustration)
    return hero
