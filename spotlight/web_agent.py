#!/usr/bin/env python3
"""Lightweight Chromium CDP browser automation CLI for AI-OS (aios-web)."""
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request

CDP_URL = "http://127.0.0.1:9222"


def get_pages():
    with urllib.request.urlopen(f"{CDP_URL}/json/list", timeout=2) as r:
        return [p for p in json.loads(r.read().decode()) if p.get("type") == "page"]


def ensure_browser():
    try:
        pages = get_pages()
        if pages:
            return pages[0]
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
                return pages[0]
        except Exception:
            pass
    raise RuntimeError("Chromium CDP did not start on 127.0.0.1:9222")


async def cdp_call(ws_url: str, method: str, params: dict = None):
    import websockets

    async with websockets.connect(ws_url, max_size=8 * 1024 * 1024) as ws:
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
    time.sleep(0.5)
    info = asyncio.run(eval_js(ws_url, "({title: document.title, url: location.href})"))
    print(json.dumps(info, ensure_ascii=False))


def cmd_dom():
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    js = r"""(() => {
        const els = Array.from(document.querySelectorAll('a[href],button,input,textarea,select,[role="button"]'));
        const items = [];
        let idx = 0;
        for (const el of els) {
            const rect = el.getBoundingClientRect();
            if (rect.width <= 0 && rect.height <= 0) continue;
            el.setAttribute('data-aios-id', String(idx));
            const tag = el.tagName.toLowerCase();
            const info = {
                idx,
                selector: `[data-aios-id="${idx}"]`,
                tag,
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
            if (idx >= 80) break;
        }
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
        const el = document.querySelector({json.dumps(selector)});
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
        const proto = tag === 'textarea' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
        if (setter) setter.call(el, {json.dumps(value)});
        else el.value = {json.dumps(value)};
        el.dispatchEvent(new Event('input', {{bubbles: true}}));
        el.dispatchEvent(new Event('change', {{bubbles: true}}));
        return "OK filled";
    }})()"""
    print(asyncio.run(eval_js(ws_url, js)))


def cmd_click(selector: str):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    js = f"""(() => {{
        const el = document.querySelector({json.dumps(selector)});
        if (!el) return "ERROR: element not found";
        el.scrollIntoView({{block: 'center'}});
        el.click();
        return "OK clicked";
    }})()"""
    print(asyncio.run(eval_js(ws_url, js)))


def cmd_eval(expr: str):
    page = ensure_browser()
    ws_url = page["webSocketDebuggerUrl"]
    print(json.dumps(asyncio.run(eval_js(ws_url, expr)), ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Usage: aios-web <open URL | dom | fill SELECTOR VALUE | click SELECTOR | eval JS>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "open" and len(sys.argv) >= 3:
        cmd_open(sys.argv[2])
    elif cmd == "dom":
        cmd_dom()
    elif cmd == "fill" and len(sys.argv) >= 4:
        cmd_fill(sys.argv[2], sys.argv[3])
    elif cmd == "click" and len(sys.argv) >= 3:
        cmd_click(sys.argv[2])
    elif cmd == "eval" and len(sys.argv) >= 3:
        cmd_eval(sys.argv[2])
    else:
        print("Invalid arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
