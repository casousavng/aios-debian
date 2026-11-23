#!/usr/bin/env python3
"""AI-OS Native macOS-style Spotlight launcher & AI command bar."""
import glob
import html
import json
import os
import re
import signal
import subprocess
import threading
import urllib.request
from pathlib import Path

import cairo
import gi
import markdown
from i18n import get_config, get_lang, set_lang, t, update_config

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

WebKit2 = None

REPLY_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  html, body { background: transparent; margin: 0; padding: 0; color: #f1f5f9;
    font-family: system-ui, -apple-system, sans-serif; font-size: 13px; line-height: 1.5;
    overflow-wrap: anywhere; word-break: break-word; max-width: 100%; overflow-x: hidden; }
  body { padding: 4px 10px 16px 6px; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.40); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(103, 232, 249, 0.65); }
  h1, h2, h3 { color: #ffffff; margin: 0.6em 0 0.3em; font-size: 14px; font-weight: 650; }
  p { margin: 0.35em 0; }
  ul, ol { margin: 0.35em 0; padding-left: 1.3em; }
  li { margin: 0.15em 0; }
  strong { color: #ffffff; }
  code { background: rgba(103, 232, 249, 0.14); color: #67e8f9; padding: 1px 5px;
    border-radius: 5px; font-family: monospace; font-size: 12px; }
  pre { background: rgba(10, 14, 20, 0.55); border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px; padding: 8px 10px; overflow-x: auto; margin: 0.45em 0; }
  pre code { background: transparent; padding: 0; color: #e2e8f0; }
  table { border-collapse: collapse; width: 100%; margin: 0.4em 0; font-size: 12px; }
  th, td { border: 1px solid rgba(255,255,255,0.14); padding: 4px 8px; text-align: left; }
  th { background: rgba(255,255,255,0.08); color: #ffffff; }
  a { color: #67e8f9; text-decoration: none; }
  .msg-row { display: flex; width: 100%; margin: 6px 0; }
  .msg-user { justify-content: flex-end; }
  .msg-ai { justify-content: flex-start; }
  .bubble { max-width: 92%; padding: 8px 12px; border-radius: 14px; }
  .bubble-user { background: rgba(103, 232, 249, 0.16); border: 1px solid rgba(103, 232, 249, 0.36); color: #f8fafc; border-bottom-right-radius: 4px; }
  .bubble-ai { background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); color: #e2e8f0; border-bottom-left-radius: 4px; }
  .bubble p:first-child { margin-top: 0; }
  .bubble p:last-child { margin-bottom: 0; }
</style></head><body>%BODY%</body></html>"""

API_BASE = "http://127.0.0.1:8765"
HOME = Path.home()
HISTORY_FILE = HOME / ".ai-os" / "history.json"
SEARCH_DIRS = [HOME / "Desktop", HOME / "Documentos", HOME / "Projetos", HOME / "Downloads"]

CSS = b"""
window.spotlight-win, window.topbar-win {
    background-color: transparent;
}
.topbar {
    background-color: rgba(20, 26, 34, 0.42);
    border-bottom: 1px solid rgba(255, 255, 255, 0.16);
    padding: 0 14px;
}
.topbar-logo {
    color: #7dd3fc;
    font-size: 14px;
    font-weight: 700;
    margin: 0;
    padding: 0;
}
button.win-dot {
    background-image: none;
    background-color: transparent;
    border: none;
    box-shadow: none;
    color: rgba(241, 245, 249, 0.70);
    font-size: 12px;
    font-weight: 500;
    border-radius: 6px;
    padding: 0 8px;
    margin: 0 2px;
    min-width: 0;
    min-height: 0;
}
button.win-dot:hover {
    background-image: none;
    background-color: rgba(255, 255, 255, 0.10);
    color: #ffffff;
}
button.win-dot-active {
    background-image: none;
    background-color: rgba(255, 255, 255, 0.12);
    border: none;
    color: #7dd3fc;
}
.topbar-item {
    color: #f8fafc;
    font-size: 12px;
    font-weight: 500;
    margin-left: 12px;
}
.popover-card {
    background-color: rgba(20, 26, 34, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.24);
    border-radius: 14px;
    padding: 12px 14px;
}
.pop-title {
    color: #f8fafc;
    font-size: 12px;
    font-weight: 600;
}
.pop-sub {
    color: #94a3b8;
    font-size: 11px;
}
button.status-trigger {
    background-image: none;
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0 2px;
    margin: 0;
    min-width: 0;
    min-height: 0;
}
button.status-trigger:hover, button.status-trigger:active {
    background-image: none;
    background: transparent;
    border: none;
    box-shadow: none;
}
.spotlight-card {
    background-image: linear-gradient(180deg, rgba(255, 255, 255, 0.16) 0%, rgba(20, 26, 34, 0.08) 100%);
    background-color: rgba(16, 21, 29, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.30);
    border-radius: 22px;
    padding: 7px 16px;
}
.draft-letter,
textview.draft-letter,
textview.draft-letter text {
    background-color: transparent;
    background-image: none;
    color: #e2e8f0;
    font-size: 13px;
}
.draft-card {
    background-color: rgba(15, 20, 28, 0.55);
    border: 1px solid rgba(103, 232, 249, 0.25);
    border-radius: 12px;
    padding: 6px 10px;
}
.search-row {
    padding: 2px 4px;
}
scrollbar.mini-scroll, scrollbar.mini-scroll trough {
    background: transparent;
    border: none;
    min-width: 6px;
    min-height: 0;
}
scrollbar.mini-scroll slider {
    background-color: rgba(103, 232, 249, 0.55);
    border-radius: 3px;
    min-width: 4px;
    min-height: 8px;
}
.search-icon,
button.search-icon {
    background: transparent;
    background-image: none;
    border: none;
    box-shadow: none;
    color: #67e8f9;
    font-size: 20px;
    font-weight: 700;
    padding: 0;
    margin: 0 8px 0 0;
    min-width: 0;
    min-height: 0;
}
button.search-icon:hover {
    background: transparent;
    color: #a5f3fc;
}
textview.search-input, textview.search-input text {
    background: transparent;
    color: #ffffff;
    font-size: 15px;
    caret-color: #67e8f9;
}
scrolledwindow.clean-scroll, scrolledwindow.clean-scroll border,
scrolledwindow.clean-scroll undershoot, scrolledwindow.clean-scroll overshoot {
    border: none;
    box-shadow: none;
    background: transparent;
    background-image: none;
}
.search-placeholder {
    color: rgba(241, 245, 249, 0.55);
    font-size: 15px;
}
.keycap-badge {
    color: #f1f5f9;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 10px;
    background-color: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.28);
    margin-right: 6px;
}
button.send-arrow {
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.22);
    box-shadow: none;
    color: #ffffff;
    font-size: 15px;
    padding: 0 10px;
    min-height: 28px;
    border-radius: 10px;
}
button.chat-pill {
    background: rgba(103, 232, 249, 0.14);
    border: 1px solid rgba(103, 232, 249, 0.34);
    box-shadow: none;
    color: #67e8f9;
    font-size: 12px;
    font-weight: 600;
    padding: 0 10px;
    min-height: 28px;
    border-radius: 10px;
}
button.chat-tab {
    background-image: none;
    background-color: rgba(20, 26, 34, 0.88);
    border: 1px solid rgba(103, 232, 249, 0.30);
    border-bottom: none;
    border-radius: 10px 10px 0 0;
    color: #67e8f9;
    font-size: 10px;
    padding: 0 18px;
    min-height: 15px;
    min-width: 0;
    box-shadow: none;
}
button.chat-tab:hover {
    background-color: rgba(103, 232, 249, 0.22);
    color: #ffffff;
}
button.chat-pill:hover,
button.send-arrow:hover {
    background-color: rgba(103, 232, 249, 0.28);
    color: #ffffff;
}
.divider {
    background-color: rgba(255, 255, 255, 0.18);
    min-height: 1px;
    margin: 4px 6px;
}
list.results-list {
    background: transparent;
}
list.results-list row {
    padding: 8px 12px;
    border-radius: 12px;
    border: 1px solid transparent;
    margin: 2px 4px;
    color: #f8fafc;
}
list.results-list row:selected {
    background-color: rgba(255, 255, 255, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.25);
    color: #ffffff;
}
.row-icon {
    color: #67e8f9;
    font-size: 16px;
    margin-right: 10px;
}
.row-title {
    font-size: 14px;
    font-weight: 600;
}
.row-sub {
    font-size: 11px;
    color: rgba(241, 245, 249, 0.78);
}
.ai-reply-box {
    background-color: rgba(15, 23, 42, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 14px;
    padding: 8px 12px 10px 12px;
    margin: 4px 6px 6px 6px;
}
.reply-actions {
    margin-bottom: 4px;
}
button.reply-btn {
    background-image: none;
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 11px;
    padding: 2px 8px;
    min-height: 0;
    min-width: 0;
}
button.reply-btn:hover {
    background-color: rgba(103, 232, 249, 0.22);
    color: #ffffff;
}
.ai-reply-text {
    color: #ffffff;
    font-size: 13px;
}
"""

SYSTEM_ACTIONS = [
    ("Terminal", "Abrir consola (xterm)", "utilities-terminal", lambda: subprocess.Popen(["xterm"])),
    ("Ficheiros", "Abrir gestor de ficheiros (PCManFM)", "system-file-manager", lambda: subprocess.Popen(["pcmanfm", str(HOME)])),
    ("Navegador", "Abrir Chromium", "web-browser", lambda: subprocess.Popen(["chromium"])),
    ("Estado do Sistema", "Ver CPU, RAM e disco", "utilities-system-monitor", "ask:Mostra resumo rápido de CPU, RAM e disco desta máquina."),
    ("Bloquear Ecrã", "Bloquear sessão (Super+L)", "system-lock-screen", lambda: subprocess.Popen(["/opt/ai-os/spotlight/lock.sh"])),
    ("Reiniciar VM", "Reiniciar o sistema", "system-reboot", lambda: subprocess.Popen(["sudo", "reboot"])),
    ("Desligar VM", "Desligar o sistema", "system-shutdown", lambda: subprocess.Popen(["sudo", "poweroff"])),
]


def clear_transparent(widget, ctx):
    ctx.set_operator(cairo.OPERATOR_SOURCE)
    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.paint()
    ctx.set_operator(cairo.OPERATOR_OVER)
    return False


IGNORED_DESKTOP_IDS = {
    "xterm.desktop",
    "debian-xterm.desktop",
    "debian-uxterm.desktop",
    "uxterm.desktop",
    "pcmanfm.desktop",
    "pcmanfm-desktop-pref.desktop",
    "chromium.desktop",
    "obconf.desktop",
    "picom.desktop",
    "vim.desktop",
    "htop.desktop",
}


def get_system_actions():
    return [
        (*t("act_terminal"), "utilities-terminal", lambda: subprocess.Popen(["xterm"])),
        (*t("act_files"), "system-file-manager", lambda: subprocess.Popen(["pcmanfm", str(HOME)])),
        (*t("act_browser"), "web-browser", lambda: subprocess.Popen(["chromium", "--remote-debugging-port=9222", "--remote-debugging-address=127.0.0.1"])),
        (*t("act_sysinfo"), "utilities-system-monitor", f"ask:{t('act_sysinfo_prompt')}"),
        (*t("act_lock"), "system-lock-screen", lambda: subprocess.Popen(["/opt/ai-os/spotlight/lock.sh"])),
        (*t("act_reboot"), "system-reboot", lambda: subprocess.Popen(["sudo", "reboot"])),
        (*t("act_poweroff"), "system-shutdown", lambda: subprocess.Popen(["sudo", "poweroff"])),
    ]


def get_slash_commands():
    return [
        ("/usage", t("slash_usage"), "ask_now:/usage"),
        ("/login", t("slash_login"), "local:login"),
        ("/logout", t("slash_logout"), "local:logout"),
        ("/model ", t("slash_model"), "fill:/model "),
        ("/mode ", t("slash_mode"), "fill:/mode "),
        ("/models", t("slash_models"), "ask_now:/models"),
        ("/agents", t("slash_agents"), "ask_now:/agents"),
        ("/mcp", t("slash_mcp"), "ask_now:/mcp"),
        ("/new", t("slash_new"), "ask_now:/new"),
        ("/clear", t("slash_clear"), "ask_now:/clear"),
        ("/compact", t("slash_compact"), "ask_now:/compact"),
        ("/plan ", t("slash_plan"), "fill:/plan "),
        ("/changelog", t("slash_changelog"), "ask_now:/changelog"),
        ("/help", t("slash_help"), "ask_now:/help"),
    ]


def get_system_commands():
    return [
        ("#chats", t("slash_chats"), "local:chats"),
        ("#apps", t("slash_apps"), "local:apps"),
        ("#audit", t("slash_audit"), "local:audit"),
        ("#clip", t("slash_clip"), "local:clip"),
        ("#screenshot", t("slash_screenshot"), "local:screenshot"),
        ("#displays", t("slash_displays"), "local:displays"),
        ("#lang ", t("slash_lang"), "fill:#lang "),
        ("#kb ", t("slash_kb"), "fill:#kb "),
        ("#tz ", t("slash_tz"), "fill:#tz "),
        ("#settings", t("slash_settings"), "local:settings"),
        ("#update", t("slash_update"), "local:update"),
        ("#lock", t("slash_lock"), "local:lock"),
        ("#reboot", t("act_reboot")[1], "local:reboot"),
        ("#poweroff", t("act_poweroff")[1], "local:poweroff"),
    ]


AGENT_MODES = [
    ("auto", "Execução autónoma direta / Autonomous execution"),
    ("accept-edits", "Aplica edições / Auto-apply edits"),
    ("plan", "Planeia antes / Plan before editing"),
]


def load_desktop_apps():
    apps = []
    seen = set()
    for folder in ("/usr/share/applications", str(HOME / ".local/share/applications")):
        for path in glob.glob(os.path.join(folder, "*.desktop")):
            if os.path.basename(path) in IGNORED_DESKTOP_IDS:
                continue
            name, exec_cmd, icon_name, hidden, is_terminal = None, None, "application-x-executable", False, False
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    in_entry = False
                    for line in f:
                        line = line.strip()
                        if line.startswith("["):
                            in_entry = line == "[Desktop Entry]"
                            continue
                        if not in_entry:
                            continue
                        if line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1]
                        elif line.startswith("Exec=") and not exec_cmd:
                            raw = line.split("=", 1)[1]
                            exec_cmd = " ".join(p for p in raw.split() if not p.startswith("%"))
                        elif line.startswith("Icon="):
                            icon_name = line.split("=", 1)[1]
                        elif line in ("NoDisplay=true", "Hidden=true"):
                            hidden = True
                        elif line == "Terminal=true":
                            is_terminal = True
                if name and exec_cmd and not hidden and not is_terminal and name.lower() not in seen:
                    seen.add(name.lower())
                    apps.append((name, exec_cmd, icon_name))
            except OSError:
                pass
    return apps


class WindowsPopover(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.connect("draw", clear_transparent)

        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.card.get_style_context().add_class("popover-card")
        self.card.set_size_request(260, -1)
        self.add(self.card)
        self._hovering = False
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("enter-notify-event", self._on_enter)
        self.connect("leave-notify-event", self._on_leave)

    def _on_enter(self, *_):
        self._hovering = True
        return False

    def _on_leave(self, _, event):
        if event.detail == Gdk.NotifyType.INFERIOR:
            return False
        self._hovering = False
        GLib.timeout_add(220, self._maybe_hide)
        return False

    def _maybe_hide(self):
        if not self._hovering and not getattr(self, "_trigger_hovering", False):
            self.hide()
        return False

    def show_at(self, geom, wins):
        if not self.is_visible():
            self.toggle_at(geom, wins)

    def toggle_at(self, geom, wins):
        if self.is_visible():
            self.hide()
            return
        for child in self.card.get_children():
            self.card.remove(child)

        hdr = Gtk.Label(label=t("open_windows"), xalign=0)
        hdr.get_style_context().add_class("pop-title")
        self.card.pack_start(hdr, False, False, 2)

        if not wins:
            empty = Gtk.Label(label=t("no_windows"), xalign=0)
            empty.get_style_context().add_class("pop-sub")
            self.card.pack_start(empty, False, False, 2)
        else:
            by_ws = {}
            for wid, ws_idx, app_name, title, is_active in wins:
                by_ws.setdefault(ws_idx, []).append((wid, app_name, title, is_active))
            for ws_idx in sorted(by_ws):
                ws_lbl = Gtk.Label(label=f"Desktop {ws_idx + 1}" if ws_idx >= 0 else "All", xalign=0)
                ws_lbl.get_style_context().add_class("pop-sub")
                self.card.pack_start(ws_lbl, False, False, 2)
                for wid, app_name, title, is_active in by_ws[ws_idx]:
                    low = app_name.lower()
                    if "chromium" in low:
                        icon_name = "web-browser"
                    elif "pcmanfm" in low:
                        icon_name = "system-file-manager"
                    elif "xterm" in low:
                        icon_name = "utilities-terminal"
                    elif "litemd" in low:
                        icon_name = "text-x-generic"
                    else:
                        icon_name = "application-x-executable"

                    btn = Gtk.Button()
                    btn.get_style_context().add_class("reply-btn")
                    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                    ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
                    ico.set_pixel_size(16)
                    lbl = Gtk.Label(label=title, xalign=0)
                    lbl.set_ellipsize(Pango.EllipsizeMode.END)
                    lbl.set_max_width_chars(30)
                    box.pack_start(ico, False, False, 0)
                    box.pack_start(lbl, True, True, 0)
                    if is_active:
                        dot = Gtk.Label(label="●")
                        dot.get_style_context().add_class("topbar-logo")
                        box.pack_end(dot, False, False, 0)
                    btn.add(box)
                    btn.connect("clicked", lambda _, w=wid: (self.hide(), subprocess.Popen(["wmctrl", "-i", "-a", w])))
                    self.card.pack_start(btn, False, False, 0)

        self.move(geom.x + 10, geom.y + 34)
        self.show_all()


class ControlPopover(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.connect("draw", clear_transparent)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("popover-card")
        card.set_size_request(290, -1)
        self.add(card)

        # Header: Date/Time + Timezone button
        hdr_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.dt_lbl = Gtk.Label(label="--", xalign=0)
        self.dt_lbl.get_style_context().add_class("pop-title")
        self.tz_btn = Gtk.Button(label=t("tz_btn"))
        self.tz_btn.get_style_context().add_class("reply-btn")
        self.tz_btn.connect("clicked", self._open_tz_dialog)
        hdr_row.pack_start(self.dt_lbl, True, True, 0)
        hdr_row.pack_end(self.tz_btn, False, False, 0)
        card.pack_start(hdr_row, False, False, 0)

        div1 = Gtk.Box()
        div1.get_style_context().add_class("divider")
        card.pack_start(div1, False, False, 0)

        # Section 1: Audio & Display
        self.sec1_lbl = Gtk.Label(label=t("sec_audio_display"), xalign=0)
        self.sec1_lbl.get_style_context().add_class("pop-sub")
        card.pack_start(self.sec1_lbl, False, False, 0)

        vol_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.vol_lbl = Gtk.Label(label=f"{t('volume')}: 70%", xalign=0)
        self.vol_lbl.get_style_context().add_class("pop-sub")
        vol_row.pack_start(self.vol_lbl, False, False, 0)
        card.pack_start(vol_row, False, False, 0)
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.vol_scale.set_value(70)
        self.vol_scale.set_draw_value(False)
        self.vol_scale.connect("value-changed", self.on_vol_changed)
        card.pack_start(self.vol_scale, False, False, 0)

        self.bri_lbl = Gtk.Label(label=f"{t('brightness')}: 100%", xalign=0)
        self.bri_lbl.get_style_context().add_class("pop-sub")
        card.pack_start(self.bri_lbl, False, False, 0)
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 5)
        self.bri_scale.set_value(100)
        self.bri_scale.set_draw_value(False)
        self.bri_scale.connect("value-changed", self.on_bri_changed)
        card.pack_start(self.bri_scale, False, False, 0)

        self.audio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        card.pack_start(self.audio_box, False, False, 0)

        div2 = Gtk.Box()
        div2.get_style_context().add_class("divider")
        card.pack_start(div2, False, False, 0)

        # Section 2: Connections
        self.sec2_lbl = Gtk.Label(label=t("sec_conn"), xalign=0)
        self.sec2_lbl.get_style_context().add_class("pop-sub")
        card.pack_start(self.sec2_lbl, False, False, 0)

        self.wifi_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        card.pack_start(self.wifi_box, False, False, 0)

        self.bt_btn = Gtk.Button(label=f"{t('bt_label')}: Toggle")
        self.bt_btn.get_style_context().add_class("reply-btn")
        self.bt_btn.connect("clicked", self._on_bt_toggle)
        card.pack_start(self.bt_btn, False, False, 0)

        self.bt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        card.pack_start(self.bt_box, False, False, 0)

        div3 = Gtk.Box()
        div3.get_style_context().add_class("divider")
        card.pack_start(div3, False, False, 0)

        # Section 3: System 2x2 quick actions
        self.sec3_lbl = Gtk.Label(label=t("sec_sys"), xalign=0)
        self.sec3_lbl.get_style_context().add_class("pop-sub")
        card.pack_start(self.sec3_lbl, False, False, 0)

        grid = Gtk.Grid(column_spacing=6, row_spacing=6, column_homogeneous=True)
        self.displays_btn = Gtk.Button(label=t("displays_short"))
        self.displays_btn.get_style_context().add_class("reply-btn")
        self.displays_btn.connect("clicked", lambda *_: (self.hide(), subprocess.Popen(["xrandr", "--auto"])))
        self.lock_btn = Gtk.Button(label=t("lock_short"))
        self.lock_btn.get_style_context().add_class("reply-btn")
        self.lock_btn.connect("clicked", lambda *_: (self.hide(), subprocess.Popen(["/opt/ai-os/spotlight/lock.sh"])))
        self.reboot_btn = Gtk.Button(label=t("reboot_btn"))
        self.reboot_btn.get_style_context().add_class("reply-btn")
        self.reboot_btn.connect("clicked", lambda *_: (self.hide(), subprocess.Popen(["sudo", "reboot"])))
        self.poweroff_btn = Gtk.Button(label=t("poweroff_btn"))
        self.poweroff_btn.get_style_context().add_class("reply-btn")
        self.poweroff_btn.connect("clicked", lambda *_: (self.hide(), subprocess.Popen(["sudo", "poweroff"])))
        grid.attach(self.displays_btn, 0, 0, 1, 1)
        grid.attach(self.lock_btn, 1, 0, 1, 1)
        grid.attach(self.reboot_btn, 0, 1, 1, 1)
        grid.attach(self.poweroff_btn, 1, 1, 1, 1)
        card.pack_start(grid, False, False, 0)

        self.info_lbl = Gtk.Label(label=t("podman_ready"), xalign=0)
        self.info_lbl.get_style_context().add_class("pop-sub")
        card.pack_start(self.info_lbl, False, False, 0)

        self._hovering = False
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("enter-notify-event", self._on_enter)
        self.connect("leave-notify-event", self._on_leave)

    def _open_tz_dialog(self, *_):
        self.hide()
        GLib.idle_add(self._show_tz_dialog)

    def _show_tz_dialog(self):
        import datetime
        dlg = Gtk.Dialog(title=t("tz_title"), flags=0)
        dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        dlg.set_keep_above(True)
        box = dlg.get_content_area()
        box.set_spacing(8)
        box.set_border_width(12)

        try:
            cur_tz = subprocess.check_output(["timedatectl", "show", "-p", "Timezone", "--value"], text=True).strip()
            ntp_on = subprocess.check_output(["timedatectl", "show", "-p", "NTP", "--value"], text=True).strip() == "yes"
        except Exception:
            cur_tz, ntp_on = "Europe/Lisbon", True

        box.add(Gtk.Label(label=t("tz_zone_lbl"), xalign=0))
        entry = Gtk.Entry()
        entry.set_text(cur_tz)
        box.add(entry)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for tz in ("Europe/Lisbon", "UTC", "Europe/London", "America/Sao_Paulo"):
            b = Gtk.Button(label=tz.split("/")[-1].replace("_", " "))
            b.connect("clicked", lambda _, z=tz: entry.set_text(z))
            row.pack_start(b, True, True, 0)
        box.add(row)

        ntp_chk = Gtk.CheckButton(label=t("tz_ntp"))
        ntp_chk.set_active(ntp_on)
        box.add(ntp_chk)

        box.add(Gtk.Label(label=t("tz_dt_lbl"), xalign=0))
        dt_entry = Gtk.Entry()
        orig_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        dt_entry.set_text(orig_dt)
        dt_entry.connect("changed", lambda *_: ntp_chk.set_active(False))
        box.add(dt_entry)

        dlg.add_buttons(t("cancel"), Gtk.ResponseType.CANCEL, t("confirm"), Gtk.ResponseType.OK)

        def _on_resp(d, resp):
            chosen_tz = entry.get_text().strip()
            chosen_dt = dt_entry.get_text().strip()
            use_ntp = ntp_chk.get_active()
            d.destroy()
            if resp == Gtk.ResponseType.OK:
                if chosen_tz:
                    subprocess.run(["sudo", "timedatectl", "set-timezone", chosen_tz], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if use_ntp:
                    subprocess.Popen(["sudo", "timedatectl", "set-ntp", "true"])
                elif chosen_dt:
                    subprocess.run(["sudo", "timedatectl", "set-ntp", "false"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    dt_full = chosen_dt if len(chosen_dt) > 16 else f"{chosen_dt}:00"
                    subprocess.Popen(["sudo", "timedatectl", "set-time", dt_full])

        dlg.connect("response", _on_resp)
        dlg.connect("delete-event", lambda d, *_: (d.destroy(), True)[1])
        dlg.show_all()
        dlg.present()
        return False

    def _on_enter(self, *_):
        self._hovering = True
        return False

    def _on_leave(self, _, event):
        if event.detail == Gdk.NotifyType.INFERIOR:
            return False
        self._hovering = False
        GLib.timeout_add(300, self._maybe_hide)
        return False

    def _maybe_hide(self):
        if not self._hovering:
            self.hide()
        return False

    def refresh_labels(self):
        self.tz_btn.set_label(t("tz_btn"))
        self.sec1_lbl.set_text(t("sec_audio_display"))
        self.sec2_lbl.set_text(t("sec_conn"))
        self.sec3_lbl.set_text(t("sec_sys"))
        self.vol_lbl.set_text(f"{t('volume')}: {int(self.vol_scale.get_value())}%")
        self.bri_lbl.set_text(f"{t('brightness')}: {int(self.bri_scale.get_value())}%")
        self.bt_btn.set_label(f"{t('bt_label')}: Toggle")
        self.displays_btn.set_label(t("displays_short"))
        self.lock_btn.set_label(t("lock_short"))
        self.reboot_btn.set_label(t("reboot_btn"))
        self.poweroff_btn.set_label(t("poweroff_btn"))

    def _on_bt_toggle(self, *_):
        def _w():
            try:
                req = urllib.request.Request(f"{API_BASE}/api/net/bt_toggle", data=b"{}", method="POST")
                res = json.loads(urllib.request.urlopen(req, timeout=4).read().decode())
                state = "ON" if res.get("powered") else "OFF"
                GLib.idle_add(self.bt_btn.set_label, f"{t('bt_label')}: {state}")
            except Exception:
                pass
        threading.Thread(target=_w, daemon=True).start()

    def _connect_wifi(self, ssid):
        self.hide()
        GLib.idle_add(self._show_wifi_dialog, ssid)

    def _show_wifi_dialog(self, ssid):
        dlg = Gtk.Dialog(title=ssid, flags=0)
        dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        dlg.add_buttons(t("cancel"), Gtk.ResponseType.CANCEL, t("confirm"), Gtk.ResponseType.OK)
        box = dlg.get_content_area()
        lbl = Gtk.Label(label=t("wifi_pw_prompt", ssid=ssid))
        entry = Gtk.Entry()
        entry.set_visibility(False)
        box.add(lbl)
        box.add(entry)

        def _on_resp(d, resp):
            pw = entry.get_text()
            d.destroy()
            if resp == Gtk.ResponseType.OK:
                req = urllib.request.Request(
                    f"{API_BASE}/api/net/wifi",
                    data=json.dumps({"ssid": ssid, "password": pw}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                threading.Thread(target=lambda: urllib.request.urlopen(req, timeout=15).read(), daemon=True).start()

        dlg.connect("response", _on_resp)
        dlg.connect("delete-event", lambda d, *_: (d.destroy(), True)[1])
        dlg.show_all()
        dlg.present()
        return False

    def on_vol_changed(self, scale):
        val = int(scale.get_value())
        self.vol_lbl.set_text(f"{t('volume')}: {val}%")
        subprocess.Popen(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val}%"], stderr=subprocess.DEVNULL)

    def on_bri_changed(self, scale):
        val = max(20, min(100, int(scale.get_value())))
        self.bri_lbl.set_text(f"{t('brightness')}: {val}%")
        res = subprocess.run(
            ["brightnessctl", "-c", "backlight", "set", f"{val}%"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if res.returncode != 0:
            try:
                out = subprocess.check_output(["xrandr", "--listmonitors"], text=True)
                mon = out.splitlines()[-1].split()[-1]
                subprocess.Popen(["xrandr", "--output", mon, "--brightness", f"{val / 100.0:.2f}"])
            except Exception:
                pass

    def toggle_at(self, geom):
        if self.is_visible():
            self.hide()
            return
        import datetime
        self.dt_lbl.set_text(datetime.datetime.now().strftime("%a %d %b · %H:%M"))
        kb = get_config().get("kb_layout", "pt").upper()
        self.info_lbl.set_text(f"{t('podman_ready')} · KB: {kb}")
        self.move(geom.x + geom.width - 304, geom.y + 34)
        self.show_all()
        threading.Thread(target=self._populate_async, daemon=True).start()

    def _populate_async(self):
        try:
            ps = subprocess.check_output(["podman", "ps", "-q"], text=True, stderr=subprocess.DEVNULL).splitlines()
            kb = get_config().get("kb_layout", "pt").upper()
            GLib.idle_add(self.info_lbl.set_text, f"{t('podman_active', n=len(ps))} · KB: {kb}")
        except Exception:
            pass
        try:
            nets = json.loads(urllib.request.urlopen(f"{API_BASE}/api/net/wifi", timeout=2).read().decode())
        except Exception:
            nets = []
        try:
            sinks = json.loads(urllib.request.urlopen(f"{API_BASE}/api/audio/sinks", timeout=2).read().decode())
        except Exception:
            sinks = []
        try:
            bdevs = json.loads(urllib.request.urlopen(f"{API_BASE}/api/bt/devices", timeout=2).read().decode())
        except Exception:
            bdevs = []

        def _apply():
            if not self.is_visible():
                return False
            for child in self.wifi_box.get_children():
                self.wifi_box.remove(child)
            if not nets:
                wl = Gtk.Label(label=t("wifi_none"), xalign=0)
                wl.get_style_context().add_class("pop-sub")
                self.wifi_box.add(wl)
            else:
                for n in nets[:4]:
                    mark = "● " if n["active"] else ""
                    b = Gtk.Button(label=f"{mark}{n['ssid']} ({n['signal']}%)")
                    b.get_style_context().add_class("reply-btn")
                    b.connect("clicked", lambda _, s=n["ssid"]: self._connect_wifi(s))
                    self.wifi_box.add(b)
            self.wifi_box.show_all()

            for child in self.audio_box.get_children():
                self.audio_box.remove(child)
            if len(sinks) > 1:
                for s in sinks[:3]:
                    mark = "● " if s["default"] else ""
                    b = Gtk.Button(label=f"{mark}{s['name'][:28]}")
                    b.get_style_context().add_class("reply-btn")
                    b.connect("clicked", lambda _, sid=s["id"]: self._set_audio_sink(sid))
                    self.audio_box.add(b)
                self.audio_box.show_all()

            for child in self.bt_box.get_children():
                self.bt_box.remove(child)
            for d in bdevs[:3]:
                mark = "● " if d["connected"] else ""
                b = Gtk.Button(label=f"{mark}{d['name'][:26]}")
                b.get_style_context().add_class("reply-btn")
                b.connect("clicked", lambda _, mac=d["mac"]: self._toggle_bt_dev(mac))
                self.bt_box.add(b)
            self.bt_box.show_all()
            return False

        GLib.idle_add(_apply)


def open_settings_dialog(spotlight):
    dlg = Gtk.Dialog(title=t("settings_title"), flags=0)
    dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
    dlg.set_keep_above(True)
    dlg.set_default_size(480, 300)
    box = dlg.get_content_area()
    box.set_border_width(12)

    nb = Gtk.Notebook()
    box.pack_start(nb, True, True, 0)

    # Tab 1: AI Agent
    tab_ai = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    tab_ai.set_border_width(14)
    cur_model, cur_mode = "", "auto"
    try:
        s_file = HOME / ".gemini" / "antigravity-cli" / "settings.json"
        if s_file.exists():
            sd = json.loads(s_file.read_text(encoding="utf-8"))
            cur_model = sd.get("model", "")
            cur_mode = sd.get("agentMode", "auto")
    except Exception:
        pass
    model_lbl = Gtk.Label(label=f"{cur_model or 'agy'} ({cur_mode})", xalign=0)
    model_lbl.get_style_context().add_class("pop-sub")
    tab_ai.pack_start(model_lbl, False, False, 0)

    prof_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    for key in ("fast", "deep", "plan"):
        b = Gtk.Button(label=t(f"prof_{key}")[0])
        def _set_prof(_, k=key):
            def _w():
                try:
                    req = urllib.request.Request(
                        f"{API_BASE}/api/agy/profile",
                        data=json.dumps({"profile": k}).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    res = json.loads(urllib.request.urlopen(req, timeout=8).read().decode())
                    GLib.idle_add(model_lbl.set_text, f"{res.get('model', '')} ({res.get('mode', 'auto')})")
                except Exception:
                    pass
            threading.Thread(target=_w, daemon=True).start()
        b.connect("clicked", _set_prof)
        prof_row.pack_start(b, True, True, 0)
    tab_ai.pack_start(prof_row, False, False, 0)

    auth_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    login_b = Gtk.Button(label="/login")
    login_b.connect("clicked", lambda *_: (dlg.destroy(), spotlight.start_agy_login()))
    logout_b = Gtk.Button(label="/logout")
    logout_b.connect("clicked", lambda *_: (dlg.destroy(), spotlight.do_agy_logout()))
    auth_row.pack_start(login_b, True, True, 0)
    auth_row.pack_start(logout_b, True, True, 0)
    tab_ai.pack_start(auth_row, False, False, 0)
    nb.append_page(tab_ai, Gtk.Label(label=t("settings_ai")))

    # Tab 2: Chat & Language
    tab_ui = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    tab_ui.set_border_width(14)
    cur_fs = int(get_config().get("chat_font_size", 13))
    fs_lbl = Gtk.Label(label=f"Texto do Chat: {cur_fs}px" if get_lang() == "pt" else f"Chat Text: {cur_fs}px", xalign=0)
    tab_ui.pack_start(fs_lbl, False, False, 0)
    fs_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 8, 18, 1)
    fs_scale.set_value(cur_fs)
    fs_scale.set_draw_value(False)

    prev_frame = Gtk.Box()
    prev_frame.get_style_context().add_class("draft-card")
    prev_lbl = Gtk.Label(xalign=0)
    prev_lbl.set_line_wrap(True)
    prev_sample = "Exemplo de texto na resposta do chat." if get_lang() == "pt" else "Sample chat reply text preview."
    prev_lbl.set_markup(f'<span size="{cur_fs * 1024}">{prev_sample}</span>')
    prev_frame.pack_start(prev_lbl, True, True, 0)

    def _on_fs(s):
        px = int(s.get_value())
        fs_lbl.set_text(f"Texto do Chat: {px}px" if get_lang() == "pt" else f"Chat Text: {px}px")
        prev_lbl.set_markup(f'<span size="{px * 1024}">{prev_sample}</span>')
        update_config(chat_font_size=px)
        if spotlight.reply_view and getattr(spotlight, "_reply_ready", False):
            spotlight.reply_view.evaluate_javascript(
                f"document.body.style.fontSize='{px}px'; document.body.scrollHeight;",
                -1, None, None, None, spotlight._on_reply_height, None,
            )
    fs_scale.connect("value-changed", _on_fs)
    tab_ui.pack_start(fs_scale, False, False, 0)
    tab_ui.pack_start(prev_frame, False, False, 0)

    lang_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    for code, name in (("pt", "Português (PT-PT)"), ("en", "English (EN)")):
        lb = Gtk.Button(label=name)
        def _set_l(_, c=code):
            if spotlight.topbar and not spotlight.topbar._confirm_lang_switch():
                return
            set_lang(c)
            if spotlight.topbar:
                spotlight.topbar.apply_lang()
            spotlight.apply_lang()
        lb.connect("clicked", _set_l)
        lang_row.pack_start(lb, True, True, 0)
    tab_ui.pack_start(lang_row, False, False, 0)

    kb_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    for code in ("pt", "us", "es", "fr", "gb"):
        kb_b = Gtk.Button(label=f"KB: {code.upper()}")
        kb_b.connect("clicked", lambda _, c=code: (subprocess.Popen(["setxkbmap", c]), update_config(kb_layout=c)))
        kb_row.pack_start(kb_b, True, True, 0)
    tab_ui.pack_start(kb_row, False, False, 0)
    nb.append_page(tab_ui, Gtk.Label(label=t("settings_ui_tab")))

    # Tab 3: System (non-duplicated OS tools)
    tab_sys = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    tab_sys.set_border_width(14)
    grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)
    disp_b = Gtk.Button(label=t("displays_short"))
    disp_b.connect("clicked", lambda *_: subprocess.Popen(["xrandr", "--auto"]))
    grid.attach(disp_b, 0, 0, 1, 1)
    upd_b = Gtk.Button(label="#update")
    upd_b.connect("clicked", lambda *_: (dlg.destroy(), subprocess.Popen(["/opt/ai-os/spotlight/update.sh"])))
    grid.attach(upd_b, 1, 0, 1, 1)
    tab_sys.pack_start(grid, False, False, 0)
    nb.append_page(tab_sys, Gtk.Label(label=t("settings_sys")))

    dlg.add_buttons(t("close_btn"), Gtk.ResponseType.CLOSE)
    dlg.connect("response", lambda d, *_: d.destroy())
    dlg.connect("delete-event", lambda d, *_: (d.destroy(), True)[1])
    dlg.show_all()
    dlg.present()

    def _set_audio_sink(self, sink_id):
        req = urllib.request.Request(
            f"{API_BASE}/api/audio/default",
            data=json.dumps({"id": sink_id}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        threading.Thread(target=lambda: urllib.request.urlopen(req, timeout=3).read(), daemon=True).start()
        self.hide()

    def _toggle_bt_dev(self, mac):
        req = urllib.request.Request(
            f"{API_BASE}/api/bt/connect",
            data=json.dumps({"mac": mac}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        threading.Thread(target=lambda: urllib.request.urlopen(req, timeout=8).read(), daemon=True).start()
        self.hide()


class TopBarWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("AITopBar")
        self.set_wmclass("AITopBar", "AITopBar")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_accept_focus(False)
        self.set_focus_on_map(False)
        self.set_keep_above(False)
        self.stick()
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.get_style_context().add_class("topbar-win")

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)
        self.connect("draw", clear_transparent)
        self.connect("draw", clear_transparent)

        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geom = monitor.get_geometry()

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.get_style_context().add_class("topbar")
        bar.set_size_request(geom.width, 28)
        self.add(bar)

        self.win_popover = WindowsPopover()
        self.logo_btn = Gtk.Button()
        self.logo_btn.set_can_focus(False)
        self.logo_btn.set_valign(Gtk.Align.CENTER)
        self.logo_btn.get_style_context().add_class("status-trigger")
        self.logo_lbl = Gtk.Label(label="◉")
        self.logo_lbl.set_valign(Gtk.Align.CENTER)
        self.logo_lbl.get_style_context().add_class("topbar-logo")
        self.logo_btn.add(self.logo_lbl)
        self.logo_btn.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.logo_btn.connect("enter-notify-event", self._on_logo_enter)
        self.logo_btn.connect("leave-notify-event", self._on_logo_leave)
        self.logo_btn.connect("clicked", lambda *_: self.win_popover.toggle_at(geom, self._last_windows or []))
        bar.pack_start(self.logo_btn, False, False, 0)

        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.ws_btns = []
        for idx in range(4):
            wb = Gtk.Button(label=str(idx + 1))
            wb.set_can_focus(False)
            wb.set_valign(Gtk.Align.CENTER)
            wb.get_style_context().add_class("win-dot")
            wb.connect("clicked", lambda _, i=idx: subprocess.Popen(["wmctrl", "-s", str(i)]))
            self.ws_btns.append(wb)
            self.ws_box.pack_start(wb, False, False, 0)
        bar.pack_start(self.ws_box, False, False, 0)
        self._last_ws = -1
        self._bat_warned_15 = False
        self._bat_warned_5 = False

        self.dots_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.pack_start(self.dots_box, False, False, 0)
        self._last_windows = None

        self.popover = ControlPopover()

        status_btn = Gtk.Button()
        status_btn.set_can_focus(False)
        status_btn.get_style_context().add_class("status-trigger")
        status_btn.connect("clicked", lambda *_: self.popover.toggle_at(geom))
        status_inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        status_btn.add(status_inner)
        bar.pack_end(status_btn, False, False, 0)

        self.lang_btn = Gtk.Button(label=get_lang().upper())
        self.lang_btn.set_can_focus(False)
        self.lang_btn.set_valign(Gtk.Align.CENTER)
        self.lang_btn.get_style_context().add_class("win-dot")
        self.lang_btn.set_tooltip_text("PT-PT / EN")
        self.on_lang_changed = None
        self.lang_btn.connect("clicked", self._toggle_lang)
        bar.pack_end(self.lang_btn, False, False, 0)

        self.clock_lbl = Gtk.Label(label="--:--")
        self.clock_lbl.get_style_context().add_class("topbar-item")
        status_inner.pack_end(self.clock_lbl, False, False, 0)

        bat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.bat_icon = Gtk.Image.new_from_icon_name("battery-full-charged-symbolic", Gtk.IconSize.MENU)
        self.bat_lbl = Gtk.Label(label="AC")
        bat_box.get_style_context().add_class("topbar-item")
        bat_box.pack_start(self.bat_icon, False, False, 0)
        bat_box.pack_start(self.bat_lbl, False, False, 0)
        status_inner.pack_end(bat_box, False, False, 0)

        wifi_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.wifi_icon = Gtk.Image.new_from_icon_name("network-wireless-symbolic", Gtk.IconSize.MENU)
        self.wifi_lbl = Gtk.Label(label="...")
        wifi_box.get_style_context().add_class("topbar-item")
        wifi_box.pack_start(self.wifi_icon, False, False, 0)
        wifi_box.pack_start(self.wifi_lbl, False, False, 0)
        status_inner.pack_end(wifi_box, False, False, 0)

        self.move(geom.x, geom.y)
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.connect("scroll-event", self._on_topbar_scroll)
        self.show_all()
        self.refresh_windows()
        GLib.timeout_add_seconds(1, self.refresh_windows)

    def _on_topbar_scroll(self, _, event):
        delta = 0
        if event.direction in (Gdk.ScrollDirection.LEFT, Gdk.ScrollDirection.UP):
            delta = -1
        elif event.direction in (Gdk.ScrollDirection.RIGHT, Gdk.ScrollDirection.DOWN):
            delta = 1
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            ok, dx, dy = event.get_scroll_deltas()
            if ok:
                val = dx if abs(dx) >= abs(dy) else dy
                if val > 0.2:
                    delta = 1
                elif val < -0.2:
                    delta = -1
        if delta != 0 and self._last_ws >= 0:
            nxt = max(0, min(3, self._last_ws + delta))
            if nxt != self._last_ws:
                subprocess.Popen(["wmctrl", "-s", str(nxt)])
        return True

    def refresh_windows(self):
        cur_ws = 0
        try:
            ws_out = subprocess.check_output(["wmctrl", "-d"], text=True, stderr=subprocess.DEVNULL)
            for line in ws_out.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "*":
                    cur_ws = int(parts[0])
                    break
        except Exception:
            pass

        try:
            out = subprocess.check_output(["wmctrl", "-l", "-x"], text=True, stderr=subprocess.DEVNULL)
            act_out = subprocess.check_output(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"], text=True, stderr=subprocess.DEVNULL
            )
            active_id = act_out.strip().split()[-1].lower()
            if active_id.startswith("0x"):
                active_int = int(active_id, 16)
            else:
                active_int = 0
        except Exception:
            return True

        wins = []
        occupied_ws = set()
        for line in out.splitlines():
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            wid, ws_str, wm_class, _, title = parts
            if "AITopBar" in wm_class or "AISpotlight" in wm_class:
                continue
            if wm_class == "pcmanfm.Pcmanfm" and title == "pcmanfm":
                continue
            try:
                ws_idx = int(ws_str)
            except ValueError:
                ws_idx = 0
            if ws_idx >= 0:
                occupied_ws.add(ws_idx)
            is_active = int(wid, 16) == active_int
            app_name = wm_class.split(".")[-1] if "." in wm_class else wm_class
            wins.append((wid, ws_idx, app_name, title, is_active))

        for idx, wb in enumerate(self.ws_btns):
            lbl = f"{idx + 1}•" if idx in occupied_ws else str(idx + 1)
            if wb.get_label() != lbl:
                wb.set_label(lbl)
            ctx = wb.get_style_context()
            if idx == cur_ws:
                ctx.add_class("win-dot-active")
            else:
                ctx.remove_class("win-dot-active")

        if (wins, cur_ws) == (self._last_windows, self._last_ws):
            return True
        self._last_windows = wins
        self._last_ws = cur_ws

        for child in self.dots_box.get_children():
            self.dots_box.remove(child)
        for wid, ws_idx, app_name, title, is_active in wins:
            if ws_idx not in (cur_ws, -1):
                continue
            low = app_name.lower()
            if "chromium" in low:
                icon_name, label_txt = "web-browser", "Browser"
            elif "pcmanfm" in low:
                icon_name, label_txt = "system-file-manager", "Ficheiros"
            elif "xterm" in low:
                icon_name, label_txt = "utilities-terminal", "Terminal"
            elif "litemd" in low:
                icon_name, label_txt = "text-x-generic", "LiteMD"
            else:
                icon_name, label_txt = "application-x-executable", app_name[:12]

            btn = Gtk.Button()
            btn.set_can_focus(False)
            btn.set_valign(Gtk.Align.CENTER)
            btn.set_tooltip_text(title)
            inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            ico.set_pixel_size(14)
            lbl = Gtk.Label(label=label_txt)
            inner.pack_start(ico, False, False, 0)
            inner.pack_start(lbl, False, False, 0)
            btn.add(inner)

            ctx = btn.get_style_context()
            ctx.add_class("win-dot")
            if is_active:
                ctx.add_class("win-dot-active")
            btn.connect("clicked", lambda _, w=wid: subprocess.Popen(["wmctrl", "-i", "-a", w]))
            self.dots_box.add(btn)
        self.dots_box.show_all()
        return True

    def _on_logo_enter(self, *_):
        self.win_popover._trigger_hovering = True
        geom = self.get_screen().get_monitor_geometry(0)
        self.win_popover.show_at(geom, self._last_windows or [])
        return False

    def _on_logo_leave(self, _, event):
        if event.detail == Gdk.NotifyType.INFERIOR:
            return False
        self.win_popover._trigger_hovering = False
        GLib.timeout_add(220, self.win_popover._maybe_hide)
        return False

    def _confirm_lang_switch(self):
        dlg = Gtk.MessageDialog(
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=t("lang_confirm_title"),
        )
        dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        dlg.set_keep_above(True)
        dlg.format_secondary_text(t("lang_confirm_msg"))
        dlg.add_button(t("cancel"), Gtk.ResponseType.CANCEL)
        dlg.add_button(t("confirm"), Gtk.ResponseType.OK)
        resp = dlg.run()
        dlg.destroy()
        return resp == Gtk.ResponseType.OK

    def _toggle_lang(self, *_):
        if not self._confirm_lang_switch():
            return
        nxt = "en" if get_lang() == "pt" else "pt"
        set_lang(nxt)
        self.apply_lang()
        if self.on_lang_changed:
            self.on_lang_changed()

    def apply_lang(self):
        self.lang_btn.set_label(get_lang().upper())
        self.popover.refresh_labels()
        if self.win_popover.is_visible():
            self.win_popover.hide()
            self.win_popover.toggle_at(self.get_screen().get_monitor_geometry(0), self._last_windows or [])

    def set_ai_busy(self, busy: bool):
        self.logo_lbl.set_text("✦ AI..." if busy else "◉")

    def update_status(self, data):
        wifi = data.get("wifi", "N/D")
        bat = data.get("battery", "AC")
        now = data.get("time", "--:--")
        if wifi in ("Offline", "N/D"):
            icon_name = "network-offline-symbolic"
        elif wifi == "Online":
            icon_name = "network-wired-symbolic"
        else:
            icon_name = "network-wireless-symbolic"
        self.wifi_icon.set_from_icon_name(icon_name, Gtk.IconSize.MENU)
        self.wifi_lbl.set_text(wifi)
        self.bat_lbl.set_text(bat)
        if bat.endswith("%"):
            try:
                pct = int(bat.rstrip("%"))
                if pct <= 5 and not self._bat_warned_5:
                    self._bat_warned_5 = True
                    subprocess.Popen(["notify-send", "-u", "critical", "AI-OS", t("bat_crit", pct=pct)])
                elif pct <= 15 and not self._bat_warned_15:
                    self._bat_warned_15 = True
                    subprocess.Popen(["notify-send", "AI-OS", t("bat_low", pct=pct)])
                elif pct > 20:
                    self._bat_warned_15 = False
                    self._bat_warned_5 = False
            except ValueError:
                pass
        else:
            self._bat_warned_15 = False
            self._bat_warned_5 = False
        self.clock_lbl.set_text(now)


class SpotlightWindow(Gtk.Window):
    def __init__(self, topbar=None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.topbar = topbar
        self.set_title("AISpotlight")
        self.set_wmclass("AISpotlight", "AISpotlight")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.stick()
        self.set_accept_focus(True)
        self.set_focus_on_map(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.get_style_context().add_class("spotlight-win")

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)
        self.connect("draw", clear_transparent)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.apps = load_desktop_apps()
        self.agy_models_cache = []
        cfg = get_config()
        saved_kb = cfg.get("kb_layout")
        if saved_kb:
            subprocess.Popen(["setxkbmap", saved_kb])
        last_cid = cfg.get("last_chat_id")
        if last_cid and (HOME / ".ai-os" / "chats" / f"{last_cid}.md").exists():
            self.current_chat_id = last_cid
        else:
            self.current_chat_id = None
        self.awaiting_auth_code = False
        self.last_reply_md = ""
        self.history = self._load_history()
        self.hist_idx = len(self.history)
        self.clip_history = []
        self._clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._clipboard.connect("owner-change", self._on_clip_change)
        self.results = []
        self._last_match_keys = None
        threading.Thread(target=self._prefetch_models, daemon=True).start()

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(outer)

        self.resume_chat_btn = Gtk.Button()
        self._chat_btn_lbl = Gtk.Label(label="▲")
        self._chat_btn_lbl.show()
        self.resume_chat_btn.add(self._chat_btn_lbl)
        self.resume_chat_btn.set_halign(Gtk.Align.END)
        self.resume_chat_btn.set_margin_end(18)
        self.resume_chat_btn.get_style_context().add_class("chat-tab")
        self.resume_chat_btn.set_can_focus(False)
        self.resume_chat_btn.set_no_show_all(True)
        self.resume_chat_btn.connect("clicked", self._toggle_current_chat)
        outer.pack_start(self.resume_chat_btn, False, False, 0)

        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.card.get_style_context().add_class("spotlight-card")
        self.card.set_size_request(720, -1)
        outer.pack_start(self.card, False, False, 0)

        # AI reply pane (grows upwards above input bar, rendered Markdown via WebKit2)
        self.reply_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.reply_box.get_style_context().add_class("ai-reply-box")
        actions_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        actions_row.get_style_context().add_class("reply-actions")
        self.copy_btn = Gtk.Button(label=t("copy"))
        self.copy_btn.get_style_context().add_class("reply-btn")
        self.copy_btn.set_can_focus(False)
        self.copy_btn.connect("clicked", self.on_copy_reply)
        self.litemd_btn = Gtk.Button(label=t("open_litemd"))
        self.litemd_btn.get_style_context().add_class("reply-btn")
        self.litemd_btn.set_can_focus(False)
        self.litemd_btn.connect("clicked", self.on_open_litemd)
        self.new_chat_btn = Gtk.Button(label="/new")
        self.new_chat_btn.get_style_context().add_class("reply-btn")
        self.new_chat_btn.set_can_focus(False)
        self.new_chat_btn.connect("clicked", lambda *_: (setattr(self, "current_chat_id", None), update_config(last_chat_id=None), self.hide_results(), self.show_reply(t("new_chat"))))
        actions_row.pack_end(self.litemd_btn, False, False, 0)
        actions_row.pack_end(self.copy_btn, False, False, 0)
        actions_row.pack_end(self.new_chat_btn, False, False, 0)
        self.reply_box.pack_start(actions_row, False, False, 0)

        self.reply_scroll = Gtk.ScrolledWindow()
        self.reply_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.reply_scroll.get_style_context().add_class("clean-scroll")
        self.reply_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.reply_scroll.set_min_content_height(48)
        self.reply_scroll.set_max_content_height(440)
        self.reply_scroll.set_propagate_natural_height(True)
        self.reply_box.pack_start(self.reply_scroll, True, True, 0)
        self.reply_view = None
        self.card.pack_start(self.reply_box, False, False, 0)

        # Results list (grows upwards above input bar)
        self.listbox = Gtk.ListBox()
        self.listbox.get_style_context().add_class("results-list")
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self.on_row_activated)
        self.list_scroll = Gtk.ScrolledWindow()
        self.list_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.list_scroll.get_style_context().add_class("clean-scroll")
        self.list_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.list_scroll.set_max_content_height(260)
        self.list_scroll.set_propagate_natural_height(True)
        self.list_scroll.add(self.listbox)
        self.card.pack_start(self.list_scroll, False, False, 0)

        # Draft "letter" card above Spotlight bar when prompt exceeds 1 line
        self.draft_box = Gtk.ScrolledWindow()
        self.draft_box.set_shadow_type(Gtk.ShadowType.NONE)
        self.draft_box.get_style_context().add_class("clean-scroll")
        self.draft_box.get_style_context().add_class("draft-card")
        self.draft_box.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.draft_box.set_max_content_height(180)
        self.draft_box.set_propagate_natural_height(True)
        self.draft_box.set_no_show_all(True)
        self.draft_view = None
        self.card.pack_start(self.draft_box, False, False, 0)

        self.divider = Gtk.Box()
        self.divider.get_style_context().add_class("divider")
        self.card.pack_start(self.divider, False, False, 0)

        # Bottom Input / Command Row
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        top_row.get_style_context().add_class("search-row")

        icon_btn = Gtk.Button(label="✦")
        icon_btn.set_valign(Gtk.Align.CENTER)
        icon_btn.set_margin_top(2)
        icon_btn.set_can_focus(False)
        icon_btn.set_relief(Gtk.ReliefStyle.NONE)
        icon_btn.get_style_context().add_class("search-icon")
        icon_btn.set_tooltip_text(t("settings_title"))
        icon_btn.connect("clicked", lambda *_: open_settings_dialog(self))
        top_row.pack_start(icon_btn, False, False, 0)

        self.entry_scroll = Gtk.ScrolledWindow()
        self.entry_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.entry_scroll.get_style_context().add_class("clean-scroll")
        self.entry_scroll.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.NEVER)
        self.entry_scroll.set_min_content_height(22)
        self.entry_scroll.set_max_content_height(24)
        self.entry_scroll.set_size_request(-1, 24)
        self.entry_scroll.set_vexpand(False)
        self.entry_scroll.set_propagate_natural_height(False)
        self.entry_scroll.set_valign(Gtk.Align.CENTER)

        self.entry = Gtk.TextView()
        self.entry.set_wrap_mode(Gtk.WrapMode.NONE)
        self.entry.set_accepts_tab(False)
        self.entry.set_pixels_above_lines(1)
        self.entry.set_pixels_below_lines(1)
        self.entry.get_style_context().add_class("search-input")
        self.entry_buf = self.entry.get_buffer()
        self.entry_buf.connect("changed", self.on_search_changed)
        self.entry.connect("key-press-event", self.on_entry_key_press)
        self.entry_scroll.add(self.entry)

        self.draft_view = Gtk.TextView.new_with_buffer(self.entry_buf)
        self.draft_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.draft_view.set_accepts_tab(False)
        self.draft_view.set_pixels_above_lines(2)
        self.draft_view.set_pixels_below_lines(2)
        self.draft_view.get_style_context().add_class("draft-letter")
        self.draft_view.connect("key-press-event", self.on_entry_key_press)
        self.draft_box.add(self.draft_view)

        overlay = Gtk.Overlay()
        overlay.add(self.entry_scroll)
        self.placeholder_lbl = Gtk.Label(label=t("placeholder"), xalign=0)
        self.placeholder_lbl.set_valign(Gtk.Align.CENTER)
        self.placeholder_lbl.set_margin_top(2)
        self.placeholder_lbl.get_style_context().add_class("search-placeholder")
        self.placeholder_lbl.set_no_show_all(True)
        self.placeholder_lbl.show()
        overlay.add_overlay(self.placeholder_lbl)
        overlay.set_overlay_pass_through(self.placeholder_lbl, True)

        if self.topbar:
            self.topbar.on_lang_changed = self.apply_lang

        v_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        v_wrap.pack_start(overlay, True, True, 0)
        top_row.pack_start(v_wrap, True, True, 0)

        vadj = self.entry_scroll.get_vadjustment()
        self.mini_scroll = Gtk.Scrollbar(orientation=Gtk.Orientation.VERTICAL, adjustment=vadj)
        self.mini_scroll.get_style_context().add_class("mini-scroll")
        self.mini_scroll.set_size_request(6, 24)
        self.mini_scroll.set_valign(Gtk.Align.CENTER)
        self.mini_scroll.set_no_show_all(True)
        vadj.connect("changed", lambda a: self.mini_scroll.set_visible(a.get_upper() > a.get_page_size() + 2))
        top_row.pack_start(self.mini_scroll, False, False, 0)

        self.send_btn = Gtk.Button(label="→")
        self.send_btn.set_valign(Gtk.Align.CENTER)
        self.send_btn.set_size_request(38, 28)
        self.send_btn.get_style_context().add_class("send-arrow")
        self.send_btn.set_can_focus(False)
        self.send_btn.connect("clicked", self.on_activate)
        top_row.pack_end(self.send_btn, False, False, 0)

        self.stop_btn = Gtk.Button(label="■")
        self.stop_btn.set_valign(Gtk.Align.CENTER)
        self.stop_btn.set_size_request(38, 28)
        self.stop_btn.get_style_context().add_class("send-arrow")
        self.stop_btn.set_can_focus(False)
        self.stop_btn.set_no_show_all(True)
        self.stop_btn.connect("clicked", self.on_stop_ai)
        top_row.pack_end(self.stop_btn, False, False, 0)
        self._cancelled = False

        self.card.pack_start(top_row, False, False, 0)

        self._last_pos = None
        self.connect("key-press-event", self.on_key_press)
        self.connect("button-press-event", lambda *_: (self.focus_spotlight(), False)[1])
        self.connect("show", self.on_show)
        self.connect("delete-event", lambda *_: True)
        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("size-allocate", lambda *_: self.dock_bottom())

        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geom = monitor.get_geometry()
        hints = Gdk.Geometry()
        hints.max_width = 720
        hints.max_height = max(240, min(540, geom.height - 80))
        self.set_geometry_hints(None, hints, Gdk.WindowHints.MAX_SIZE)

        self.show_all()
        self.hide_results()
        self.dock_bottom()
        self.refresh_status()
        GLib.timeout_add_seconds(10, self.refresh_status)
        GLib.timeout_add_seconds(600, self.refresh_wallpaper)
        GLib.timeout_add(1500, self._check_oobe)

    def apply_lang(self):
        self.placeholder_lbl.set_text(t("placeholder"))
        self.copy_btn.set_label(t("copy"))
        self.litemd_btn.set_label(t("open_litemd"))
        self._last_match_keys = None
        if self.get_query_text().strip():
            self.on_search_changed()

    def get_query_text(self):
        start, end = self.entry_buf.get_bounds()
        return self.entry_buf.get_text(start, end, True)

    def clear_query(self):
        self.entry_buf.set_text("")

    def dock_bottom(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geom = monitor.get_geometry()
        alloc = self.get_allocation()
        w = 720
        h = max(alloc.height, 56)
        x = geom.x + (geom.width - w) // 2
        y = geom.y + geom.height - h - 24
        if self._last_pos != (x, y):
            self._last_pos = (x, y)
            self.move(x, y)

    def on_show(self, *_):
        self.dock_bottom()
        self.entry.grab_focus()

    def on_focus_in(self, *_):
        self.set_opacity(1.0)
        return False

    def on_focus_out(self, *_):
        if not self.get_query_text().strip() and not self.reply_box.is_visible():
            self.set_opacity(0.80)
        return False

    def focus_spotlight(self):
        attach = Path("/tmp/aios_attach.txt")
        if attach.exists():
            try:
                txt = attach.read_text(encoding="utf-8")
                attach.unlink()
                if txt:
                    self.entry_buf.set_text(txt)
                    self.entry_buf.place_cursor(self.entry_buf.get_end_iter())
            except OSError:
                pass
        self.show()
        self.present_with_time(Gdk.CURRENT_TIME)
        self.set_opacity(1.0)
        self._sync_chat_btn()
        self.entry.grab_focus()

    def refresh_wallpaper(self):
        subprocess.Popen(["python3", "/opt/ai-os/spotlight/wallpaper.py"])
        return True

    def _check_oobe(self):
        def _w():
            try:
                res = json.loads(urllib.request.urlopen(f"{API_BASE}/api/agy/auth/status", timeout=3).read().decode())
                if res.get("installed") and not res.get("authenticated"):
                    GLib.idle_add(self._show_oobe_dialog)
            except Exception:
                pass
        threading.Thread(target=_w, daemon=True).start()
        return False

    def _show_oobe_dialog(self):
        dlg = Gtk.Dialog(title=t("oobe_title"), flags=0)
        dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        dlg.set_keep_above(True)
        box = dlg.get_content_area()
        box.set_spacing(10)
        box.set_border_width(14)
        lbl = Gtk.Label(label=t("oobe_msg"), xalign=0)
        box.add(lbl)
        lang_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for code, name in (("pt", "Português (PT-PT)"), ("en", "English (EN)")):
            b = Gtk.Button(label=name)
            b.connect("clicked", lambda _, c=code: (set_lang(c), self.topbar and self.topbar.apply_lang(), self.apply_lang(), lbl.set_text(t("oobe_msg"))))
            lang_row.pack_start(b, True, True, 0)
        box.add(lang_row)
        dlg.add_buttons(t("oobe_later"), Gtk.ResponseType.CANCEL, t("oobe_login"), Gtk.ResponseType.OK)
        dlg.show_all()
        resp = dlg.run()
        dlg.destroy()
        if resp == Gtk.ResponseType.OK:
            self.start_agy_login()

    def _sync_chat_btn(self):
        if self.current_chat_id:
            self._chat_btn_lbl.set_text("▼" if self.reply_box.is_visible() else "▲")
            self._chat_btn_lbl.show()
            self.resume_chat_btn.show()
        else:
            self.resume_chat_btn.hide()

    def _toggle_current_chat(self, *_):
        if self.reply_box.is_visible():
            self.hide_results()
        elif self.current_chat_id:
            self.show_reply(self.last_reply_md or "")
        self._sync_chat_btn()

    def hide_results(self):
        was_open = (
            self.divider.is_visible()
            or self.list_scroll.is_visible()
            or self.draft_box.is_visible()
            or self.reply_box.is_visible()
        )
        self.divider.hide()
        self.list_scroll.hide()
        self.draft_box.hide()
        self.reply_box.hide()
        self._sync_chat_btn()
        if was_open:
            self.resize(720, 1)

    def on_reply_loaded(self, view, event):
        if event != WebKit2.LoadEvent.FINISHED:
            return
        view.evaluate_javascript(
            "window.scrollTo(0, document.body.scrollHeight); document.body.scrollHeight",
            -1, None, None, None, self._on_reply_height, None
        )

    def _on_reply_height(self, view, res, _):
        try:
            js_res = view.evaluate_javascript_finish(res)
            h = int(js_res.to_int32())
            self.reply_scroll.set_min_content_height(max(48, min(h + 8, 440)))
        except Exception:
            self.reply_scroll.set_min_content_height(140)

    def _load_history(self):
        try:
            if HISTORY_FILE.exists():
                return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))[-50:]
        except Exception:
            pass
        return []

    def _save_history(self, prompt):
        if not prompt or (self.history and self.history[-1] == prompt):
            self.hist_idx = len(self.history)
            return
        self.history.append(prompt)
        self.history = self.history[-50:]
        self.hist_idx = len(self.history)
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            HISTORY_FILE.write_text(json.dumps(self.history, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def on_copy_reply(self, *_):
        if self.last_reply_md:
            Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(self.last_reply_md, -1)

    def on_open_litemd(self, *_):
        if self.current_chat_id:
            chat_path = HOME / ".ai-os" / "chats" / f"{self.current_chat_id}.md"
            if chat_path.exists():
                subprocess.Popen(["litemd", str(chat_path)])
                return
        if not self.last_reply_md:
            return
        out = HOME / "Temp" / "ultima-resposta.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.last_reply_md, encoding="utf-8")
        subprocess.Popen(["litemd", str(out)])

    def _ensure_reply_view(self):
        if self.reply_view is not None:
            return
        global WebKit2
        if WebKit2 is None:
            import gi
            gi.require_version("WebKit2", "4.1")
            from gi.repository import WebKit2 as _WK2
            WebKit2 = _WK2
        self._reply_ready = False
        self.reply_view = WebKit2.WebView()
        self.reply_view.set_background_color(Gdk.RGBA(0, 0, 0, 0))
        self.reply_view.get_settings().set_enable_javascript(True)
        self.reply_view.connect("load-changed", self.on_reply_loaded)
        self.reply_scroll.add(self.reply_view)

    def show_reply(self, text, live_stream=False):
        self._ensure_reply_view()
        self.last_reply_md = text
        self.divider.show()
        self.list_scroll.hide()
        render_md = text
        if self.current_chat_id:
            chat_path = HOME / ".ai-os" / "chats" / f"{self.current_chat_id}.md"
            if chat_path.exists():
                hist_md = chat_path.read_text(encoding="utf-8", errors="ignore").strip()
                if live_stream:
                    pending = getattr(self, "_pending_prompt", "")
                    if pending and f"### Utilizador\n{pending}" not in hist_md[-300:]:
                        hist_md = hist_md + f"\n\n### Utilizador\n{pending}"
                    render_md = hist_md + f"\n\n### AI-OS\n{text}"
                elif hist_md:
                    render_md = hist_md
        elif live_stream and getattr(self, "_pending_prompt", ""):
            render_md = f"### Utilizador\n{self._pending_prompt}\n\n### AI-OS\n{text}"
        if "### Utilizador" in render_md or "### AI-OS" in render_md:
            parts = re.split(r"(?m)^### (Utilizador|AI-OS)\s*$", render_md)
            chunks = []
            i = 1
            while i + 1 < len(parts):
                role = "user" if parts[i] == "Utilizador" else "ai"
                content = parts[i + 1].strip()
                if content:
                    html_part = markdown.markdown(content, extensions=["fenced_code", "tables", "sane_lists", "nl2br"])
                    chunks.append(f'<div class="msg-row msg-{role}"><div class="bubble bubble-{role}">{html_part}</div></div>')
                i += 2
            body = "\n".join(chunks)
        else:
            body = markdown.markdown(
                render_md, extensions=["fenced_code", "tables", "sane_lists", "nl2br"]
            )
        fsize = int(get_config().get("chat_font_size", 13))
        if not self.reply_box.is_visible():
            self.reply_box.show_all()
        if getattr(self, "_reply_ready", False):
            js = f"document.body.style.fontSize='{fsize}px'; document.body.innerHTML = {json.dumps(body)}; window.scrollTo(0, document.body.scrollHeight); document.body.scrollHeight;"
            self.reply_view.evaluate_javascript(js, -1, None, None, None, self._on_reply_height, None)
        else:
            self._reply_ready = True
            html_out = REPLY_HTML.replace("font-size: 13px;", f"font-size: {fsize}px;").replace("%BODY%", body)
            self.reply_view.load_html(html_out, "file:///")
        self._sync_chat_btn()

    def refresh_status(self):
        def _fetch():
            try:
                with urllib.request.urlopen(f"{API_BASE}/api/status", timeout=2) as r:
                    data = json.loads(r.read().decode())
                txt = f"{data.get('wifi', 'N/D')} · {data.get('battery', 'AC')} · {data.get('time', '--:--')}"
                if self.topbar:
                    GLib.idle_add(self.topbar.update_status, data)
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()
        return True

    def _prefetch_models(self):
        try:
            with urllib.request.urlopen(f"{API_BASE}/api/agy/models", timeout=5) as r:
                self.agy_models_cache = json.loads(r.read().decode())
        except Exception:
            pass

    def build_at_matches(self, token):
        q = token.lstrip("@").lower()
        matches = []
        for base in [HOME] + SEARCH_DIRS:
            if not base.exists():
                continue
            try:
                for p in base.iterdir():
                    if p.name.startswith("."):
                        continue
                    rel = str(p).replace(str(HOME) + "/", "")
                    if not q or q in rel.lower():
                        icon_name = "folder" if p.is_dir() else "text-x-generic"
                        matches.append(("mention", f"@{rel}", t("attach_agy"), icon_name, f"@{rel} "))
                    if len(matches) >= 7:
                        return matches
            except OSError:
                pass
        return matches

    def build_matches(self, query):
        q_raw = query.lower()
        q = q_raw.strip()
        if not q:
            return []

        # If typing @mention, autocomplete files/folders for agy
        last_word = query.split()[-1] if query.split() else ""
        if last_word.startswith("@"):
            return self.build_at_matches(last_word)

        # Interactive sub-completion for /model <filter> and /mode <filter>
        if q_raw.startswith("/model "):
            filt = q_raw[7:].strip()
            if not self.agy_models_cache:
                self._prefetch_models()
            return [
                ("slash", m["label"], t("activate_model", id=m["id"]), "preferences-system", f"ask_now:/model {m['label']}")
                for m in self.agy_models_cache
                if not filt or filt in m["label"].lower() or filt in m["id"].lower()
            ][:8]

        if q_raw.startswith("/mode "):
            filt = q_raw[6:].strip()
            return [
                ("slash", mode_id, desc, "preferences-system", f"ask_now:/mode {mode_id}")
                for mode_id, desc in AGENT_MODES
                if not filt or filt in mode_id
            ]

        if q_raw.startswith("#lang "):
            return [
                ("slash", "pt", "Português (PT-PT)", "preferences-desktop-locale", "ask_now:#lang pt"),
                ("slash", "en", "English (EN)", "preferences-desktop-locale", "ask_now:#lang en"),
            ]

        if q_raw.startswith("#kb "):
            layouts = [("pt", "Português"), ("us", "English (US)"), ("es", "Español"), ("fr", "Français"), ("gb", "English (UK)")]
            filt = q_raw[4:].strip().lower()
            return [
                ("slash", code, name, "input-keyboard", f"ask_now:#kb {code}")
                for code, name in layouts
                if not filt or filt in code or filt in name.lower()
            ]

        if q_raw.startswith("#tz "):
            zones = ["Europe/Lisbon", "UTC", "Europe/London", "Europe/Madrid", "America/Sao_Paulo", "America/New_York"]
            filt = q_raw[4:].strip().lower()
            return [
                ("slash", z, t("tz_btn"), "preferences-system-time", f"ask_now:#tz {z}")
                for z in zones
                if not filt or filt in z.lower()
            ]

        # If prompt starts with #, autocomplete AI-OS system commands
        if q.startswith("#") and " " not in q:
            return [
                ("slash", cmd, desc, "preferences-system", action)
                for cmd, desc, action in get_system_commands()
                if q in cmd.lower() or q.lstrip("#") in desc.lower()
            ][:15]

        # If prompt starts with /, autocomplete agy slash commands
        if q.startswith("/") and " " not in q:
            return [
                ("slash", cmd, desc, "utilities-terminal", action)
                for cmd, desc, action in get_slash_commands()
                if q in cmd.lower() or q.lstrip("/") in desc.lower()
            ][:15]

        # If prompt contains @ or slash/hash with args, pass directly to agy
        if q.startswith(("/", "#")) or "@" in q:
            return []

        matches = []

        # 1. System actions
        for title, sub, icon_name, action in get_system_actions():
            if q in title.lower() or q in sub.lower():
                matches.append(("action", title, sub, icon_name, action))

        # 2. Desktop apps
        for name, cmd, icon_name in self.apps:
            if q in name.lower():
                matches.append(("app", name, t("open_app", cmd=cmd.split()[0]), icon_name, cmd))

        # 3. Files in user folders
        count = 0
        for base in SEARCH_DIRS:
            if not base.exists():
                continue
            for p in base.iterdir():
                if q in p.name.lower():
                    icon_name = "folder" if p.is_dir() else "text-x-generic"
                    matches.append(("file", p.name, str(p).replace(str(HOME), "~"), icon_name, str(p)))
                    count += 1
                    if count >= 6:
                        break
            if count >= 6:
                break

        return matches[:7]

    def on_search_changed(self, *_):
        raw = self.get_query_text()
        self.placeholder_lbl.set_visible(len(raw) == 0)
        text = raw.strip()
        if not text:
            self.results = []
            self._last_match_keys = None
            self.hide_results()
            return

        if self.reply_box.is_visible():
            self.reply_box.hide()
            self._sync_chat_btn()
        query_for_match = raw.lstrip() if raw.lstrip().startswith(("/", "#")) else text
        matches = self.build_matches(query_for_match)
        if not matches:
            self.results = []
            self._last_match_keys = None
            was_open = self.list_scroll.is_visible() or self.draft_box.is_visible() or self.divider.is_visible()
            self.list_scroll.hide()
            if "\n" in raw or len(raw) > 54:
                self.draft_view.show()
                self.draft_box.show()
                self.divider.show()
                adj = self.draft_box.get_vadjustment()
                GLib.idle_add(lambda: (adj.set_value(adj.get_upper()), False)[1])
            else:
                self.draft_box.hide()
                self.divider.hide()
                if was_open:
                    self.resize(720, 1)
            return

        self.draft_box.hide()

        keys = [(k, t) for k, t, _, _, _ in matches]
        if keys == self._last_match_keys and self.list_scroll.is_visible():
            self.results = matches
            return

        self._last_match_keys = keys
        self.results = matches
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        for kind, title, sub, icon_name, _ in self.results:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            ico.set_pixel_size(22)
            hbox.pack_start(ico, False, False, 0)

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            t_lbl.set_max_width_chars(68)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            s_lbl.set_max_width_chars(76)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)

        self.divider.show()
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)

    def toggle_all_apps(self, *_):
        if self.list_scroll.is_visible() and self._last_match_keys == "__all_apps__":
            self.hide_results()
            return
        self.reply_box.hide()
        self.draft_box.hide()
        matches = [("action", title, sub, icon_name, action) for title, sub, icon_name, action in get_system_actions()]
        for name, cmd, icon_name in sorted(self.apps, key=lambda a: a[0].lower()):
            matches.append(("app", name, t("open_app", cmd=cmd.split()[0]), icon_name, cmd))
        self.results = matches
        self._last_match_keys = "__all_apps__"
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for _, title, sub, icon_name, _ in matches:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            ico.set_pixel_size(20)
            hbox.pack_start(ico, False, False, 0)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)
        self.divider.show()
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)
        self._sync_chat_btn()

    def toggle_ai_profiles(self, *_):
        if self.list_scroll.is_visible() and self._last_match_keys == "__profiles__":
            self.hide_results()
            return
        self.reply_box.hide()
        self.draft_box.hide()
        matches = [
            ("profile", *t("prof_fast"), "media-playback-start", "fast"),
            ("profile", *t("prof_deep"), "preferences-system", "deep"),
            ("profile", *t("prof_plan"), "document-edit", "plan"),
            ("fontsize", *t("font_small"), "zoom-out", 12),
            ("fontsize", *t("font_normal"), "zoom-original", 13),
            ("fontsize", *t("font_large"), "zoom-in", 15),
        ]
        self.results = matches
        self._last_match_keys = "__profiles__"
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for _, title, sub, icon_name, _ in matches:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            ico.set_pixel_size(20)
            hbox.pack_start(ico, False, False, 0)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)
        self.divider.show()
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)
        self._sync_chat_btn()

    def show_chats_history(self):
        chats_dir = HOME / ".ai-os" / "chats"
        files = sorted(chats_dir.glob("*.md"), reverse=True)[:8]
        if not files:
            self.show_reply(t("no_chats"))
            return
        self.reply_box.hide()
        matches = []
        for f in files:
            preview = t("saved_chat")
            try:
                lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
                if lines:
                    preview = lines[0][:70]
            except OSError:
                pass
            matches.append(("chat", f.stem, preview, "document-open-recent", f.stem))
        self.results = matches
        self._last_match_keys = None
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for _, title, sub, icon_name, _ in matches:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            ico.set_pixel_size(20)
            hbox.pack_start(ico, False, False, 0)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            s_lbl.set_max_width_chars(70)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)
        self.divider.show()
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)

    def on_entry_key_press(self, _, event):
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval in (Gdk.KEY_h, Gdk.KEY_H):
            self.show_chats_history()
            return True
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                return False
            self.on_activate()
            return True
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down):
            if not self.history:
                return True
            if event.keyval == Gdk.KEY_Up:
                self.hist_idx = max(0, self.hist_idx - 1)
            else:
                self.hist_idx = min(len(self.history), self.hist_idx + 1)
            txt = self.history[self.hist_idx] if self.hist_idx < len(self.history) else ""
            self.entry_buf.set_text(txt)
            self.entry_buf.place_cursor(self.entry_buf.get_end_iter())
            return True
        return False

    def _on_clip_change(self, clipboard, _event):
        txt = clipboard.wait_for_text()
        if not txt or not txt.strip():
            return
        txt = txt.strip()
        if txt in self.clip_history:
            self.clip_history.remove(txt)
        self.clip_history.insert(0, txt)
        self.clip_history = self.clip_history[:15]

    def show_clip_history(self):
        if not self.clip_history:
            self.show_reply(t("no_clip"))
            return
        self.reply_box.hide()
        matches = []
        for idx, txt in enumerate(self.clip_history):
            one_line = " ".join(txt.splitlines())[:75]
            matches.append(("clip", one_line, f"{len(txt)} chars", "edit-paste", txt))
        self.results = matches
        self._last_match_keys = None
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for _, title, sub, icon_name, _ in matches:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            ico.set_pixel_size(20)
            hbox.pack_start(ico, False, False, 0)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)
        self.divider.show()
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)

    def toggle_all_apps(self, *_):
        if self.list_scroll.is_visible() and self._last_match_keys == "__all_apps__":
            self.hide_results()
            return
        self.reply_box.hide()
        self.draft_box.hide()
        matches = [("action", title, sub, icon_name, action) for title, sub, icon_name, action in get_system_actions()]
        for name, cmd, icon_name in sorted(self.apps, key=lambda a: a[0].lower()):
            matches.append(("app", name, t("open_app", cmd=cmd.split()[0]), icon_name, cmd))
        self.results = matches
        self._last_match_keys = "__all_apps__"
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for _, title, sub, icon_name, _ in matches:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            ico.set_pixel_size(20)
            hbox.pack_start(ico, False, False, 0)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)
        self.divider.show()
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)
        self._sync_chat_btn()

    def toggle_ai_profiles(self, *_):
        if self.list_scroll.is_visible() and self._last_match_keys == "__profiles__":
            self.hide_results()
            return
        self.reply_box.hide()
        self.draft_box.hide()
        matches = [
            ("profile", *t("prof_fast"), "media-playback-start", "fast"),
            ("profile", *t("prof_deep"), "preferences-system", "deep"),
            ("profile", *t("prof_plan"), "document-edit", "plan"),
            ("fontsize", *t("font_small"), "zoom-out", 12),
            ("fontsize", *t("font_normal"), "zoom-original", 13),
            ("fontsize", *t("font_large"), "zoom-in", 15),
        ]
        self.results = matches
        self._last_match_keys = "__profiles__"
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for _, title, sub, icon_name, _ in matches:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            ico.set_pixel_size(20)
            hbox.pack_start(ico, False, False, 0)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)
        self.divider.show()
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)
        self._sync_chat_btn()

    def show_chats_history(self):
        chats_dir = HOME / ".ai-os" / "chats"
        files = sorted(chats_dir.glob("*.md"), reverse=True)[:8]
        if not files:
            self.show_reply(t("no_chats"))
            return
        self.reply_box.hide()
        matches = []
        for f in files:
            preview = t("saved_chat")
            try:
                lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
                if lines:
                    preview = lines[0][:70]
            except OSError:
                pass
            matches.append(("chat", f.stem, preview, "document-open-recent", f.stem))
        self.results = matches
        self._last_match_keys = None
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for _, title, sub, icon_name, _ in matches:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            ico.set_pixel_size(20)
            hbox.pack_start(ico, False, False, 0)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            s_lbl.set_max_width_chars(70)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)
        self.divider.show()
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)

    def on_entry_key_press(self, _, event):
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval in (Gdk.KEY_h, Gdk.KEY_H):
            self.show_chats_history()
            return True
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                return False
            self.on_activate()
            return True
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down):
            if not self.history:
                return True
            if event.keyval == Gdk.KEY_Up:
                self.hist_idx = max(0, self.hist_idx - 1)
            else:
                self.hist_idx = min(len(self.history), self.hist_idx + 1)
            txt = self.history[self.hist_idx] if self.hist_idx < len(self.history) else ""
            self.entry_buf.set_text(txt)
            self.entry_buf.place_cursor(self.entry_buf.get_end_iter())
            return True
        return False

    def execute_item(self, item):
        kind, _, _, _, payload = item
        if kind == "ai":
            self.send_to_ai(payload)
        elif kind == "action":
            if isinstance(payload, str) and payload.startswith("ask:"):
                self.send_to_ai(payload[4:])
            else:
                payload()
                self.clear_query()
                self.hide_results()
        elif kind == "app":
            subprocess.Popen(payload, shell=True)
            self.clear_query()
            self.hide_results()
        elif kind == "slash":
            if payload == "local:chats":
                self.clear_query()
                self.show_chats_history()
            elif payload == "local:apps":
                self.clear_query()
                self.toggle_all_apps()
            elif payload == "local:audit":
                self.clear_query()
                self.hide_results()
                af = HOME / ".ai-os" / "audit.log"
                if not af.exists():
                    self.show_reply(t("audit_empty"))
                else:
                    lines = af.read_text(encoding="utf-8", errors="ignore").splitlines()[-15:]
                    self.show_reply("```text\n" + "\n".join(reversed(lines)) + "\n```")
            elif payload == "local:clip":
                self.clear_query()
                self.show_clip_history()
            elif payload == "local:lock":
                self.clear_query()
                self.hide_results()
                subprocess.Popen(["/opt/ai-os/spotlight/lock.sh"])
            elif payload == "local:screenshot":
                self.clear_query()
                self.hide_results()
                self.hide()
                subprocess.Popen(["/opt/ai-os/spotlight/screenshot.sh", "--delay"])
            elif payload == "local:displays":
                self.clear_query()
                self.hide_results()
                subprocess.Popen(["xrandr", "--auto"])
                self.show_reply(t("displays_ok"))
            elif payload == "local:settings":
                self.clear_query()
                self.hide_results()
                open_settings_dialog(self)
            elif payload == "local:reboot":
                self.clear_query()
                self.hide_results()
                subprocess.Popen(["sudo", "reboot"])
            elif payload == "local:poweroff":
                self.clear_query()
                self.hide_results()
                subprocess.Popen(["sudo", "poweroff"])
            elif payload == "local:update":
                self.clear_query()
                self.hide_results()
                self.show_reply(t("update_started"))
                def _run_upd():
                    try:
                        subprocess.check_call(["/opt/ai-os/spotlight/update.sh"])
                        GLib.idle_add(self.show_reply, t("update_done"))
                    except Exception as e:
                        GLib.idle_add(self.show_reply, t("update_fail", err=e))
                threading.Thread(target=_run_upd, daemon=True).start()
            elif payload == "local:login":
                self.clear_query()
                self.hide_results()
                self.start_agy_login()
            elif payload == "local:logout":
                self.clear_query()
                self.hide_results()
                self.do_agy_logout()
            elif payload.startswith("ask_now:"):
                cmd_txt = payload.split(":", 1)[1]
                self.clear_query()
                self.hide_results()
                self.send_to_ai(cmd_txt)
            else:
                fill_txt = payload.split(":", 1)[1]
                self.entry_buf.set_text(fill_txt)
                self.entry_buf.place_cursor(self.entry_buf.get_end_iter())
                self.entry.grab_focus()
        elif kind == "mention":
            raw = self.get_query_text()
            parts = raw.rsplit(None, 1)
            new_text = (parts[0] + " " + payload) if len(parts) == 2 else payload
            self.entry_buf.set_text(new_text)
            end_iter = self.entry_buf.get_end_iter()
            self.entry_buf.place_cursor(end_iter)
            self.entry.grab_focus()
        elif kind == "profile":
            self.clear_query()
            self.hide_results()
            def _set_p():
                try:
                    req = urllib.request.Request(
                        f"{API_BASE}/api/agy/profile",
                        data=json.dumps({"profile": payload}).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    res = json.loads(urllib.request.urlopen(req, timeout=8).read().decode())
                    name = t(f"prof_{payload}")[0]
                    GLib.idle_add(self.show_reply, t("prof_set", name=name, model=res.get("model", "")))
                except Exception as e:
                    GLib.idle_add(self.show_reply, f"Erro: {e}")
            threading.Thread(target=_set_p, daemon=True).start()
        elif kind == "fontsize":
            update_config(chat_font_size=payload)
            self.clear_query()
            self.hide_results()
            self.show_reply(t("font_set", px=payload))
        elif kind == "clip":
            self._clipboard.set_text(payload, -1)
            self.clear_query()
            self.hide_results()
            subprocess.Popen(["notify-send", "AI-OS", t("clip_copied")])
        elif kind == "chat":
            self.current_chat_id = payload
            update_config(last_chat_id=payload)
            chat_path = HOME / ".ai-os" / "chats" / f"{payload}.md"
            if chat_path.exists():
                self.show_reply(chat_path.read_text(encoding="utf-8")[-3000:])
            self.clear_query()
        elif kind == "file":
            subprocess.Popen(["xdg-open", payload])
            self.clear_query()
            self.hide_results()

    def start_agy_login(self):
        self.show_reply(t("processing"))
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text("", -1)

        def _worker():
            try:
                req = urllib.request.Request(f"{API_BASE}/api/agy/auth/login_start", data=b"{}", method="POST")
                with urllib.request.urlopen(req, timeout=20) as r:
                    res = json.loads(r.read().decode())
                if res.get("ok"):
                    self.awaiting_auth_code = True
                    GLib.idle_add(self.show_reply, t("login_started"))
                    GLib.timeout_add(400, self._poll_auth_clipboard)
                else:
                    GLib.idle_add(self.show_reply, t("login_fail", err=res.get("error", "unknown")))
            except Exception as e:
                GLib.idle_add(self.show_reply, t("login_fail", err=e))

        threading.Thread(target=_worker, daemon=True).start()

    def _poll_auth_clipboard(self):
        if not self.awaiting_auth_code:
            return False
        clip = (Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text() or "").strip()
        if clip.startswith("4/0") and len(clip) > 20:
            self.submit_agy_code(clip)
            return False
        return True

    def submit_agy_code(self, code):
        self.awaiting_auth_code = False
        self.show_reply(t("processing"))

        def _worker():
            try:
                req = urllib.request.Request(
                    f"{API_BASE}/api/agy/auth/login_code",
                    data=json.dumps({"code": code}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as r:
                    res = json.loads(r.read().decode())
                if res.get("ok"):
                    GLib.idle_add(self.clear_query)
                    GLib.idle_add(self.show_reply, t("login_ok"))
                    GLib.timeout_add(2500, lambda: (self.hide_results(), False)[1])
                else:
                    GLib.idle_add(self.show_reply, t("login_fail", err=res.get("error", "unknown")))
            except Exception as e:
                GLib.idle_add(self.show_reply, t("login_fail", err=e))

        threading.Thread(target=_worker, daemon=True).start()

    def do_agy_logout(self):
        self.awaiting_auth_code = False
        try:
            req = urllib.request.Request(f"{API_BASE}/api/agy/auth/logout", data=b"{}", method="POST")
            urllib.request.urlopen(req, timeout=5).read()
            self.show_reply(t("logout_ok"))
        except Exception as e:
            self.show_reply(t("login_fail", err=e))

    def _set_busy(self, busy: bool):
        self.send_btn.set_visible(not busy)
        self.stop_btn.set_visible(busy)
        self.entry.set_editable(not busy)
        self.entry.set_sensitive(not busy)
        if self.draft_view:
            self.draft_view.set_editable(not busy)
            self.draft_view.set_sensitive(not busy)
        self.placeholder_lbl.set_text(t("processing") if busy else t("placeholder"))
        if not busy:
            self.entry.grab_focus()
        if self.topbar:
            self.topbar.set_ai_busy(busy)

    def on_stop_ai(self, *_):
        self._cancelled = True
        self._set_busy(False)
        self.show_reply(t("ai_stopped"))
        req = urllib.request.Request(f"{API_BASE}/api/ask_stop", data=b"{}", method="POST")
        threading.Thread(target=lambda: urllib.request.urlopen(req, timeout=3).read(), daemon=True).start()

    def send_to_ai(self, prompt):
        if prompt.strip().startswith(("#lang ", "/lang ")):
            if self.topbar and not self.topbar._confirm_lang_switch():
                return
            lang = set_lang(prompt.split(None, 1)[1].strip())
            if self.topbar:
                self.topbar.apply_lang()
            self.apply_lang()
            self.show_reply(t("lang_changed"))
            return

        if prompt.strip().startswith("#kb "):
            layout = prompt.split(None, 1)[1].strip().lower()
            subprocess.Popen(["setxkbmap", layout])
            update_config(kb_layout=layout)
            self.clear_query()
            self.show_reply(t("kb_changed", layout=layout))
            return

        if prompt.strip().startswith("#tz "):
            tz = prompt.split(None, 1)[1].strip()
            subprocess.Popen(["sudo", "timedatectl", "set-timezone", tz])
            subprocess.Popen(["sudo", "timedatectl", "set-ntp", "true"])
            self.clear_query()
            self.show_reply(t("tz_ok", tz=tz))
            return

        if prompt.strip() in ("/new", "/clear"):
            self.current_chat_id = None
            update_config(last_chat_id=None)
        self._pending_prompt = prompt
        self._cancelled = False
        self._save_history(prompt)
        self.clear_query()
        self.show_reply(t("processing"), live_stream=True)
        self._set_busy(True)

        def _worker():
            import time
            acc = []
            last_render = 0.0
            final_reply = None
            try:
                req = urllib.request.Request(
                    f"{API_BASE}/api/ask_stream",
                    data=json.dumps({"prompt": prompt, "chat_id": self.current_chat_id}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=180) as r:
                    for raw in r:
                        line = raw.decode("utf-8", errors="ignore").strip()
                        if not line:
                            continue
                        ev = json.loads(line)
                        if ev.get("done"):
                            self.current_chat_id = ev.get("chat_id")
                            if self.current_chat_id:
                                update_config(last_chat_id=self.current_chat_id)
                            final_reply = ev.get("reply", "Concluído.")
                        elif ev.get("status") and not acc:
                            raw_t = str(ev["status"])
                            friendly = {
                                "run_command": "sistema" if get_lang() == "pt" else "system",
                                "read_file": "leitura" if get_lang() == "pt" else "reading",
                                "view_file": "leitura" if get_lang() == "pt" else "reading",
                                "write_file": "escrita" if get_lang() == "pt" else "writing",
                                "edit_file": "edição" if get_lang() == "pt" else "editing",
                                "search_web": "pesquisa web" if get_lang() == "pt" else "web search",
                            }.get(raw_t, "ação" if get_lang() == "pt" else "action")
                            GLib.idle_add(self.show_reply, f"⚙ {t('step_tool', tool=friendly)}", True)
                        elif ev.get("delta"):
                            acc.append(ev["delta"])
                            now = time.monotonic()
                            if now - last_render > 0.18:
                                last_render = now
                                GLib.idle_add(self.show_reply, "".join(acc), True)
                reply = final_reply or "".join(acc) or "Concluído."
            except Exception as e:
                reply = f"Erro ao contactar backend AI-OS: {e}"

            if not self._cancelled:
                GLib.idle_add(self.show_reply, reply)
            GLib.idle_add(self._set_busy, False)
            if not self.has_toplevel_focus() and not self._cancelled:
                subprocess.Popen(["notify-send", "AI-OS Spotlight", t("done_notify")])

        threading.Thread(target=_worker, daemon=True).start()

    def on_activate(self, *_):
        row = self.listbox.get_selected_row()
        if row and self.results:
            self.execute_item(self.results[row.get_index()])
        else:
            text = self.get_query_text().strip()
            if text:
                if self.awaiting_auth_code:
                    self.clear_query()
                    self.submit_agy_code(text)
                else:
                    self.send_to_ai(text)

    def on_row_activated(self, _, row):
        if row and self.results:
            self.execute_item(self.results[row.get_index()])

    def on_key_press(self, _, event):
        key = event.keyval
        if key == Gdk.KEY_Escape:
            self.clear_query()
            self.hide_results()
            return True
        if key in (Gdk.KEY_Down, Gdk.KEY_Up) and self.results:
            cur = self.listbox.get_selected_row()
            idx = cur.get_index() if cur else 0
            nxt = min(idx + 1, len(self.results) - 1) if key == Gdk.KEY_Down else max(idx - 1, 0)
            target = self.listbox.get_row_at_index(nxt)
            if target:
                self.listbox.select_row(target)
                alloc = target.get_allocation()
                vadj = self.list_scroll.get_vadjustment()
                vadj.clamp_page(alloc.y, alloc.y + alloc.height)
            return True
        return False


def main():
    topbar = TopBarWindow()
    win = SpotlightWindow(topbar=topbar)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, lambda *_: (win.focus_spotlight(), True)[1])
    Gtk.main()


if __name__ == "__main__":
    main()
