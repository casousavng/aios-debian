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
from i18n import get_lang, set_lang, t

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, GLib, Gtk, Pango, WebKit2  # noqa: E402

REPLY_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  html, body { background: transparent; margin: 0; padding: 0; color: #f1f5f9;
    font-family: system-ui, -apple-system, sans-serif; font-size: 13px; line-height: 1.5;
    overflow-wrap: anywhere; word-break: break-word; max-width: 100%; overflow-x: hidden; }
  body { padding: 4px 6px; }
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
    background-color: rgba(20, 26, 34, 0.74);
    border: 1px solid rgba(255, 255, 255, 0.30);
    border-radius: 22px;
    padding: 8px 16px;
}
.search-row {
    padding: 4px 4px;
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
.search-icon {
    color: #67e8f9;
    font-size: 20px;
    font-weight: 700;
    margin-right: 10px;
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
    font-size: 16px;
    padding: 2px 10px;
    border-radius: 10px;
}
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
    ("Bloquear Ecrã", "Bloquear sessão (Super+L)", "system-lock-screen", lambda: subprocess.Popen(["i3lock", "-c", "0f1117"])),
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
        (*t("act_browser"), "web-browser", lambda: subprocess.Popen(["chromium"])),
        (*t("act_sysinfo"), "utilities-system-monitor", f"ask:{t('act_sysinfo_prompt')}"),
        (*t("act_lock"), "system-lock-screen", lambda: subprocess.Popen(["i3lock", "-c", "0f1117"])),
        (*t("act_reboot"), "system-reboot", lambda: subprocess.Popen(["sudo", "reboot"])),
        (*t("act_poweroff"), "system-shutdown", lambda: subprocess.Popen(["sudo", "poweroff"])),
    ]


def get_slash_commands():
    return [
        ("/usage", t("slash_usage"), "ask_now:/usage"),
        ("/chats", t("slash_chats"), "local:chats"),
        ("/model ", t("slash_model"), "fill:/model "),
        ("/mode ", t("slash_mode"), "fill:/mode "),
        ("/lang ", t("slash_lang"), "fill:/lang "),
        ("/login", t("slash_login"), "local:login"),
        ("/logout", t("slash_logout"), "local:logout"),
        ("/lock", t("slash_lock"), "local:lock"),
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
            for wid, app_name, title, is_active in wins:
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

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("popover-card")
        card.set_size_request(270, -1)
        self.add(card)

        self.vol_lbl = Gtk.Label(label=t("volume"), xalign=0)
        self.vol_lbl.get_style_context().add_class("pop-title")
        card.pack_start(self.vol_lbl, False, False, 0)
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.vol_scale.set_value(70)
        self.vol_scale.set_draw_value(False)
        self.vol_scale.connect("value-changed", self.on_vol_changed)
        card.pack_start(self.vol_scale, False, False, 0)

        self.bri_lbl = Gtk.Label(label=t("brightness"), xalign=0)
        self.bri_lbl.get_style_context().add_class("pop-title")
        card.pack_start(self.bri_lbl, False, False, 0)
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 5)
        self.bri_scale.set_value(100)
        self.bri_scale.set_draw_value(False)
        self.bri_scale.connect("value-changed", self.on_bri_changed)
        card.pack_start(self.bri_scale, False, False, 0)

        self.info_lbl = Gtk.Label(label=t("podman_ready"), xalign=0)
        self.info_lbl.get_style_context().add_class("pop-sub")
        card.pack_start(self.info_lbl, False, False, 0)

        self.lock_btn = Gtk.Button(label=t("lock_btn"))
        self.lock_btn.get_style_context().add_class("reply-btn")
        self.lock_btn.connect("clicked", lambda *_: (self.hide(), subprocess.Popen(["i3lock", "-c", "0f1117"])))
        card.pack_start(self.lock_btn, False, False, 0)
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
        GLib.timeout_add(300, self._maybe_hide)
        return False

    def _maybe_hide(self):
        if not self._hovering:
            self.hide()
        return False

    def refresh_labels(self):
        self.vol_lbl.set_text(t("volume"))
        self.bri_lbl.set_text(t("brightness"))
        self.lock_btn.set_label(t("lock_btn"))

    def on_vol_changed(self, scale):
        val = int(scale.get_value())
        subprocess.Popen(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val}%"], stderr=subprocess.DEVNULL)

    def on_bri_changed(self, scale):
        val = max(20, min(100, int(scale.get_value())))
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
        try:
            ps = subprocess.check_output(["podman", "ps", "-q"], text=True, stderr=subprocess.DEVNULL).splitlines()
            self.info_lbl.set_text(f"Contentores Podman ativos: {len(ps)}")
        except Exception:
            self.info_lbl.set_text("Podman pronto")
        self.move(geom.x + geom.width - 284, geom.y + 34)
        self.show_all()


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
        self.show_all()
        self.refresh_windows()
        GLib.timeout_add_seconds(1, self.refresh_windows)

    def refresh_windows(self):
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
        for line in out.splitlines():
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            wid, _, wm_class, _, title = parts
            if "AITopBar" in wm_class or "AISpotlight" in wm_class:
                continue
            if wm_class == "pcmanfm.Pcmanfm" and title == "pcmanfm":
                continue
            is_active = int(wid, 16) == active_int
            app_name = wm_class.split(".")[-1] if "." in wm_class else wm_class
            wins.append((wid, app_name, title, is_active))

        if wins == self._last_windows:
            return True
        self._last_windows = wins

        for child in self.dots_box.get_children():
            self.dots_box.remove(child)
        for wid, app_name, title, is_active in wins:
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
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=t("lang_confirm_title"),
        )
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
        self.current_chat_id = None
        self.awaiting_auth_code = False
        self.last_reply_md = ""
        self.history = self._load_history()
        self.hist_idx = len(self.history)
        self.results = []
        self._last_match_keys = None
        threading.Thread(target=self._prefetch_models, daemon=True).start()

        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.card.get_style_context().add_class("spotlight-card")
        self.card.set_size_request(720, -1)
        self.add(self.card)

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
        actions_row.pack_end(self.litemd_btn, False, False, 0)
        actions_row.pack_end(self.copy_btn, False, False, 0)
        self.reply_box.pack_start(actions_row, False, False, 0)

        self.reply_view = WebKit2.WebView()
        self.reply_view.set_background_color(Gdk.RGBA(0, 0, 0, 0))
        wsettings = self.reply_view.get_settings()
        wsettings.set_enable_javascript(True)
        self.reply_view.connect("load-changed", self.on_reply_loaded)
        self.reply_view.set_size_request(-1, 48)
        self.reply_box.pack_start(self.reply_view, True, True, 0)
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

        self.divider = Gtk.Box()
        self.divider.get_style_context().add_class("divider")
        self.card.pack_start(self.divider, False, False, 0)

        # Bottom Input / Command Row
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        top_row.get_style_context().add_class("search-row")

        icon = Gtk.Label(label="✦")
        icon.get_style_context().add_class("search-icon")
        top_row.pack_start(icon, False, False, 0)

        self.entry_scroll = Gtk.ScrolledWindow()
        self.entry_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.entry_scroll.get_style_context().add_class("clean-scroll")
        self.entry_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)
        self.entry_scroll.set_min_content_height(22)
        self.entry_scroll.set_max_content_height(24)
        self.entry_scroll.set_size_request(-1, 24)
        self.entry_scroll.set_vexpand(False)
        self.entry_scroll.set_propagate_natural_height(False)
        self.entry_scroll.set_valign(Gtk.Align.CENTER)

        self.entry = Gtk.TextView()
        self.entry.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.entry.set_accepts_tab(False)
        self.entry.set_pixels_above_lines(1)
        self.entry.set_pixels_below_lines(1)
        self.entry.get_style_context().add_class("search-input")
        self.entry_buf = self.entry.get_buffer()
        self.entry_buf.connect("changed", self.on_search_changed)
        self.entry.connect("key-press-event", self.on_entry_key_press)
        self.entry_scroll.add(self.entry)

        overlay = Gtk.Overlay()
        overlay.set_size_request(-1, 24)
        overlay.add(self.entry_scroll)
        self.placeholder_lbl = Gtk.Label(label=t("placeholder"), xalign=0)
        self.placeholder_lbl.get_style_context().add_class("search-placeholder")
        self.placeholder_lbl.set_no_show_all(True)
        self.placeholder_lbl.show()
        overlay.add_overlay(self.placeholder_lbl)
        overlay.set_overlay_pass_through(self.placeholder_lbl, True)

        if self.topbar:
            self.topbar.on_lang_changed = self.apply_lang

        v_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        v_wrap.pack_start(overlay, True, False, 0)
        top_row.pack_start(v_wrap, True, True, 0)

        vadj = self.entry_scroll.get_vadjustment()
        self.mini_scroll = Gtk.Scrollbar(orientation=Gtk.Orientation.VERTICAL, adjustment=vadj)
        self.mini_scroll.get_style_context().add_class("mini-scroll")
        self.mini_scroll.set_size_request(6, 24)
        self.mini_scroll.set_valign(Gtk.Align.CENTER)
        self.mini_scroll.set_no_show_all(True)
        vadj.connect("changed", lambda a: self.mini_scroll.set_visible(a.get_upper() > a.get_page_size() + 2))
        top_row.pack_start(self.mini_scroll, False, False, 0)

        self.status_lbl = Gtk.Label(label="⌘ Space")
        self.status_lbl.get_style_context().add_class("keycap-badge")
        top_row.pack_start(self.status_lbl, False, False, 0)

        send_btn = Gtk.Button(label="→")
        send_btn.get_style_context().add_class("send-arrow")
        send_btn.set_can_focus(False)
        send_btn.connect("clicked", self.on_activate)
        top_row.pack_end(send_btn, False, False, 0)

        self.card.pack_start(top_row, False, False, 0)

        self._last_pos = None
        self.connect("key-press-event", self.on_key_press)
        self.connect("button-press-event", lambda *_: (self.focus_spotlight(), False)[1])
        self.connect("show", self.on_show)
        self.connect("delete-event", lambda *_: True)
        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("size-allocate", lambda *_: self.dock_bottom())

        self.show_all()
        self.hide_results()
        self.dock_bottom()
        self.refresh_status()
        GLib.timeout_add_seconds(10, self.refresh_status)
        GLib.timeout_add_seconds(600, self.refresh_wallpaper)

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
        self.show()
        self.present_with_time(Gdk.CURRENT_TIME)
        self.set_opacity(1.0)
        self.entry.grab_focus()

    def refresh_wallpaper(self):
        subprocess.Popen(["python3", "/opt/ai-os/spotlight/wallpaper.py"])
        return True

    def hide_results(self):
        self.divider.hide()
        self.list_scroll.hide()
        self.reply_box.hide()
        self.resize(720, 1)

    def on_reply_loaded(self, view, event):
        if event != WebKit2.LoadEvent.FINISHED:
            return
        view.evaluate_javascript(
            "document.body.scrollHeight", -1, None, None, None, self._on_reply_height, None
        )

    def _on_reply_height(self, view, res, _):
        try:
            js_res = view.evaluate_javascript_finish(res)
            h = int(js_res.to_int32())
            view.set_size_request(-1, max(36, min(h + 8, 320)))
        except Exception:
            view.set_size_request(-1, 140)

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
        if not self.last_reply_md:
            return
        out = HOME / "Temp" / "ultima-resposta.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.last_reply_md, encoding="utf-8")
        subprocess.Popen(["litemd", str(out)])

    def show_reply(self, text):
        self.last_reply_md = text
        self.divider.show()
        self.list_scroll.hide()
        body = markdown.markdown(
            text, extensions=["fenced_code", "tables", "sane_lists", "nl2br"]
        )
        self.reply_view.load_html(REPLY_HTML.replace("%BODY%", body), "file:///")
        self.reply_box.show_all()

    def refresh_status(self):
        def _fetch():
            try:
                with urllib.request.urlopen(f"{API_BASE}/api/status", timeout=2) as r:
                    data = json.loads(r.read().decode())
                txt = f"{data.get('wifi', 'N/D')} · {data.get('battery', 'AC')} · {data.get('time', '--:--')}"
                GLib.idle_add(self.status_lbl.set_tooltip_text, txt)
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

        if q_raw.startswith("/lang "):
            return [
                ("slash", "pt", "Português (PT-PT)", "preferences-desktop-locale", "ask_now:/lang pt"),
                ("slash", "en", "English (EN)", "preferences-desktop-locale", "ask_now:/lang en"),
            ]

        # If prompt starts with /, autocomplete agy slash commands
        if q.startswith("/") and " " not in q:
            return [
                ("slash", cmd, desc, "utilities-terminal", action)
                for cmd, desc, action in get_slash_commands()
                if q in cmd.lower() or q.lstrip("/") in desc.lower()
            ][:15]

        # If prompt contains @ or slash with args, pass directly to agy
        if q.startswith("/") or "@" in q:
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

        self.reply_box.hide()
        query_for_match = raw.lstrip() if raw.lstrip().startswith("/") else text
        matches = self.build_matches(query_for_match)
        if not matches:
            self.results = []
            if self._last_match_keys:
                self._last_match_keys = None
                self.divider.hide()
                self.list_scroll.hide()
                self.resize(720, 1)
            return

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
            elif payload == "local:lock":
                self.clear_query()
                self.hide_results()
                subprocess.Popen(["i3lock", "-c", "0f1117"])
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
        elif kind == "chat":
            self.current_chat_id = payload
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

    def send_to_ai(self, prompt):
        if prompt.strip().startswith("/lang "):
            if self.topbar and not self.topbar._confirm_lang_switch():
                return
            lang = set_lang(prompt.split(None, 1)[1].strip())
            if self.topbar:
                self.topbar.apply_lang()
            self.apply_lang()
            self.show_reply(t("lang_changed"))
            return

        self._save_history(prompt)
        self.show_reply(t("processing"))
        if self.topbar:
            GLib.idle_add(self.topbar.set_ai_busy, True)

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
                            final_reply = ev.get("reply", "Concluído.")
                        elif ev.get("delta"):
                            acc.append(ev["delta"])
                            now = time.monotonic()
                            if now - last_render > 0.18:
                                last_render = now
                                GLib.idle_add(self.show_reply, "".join(acc))
                reply = final_reply or "".join(acc) or "Concluído."
            except Exception as e:
                reply = f"Erro ao contactar backend AI-OS: {e}"

            GLib.idle_add(self.show_reply, reply)
            if self.topbar:
                GLib.idle_add(self.topbar.set_ai_busy, False)
            if not self.has_toplevel_focus():
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
