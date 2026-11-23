#!/usr/bin/env python3
"""Chromium CDP browser automation CLI v2 for AI-OS (aios-web)."""
import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CDP_URL = "http://127.0.0.1:9222"
TAB_STATE = Path("/tmp/aios_web_tab.txt")

KEY_CODES = {
    "Enter": ("\r", 13),
    "Return": ("\r", 13),
    "Tab": ("\t", 9),
    "Escape": ("", 27),
    "Esc": ("", 27),
    "Backspace": ("", 8),
    "Space": (" ", 32),
    "ArrowDown": ("", 40),
    "ArrowUp": ("", 38),
    "ArrowLeft": ("", 37),
    "ArrowRight": ("", 39),
}


def get_pages():
    with urllib.request.urlopen(f"{CDP_URL}/json/list", timeout=2) as r:
        return [p for p in json.loads(r.read().decode()) if p.get("type") == "page"]


def _pick_page(pages):
    if TAB_STATE.exists():
        wanted = TAB_STATE.read_text(encoding="utf-8").strip()
        for p in pages:
            if p.get("id") == wanted:
                return p
    return pages[0]


def ensure_browser():
    try:
        pages = get_pages()
        if pages:
            return _pick_page(pages)
    except Exception:
        pass

    env = os.environ.copy()
    env.setdefault("DISPLAY", ":0")
    subprocess.Popen(
        [
            "chromium",
            "--remote-debugging-port=9222",
            "--remote-debugging-address=127.0.0.1",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(40):
        time.sleep(0.25)
        try:
            pages = get_pages()
            if pages:
                TAB_STATE.write_text(pages[0]["id"], encoding="utf-8")
                return pages[0]
        except Exception:
            pass
    raise RuntimeError("Chromium CDP did not start on 127.0.0.1:9222")


async def cdp_call(ws_url: str, method: str, params: dict = None):
    import websockets

    async with websockets.connect(ws_url, max_size=16 * 1024 * 1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                if "error" in msg:
                    raise RuntimeError(msg["error"].get("message", str(msg["error"])))
                return msg.get("result", {})


async def eval_js(ws_url: str, expr: str):
    res = await cdp_call(
        ws_url,
        "Runtime.evaluate",
        {"expression": expr, "returnByValue": True, "awaitPromise": True},
    )
    if "exceptionDetails" in res:
        raise RuntimeError(res["exceptionDetails"].get("text", "JS error"))
    return res.get("result", {}).get("value")


DEEP_QUERY_JS = r"""
function deepFind(selector, root = document) {
    let found = root.querySelector(selector);
    if (found) return found;
    for (const el of root.querySelectorAll('*')) {
        if (el.shadowRoot) {
            found = deepFind(selector, el.shadowRoot);
            if (found) return found;
        }
    }
    for (const ifr of root.querySelectorAll('iframe')) {
        try {
            if (ifr.contentDocument) {
                found = deepFind(selector, ifr.contentDocument);
                if (found) return found;
            }
        } catch (_) {}
    }
    return null;
}
"""


def cmd_open(url: str):
    if not url.startswith(("http://", "https://", "file://")):
        url = "https://" + url
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    asyncio.run(cdp_call(ws_url, "Page.enable"))
    asyncio.run(cdp_call(ws_url, "Page.navigate", {"url": url}))
    for _ in range(40):
        time.sleep(0.25)
        state = asyncio.run(eval_js(ws_url, "document.readyState"))
        if state in ("interactive", "complete"):
            break
    time.sleep(0.4)
    info = asyncio.run(eval_js(ws_url, "({title: document.title, url: location.href})"))
    print(json.dumps(info, ensure_ascii=False))


def cmd_tabs():
    ensure_browser()
    pages = get_pages()
    cur = _pick_page(pages)["id"]
    out = [
        {"idx": i, "active": p["id"] == cur, "title": p.get("title", ""), "url": p.get("url", "")}
        for i, p in enumerate(pages)
    ]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_tab(idx_str: str):
    ensure_browser()
    pages = get_pages()
    idx = int(idx_str)
    if idx < 0 or idx >= len(pages):
        print(f"ERROR: tab index {idx} out of range (0..{len(pages)-1})")
        sys.exit(1)
    p = pages[idx]
    TAB_STATE.write_text(p["id"], encoding="utf-8")
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/activate/{p['id']}", timeout=2).read()
    except Exception:
        pass
    print(json.dumps({"idx": idx, "title": p.get("title", ""), "url": p.get("url", "")}, ensure_ascii=False))


def cmd_dom():
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    js = r"""(() => {
        const items = [];
        let idx = 0;
        function collect(root, frameTag) {
            const els = Array.from(root.querySelectorAll('a[href],button,input,textarea,select,[role="button"]'));
            for (const el of els) {
                const rect = el.getBoundingClientRect();
                if (rect.width <= 0 && rect.height <= 0) continue;
                el.setAttribute('data-aios-id', String(idx));
                const tag = el.tagName.toLowerCase();
                const info = {
                    idx,
                    selector: `[data-aios-id="${idx}"]`,
                    tag,
                    frame: frameTag || undefined,
                    type: el.getAttribute('type') || undefined,
                    name: el.getAttribute('name') || undefined,
                    id: el.id || undefined,
                    placeholder: el.getAttribute('placeholder') || undefined,
                    aria: el.getAttribute('aria-label') || undefined,
                    text: (el.innerText || el.value || '').trim().slice(0, 60) || undefined,
                    href: tag === 'a' ? (el.getAttribute('href') || '').slice(0, 80) : undefined
                };
                Object.keys(info).forEach(k => info[k] === undefined && delete info[k]);
                items.push(info);
                idx++;
                if (idx >= 100) return;
            }
            for (const el of root.querySelectorAll('*')) {
                if (el.shadowRoot && idx < 100) collect(el.shadowRoot, frameTag);
            }
            for (const ifr of root.querySelectorAll('iframe')) {
                if (idx >= 100) break;
                try {
                    if (ifr.contentDocument) collect(ifr.contentDocument, ifr.id || ifr.name || 'iframe');
                } catch (_) {}
            }
        }
        collect(document, null);
        return {
            title: document.title,
            url: location.href,
            text_preview: (document.body ? document.body.innerText : '').replace(/\s+/g, ' ').trim().slice(0, 1200),
            elements: items
        };
    })()"""
    res = asyncio.run(eval_js(ws_url, js))
    print(json.dumps(res, ensure_ascii=False, indent=2))


def cmd_fill(selector: str, value: str):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    js = f"""(() => {{
        {DEEP_QUERY_JS}
        const el = deepFind({json.dumps(selector)});
        if (!el) return "ERROR: element not found";
        el.scrollIntoView({{block: 'center'}});
        el.focus();
        const tag = el.tagName.toLowerCase();
        if (tag === 'input' && (el.type === 'checkbox' || el.type === 'radio')) {{
            const want = {json.dumps(value)}.toLowerCase();
            el.checked = ['true', '1', 'yes', 'on', 'sim'].includes(want);
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return "OK checkbox=" + el.checked;
        }}
        if (tag === 'select') {{
            el.value = {json.dumps(value)};
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return "OK select=" + el.value;
        }}
        const win = el.ownerDocument.defaultView || window;
        const proto = tag === 'textarea' ? win.HTMLTextAreaElement.prototype : win.HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
        if (setter) setter.call(el, {json.dumps(value)});
        else el.value = {json.dumps(value)};
        el.dispatchEvent(new Event('input', {{bubbles: true}}));
        el.dispatchEvent(new Event('change', {{bubbles: true}}));
        return "OK filled";
    }})()"""
    out = asyncio.run(eval_js(ws_url, js))
    print(out)
    if str(out).startswith("ERROR"):
        sys.exit(1)


def cmd_click(selector: str):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    js = f"""(() => {{
        {DEEP_QUERY_JS}
        const el = deepFind({json.dumps(selector)});
        if (!el) return "ERROR: element not found";
        el.scrollIntoView({{block: 'center'}});
        el.click();
        return "OK clicked";
    }})()"""
    out = asyncio.run(eval_js(ws_url, js))
    print(out)
    if str(out).startswith("ERROR"):
        sys.exit(1)


def cmd_press(key_name: str):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    text, vk = KEY_CODES.get(key_name, (key_name, 0))

    async def _send():
        await cdp_call(ws_url, "Input.dispatchKeyEvent", {
            "type": "rawKeyDown", "key": key_name, "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk,
        })
        if text:
            await cdp_call(ws_url, "Input.dispatchKeyEvent", {"type": "char", "text": text})
        await cdp_call(ws_url, "Input.dispatchKeyEvent", {
            "type": "keyUp", "key": key_name, "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk,
        })

    asyncio.run(_send())
    print(f"OK pressed {key_name}")


def cmd_scroll(direction: str):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    d = direction.lower()
    if d == "down":
        expr = "window.scrollBy(0, 500); window.scrollY"
    elif d == "up":
        expr = "window.scrollBy(0, -500); window.scrollY"
    elif d == "top":
        expr = "window.scrollTo(0, 0); 0"
    elif d == "bottom":
        expr = "window.scrollTo(0, document.body.scrollHeight); window.scrollY"
    else:
        expr = f"window.scrollBy(0, {int(d)}); window.scrollY"
    print(f"OK scrollY={asyncio.run(eval_js(ws_url, expr))}")


def cmd_wait(selector: str, timeout_s: float = 10.0):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    deadline = time.monotonic() + timeout_s
    js = f"(() => {{ {DEEP_QUERY_JS} return Boolean(deepFind({json.dumps(selector)})); }})()"
    while time.monotonic() < deadline:
        if asyncio.run(eval_js(ws_url, js)):
            print(f"OK found {selector}")
            return
        time.sleep(0.25)
    print(f"ERROR: timeout waiting for {selector}")
    sys.exit(1)


def cmd_screenshot(out_path: str):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    res = asyncio.run(cdp_call(ws_url, "Page.captureScreenshot", {"format": "png"}))
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(base64.b64decode(res["data"]))
    print(f"OK saved {p}")


def cmd_eval(expr: str):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    print(json.dumps(asyncio.run(eval_js(ws_url, expr)), ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Usage: aios-web <open URL | tabs | tab IDX | dom | fill SEL VAL | click SEL | press KEY | scroll DIR | wait SEL [SEC] | screenshot [PATH] | eval JS>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "open" and len(sys.argv) >= 3:
        cmd_open(sys.argv[2])
    elif cmd == "tabs":
        cmd_tabs()
    elif cmd == "tab" and len(sys.argv) >= 3:
        cmd_tab(sys.argv[2])
    elif cmd == "dom":
        cmd_dom()
    elif cmd == "fill" and len(sys.argv) >= 4:
        cmd_fill(sys.argv[2], sys.argv[3])
    elif cmd == "click" and len(sys.argv) >= 3:
        cmd_click(sys.argv[2])
    elif cmd == "press" and len(sys.argv) >= 3:
        cmd_press(sys.argv[2])
    elif cmd == "scroll" and len(sys.argv) >= 3:
        cmd_scroll(sys.argv[2])
    elif cmd == "wait" and len(sys.argv) >= 3:
        cmd_wait(sys.argv[2], float(sys.argv[3]) if len(sys.argv) >= 4 else 10.0)
    elif cmd == "screenshot":
        cmd_screenshot(sys.argv[2] if len(sys.argv) >= 3 else str(Path.home() / "Temp" / "web.png"))
    elif cmd == "eval" and len(sys.argv) >= 3:
        cmd_eval(sys.argv[2])
    else:
        print("Invalid arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
