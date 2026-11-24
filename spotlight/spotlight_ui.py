#!/usr/bin/env python3
"""AI-OS Native macOS-style Spotlight launcher & AI command bar."""
import glob
import json
import math
import os
import re
import signal
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import cairo
import gi
import markdown
from i18n import get_config, get_lang, human_cron, is_dangerous_prompt, set_lang, t, update_config

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango  # noqa: E402

WebKit2 = None

REPLY_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  html, body { background: transparent; margin: 0; padding: 0; color: #f1f5f9;
    font-family: system-ui, -apple-system, sans-serif; font-size: 13px; line-height: 1.5;
    overflow-wrap: anywhere; word-break: break-word; max-width: 100%; overflow-x: hidden; }
  body { padding: 4px 10px 6px 6px; }
  p:first-child { margin-top: 0; }
  p:last-child { margin-bottom: 0; }
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
  pre { position: relative; background: rgba(10, 14, 20, 0.55); border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px; padding: 26px 10px 10px; overflow-x: auto; margin: 0.45em 0; }
  pre code { background: transparent; padding: 0; color: #e2e8f0; }
  .code-copy-btn { position: absolute; top: 5px; right: 6px; background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.16); border-radius: 6px; color: #cbd5e1;
    font-size: 10px; padding: 1px 7px; cursor: pointer; font-family: system-ui, sans-serif; }
  .code-copy-btn:hover { background: rgba(103, 232, 249, 0.20); color: #ffffff; }
  table { border-collapse: collapse; width: 100%; margin: 0.4em 0; font-size: 12px; }
  th, td { border: 1px solid rgba(255,255,255,0.14); padding: 4px 8px; text-align: left; }
  th { background: rgba(255,255,255,0.08); color: #ffffff; }
  a { color: #67e8f9; text-decoration: none; }
  a:hover { text-decoration: underline; }
  img { max-width: 100%; max-height: 220px; border-radius: 10px; cursor: pointer; display: block; margin: 6px 0 4px; border: 1px solid rgba(255,255,255,0.14); }
  .img-card { position: relative; display: inline-block; max-width: 100%; margin: 4px 0; }
  .img-actions { display: flex; gap: 6px; margin-top: 4px; }
  .img-act-btn { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(103, 232, 249, 0.32);
    border-radius: 6px; color: #67e8f9; font-size: 11px; padding: 2px 9px; cursor: pointer; font-family: system-ui, sans-serif; }
  .img-act-btn:hover { background: rgba(103, 232, 249, 0.22); color: #ffffff; }
  .msg-row { display: flex; width: 100%; margin: 8px 0; }
  .msg-user { justify-content: flex-end; }
  .msg-ai { justify-content: flex-start; }
  .bubble { position: relative; padding: 8px 12px; border-radius: 14px; }
  .bubble-user { max-width: 84%; background: rgba(103, 232, 249, 0.14); border: 1px solid rgba(103, 232, 249, 0.34); color: #f8fafc; border-bottom-right-radius: 4px; }
  .bubble-ai { width: 100%; max-width: 100%; background: transparent; border: none; padding: 2px 2px 14px 2px; color: #e2e8f0; }
  .msg-copy-btn { position: absolute; right: 4px; bottom: 2px; opacity: 0; transition: opacity 0.15s;
    background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255,255,255,0.16); border-radius: 6px;
    color: #cbd5e1; font-size: 10px; padding: 1px 6px; cursor: pointer; font-family: system-ui, sans-serif; }
  .bubble:hover .msg-copy-btn { opacity: 1; }
  .msg-copy-btn:hover { background: rgba(103, 232, 249, 0.22); color: #ffffff; }
  .bubble p:first-child { margin-top: 0; }
  .bubble p:last-child { margin-bottom: 0; }
  .file-chip { display: inline-flex; align-items: center; gap: 4px; background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(103, 232, 249, 0.35);
    color: #67e8f9; border-radius: 8px; padding: 1px 7px; font-size: 11px; margin: 0 2px; vertical-align: middle; }
  .thinking-pill { display: inline-flex; align-items: center; gap: 7px; color: #94a3b8; font-size: 12px; }
  .live-dot { width: 7px; height: 7px; border-radius: 50%; background: #67e8f9;
    animation: pulseDot 1.1s ease-in-out infinite; display: inline-block; }
  @keyframes pulseDot { 0%, 100% { opacity: 0.35; transform: scale(0.85); } 50% { opacity: 1; transform: scale(1.15); } }
</style>
<script>
window.copyText = function(txt) {
  var ta = document.createElement('textarea');
  ta.value = txt;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } catch(e) {}
  document.body.removeChild(ta);
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(txt).catch(function(){});
  }
};
window.enhanceReply = function() {
  document.querySelectorAll('pre').forEach(function(pre) {
    if (pre.querySelector('.code-copy-btn')) return;
    var btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.textContent = 'Copiar';
    btn.onclick = function(e) {
      e.stopPropagation();
      var code = pre.querySelector('code');
      var txt = code ? code.innerText : pre.innerText;
      window.copyText(txt);
      btn.textContent = '✓';
      setTimeout(function() { btn.textContent = 'Copiar'; }, 1200);
    };
    pre.appendChild(btn);
  });
  document.querySelectorAll('.bubble-ai').forEach(function(b) {
    if (b.querySelector('.msg-copy-btn') || b.querySelector('.thinking-pill')) return;
    var mb = document.createElement('button');
    mb.className = 'msg-copy-btn';
    mb.textContent = 'Copiar';
    mb.onclick = function(e) {
      e.stopPropagation();
      var clone = b.cloneNode(true);
      clone.querySelectorAll('.msg-copy-btn, .code-copy-btn').forEach(function(x){ x.remove(); });
      window.copyText(clone.innerText.trim());
      mb.textContent = '✓';
      setTimeout(function() { mb.textContent = 'Copiar'; }, 1200);
    };
    b.appendChild(mb);
  });
  document.querySelectorAll('a[href^="file://"]').forEach(function(a) {
    var href = a.getAttribute('href') || '';
    if (/\.(png|jpe?g|webp|gif|bmp|svg)(\?.*)?$/i.test(href) && !a.dataset.thumbInjected) {
      a.dataset.thumbInjected = '1';
      var im = document.createElement('img');
      im.src = href;
      a.parentNode.insertBefore(im, a.nextSibling);
    }
  });
  document.querySelectorAll('img').forEach(function(img) {
    var raw = img.getAttribute('src') || '';
    if (raw.startsWith('/')) img.src = 'file://' + raw;
    if (img.dataset.boundPreview) return;
    img.dataset.boundPreview = '1';
    var card = document.createElement('div');
    card.className = 'img-card';
    img.parentNode.insertBefore(card, img);
    card.appendChild(img);
    var bar = document.createElement('div');
    bar.className = 'img-actions';
    var bPrev = document.createElement('button');
    bPrev.className = 'img-act-btn';
    bPrev.textContent = 'Preview';
    bPrev.onclick = function(e) { e.preventDefault(); e.stopPropagation(); window.location.href = 'aios-preview://' + encodeURIComponent(img.src); };
    var bSave = document.createElement('button');
    bSave.className = 'img-act-btn';
    bSave.textContent = 'Guardar';
    bSave.onclick = function(e) { e.preventDefault(); e.stopPropagation(); window.location.href = 'aios-save://' + encodeURIComponent(img.src); };
    bar.appendChild(bPrev);
    bar.appendChild(bSave);
    card.appendChild(bar);
    img.onclick = function(e) {
      e.preventDefault();
      e.stopPropagation();
      window.location.href = 'aios-preview://' + encodeURIComponent(img.src);
    };
  });
};
</script></head><body>%BODY%<script>window.enhanceReply();</script></body></html>"""

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
.seg-bar {
    background-color: rgba(255, 255, 255, 0.06);
    border-radius: 9px;
    padding: 2px;
}
.seg-btn {
    background-image: none;
    background-color: transparent;
    border: none;
    box-shadow: none;
    border-radius: 7px;
    color: #94a3b8;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 8px;
}
.seg-btn-active {
    background-color: rgba(103, 232, 249, 0.16);
    color: #67e8f9;
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
    background-color: transparent;
    border: none;
    border-radius: 0;
    padding: 2px 2px 4px 2px;
    margin: 2px 0 4px 0;
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
button.btn-primary {
    background-image: none;
    background-color: rgba(14, 165, 233, 0.22);
    border: 1px solid rgba(103, 232, 249, 0.50);
    border-radius: 7px;
    color: #7dd3fc;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 10px;
    min-height: 0;
    min-width: 0;
}
button.btn-primary:hover {
    background-color: rgba(14, 165, 233, 0.36);
    color: #ffffff;
}
.ai-reply-text {
    color: #ffffff;
    font-size: 13px;
}
.tb-clock {
    font-feature-settings: "tnum";
    min-width: 44px;
}
scale {
    padding: 6px 8px;
}
scale trough {
    background-color: rgba(255, 255, 255, 0.14);
    border-radius: 999px;
    min-height: 4px;
    border: none;
}
scale highlight {
    background-image: linear-gradient(90deg, #0891b2, #67e8f9);
    background-color: #67e8f9;
    border-radius: 999px;
    min-height: 4px;
}
scale slider {
    background-image: none;
    background-color: #f8fafc;
    border: 1.5px solid #67e8f9;
    border-radius: 999px;
    min-width: 12px;
    min-height: 12px;
    margin: -5px 0;
    box-shadow: none;
}
"""


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
        (*t("act_files"), "system-file-manager", lambda: subprocess.Popen(["nemo", str(HOME)])),
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
        ("/new", t("slash_new"), "local:new_chat"),
        ("/clear", t("slash_clear"), "local:new_chat"),
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
        ("#ports", t("slash_ports"), "local:ports"),
        ("#podman", t("slash_podman"), "local:podman"),
        ("#clean", t("slash_clean"), "local:clean"),
        ("#proj", t("slash_proj"), "local:proj"),
        ("#grep ", t("slash_grep"), "fill:#grep "),
        ("#health", t("slash_health"), "local:health"),
        ("#keys", t("slash_keys"), "local:keys"),
        ("#notif", t("slash_notif"), "local:notif"),
        ("#clip", t("slash_clip"), "local:clip"),
        ("#screenshot", t("slash_screenshot"), "local:screenshot"),
        ("#displays", t("slash_displays"), "local:displays"),
        ("#lang ", t("slash_lang"), "fill:#lang "),
        ("#kb ", t("slash_kb"), "fill:#kb "),
        ("#tz ", t("slash_tz"), "fill:#tz "),
        ("#remind ", t("slash_remind"), "fill:#remind "),
        ("#reminders", t("slash_reminders"), "local:reminders"),
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
        self._trigger_hovering = False
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
                    elif "pcmanfm" in low or "nemo" in low:
                        icon_name = "system-file-manager"
                    elif "xterm" in low:
                        icon_name = "utilities-terminal"
                    elif "litemd" in low:
                        icon_name = "text-x-generic"
                    elif "aios-settings" in low:
                        icon_name = "preferences-system"
                    else:
                        icon_name = "application-x-executable"

                    row_w = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                    btn = Gtk.Button()
                    btn.get_style_context().add_class("reply-btn")
                    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                    ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
                    ico.set_pixel_size(16)
                    lbl = Gtk.Label(label=title, xalign=0)
                    lbl.set_ellipsize(Pango.EllipsizeMode.END)
                    lbl.set_max_width_chars(26)
                    box.pack_start(ico, False, False, 0)
                    box.pack_start(lbl, True, True, 0)
                    if is_active:
                        dot = Gtk.Label(label="●")
                        dot.get_style_context().add_class("topbar-logo")
                        box.pack_end(dot, False, False, 0)
                    btn.add(box)
                    btn.connect("clicked", lambda _, w=wid: (self.hide(), subprocess.Popen(["wmctrl", "-i", "-a", w])))
                    xb = Gtk.Button(label="×")
                    xb.get_style_context().add_class("reply-btn")
                    xb.connect("clicked", lambda _, w=wid: (subprocess.Popen(["wmctrl", "-i", "-c", w]), self.hide()))
                    row_w.pack_start(btn, True, True, 0)
                    row_w.pack_end(xb, False, False, 0)
                    self.card.pack_start(row_w, False, False, 0)

        self.move(geom.x + 10, geom.y + 34)
        self.show_all()


class RemindersPopover(Gtk.Window):
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

        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.card.get_style_context().add_class("popover-card")
        self.card.set_size_request(330, -1)
        self.add(self.card)

        seg = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        seg.set_homogeneous(True)
        seg.get_style_context().add_class("seg-bar")
        self.tab_notif_btn = Gtk.Button(label=t("bell_tab_notif"))
        self.tab_notif_btn.set_can_focus(False)
        self.tab_notif_btn.get_style_context().add_class("seg-btn")
        self.tab_notif_btn.get_style_context().add_class("seg-btn-active")
        self.tab_auto_btn = Gtk.Button(label=t("bell_tab_auto"))
        self.tab_auto_btn.set_can_focus(False)
        self.tab_auto_btn.get_style_context().add_class("seg-btn")
        seg.pack_start(self.tab_notif_btn, True, True, 0)
        seg.pack_start(self.tab_auto_btn, True, True, 0)
        self.card.pack_start(seg, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_vhomogeneous(False)
        self.card.pack_start(self.stack, True, True, 0)

        # Tab 1: Notificações
        tab_notif = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        nhdr_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.notif_hdr = Gtk.Label(label=t("bell_notif_hdr"), xalign=0)
        self.notif_hdr.get_style_context().add_class("pop-title")
        self.dnd_btn = Gtk.Button(label=t("dnd_btn"))
        self.dnd_btn.get_style_context().add_class("reply-btn")
        self.dnd_btn.connect("clicked", self._toggle_dnd)
        self.clear_btn = Gtk.Button(label=t("bell_clear"))
        self.clear_btn.get_style_context().add_class("reply-btn")
        self.clear_btn.connect("clicked", self._clear_notifs)
        nhdr_row.pack_start(self.notif_hdr, True, True, 0)
        nhdr_row.pack_end(self.clear_btn, False, False, 0)
        nhdr_row.pack_end(self.dnd_btn, False, False, 0)
        self.on_dnd_changed = None
        tab_notif.pack_start(nhdr_row, False, False, 0)
        self.notif_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        tab_notif.pack_start(self.notif_box, False, False, 0)
        self.stack.add_named(tab_notif, "notif")

        # Tab 2: Automações (Lembretes & Crons)
        tab_auto = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.sched_hdr = Gtk.Label(label=t("bell_sched_hdr"), xalign=0)
        self.sched_hdr.get_style_context().add_class("pop-title")
        tab_auto.pack_start(self.sched_hdr, False, False, 0)
        self.sched_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        tab_auto.pack_start(self.sched_box, False, False, 0)
        self.stack.add_named(tab_auto, "auto")

        self.tab_notif_btn.connect("clicked", lambda *_: self._switch_tab("notif"))
        self.tab_auto_btn.connect("clicked", lambda *_: self._switch_tab("auto"))

        self._hovering = False
        self._trigger_hovering = False
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
        GLib.timeout_add(240, self._maybe_hide)
        return False

    def _maybe_hide(self):
        if not self._hovering and not self._trigger_hovering:
            self.hide()
        return False

    def _place_top_right(self, min_w=330):
        display = Gdk.Display.get_default()
        mon = display.get_primary_monitor() or display.get_monitor(0)
        geom = mon.get_geometry()
        pw = max(self.get_size()[0], self.get_preferred_width()[1], min_w)
        self.move(geom.x + geom.width - pw - 10, geom.y + 34)

    def show_at(self, _geom):
        if self.is_visible():
            return
        self.refresh_labels()
        self.show_all()
        self._place_top_right(330)
        self._load_async()

    def _switch_tab(self, name):
        self.stack.set_visible_child_name(name)
        for btn, key in [(self.tab_notif_btn, "notif"), (self.tab_auto_btn, "auto")]:
            ctx = btn.get_style_context()
            if key == name:
                ctx.add_class("seg-btn-active")
            else:
                ctx.remove_class("seg-btn-active")
        self.resize(330, 1)
        self._place_top_right(330)

    def refresh_labels(self):
        self.sched_hdr.set_text(t("bell_sched_hdr"))
        self.notif_hdr.set_text(t("bell_notif_hdr"))
        self.tab_notif_btn.set_label(t("bell_tab_notif"))
        self.tab_auto_btn.set_label(t("bell_tab_auto"))
        self.clear_btn.set_label(t("bell_clear"))

    def toggle_at(self, geom):
        if self.is_visible():
            self.hide()
            return
        self.refresh_labels()
        self.move(geom.x + geom.width - 344, geom.y + 34)
        self.show_all()
        self._load_async()

    def _toggle_dnd(self, *_):
        subprocess.run(["dunstctl", "set-paused", "toggle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._sync_dnd_ui()

    def _sync_dnd_ui(self):
        paused = False
        try:
            paused = subprocess.check_output(["dunstctl", "is-paused"], text=True, stderr=subprocess.DEVNULL).strip() == "true"
        except Exception:
            pass
        ctx = self.dnd_btn.get_style_context()
        ctx.add_class("seg-btn-active") if paused else ctx.remove_class("seg-btn-active")
        if self.on_dnd_changed:
            self.on_dnd_changed(paused)

    def _clear_notifs(self, *_):
        def _w():
            try:
                req = urllib.request.Request(f"{API_BASE}/api/notifications", method="DELETE")
                urllib.request.urlopen(req, timeout=2).read()
            except Exception:
                pass
            GLib.idle_add(self._load_async)
        threading.Thread(target=_w, daemon=True).start()

    def _delete_sched(self, kind, sid):
        ep = "reminders" if kind == "rem" else "crons"
        def _w():
            try:
                req = urllib.request.Request(f"{API_BASE}/api/{ep}/{sid}", method="DELETE")
                urllib.request.urlopen(req, timeout=2).read()
            except Exception:
                pass
            GLib.idle_add(self._load_async)
        threading.Thread(target=_w, daemon=True).start()

    def _toggle_cron(self, cid):
        def _w():
            try:
                req = urllib.request.Request(f"{API_BASE}/api/crons/{cid}/toggle", data=b"{}", method="POST")
                urllib.request.urlopen(req, timeout=2).read()
            except Exception:
                pass
            GLib.idle_add(self._load_async)
        threading.Thread(target=_w, daemon=True).start()

    def _load_async(self):
        def _fetch():
            rems, crons, notifs = [], [], []
            for ep, target in [("reminders", rems), ("crons", crons), ("notifications", notifs)]:
                try:
                    with urllib.request.urlopen(f"{API_BASE}/api/{ep}", timeout=2) as r:
                        target.extend(json.loads(r.read().decode()))
                except Exception:
                    pass
            def _apply():
                if not self.is_visible():
                    return False
                for c in self.sched_box.get_children():
                    self.sched_box.remove(c)
                if not rems and not crons:
                    lbl = Gtk.Label(label=t("reminders_empty"), xalign=0)
                    lbl.get_style_context().add_class("pop-sub")
                    self.sched_box.add(lbl)
                for it in rems[:5]:
                    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                    lbl = Gtk.Label(label=f"• {it.get('message', '')[:32]}", xalign=0)
                    lbl.get_style_context().add_class("pop-sub")
                    xb = Gtk.Button(label="✕")
                    xb.get_style_context().add_class("reply-btn")
                    xb.connect("clicked", lambda _, sid=it.get("id"): self._delete_sched("rem", sid))
                    row.pack_start(lbl, True, True, 0)
                    row.pack_end(xb, False, False, 0)
                    self.sched_box.add(row)
                for it in crons[:5]:
                    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                    when = human_cron(it.get("schedule", ""))
                    is_paused = bool(it.get("paused"))
                    prefix = "[Pausado] " if is_paused else "• "
                    lbl = Gtk.Label(label=f"{prefix}{when} · {it.get('label', '')}", xalign=0)
                    lbl.set_ellipsize(Pango.EllipsizeMode.END)
                    lbl.set_max_width_chars(30)
                    lbl.get_style_context().add_class("pop-sub")
                    pb = Gtk.Button()
                    p_ico = Gtk.Image.new_from_icon_name(
                        "media-playback-start-symbolic" if is_paused else "media-playback-pause-symbolic",
                        Gtk.IconSize.MENU,
                    )
                    p_ico.set_pixel_size(12)
                    pb.add(p_ico)
                    pb.get_style_context().add_class("reply-btn")
                    pb.connect("clicked", lambda _, cid=it.get("id"): self._toggle_cron(cid))
                    xb = Gtk.Button(label="×")
                    xb.get_style_context().add_class("reply-btn")
                    xb.connect("clicked", lambda _, sid=it.get("id"): self._delete_sched("cron", sid))
                    row.pack_start(lbl, True, True, 0)
                    row.pack_end(xb, False, False, 0)
                    row.pack_end(pb, False, False, 0)
                    self.sched_box.add(row)
                self.sched_box.show_all()
                auto_cnt = len(rems) + len(crons)
                notif_cnt = len(notifs)
                self.tab_auto_btn.set_label(f"{t('bell_tab_auto')} ({auto_cnt})" if auto_cnt else t("bell_tab_auto"))
                self.tab_notif_btn.set_label(f"{t('bell_tab_notif')} ({notif_cnt})" if notif_cnt else t("bell_tab_notif"))

                for c in self.notif_box.get_children():
                    self.notif_box.remove(c)
                if not notifs:
                    lbl = Gtk.Label(label=t("notif_empty"), xalign=0)
                    lbl.get_style_context().add_class("pop-sub")
                    self.notif_box.add(lbl)
                else:
                    for line in reversed(notifs[-5:]):
                        short = line.split(" | ", 1)[-1] if " | " in line else line
                        lbl = Gtk.Label(label=short[:42], xalign=0)
                        lbl.get_style_context().add_class("pop-sub")
                        self.notif_box.add(lbl)
                self.notif_box.show_all()
                return False
            GLib.idle_add(_apply)
        threading.Thread(target=_fetch, daemon=True).start()


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
        card.set_size_request(310, -1)
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

        seg = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        seg.set_homogeneous(True)
        seg.get_style_context().add_class("seg-bar")
        self.tab_audio_btn = Gtk.Button(label=t("sec_audio_display"))
        self.tab_conn_btn = Gtk.Button(label=t("sec_conn"))
        self.tab_sys_btn = Gtk.Button(label=t("sec_sys"))
        for idx, b in enumerate((self.tab_audio_btn, self.tab_conn_btn, self.tab_sys_btn)):
            b.set_can_focus(False)
            b.get_style_context().add_class("seg-btn")
            if idx == 0:
                b.get_style_context().add_class("seg-btn-active")
            seg.pack_start(b, True, True, 0)
        card.pack_start(seg, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_vhomogeneous(False)
        card.pack_start(self.stack, True, True, 0)

        # Tab 1: Audio & Display
        tab_audio = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.vol_lbl = Gtk.Label(label=f"{t('volume')}: 70%", xalign=0)
        self.vol_lbl.get_style_context().add_class("pop-sub")
        tab_audio.pack_start(self.vol_lbl, False, False, 0)
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.vol_scale.set_value(70)
        self.vol_scale.set_draw_value(False)
        self.vol_scale.connect("value-changed", self.on_vol_changed)
        tab_audio.pack_start(self.vol_scale, False, False, 0)

        self.bri_lbl = Gtk.Label(label=f"{t('brightness')}: 100%", xalign=0)
        self.bri_lbl.get_style_context().add_class("pop-sub")
        tab_audio.pack_start(self.bri_lbl, False, False, 0)
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 5)
        self.bri_scale.set_value(100)
        self.bri_scale.set_draw_value(False)
        self.bri_scale.connect("value-changed", self.on_bri_changed)
        tab_audio.pack_start(self.bri_scale, False, False, 0)

        self.audio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        tab_audio.pack_start(self.audio_box, False, False, 0)
        self.stack.add_named(tab_audio, "audio")

        # Tab 2: Connections
        tab_conn = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.wifi_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        tab_conn.pack_start(self.wifi_box, False, False, 0)

        self.bt_btn = Gtk.Button(label=f"{t('bt_label')}: Toggle")
        self.bt_btn.get_style_context().add_class("reply-btn")
        self.bt_btn.connect("clicked", self._on_bt_toggle)
        tab_conn.pack_start(self.bt_btn, False, False, 0)

        self.bt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        tab_conn.pack_start(self.bt_box, False, False, 0)
        self.stack.add_named(tab_conn, "conn")

        # Tab 3: System 2x2 quick actions
        tab_sys = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        grid = Gtk.Grid(column_spacing=6, row_spacing=6, column_homogeneous=True)
        self.displays_btn = Gtk.Button(label=t("displays_short"))
        self.displays_btn.get_style_context().add_class("reply-btn")
        self.displays_btn.connect("clicked", lambda *_: (self.hide(), open_displays_dialog()))
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
        tab_sys.pack_start(grid, False, False, 0)

        self.info_lbl = Gtk.Label(label=t("podman_ready"), xalign=0)
        self.info_lbl.get_style_context().add_class("pop-sub")
        tab_sys.pack_start(self.info_lbl, False, False, 0)
        self.stack.add_named(tab_sys, "sys")

        self.tab_audio_btn.connect("clicked", lambda *_: self._switch_tab("audio"))
        self.tab_conn_btn.connect("clicked", lambda *_: self._switch_tab("conn"))
        self.tab_sys_btn.connect("clicked", lambda *_: self._switch_tab("sys"))

        self._hovering = False
        self._trigger_hovering = False
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
        if not self._hovering and not self._trigger_hovering:
            self.hide()
        return False

    def _place_top_right(self, min_w=310):
        display = Gdk.Display.get_default()
        mon = display.get_primary_monitor() or display.get_monitor(0)
        geom = mon.get_geometry()
        pw = max(self.get_size()[0], self.get_preferred_width()[1], min_w)
        self.move(geom.x + geom.width - pw - 10, geom.y + 34)

    def _switch_tab(self, name):
        self.stack.set_visible_child_name(name)
        for btn, key in [(self.tab_audio_btn, "audio"), (self.tab_conn_btn, "conn"), (self.tab_sys_btn, "sys")]:
            ctx = btn.get_style_context()
            if key == name:
                ctx.add_class("seg-btn-active")
            else:
                ctx.remove_class("seg-btn-active")
        self.resize(310, 1)
        self._place_top_right(310)

    def refresh_labels(self):
        self.tz_btn.set_label(t("tz_btn"))
        self.tab_audio_btn.set_label(t("sec_audio_display"))
        self.tab_conn_btn.set_label(t("sec_conn"))
        self.tab_sys_btn.set_label(t("sec_sys"))
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

    def _set_audio_sink(self, sink_id):
        def _w():
            try:
                req = urllib.request.Request(
                    f"{API_BASE}/api/audio/default",
                    data=json.dumps({"id": sink_id}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=3).read()
            except Exception:
                pass
        threading.Thread(target=_w, daemon=True).start()
        self.hide()

    def _toggle_bt_dev(self, mac):
        def _w():
            try:
                req = urllib.request.Request(
                    f"{API_BASE}/api/bt/connect",
                    data=json.dumps({"mac": mac}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=8).read()
            except Exception:
                pass
        threading.Thread(target=_w, daemon=True).start()
        self.hide()

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

    def show_at(self, _geom):
        if self.is_visible():
            return
        import datetime
        self.dt_lbl.set_text(datetime.datetime.now().strftime("%a %d %b · %H:%M"))
        kb = get_config().get("kb_layout", "pt").upper()
        self.info_lbl.set_text(f"{t('podman_ready')} · KB: {kb}")
        self.show_all()
        self._place_top_right(310)
        threading.Thread(target=self._populate_async, daemon=True).start()

    def toggle_at(self, geom):
        if self.is_visible():
            self.hide()
            return
        self.show_at(geom)

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
            if not self.is_visible() and not prompt.strip().startswith(("/usage", "/models", "/agents", "/help")):
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


def open_image_preview(parent, fpath):
    p = Path(fpath)
    if not p.exists():
        return
    dlg = Gtk.Dialog(title=p.name, transient_for=parent if isinstance(parent, Gtk.Window) else None, flags=0)
    dlg.set_wmclass("AI-OS", "AI-OS")
    dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
    dlg.set_default_size(520, 400)
    box = dlg.get_content_area()
    box.set_border_width(12)
    box.set_spacing(8)
    orig_pb = None
    try:
        orig_pb = GdkPixbuf.Pixbuf.new_from_file(str(p))
        w, h = orig_pb.get_width(), orig_pb.get_height()
        scale = min(680 / max(w, 1), 460 / max(h, 1), 1.0)
        disp_pb = orig_pb if scale >= 1.0 else orig_pb.scale_simple(max(1, int(w * scale)), max(1, int(h * scale)), GdkPixbuf.InterpType.BILINEAR)
        img_w = Gtk.Image.new_from_pixbuf(disp_pb)
        kb = round(p.stat().st_size / 1024, 1)
        meta = Gtk.Label(label=f"{p.name} · {w}×{h} px · {kb} KB", xalign=0)
        meta.get_style_context().add_class("pop-sub")
        box.pack_start(meta, False, False, 0)
        box.pack_start(img_w, True, True, 0)
    except Exception as e:
        box.pack_start(Gtk.Label(label=str(e)), True, True, 0)

    act_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    save_b = Gtk.Button(label=t("img_save_btn"))
    copy_b = Gtk.Button(label=t("img_copy_btn"))
    def _save(_):
        fc = Gtk.FileChooserDialog(title=t("img_save_btn"), parent=dlg, action=Gtk.FileChooserAction.SAVE)
        fc.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        fc.set_do_overwrite_confirmation(True)
        for d in (HOME / "Imagens", HOME / "Pictures", HOME / "Desktop"):
            if d.exists():
                fc.set_current_folder(str(d))
                break
        fc.set_current_name(p.name)
        if fc.run() == Gtk.ResponseType.OK:
            import shutil
            shutil.copy2(str(p), fc.get_filename())
            save_b.set_label(t("img_saved"))
            GLib.timeout_add(1600, lambda: (save_b.get_realized() and save_b.set_label(t("img_save_btn")), False)[1])
        fc.destroy()
    def _copy(_):
        if orig_pb:
            Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_image(orig_pb)
            copy_b.set_label(t("img_copied"))
            GLib.timeout_add(1600, lambda: (copy_b.get_realized() and copy_b.set_label(t("img_copy_btn")), False)[1])
    save_b.connect("clicked", _save)
    copy_b.connect("clicked", _copy)
    act_row.pack_start(save_b, True, True, 0)
    act_row.pack_start(copy_b, True, True, 0)
    box.pack_start(act_row, False, False, 0)
    dlg.add_buttons(t("close_btn"), Gtk.ResponseType.CLOSE)
    dlg.connect("response", lambda d, *_: d.destroy())
    dlg.show_all()
    dlg.present()


def open_displays_dialog(parent=None):
    outputs = []
    try:
        out = subprocess.check_output(["xrandr", "--query"], text=True, stderr=subprocess.DEVNULL)
        cur = None
        for line in out.splitlines():
            m = re.match(r"^(\S+)\s+connected\b", line)
            if m:
                cur = {"name": m.group(1), "modes": [], "active": None}
                outputs.append(cur)
                continue
            if cur and line.startswith("   "):
                parts = line.split()
                if parts and re.match(r"^\d+x\d+$", parts[0]):
                    if parts[0] not in cur["modes"]:
                        cur["modes"].append(parts[0])
                    if "*" in line:
                        cur["active"] = parts[0]
            elif line and not line.startswith(" "):
                cur = None
    except Exception:
        pass

    dlg = Gtk.Dialog(title=t("displays_short"), transient_for=parent, flags=0)
    dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
    dlg.set_default_size(340, -1)
    box = dlg.get_content_area()
    box.set_spacing(8)
    box.set_border_width(14)

    combos = []
    if not outputs:
        box.pack_start(Gtk.Label(label="xrandr N/D"), False, False, 0)
    for o in outputs:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label=o["name"], xalign=0)
        lbl.set_size_request(90, -1)
        combo = Gtk.ComboBoxText()
        for idx, mode in enumerate(o["modes"][:15]):
            combo.append_text(mode)
            if mode == o["active"]:
                combo.set_active(idx)
        if combo.get_active() < 0 and o["modes"]:
            combo.set_active(0)
        row.pack_start(lbl, False, False, 0)
        row.pack_start(combo, True, True, 0)
        box.pack_start(row, False, False, 0)
        combos.append((o["name"], combo))

    auto_b = Gtk.Button(label="Auto (xrandr --auto)")
    auto_b.connect("clicked", lambda *_: subprocess.Popen(["xrandr", "--auto"]))
    box.pack_start(auto_b, False, False, 0)

    dlg.add_buttons(t("cancel"), Gtk.ResponseType.CANCEL, t("confirm"), Gtk.ResponseType.OK)
    def _on_resp(d, resp):
        if resp == Gtk.ResponseType.OK:
            for oname, combo in combos:
                mode = combo.get_active_text()
                if mode:
                    subprocess.Popen(["xrandr", "--output", oname, "--mode", mode])
        d.destroy()
    dlg.connect("response", _on_resp)
    dlg.show_all()
    dlg.present()


def open_settings_dialog(spotlight):
    existing = getattr(spotlight, "_settings_dlg", None)
    if existing is not None:
        cur_fs = int(get_config().get("chat_font_size", 13))
        if getattr(spotlight, "_on_settings_font", None):
            spotlight._on_settings_font(cur_fs)
        existing.present()
        return
    dlg = Gtk.Dialog(title=t("settings_title"), flags=0)
    dlg.set_wmclass("aios-settings", "AI-OS Settings")
    spotlight._settings_dlg = dlg
    dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
    dlg.set_keep_above(True)
    dlg.set_default_size(480, 300)
    box = dlg.get_content_area()
    box.set_border_width(12)

    nb = Gtk.Notebook()
    box.pack_start(nb, True, True, 0)

    # Tab 1: AI Agent
    pt = get_lang() == "pt"
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
    prof_hdr = Gtk.Label(label="Modelo & Perfil" if pt else "Model & Profile", xalign=0)
    prof_hdr.get_style_context().add_class("pop-sub")
    tab_ai.pack_start(prof_hdr, False, False, 0)
    model_lbl = Gtk.Label(label=f"{cur_model or 'AI-OS'} ({cur_mode})", xalign=0)
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
                    txt = f"{res.get('model', '')} ({res.get('mode', 'auto')})"
                    GLib.idle_add(lambda: (model_lbl.get_realized() and model_lbl.set_text(txt), False)[1])
                except Exception:
                    pass
            threading.Thread(target=_w, daemon=True).start()
        b.connect("clicked", _set_prof)
        prof_row.pack_start(b, True, True, 0)
    tab_ai.pack_start(prof_row, False, False, 0)

    tab_ai.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)
    auth_hdr = Gtk.Label(label="Conta & Consumo" if pt else "Account & Usage", xalign=0)
    auth_hdr.get_style_context().add_class("pop-sub")
    tab_ai.pack_start(auth_hdr, False, False, 0)

    auth_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    login_b = Gtk.Button(label="Iniciar Sessão" if pt else "Sign In")
    login_b.connect("clicked", lambda *_: (dlg.destroy(), spotlight.start_agy_login()))
    logout_b = Gtk.Button(label="Terminar Sessão" if pt else "Sign Out")
    logout_b.connect("clicked", lambda *_: (dlg.destroy(), spotlight.do_agy_logout()))
    usage_b = Gtk.Button(label="Consumo" if pt else "Usage")
    usage_b.connect("clicked", lambda *_: (dlg.destroy(), spotlight.send_to_ai("/usage")))
    auth_row.pack_start(login_b, True, True, 0)
    auth_row.pack_start(logout_b, True, True, 0)
    auth_row.pack_start(usage_b, True, True, 0)
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

    _syncing_fs = [False]

    def _apply_fs_ui(px):
        fs_lbl.set_text(f"Texto do Chat: {px}px" if get_lang() == "pt" else f"Chat Text: {px}px")
        prev_lbl.set_markup(f'<span size="{px * 1024}">{prev_sample}</span>')

    def _on_fs(s):
        if _syncing_fs[0]:
            return
        px = int(s.get_value())
        _apply_fs_ui(px)
        update_config(chat_font_size=px)
        if spotlight.reply_view and getattr(spotlight, "_reply_ready", False):
            spotlight.reply_view.evaluate_javascript(
                f"document.body.style.fontSize='{px}px'; (() => {{ const r = document.createRange(); r.selectNodeContents(document.body); return Math.max(32, Math.ceil(r.getBoundingClientRect().height) + 12); }})();",
                -1, None, None, None, spotlight._on_reply_height, None,
            )

    def _sync_from_chat(px):
        _syncing_fs[0] = True
        try:
            fs_scale.set_value(px)
            _apply_fs_ui(px)
        finally:
            _syncing_fs[0] = False

    fs_scale.connect("value-changed", _on_fs)
    spotlight._on_settings_font = _sync_from_chat
    tab_ui.pack_start(fs_scale, False, False, 0)
    tab_ui.pack_start(prev_frame, False, False, 0)
    tab_ui.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

    lang_hdr = Gtk.Label(label="Idioma" if get_lang() == "pt" else "Language", xalign=0)
    lang_hdr.get_style_context().add_class("pop-sub")
    tab_ui.pack_start(lang_hdr, False, False, 0)
    lang_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    lang_btns = {}
    cur_lang = get_lang()
    for code, name in (("pt", "Português (PT-PT)"), ("en", "English (EN)")):
        lb = Gtk.Button(label=name)
        if code == cur_lang:
            lb.get_style_context().add_class("seg-btn-active")
        def _set_l(_, c=code):
            if spotlight.topbar and not spotlight.topbar._confirm_lang_switch():
                return
            set_lang(c)
            if spotlight.topbar:
                for p in (spotlight.topbar.popover, spotlight.topbar.rem_popover, spotlight.topbar.win_popover):
                    p.hide()
                spotlight.topbar.apply_lang()
            spotlight.apply_lang()
            keep = {spotlight, spotlight.topbar}
            if spotlight.topbar:
                keep.update((spotlight.topbar.popover, spotlight.topbar.rem_popover, spotlight.topbar.win_popover))
            for w in list(Gtk.Window.list_toplevels()):
                if w not in keep:
                    w.destroy()
            spotlight._settings_dlg = None
            spotlight._on_settings_font = None
        lb.connect("clicked", _set_l)
        lang_btns[code] = lb
        lang_row.pack_start(lb, True, True, 0)
    tab_ui.pack_start(lang_row, False, False, 0)

    kb_hdr = Gtk.Label(label="Teclado" if get_lang() == "pt" else "Keyboard", xalign=0)
    kb_hdr.get_style_context().add_class("pop-sub")
    tab_ui.pack_start(kb_hdr, False, False, 0)
    kb_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    kb_btns = {}
    cur_kb = get_config().get("kb_layout", "pt").lower()
    for code in ("pt", "us", "es", "fr", "gb"):
        kb_b = Gtk.Button(label=code.upper())
        if code == cur_kb:
            kb_b.get_style_context().add_class("seg-btn-active")
        def _set_kb(_, c=code):
            subprocess.Popen(["setxkbmap", c])
            update_config(kb_layout=c)
            for k, btn in kb_btns.items():
                ctx = btn.get_style_context()
                ctx.add_class("seg-btn-active") if k == c else ctx.remove_class("seg-btn-active")
        kb_b.connect("clicked", _set_kb)
        kb_btns[code] = kb_b
        kb_row.pack_start(kb_b, True, True, 0)
    tab_ui.pack_start(kb_row, False, False, 0)
    nb.append_page(tab_ui, Gtk.Label(label=t("settings_ui_tab")))

    # Tab 3: System (non-duplicated OS tools)
    tab_sys = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    tab_sys.set_border_width(14)
    diag_hdr = Gtk.Label(label="Hardware & Diagnóstico" if pt else "Hardware & Diagnostics", xalign=0)
    diag_hdr.get_style_context().add_class("pop-sub")
    tab_sys.pack_start(diag_hdr, False, False, 0)
    diag_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    disp_b = Gtk.Button(label=t("displays_short"))
    disp_b.connect("clicked", lambda *_: open_displays_dialog(dlg))
    health_b = Gtk.Button(label="Saúde do SO" if pt else "OS Health")
    health_b.connect("clicked", lambda *_: (dlg.destroy(), spotlight.execute_item(("slash", "#health", "", "", "local:health"))))
    keys_b = Gtk.Button(label="Atalhos" if pt else "Shortcuts")
    keys_b.connect("clicked", lambda *_: (dlg.destroy(), spotlight.execute_item(("slash", "#keys", "", "", "local:keys"))))
    for b in (disp_b, health_b, keys_b):
        diag_row.pack_start(b, True, True, 0)
    tab_sys.pack_start(diag_row, False, False, 0)

    tab_sys.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)
    maint_hdr = Gtk.Label(label="Manutenção & Containers" if pt else "Maintenance & Containers", xalign=0)
    maint_hdr.get_style_context().add_class("pop-sub")
    tab_sys.pack_start(maint_hdr, False, False, 0)
    maint_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    upd_b = Gtk.Button(label="Atualizar Sistema" if pt else "System Update")
    upd_b.connect("clicked", lambda *_: (dlg.destroy(), subprocess.Popen(["/opt/ai-os/spotlight/update.sh"])))
    podman_b = Gtk.Button(label="Podman")
    podman_b.connect("clicked", lambda *_: (dlg.destroy(), spotlight.execute_item(("slash", "#podman", "", "", "local:podman"))))
    clean_b = Gtk.Button(label=t("clean_btn"))
    clean_lbl = Gtk.Label(label="", xalign=0)
    clean_lbl.set_line_wrap(True)
    clean_lbl.get_style_context().add_class("muted")
    def _run_clean(*_):
        clean_b.set_sensitive(False)
        clean_lbl.set_text(t("clean_running"))
        def _bg():
            msg = t("clean_done", mb=0, items="-")
            try:
                req = urllib.request.Request(f"{API_BASE}/api/system/clean", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=45) as r:
                    res = json.loads(r.read().decode())
                items = ", ".join(res.get("cleaned") or []) or "-"
                msg = t("clean_done", mb=res.get("freed_mb", 0), items=items).replace("**", "")
            except Exception as e:
                msg = str(e)
            GLib.idle_add(lambda: (clean_lbl.set_text(msg), clean_b.set_sensitive(True), False)[2])
        threading.Thread(target=_bg, daemon=True).start()
    clean_b.connect("clicked", _run_clean)
    for b in (upd_b, podman_b, clean_b):
        maint_row.pack_start(b, True, True, 0)
    tab_sys.pack_start(maint_row, False, False, 0)
    tab_sys.pack_start(clean_lbl, False, False, 0)
    nb.append_page(tab_sys, Gtk.Label(label=t("settings_sys")))

    dlg.add_buttons(t("close_btn"), Gtk.ResponseType.CLOSE)
    def _close_dlg(d, *_):
        spotlight._on_settings_font = None
        spotlight._settings_dlg = None
        d.destroy()
        return True
    dlg.connect("response", _close_dlg)
    dlg.connect("delete-event", _close_dlg)
    dlg.connect("destroy", lambda *_: (setattr(spotlight, "_settings_dlg", None), setattr(spotlight, "_on_settings_font", None)))
    dlg.show_all()
    dlg.present()


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
        self.rem_popover = RemindersPopover()

        status_btn = Gtk.Button()
        status_btn.set_can_focus(False)
        status_btn.get_style_context().add_class("status-trigger")
        status_btn.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        status_btn.connect("enter-notify-event", lambda *_: (self.rem_popover.hide(), self.win_popover.hide(), setattr(self.popover, "_trigger_hovering", True), self.popover.show_at(geom), False)[4])
        status_btn.connect("leave-notify-event", lambda _, ev: False if ev.detail == Gdk.NotifyType.INFERIOR else (setattr(self.popover, "_trigger_hovering", False), GLib.timeout_add(240, self.popover._maybe_hide), False)[2])
        status_btn.connect("clicked", lambda *_: (self.rem_popover.hide(), self.popover.toggle_at(geom)))
        status_inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        status_btn.add(status_inner)
        bar.pack_end(status_btn, False, False, 0)

        self.bell_btn = Gtk.Button()
        bell_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        self.bell_ico = Gtk.Image.new_from_icon_name("notifications-symbolic", Gtk.IconSize.MENU)
        self.bell_ico.set_pixel_size(14)
        self.bell_lbl = Gtk.Label(label="")
        self.bell_lbl.get_style_context().add_class("topbar-item")
        bell_box.pack_start(self.bell_ico, False, False, 0)
        bell_box.pack_start(self.bell_lbl, False, False, 0)
        self.bell_btn.add(bell_box)
        self.rem_popover.on_dnd_changed = lambda p: self.bell_ico.set_from_icon_name(
            "notifications-disabled-symbolic" if p else "notifications-symbolic", Gtk.IconSize.MENU
        )
        self.rem_popover._sync_dnd_ui()
        self.bell_btn.set_can_focus(False)
        self.bell_btn.set_valign(Gtk.Align.CENTER)
        self.bell_btn.get_style_context().add_class("status-trigger")
        self.bell_btn.set_tooltip_text(t("bell_tip"))
        self.on_lang_changed = None
        self.bell_btn.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.bell_btn.connect("enter-notify-event", lambda *_: (self.popover.hide(), self.win_popover.hide(), setattr(self.rem_popover, "_trigger_hovering", True), self.rem_popover.show_at(geom), False)[4])
        self.bell_btn.connect("leave-notify-event", lambda _, ev: False if ev.detail == Gdk.NotifyType.INFERIOR else (setattr(self.rem_popover, "_trigger_hovering", False), GLib.timeout_add(240, self.rem_popover._maybe_hide), False)[2])
        self.bell_btn.connect("clicked", lambda *_: (self.popover.hide(), self.rem_popover.toggle_at(geom)))
        bar.pack_end(self.bell_btn, False, False, 0)

        self.clock_lbl = Gtk.Label(label="--:--")
        self.clock_lbl.set_width_chars(5)
        self.clock_lbl.set_xalign(0.5)
        self.clock_lbl.get_style_context().add_class("topbar-item")
        self.clock_lbl.get_style_context().add_class("tb-clock")
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
        self.connect("realize", lambda *_: self._set_top_strut(geom))
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.connect("scroll-event", self._on_topbar_scroll)
        self.show_all()
        self.refresh_windows()
        GLib.timeout_add_seconds(1, self.refresh_windows)

    def _set_top_strut(self, geom):
        win = self.get_window()
        if not win:
            return
        try:
            xid = str(win.get_xid())
            x0, x1 = geom.x, geom.x + geom.width - 1
            subprocess.Popen(["xprop", "-id", xid, "-f", "_NET_WM_STRUT", "32c", "-set", "_NET_WM_STRUT", "0,0,28,0"])
            subprocess.Popen(["xprop", "-id", xid, "-f", "_NET_WM_STRUT_PARTIAL", "32c", "-set", "_NET_WM_STRUT_PARTIAL", f"0,0,28,0,0,0,0,0,{x0},{x1},0,0"])
        except Exception:
            pass

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
            if (wm_class == "pcmanfm.Pcmanfm" and title == "pcmanfm") or wm_class == "nemo-desktop.Nemo-desktop":
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
            elif "pcmanfm" in low or "nemo" in low:
                icon_name, label_txt = "system-file-manager", "Ficheiros"
            elif "xterm" in low:
                icon_name, label_txt = "utilities-terminal", "Terminal"
            elif "litemd" in low:
                icon_name, label_txt = "text-x-generic", "LiteMD"
            elif "aios-settings" in low:
                icon_name, label_txt = "preferences-system", "Definições" if get_lang() == "pt" else "Settings"
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

    def apply_lang(self):
        self.bell_btn.set_tooltip_text(t("bell_tip"))
        self.rem_popover.refresh_labels()
        self.popover.refresh_labels()
        if self.win_popover.is_visible():
            self.win_popover.hide()
            self.win_popover.toggle_at(self.get_screen().get_monitor_geometry(0), self._last_windows or [])

    def set_ai_busy(self, busy: bool):
        self.logo_lbl.set_text("✦ AI..." if busy else "◉")

    def update_status(self, data):
        alerts = int(data.get("alerts", 0) or 0)
        self.bell_lbl.set_text(str(alerts) if alerts > 0 else "")
        self.bell_lbl.set_visible(alerts > 0)
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
        self.set_gravity(Gdk.Gravity.SOUTH)
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
        self.new_chat_btn = Gtk.Button(label=t("new_chat_btn"))
        self.new_chat_btn.get_style_context().add_class("btn-primary")
        self.new_chat_btn.set_can_focus(False)
        self.new_chat_btn.connect("clicked", lambda *_: self._reset_new_chat())
        actions_row.pack_start(self.new_chat_btn, False, False, 0)

        self.litemd_btn = Gtk.Button(label=t("open_litemd"))
        self.litemd_btn.get_style_context().add_class("reply-btn")
        self.litemd_btn.set_can_focus(False)
        self.litemd_btn.connect("clicked", self.on_open_litemd)
        font_inc_btn = Gtk.Button(label="A+")
        font_inc_btn.get_style_context().add_class("reply-btn")
        font_inc_btn.set_can_focus(False)
        font_inc_btn.connect("clicked", lambda *_: self._step_chat_font(1))
        font_dec_btn = Gtk.Button(label="A-")
        font_dec_btn.get_style_context().add_class("reply-btn")
        font_dec_btn.set_can_focus(False)
        font_dec_btn.connect("clicked", lambda *_: self._step_chat_font(-1))
        actions_row.pack_end(self.litemd_btn, False, False, 0)
        actions_row.pack_end(font_inc_btn, False, False, 0)
        actions_row.pack_end(font_dec_btn, False, False, 0)
        self.reply_box.pack_start(actions_row, False, False, 0)

        self.reply_scroll = Gtk.ScrolledWindow()
        self.reply_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.reply_scroll.get_style_context().add_class("clean-scroll")
        self.reply_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.reply_scroll.set_min_content_height(32)
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
        self.star_btn = icon_btn
        icon_btn.set_valign(Gtk.Align.CENTER)
        icon_btn.set_margin_top(2)
        icon_btn.set_can_focus(False)
        icon_btn.set_relief(Gtk.ReliefStyle.NONE)
        icon_btn.get_style_context().add_class("search-icon")
        icon_btn.set_tooltip_text(t("settings_title"))
        icon_btn.connect("clicked", lambda *_: open_settings_dialog(self))
        top_row.pack_start(icon_btn, False, False, 0)
        GLib.timeout_add(140, self._pulse_star)

        self.entry_scroll = Gtk.ScrolledWindow()
        self.entry_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.entry_scroll.get_style_context().add_class("clean-scroll")
        self.entry_scroll.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.EXTERNAL)
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
        drop_targets = [
            Gtk.TargetEntry.new("text/uri-list", 0, 0),
            Gtk.TargetEntry.new("x-special/gnome-copied-files", 0, 1),
            Gtk.TargetEntry.new("text/plain", 0, 2),
        ]
        self.entry.drag_dest_set(Gtk.DestDefaults.ALL, drop_targets, Gdk.DragAction.COPY)
        self.entry.connect("drag-data-received", self._on_file_drop)
        self.drag_dest_set(Gtk.DestDefaults.ALL, drop_targets, Gdk.DragAction.COPY)
        self.connect("drag-data-received", self._on_file_drop)
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

    def _step_chat_font(self, delta):
        cur = int(get_config().get("chat_font_size", 13))
        px = max(8, min(18, cur + delta))
        update_config(chat_font_size=px)
        cb = getattr(self, "_on_settings_font", None)
        if cb:
            try:
                cb(px)
            except Exception:
                pass
        if self.reply_view and getattr(self, "_reply_ready", False):
            self.reply_view.evaluate_javascript(
                f"document.body.style.fontSize='{px}px'; (() => {{ const r = document.createRange(); r.selectNodeContents(document.body); return Math.max(32, Math.ceil(r.getBoundingClientRect().height) + 12); }})();",
                -1, None, None, None, self._on_reply_height, None,
            )

    def _reset_new_chat(self):
        self.current_chat_id = None
        update_config(last_chat_id=None)
        self.hide_results()
        self.clear_query()
        self._flash_placeholder(t("new_chat"), 2500)
        self.entry.grab_focus()

    def _flash_placeholder(self, msg, ms=2500):
        fid = getattr(self, "_flash_id", 0) + 1
        self._flash_id = fid
        self.placeholder_lbl.set_text(msg)
        def _restore():
            if getattr(self, "_flash_id", 0) == fid and not getattr(self, "_busy", False):
                self.placeholder_lbl.set_text(t("placeholder"))
            return False
        GLib.timeout_add(ms, _restore)

    def apply_lang(self):
        self.placeholder_lbl.set_text(t("placeholder"))
        self.litemd_btn.set_label(t("open_litemd"))
        self.new_chat_btn.set_label(t("new_chat_btn"))
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
        h = alloc.height if alloc.height > 1 else 48
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
        if getattr(self, "_settings_dlg", None) is not None:
            return False
        if self.reply_box.is_visible() or self.list_scroll.is_visible() or self.draft_box.is_visible():
            self.hide_results()
        if not self.get_query_text().strip():
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
        elif self.resume_chat_btn.is_visible():
            self.resume_chat_btn.hide()
            self.resize(720, 1)

    def _toggle_current_chat(self, *_):
        if self.reply_box.is_visible():
            self.hide_results()
        elif self.current_chat_id:
            self.show_reply(self.last_reply_md or "")
        self._sync_chat_btn()

    def _show_list_scroll(self):
        self.card.set_size_request(720, -1)
        self.list_scroll.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)
        self.resize(720, 1)

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
            self.card.set_size_request(720, -1)
            self.resize(720, 1)

    def on_reply_loaded(self, view, event):
        if event != WebKit2.LoadEvent.FINISHED:
            return
        self._reply_ready = True
        self._reply_loading = False
        measure_js = "window.enhanceReply(); (() => { const r = document.createRange(); r.selectNodeContents(document.body); return Math.max(32, Math.ceil(r.getBoundingClientRect().height) + 12); })()"
        pending = getattr(self, "_pending_reply_update", None)
        if pending:
            self._pending_reply_update = None
            fsize, body = pending
            js = f"document.body.style.fontSize='{fsize}px'; document.body.innerHTML = {json.dumps(body)}; window.scrollTo(0, document.body.scrollHeight); {measure_js};"
            view.evaluate_javascript(js, -1, None, None, None, self._on_reply_height, None)
            return
        view.evaluate_javascript(
            f"window.scrollTo(0, document.body.scrollHeight); {measure_js}",
            -1, None, None, None, self._on_reply_height, None
        )

    def _on_reply_height(self, view, res, _):
        try:
            js_res = view.evaluate_javascript_finish(res)
            h = int(js_res.to_int32())
            self.reply_scroll.set_min_content_height(max(32, min(h, 440)))
        except Exception:
            self.reply_scroll.set_min_content_height(140)
        self.resize(720, 1)

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
        self.reply_view.connect("decide-policy", self._on_reply_policy)
        self.reply_scroll.add(self.reply_view)

    def _on_reply_policy(self, _view, decision, d_type):
        if d_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri() or ""
            if uri.startswith(("aios-preview://", "aios-save://")):
                from urllib.parse import unquote, urlparse
                is_save = uri.startswith("aios-save://")
                raw = unquote(uri.split("://", 1)[1])
                fpath = unquote(urlparse(raw).path) if raw.startswith("file://") else raw
                decision.ignore()
                if is_save:
                    p = Path(fpath)
                    if p.exists():
                        fc = Gtk.FileChooserDialog(title=t("img_save_btn"), parent=self, action=Gtk.FileChooserAction.SAVE)
                        fc.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
                        fc.set_do_overwrite_confirmation(True)
                        for d in (HOME / "Imagens", HOME / "Pictures", HOME / "Desktop"):
                            if d.exists():
                                fc.set_current_folder(str(d))
                                break
                        fc.set_current_name(p.name)
                        if fc.run() == Gtk.ResponseType.OK:
                            import shutil
                            shutil.copy2(str(p), fc.get_filename())
                        fc.destroy()
                else:
                    open_image_preview(self, fpath)
                return True
            if uri.startswith(("http://", "https://")):
                decision.ignore()
                subprocess.Popen(["chromium", uri])
                return True
            if uri.startswith("file://") and uri != "file:///":
                from urllib.parse import unquote, urlparse
                fpath = unquote(urlparse(uri).path)
                decision.ignore()
                if fpath.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg")):
                    open_image_preview(self, fpath)
                elif fpath.endswith(".md"):
                    subprocess.Popen(["/opt/ai-os/spotlight/litemd.py", fpath])
                else:
                    subprocess.Popen(["xdg-open", fpath])
                return True
        return False

    def show_reply(self, text, live_stream=False):
        self._ensure_reply_view()
        self.last_reply_md = text
        self.divider.show()
        self.list_scroll.hide()
        self.draft_box.hide()
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
                    if role == "user":
                        import html as _html
                        def _chip(m):
                            full = m.group(1)
                            bname = full.rstrip("/").split("/")[-1] or full
                            svg = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
                            return f'<span class="file-chip" title="{_html.escape(full)}">{svg}{_html.escape(bname)}</span>'
                        content_fmt = re.sub(r"@([^\s]+)", _chip, _html.escape(content)).replace("\n", "<br>")
                        html_part = f"<p>{content_fmt}</p>"
                    else:
                        if live_stream and i + 2 >= len(parts) and (content.startswith("⚙ ") or content == t("processing")):
                            import html as _html
                            html_part = f'<span class="thinking-pill"><span class="live-dot"></span>{_html.escape(content.lstrip("⚙ "))}</span>'
                        else:
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
            js = f"document.body.style.fontSize='{fsize}px'; document.body.innerHTML = {json.dumps(body)}; window.enhanceReply(); window.scrollTo(0, document.body.scrollHeight); (() => {{ const r = document.createRange(); r.selectNodeContents(document.body); return Math.max(32, Math.ceil(r.getBoundingClientRect().height) + 12); }})();"
            self.reply_view.evaluate_javascript(js, -1, None, None, None, self._on_reply_height, None)
        elif getattr(self, "_reply_loading", False):
            self._pending_reply_update = (fsize, body)
        else:
            self._reply_loading = True
            self._pending_reply_update = None
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

    def _scan_files(self, query_lower, bases, limit=6, max_depth=3, time_budget=0.06):
        import time
        deadline = time.monotonic() + time_budget
        skip_dirs = {"node_modules", "__pycache__", "venv", ".venv", "target", "dist", "build"}
        prefix_hits, sub_hits = [], []
        seen = set()
        queue = [(b, 0) for b in bases if b.exists()]
        while queue and time.monotonic() < deadline and (len(prefix_hits) + len(sub_hits)) < limit * 2:
            cur, depth = queue.pop(0)
            try:
                with os.scandir(cur) as it:
                    for ent in it:
                        name = ent.name
                        if name.startswith(".") or name in skip_dirs:
                            continue
                        p_str = ent.path
                        if p_str in seen:
                            continue
                        nl = name.lower()
                        is_dir = False
                        try:
                            is_dir = ent.is_dir(follow_symlinks=False)
                        except OSError:
                            pass
                        if not query_lower or query_lower in nl:
                            seen.add(p_str)
                            item = (name, p_str, is_dir)
                            if query_lower and nl.startswith(query_lower):
                                prefix_hits.append(item)
                            else:
                                sub_hits.append(item)
                        if is_dir and depth + 1 < max_depth:
                            queue.append((Path(p_str), depth + 1))
            except OSError:
                continue
        return (prefix_hits + sub_hits)[:limit]

    def build_at_matches(self, token):
        q = token.lstrip("@").lower()
        hits = self._scan_files(q, SEARCH_DIRS + [HOME], limit=7, max_depth=3)
        return [
            ("mention", f"@{p.replace(str(HOME) + '/', '')}", t("attach_agy"), "folder" if is_dir else "text-x-generic", f"@{p.replace(str(HOME) + '/', '')} ")
            for _, p, is_dir in hits
        ]

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

        # 2.5 Projects in ~/Projetos
        proj_dir = HOME / "Projetos"
        if proj_dir.exists():
            try:
                for p in sorted(proj_dir.iterdir()):
                    if p.is_dir() and not p.name.startswith(".") and q in p.name.lower():
                        is_git = (p / ".git").exists()
                        sub = "~/Projetos (Git)" if is_git else "~/Projetos"
                        matches.append(("open_proj", p.name, sub, "utilities-terminal", str(p)))
            except OSError:
                pass

        # 3. Recursive files in user folders (BFS up to depth 3, 60ms budget)
        for name, p_str, is_dir in self._scan_files(q, SEARCH_DIRS, limit=6, max_depth=3):
            icon_name = "folder" if is_dir else "text-x-generic"
            matches.append(("file", name, p_str.replace(str(HOME), "~"), icon_name, p_str))

        return matches[:7]

    def on_search_changed(self, *_):
        raw = self.get_query_text()
        if raw:
            self._flash_id = getattr(self, "_flash_id", 0) + 1
            if not getattr(self, "_busy", False):
                self.placeholder_lbl.set_text(t("placeholder"))
        self.placeholder_lbl.set_visible(len(raw) == 0)
        text = raw.strip()
        if not text:
            self.results = []
            self._last_match_keys = None
            self.hide_results()
            return

        was_reply = self.reply_box.is_visible()
        if was_reply:
            self.reply_box.hide()
            self._sync_chat_btn()
        query_for_match = raw.lstrip() if raw.lstrip().startswith(("/", "#")) else text
        matches = self.build_matches(query_for_match)
        if not matches:
            self.results = []
            self._last_match_keys = None
            was_open = was_reply or self.list_scroll.is_visible() or self.draft_box.is_visible() or self.divider.is_visible()
            self.list_scroll.hide()
            if "\n" in raw or len(raw) > 54:
                self.draft_view.show()
                self.draft_box.show()
                self.divider.show()
                self.resize(720, 1)
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
        self._show_list_scroll()

    def _on_clip_change(self, clipboard, _event):
        txt = clipboard.wait_for_text()
        if not txt or not txt.strip():
            return
        txt = txt.strip()
        if txt in self.clip_history:
            self.clip_history.remove(txt)
        self.clip_history.insert(0, txt)
        self.clip_history = self.clip_history[:15]

    def _populate_list(self, matches):
        self.reply_box.hide()
        self.draft_box.hide()
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
            t_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            t_lbl.set_max_width_chars(64)
            t_lbl.get_style_context().add_class("row-title")
            s_lbl = Gtk.Label(label=sub, xalign=0)
            s_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            s_lbl.set_max_width_chars(72)
            s_lbl.get_style_context().add_class("row-sub")
            box.pack_start(t_lbl, False, False, 0)
            box.pack_start(s_lbl, False, False, 0)
            hbox.pack_start(box, True, True, 0)
            row.add(hbox)
            self.listbox.add(row)
        self.divider.show()
        self._show_list_scroll()

    def _load_clip_pins(self):
        pf = HOME / ".ai-os" / "clip_pins.json"
        try:
            if pf.exists():
                return json.loads(pf.read_text(encoding="utf-8"))[:10]
        except Exception:
            pass
        return []

    def _save_clip_pins(self, pins):
        pf = HOME / ".ai-os" / "clip_pins.json"
        pf.parent.mkdir(parents=True, exist_ok=True)
        pf.write_text(json.dumps(pins[:10], indent=2), encoding="utf-8")

    def show_clip_history(self):
        pins = self._load_clip_pins()
        if not self.clip_history and not pins:
            self.show_reply(t("no_clip"))
            return
        matches = []
        if self.clip_history and self.clip_history[0] not in pins:
            latest = self.clip_history[0]
            matches.append(("pin_clip", f"+ {t('clip_pin')}: {' '.join(latest.splitlines())[:55]}", f"{len(latest)} chars", "bookmark-new", latest))
        for txt in pins:
            matches.append(("clip", f"[Pin] {' '.join(txt.splitlines())[:65]}", f"{len(txt)} chars", "emblem-favorite", txt))
        for txt in self.clip_history:
            if txt not in pins:
                one_line = " ".join(txt.splitlines())[:75]
                matches.append(("clip", one_line, f"{len(txt)} chars", "edit-paste", txt))
        self._populate_list(matches)

    def show_podman_menu(self):
        matches = [("podman_prune", t("podman_purge"), t("podman_purge_sub"), "user-trash", "")]
        try:
            with urllib.request.urlopen(f"{API_BASE}/api/podman", timeout=4) as r:
                data = json.loads(r.read().decode())
            for c in data.get("containers", []):
                running = c.get("state", "").lower() == "running"
                kind = "podman_stop" if running else "podman_rm"
                mark = "▶" if running else "■"
                act_lbl = "Parar" if running else "Remover"
                sub = f"{c.get('status', '')} · {c.get('ports') or '-'} · Enter: {act_lbl}"
                matches.append((kind, f"{mark} {c['name']} ({c.get('image', '')})", sub, "utilities-terminal", c["name"]))
            for img in data.get("images", []):
                matches.append(("podman_rmi", f"Imagem: {img['name']}", f"{img.get('size', '')} · Enter: Apagar imagem", "drive-harddisk", img["id"]))
        except Exception:
            pass
        if len(matches) == 1:
            self.hide_results()
            self.show_reply(t("podman_empty"))
            return
        self._populate_list(matches)

    def run_system_clean(self):
        self.hide_results()
        self.show_reply(t("clean_running"))
        def _bg():
            msg = t("clean_done", mb=0, items="-")
            try:
                req = urllib.request.Request(f"{API_BASE}/api/system/clean", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=45) as r:
                    res = json.loads(r.read().decode())
                items = ", ".join(res.get("cleaned") or []) or "-"
                msg = t("clean_done", mb=res.get("freed_mb", 0), items=items)
            except Exception as e:
                msg = f"Erro: {e}"
            GLib.idle_add(lambda: (self.show_reply(msg), False)[1])
        threading.Thread(target=_bg, daemon=True).start()

    def show_ports_menu(self):
        matches = []
        try:
            with urllib.request.urlopen(f"{API_BASE}/api/ports", timeout=3) as r:
                data = json.loads(r.read().decode())
            for c in data.get("containers", []):
                matches.append(("stop_container", f"Container: {c['name']}", c.get("ports") or c["id"], "utilities-terminal", c["name"]))
            for p in data.get("ports", []):
                tag = "Parar processo" if p.get("mine") else "Sistema (root)"
                matches.append(("stop_port" if p.get("mine") else "noop", f":{p['port']} — {p['name']} (PID {p['pid']})", tag, "network-server", p["pid"]))
        except Exception:
            pass
        if not matches:
            self.hide_results()
            self.show_reply(t("ports_empty"))
            return
        self._populate_list(matches)

    def show_projects_menu(self):
        proj_dir = HOME / "Projetos"
        matches = []
        if proj_dir.exists():
            try:
                for p in sorted(proj_dir.iterdir()):
                    if p.is_dir() and not p.name.startswith("."):
                        branch = ""
                        head = p / ".git" / "HEAD"
                        if head.exists():
                            try:
                                ref = head.read_text(encoding="utf-8").strip()
                                branch = f"git:{ref.split('/')[-1]}"
                            except OSError:
                                branch = "git"
                        matches.append(("open_proj", p.name, branch or str(p).replace(str(HOME), "~"), "utilities-terminal", str(p)))
            except OSError:
                pass
        if not matches:
            self.hide_results()
            self.show_reply(t("proj_empty"))
            return
        self._populate_list(matches)

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
        self._show_list_scroll()
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
        self._show_list_scroll()
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
        self._show_list_scroll()

    def _on_file_drop(self, widget, context, _x, _y, selection, _info, timestamp):
        uris = list(selection.get_uris() or [])
        if not uris:
            raw_txt = selection.get_text() or ""
            for line in raw_txt.splitlines():
                line = line.strip()
                if line.startswith("file://"):
                    uris.append(line)
        if not uris:
            Gtk.drag_finish(context, False, False, timestamp)
            return
        from urllib.parse import unquote, urlparse
        tokens = []
        home_prefix = str(HOME) + "/"
        for uri in uris:
            if uri.startswith("file://"):
                p = unquote(urlparse(uri).path)
                rel = p[len(home_prefix):] if p.startswith(home_prefix) else p
                tokens.append(f"@{rel}")
        if tokens:
            self.entry_buf.insert_at_cursor(" ".join(tokens) + " ")
            self.focus_spotlight()
            if widget is self.entry:
                widget.stop_emission_by_name("drag-data-received")
        Gtk.drag_finish(context, bool(tokens), False, timestamp)

    def on_entry_key_press(self, _, event):
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval in (Gdk.KEY_v, Gdk.KEY_V):
            cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            if not cb.wait_is_text_available() and cb.wait_is_image_available():
                pb = cb.wait_for_image()
                if pb:
                    import time
                    tmp_dir = HOME / ".ai-os" / "tmp"
                    tmp_dir.mkdir(parents=True, exist_ok=True)
                    img_path = tmp_dir / f"clip_{int(time.time())}.png"
                    pb.savev(str(img_path), "png", [], [])
                    self.entry_buf.insert_at_cursor(f"@{img_path} ")
                    return True
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

    def show_reminders_menu(self):
        matches = []
        try:
            with urllib.request.urlopen(f"{API_BASE}/api/reminders", timeout=2) as r:
                for it in json.loads(r.read().decode()):
                    matches.append(("del_reminder", f"• {it.get('message', '')}", f"Timer ({it.get('id')}) — Enter/Click to remove", "alarm-symbolic", it.get("id")))
        except Exception:
            pass
        try:
            with urllib.request.urlopen(f"{API_BASE}/api/crons", timeout=2) as r:
                for it in json.loads(r.read().decode()):
                    when = human_cron(it.get("schedule", ""))
                    matches.append(("del_cron", f"↻ {it.get('label', '')}", f"{when} ({it.get('kind')}) — Enter/Click to remove", "preferences-system-time", it.get("id")))
        except Exception:
            pass
        if not matches:
            self.hide_results()
            self.show_reply(t("reminders_empty"))
            return
        self.reply_box.hide()
        self.draft_box.hide()
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
        self._show_list_scroll()

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
        elif kind == "pin_clip":
            pins = self._load_clip_pins()
            if payload not in pins:
                pins.insert(0, payload)
                self._save_clip_pins(pins)
            self.clear_query()
            self.show_clip_history()
        elif kind == "open_proj":
            self.clear_query()
            self.hide_results()
            subprocess.Popen(["xterm", "-e", "bash", "-lc", f"cd {json.dumps(payload)} && exec bash"])
        elif kind in ("stop_port", "stop_container"):
            body = {"pid": payload} if kind == "stop_port" else {"container": payload}
            def _kill():
                try:
                    req = urllib.request.Request(
                        f"{API_BASE}/api/ports/kill",
                        data=json.dumps(body).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    urllib.request.urlopen(req, timeout=8).read()
                except Exception:
                    pass
                GLib.idle_add(lambda: (self.hide_results(), self.show_reply(t("port_stopped")), False)[2])
            threading.Thread(target=_kill, daemon=True).start()
            self.clear_query()
        elif kind in ("podman_stop", "podman_rm", "podman_rmi", "podman_prune"):
            act = kind.split("_", 1)[1]
            def _pod():
                try:
                    req = urllib.request.Request(
                        f"{API_BASE}/api/podman/action",
                        data=json.dumps({"action": act, "target": payload or None}).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    urllib.request.urlopen(req, timeout=30).read()
                except Exception:
                    pass
                GLib.idle_add(lambda: (self.hide_results(), self.show_reply(t("podman_done")), False)[2])
            threading.Thread(target=_pod, daemon=True).start()
            self.clear_query()
        elif kind == "noop":
            pass
        elif kind in ("del_reminder", "del_cron"):
            ep = "reminders" if kind == "del_reminder" else "crons"
            def _del():
                try:
                    req = urllib.request.Request(f"{API_BASE}/api/{ep}/{payload}", method="DELETE")
                    urllib.request.urlopen(req, timeout=3).read()
                except Exception:
                    pass
                GLib.idle_add(lambda: (self.hide_results(), self.show_reply(t("reminder_deleted")), False)[2])
            threading.Thread(target=_del, daemon=True).start()
            self.clear_query()
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
            elif payload == "local:notif":
                self.clear_query()
                self.hide_results()
                nf = HOME / ".ai-os" / "notifications.log"
                if not nf.exists():
                    self.show_reply(t("notif_empty"))
                else:
                    lines = nf.read_text(encoding="utf-8", errors="ignore").splitlines()[-20:]
                    self.show_reply("```text\n" + "\n".join(reversed(lines)) + "\n```" if lines else t("notif_empty"))
            elif payload == "local:clip":
                self.clear_query()
                self.show_clip_history()
            elif payload == "local:new_chat":
                self._reset_new_chat()
            elif payload == "local:ports":
                self.clear_query()
                self.show_ports_menu()
            elif payload == "local:podman":
                self.clear_query()
                self.show_podman_menu()
            elif payload == "local:clean":
                self.clear_query()
                self.run_system_clean()
            elif payload == "local:proj":
                self.clear_query()
                self.show_projects_menu()
            elif payload == "local:keys":
                self.clear_query()
                self.hide_results()
                self.show_reply(
                    "| Atalho | Ação |\n|---|---|\n"
                    "| `Super+Espaço` / `Alt+Espaço` | Focar Spotlight |\n"
                    "| `Super+T` | Abrir Terminal (`xterm`) |\n"
                    "| `Super+L` | Bloquear ecrã (`i3lock`) |\n"
                    "| `Super+1..4` | Mudar de Workspace |\n"
                    "| `Super+Shift+1..4` | Mover janela para Workspace |\n"
                    "| `Super+←/→/↑/↓` | Encaixar / Maximizar janela |\n"
                    "| `Alt+Arrastar` / `Alt+F4` | Mover / Fechar qualquer janela |\n"
                    "| `Print` / `Ctrl+V` | Captura ou colar imagem no chat |\n"
                    "| `Ctrl+H` | Histórico de conversas |"
                )
            elif payload == "local:health":
                self.clear_query()
                self.hide_results()
                import shutil
                du = shutil.disk_usage("/")
                disk_pct = int(du.used * 100 / du.total)
                ram_line = ""
                try:
                    mi = {k: int(v.split()[0]) for k, v in (l.split(":", 1) for l in Path("/proc/meminfo").read_text().splitlines() if ":" in l)}
                    tot_m = mi.get("MemTotal", 1) // 1024
                    avail_m = mi.get("MemAvailable", 0) // 1024
                    ram_line = f"{tot_m - avail_m} / {tot_m} MB"
                except Exception:
                    ram_line = "N/D"
                svcs = []
                for name, pat in [("server.py", "server.py"), ("nemo-desktop", "nemo-desktop"), ("dunst", "^dunst$"), ("picom", "^picom"), ("cron", "cron")]:
                    ok = subprocess.run(["pgrep", "-f", pat], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
                    svcs.append(f"| `{name}` | {'OK' if ok else 'OFF'} |")
                self.show_reply(
                    "| Componente | Estado |\n|---|---|\n"
                    + "\n".join(svcs)
                    + f"\n| Disco `/` | {disk_pct}% ({du.free // (1024**3)} GB livres) |\n"
                    + f"| RAM | {ram_line} |"
                )
            elif payload == "local:reminders":
                self.clear_query()
                self.show_reminders_menu()
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
                open_displays_dialog(self)
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
        self.placeholder_lbl.set_text(t("placeholder"))
        if not busy:
            self.entry.grab_focus()
        if self.topbar:
            self.topbar.set_ai_busy(busy)

    def on_stop_ai(self, *_):
        self._cancelled = True
        self._active_run_id = getattr(self, "_active_run_id", 0) + 1
        self._set_busy(False)
        self.show_reply(t("ai_stopped"))
        def _stop_req():
            try:
                req = urllib.request.Request(f"{API_BASE}/api/ask_stop", data=b"{}", method="POST")
                urllib.request.urlopen(req, timeout=3).read()
            except Exception:
                pass
        threading.Thread(target=_stop_req, daemon=True).start()

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

        if prompt.strip().startswith("#grep "):
            term = prompt.split(None, 1)[1].strip().lower()
            self.clear_query()
            hits = []
            skip = {".git", "node_modules", "__pycache__", "venv", ".venv"}
            for base in [HOME / "Documentos", HOME / "Desktop", HOME / "Projetos"]:
                if not base.exists():
                    continue
                for root, dirs, files in os.walk(base):
                    dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
                    for fn in files:
                        if fn.startswith(".") or fn.endswith((".png", ".jpg", ".pdf", ".pyc", ".iso")):
                            continue
                        fp = Path(root) / fn
                        try:
                            if fp.stat().st_size > 262144:
                                continue
                            for idx, line in enumerate(fp.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                                if term in line.lower():
                                    hits.append(("file", f"{fn}:{idx}", line.strip()[:70], "text-x-generic", str(fp)))
                                    break
                        except OSError:
                            continue
                        if len(hits) >= 12:
                            break
                    if len(hits) >= 12:
                        break
                if len(hits) >= 12:
                    break
            if hits:
                self._populate_list(hits)
            else:
                self.hide_results()
                self.show_reply(t("grep_empty"))
            return

        if prompt.strip() in ("#remind", "#reminders", "#crons"):
            self.clear_query()
            self.show_reminders_menu()
            return

        if prompt.strip().startswith("#remind "):
            m = re.match(r"^#remind\s+(\d+)\s*([smhSMH]?)\s+(.+)$", prompt.strip())
            if not m:
                self.show_reply(t("remind_usage"))
                return
            val, unit, msg = int(m.group(1)), (m.group(2) or "m").lower(), m.group(3).strip()
            mult = {"s": 1, "m": 60, "h": 3600}[unit]
            req = urllib.request.Request(
                f"{API_BASE}/api/reminders",
                data=json.dumps({"delay_seconds": val * mult, "message": msg}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            def _save_rem():
                try:
                    urllib.request.urlopen(req, timeout=3).read()
                except Exception:
                    pass
            threading.Thread(target=_save_rem, daemon=True).start()
            self.clear_query()
            self.show_reply(t("remind_ok", when=f"{val}{unit}", msg=msg))
            return

        if prompt.strip() in ("/new", "/clear"):
            self.current_chat_id = None
            update_config(last_chat_id=None)

        confirmed = False
        if is_dangerous_prompt(prompt):
            dlg = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.NONE,
                text=t("confirm_danger_title"),
            )
            dlg.format_secondary_text(t("confirm_danger_body", prompt=prompt[:180]))
            dlg.add_button(t("cancel"), Gtk.ResponseType.CANCEL)
            dlg.add_button(t("confirm_danger_btn"), Gtk.ResponseType.OK)
            dlg.set_default_response(Gtk.ResponseType.CANCEL)
            dlg.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
            resp = dlg.run()
            dlg.destroy()
            if resp != Gtk.ResponseType.OK:
                self.show_reply(t("action_cancelled"))
                self.entry.grab_focus()
                return
            confirmed = True

        self._pending_prompt = prompt
        self._cancelled = False
        run_id = getattr(self, "_active_run_id", 0) + 1
        self._active_run_id = run_id
        chat_id_snapshot = self.current_chat_id
        self._save_history(prompt)
        self.clear_query()
        self.show_reply(t("processing"), live_stream=True)
        self._set_busy(True)

        def _worker():
            import time
            acc = []
            last_render = 0.0
            final_reply = None
            new_chat_id = None
            is_ephemeral = False
            try:
                req = urllib.request.Request(
                    f"{API_BASE}/api/ask_stream",
                    data=json.dumps({"prompt": prompt, "chat_id": chat_id_snapshot, "confirmed": confirmed}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=180) as r:
                    for raw in r:
                        if self._cancelled or run_id != self._active_run_id:
                            return
                        line = raw.decode("utf-8", errors="ignore").strip()
                        if not line:
                            continue
                        ev = json.loads(line)
                        if ev.get("done"):
                            new_chat_id = ev.get("chat_id")
                            is_ephemeral = bool(ev.get("ephemeral"))
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
                            GLib.idle_add(lambda msg=f"⚙ {t('step_tool', tool=friendly)}": (run_id == self._active_run_id and not self._cancelled and self.show_reply(msg, True), False)[1])
                        elif ev.get("delta"):
                            acc.append(ev["delta"])
                            now = time.monotonic()
                            if now - last_render > 0.18:
                                last_render = now
                                txt = "".join(acc)
                                GLib.idle_add(lambda msg=txt: (run_id == self._active_run_id and not self._cancelled and self.show_reply(msg, True), False)[1])
                reply = final_reply or "".join(acc) or "Concluído."
            except Exception as e:
                reply = f"Erro ao contactar backend AI-OS: {e}"

            def _finish():
                if self._cancelled or run_id != self._active_run_id:
                    return False
                if is_ephemeral:
                    self.current_chat_id = None
                    update_config(last_chat_id=None)
                elif new_chat_id:
                    self.current_chat_id = new_chat_id
                    update_config(last_chat_id=new_chat_id)
                self.show_reply(reply)
                self._sync_chat_btn()
                self._set_busy(False)
                if not self.has_toplevel_focus():
                    try:
                        nf = HOME / ".ai-os" / "notifications.log"
                        nf.parent.mkdir(parents=True, exist_ok=True)
                        import datetime
                        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with nf.open("a", encoding="utf-8") as f:
                            f.write(f"{ts} | AI-OS Spotlight | {t('done_notify')}\n")
                    except Exception:
                        pass
                    subprocess.Popen(["notify-send", "AI-OS Spotlight", t("done_notify")])
                return False

            GLib.idle_add(_finish)

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

    def _pulse_star(self):
        if self.get_visible() and hasattr(self, "star_btn"):
            op = 0.71 + 0.29 * math.sin(time.monotonic() * (2 * math.pi / 4.2))
            self.star_btn.set_opacity(op)
        return True

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


def _acquire_single_instance():
    import fcntl
    lock_path = Path(f"/tmp/aios-spotlight-{os.getuid()}.lock")
    fd = open(lock_path, "a+", encoding="utf-8")
    try:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        try:
            fd.seek(0)
            pid = int(fd.read().strip() or "0")
            if pid > 1:
                os.kill(pid, signal.SIGUSR1)
        except Exception:
            pass
        fd.close()
        return None
    fd.seek(0)
    fd.truncate()
    fd.write(str(os.getpid()))
    fd.flush()
    return fd


def main():
    _lock_fd = _acquire_single_instance()
    if _lock_fd is None:
        return
    topbar = TopBarWindow()
    win = SpotlightWindow(topbar=topbar)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, lambda *_: (win.focus_spotlight(), True)[1])
    Gtk.main()


if __name__ == "__main__":
    main()
