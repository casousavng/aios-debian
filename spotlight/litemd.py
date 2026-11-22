#!/usr/bin/env python3
"""LiteMD for AI-OS Debian: lightweight GTK3 + WebKit2GTK Markdown reader."""
import html
import sys
from pathlib import Path

import gi
import markdown

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, Gtk, WebKit2  # noqa: E402

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="utf-8" />
<style>
  body {
    background: #11151c;
    color: #e6edf3;
    font-family: system-ui, -apple-system, sans-serif;
    line-height: 1.65;
    max-width: 820px;
    margin: 0 auto;
    padding: 32px 28px 60px;
  }
  h1, h2, h3 { color: #f8fafc; margin-top: 1.5em; margin-bottom: 0.5em; font-weight: 650; }
  h1 { font-size: 1.85em; border-bottom: 1px solid #263040; padding-bottom: 0.3em; }
  h2 { font-size: 1.4em; border-bottom: 1px solid #1e2633; padding-bottom: 0.2em; }
  a { color: #67e8f9; text-decoration: none; }
  code {
    background: #1b222d;
    color: #7dd3fc;
    padding: 2px 6px;
    border-radius: 6px;
    font-family: monospace;
    font-size: 0.9em;
  }
  pre {
    background: #161b24;
    border: 1px solid #263040;
    border-radius: 10px;
    padding: 14px 16px;
    overflow-x: auto;
  }
  pre code { background: transparent; padding: 0; color: #e2e8f0; }
  blockquote {
    border-left: 3px solid #67e8f9;
    margin: 1em 0;
    padding: 4px 14px;
    color: #94a3b8;
    background: rgba(103, 232, 249, 0.05);
    border-radius: 0 8px 8px 0;
  }
  ul, ol { padding-left: 1.6em; }
  li { margin: 0.25em 0; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { border: 1px solid #263040; padding: 8px 12px; text-align: left; }
  th { background: #18202c; color: #f8fafc; }
  hr { border: none; border-top: 1px solid #263040; margin: 2em 0; }
</style>
</head>
<body>%BODY%</body>
</html>"""


class LiteMDWindow(Gtk.Window):
    def __init__(self, file_path: Path | None = None):
        super().__init__(title="LiteMD")
        self.set_wmclass("LiteMD", "LiteMD")
        self.set_default_size(860, 640)
        self.file_path = file_path

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title("LiteMD")
        self.set_titlebar(header)

        open_btn = Gtk.Button(label="Abrir")
        open_btn.connect("clicked", self.on_open_clicked)
        header.pack_start(open_btn)

        self.webview = WebKit2.WebView()
        settings = self.webview.get_settings()
        settings.set_enable_javascript(False)
        self.webview.set_background_color(Gdk.RGBA(0.067, 0.082, 0.11, 1.0))

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.webview)
        self.add(scroll)

        if self.file_path and self.file_path.exists():
            self.load_file(self.file_path)
        else:
            self.load_markdown("# LiteMD\n\nClica em **Abrir** para escolher um ficheiro `.md`.")

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def load_markdown(self, text: str):
        body = markdown.markdown(
            text,
            extensions=["fenced_code", "tables", "sane_lists", "nl2br"],
        )
        self.webview.load_html(HTML_TEMPLATE.replace("%BODY%", body), "file:///")

    def load_file(self, path: Path):
        self.file_path = path
        self.set_title(f"{path.name} — LiteMD")
        self.get_titlebar().set_subtitle(str(path))
        try:
            self.load_markdown(path.read_text(encoding="utf-8"))
        except Exception as e:
            self.load_markdown(f"# Erro ao abrir ficheiro\n\n`{html.escape(str(e))}`")

    def on_open_clicked(self, *_):
        dlg = Gtk.FileChooserDialog(
            title="Abrir Markdown",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filt = Gtk.FileFilter()
        filt.set_name("Markdown (*.md)")
        filt.add_pattern("*.md")
        dlg.add_filter(filt)
        if dlg.run() == Gtk.ResponseType.OK:
            self.load_file(Path(dlg.get_filename()))
        dlg.destroy()


if __name__ == "__main__":
    arg = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else None
    LiteMDWindow(arg)
    Gtk.main()
