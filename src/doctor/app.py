"""Native GTK 4 interface. All diagnostics run outside the UI thread."""
from __future__ import annotations

import argparse
import threading
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Graphene, Gtk
from . import __version__
from .core import Finding, check_app, list_flatpaks, scan


CSS = """
window { background: #080808; color: #f5f5f5; }
.hero { font-size: 30px; font-weight: 800; letter-spacing: -1px; }
.muted { color: #b3b3b3; }
.eyebrow { color: #d0d0d0; font-weight: 700; font-size: 12px; }
.card { background: #191919; border: 1px solid #383838; border-radius: 16px; padding: 18px; }
.card-title { font-size: 16px; font-weight: 700; }
.pill { border-radius: 10px; padding: 4px 9px; font-size: 11px; font-weight: 700; }
.ok { background: #2a2a2a; color: #dedede; }
.warning { background: #353535; color: #ffffff; border: 1px solid #777777; }
.critical { background: #454545; color: #ffffff; border: 1px solid #ededed; }
.info, .unknown { background: #272727; color: #d5d5d5; }
button { background-image: none; color: #f5f5f5; }
.primary { background: #363636; color: #ffffff; border: 1px solid #6b6b6b; border-radius: 12px; padding: 12px 22px; font-weight: 700; }
.primary:hover { background: #474747; }
.primary:active { background: #292929; }
.soft { background: #262626; border: 1px solid #3a3a3a; border-radius: 12px; padding: 10px 16px; }
.soft:hover { background: #353535; }
.soft:active { background: #202020; }
dropdown > button { background: #2a2a2a; border: 1px solid #414141; }
popover contents { background: #191919; color: #f5f5f5; }
listview row:selected { background: #414141; color: #ffffff; }
selection { background: #555555; color: #ffffff; }
:focus-visible { outline-color: #b8b8b8; }
.summary { background: #202020; border: 1px solid #343434; border-radius: 16px; padding: 18px; }
.evidence { color: #c5c5c5; font-family: monospace; font-size: 12px; }
.metric { font-size: 32px; font-weight: 800; }
.metric-bar trough { background: #333333; min-height: 6px; border: 0; border-radius: 8px; }
.metric-bar progress { background: #dddddd; min-height: 6px; border: 0; border-radius: 8px; }
headerbar { background: #080808; box-shadow: none; }
"""
STATUS = {"ok": "İyi", "warning": "Dikkat", "critical": "Önemli", "info": "Bilgi", "unknown": "Kontrol edilemedi"}


def label(text: str, css: str = "", wrap: bool = True) -> Gtk.Label:
    item = Gtk.Label(label=text, xalign=0, wrap=wrap)
    if css:
        item.add_css_class(css)
    return item


def box(spacing: int = 8, horizontal: bool = False) -> Gtk.Box:
    return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL if horizontal else Gtk.Orientation.VERTICAL, spacing=spacing)

