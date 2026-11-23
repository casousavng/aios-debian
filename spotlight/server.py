#!/usr/bin/env python3
import json
import os
import pty
import re
import select
import subprocess
import time
import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import psutil
import uvicorn
from i18n import get_lang, t

app = FastAPI()
BASE_DIR = Path("/opt/ai-os/spotlight")
HOME = Path.home()
CHATS_DIR = HOME / ".ai-os" / "chats"
LOGS_DIR = HOME / ".ai-os" / "logs"
CHATS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class PromptRequest(BaseModel):
    prompt: str
    chat_id: str | None = None

def get_wifi_status() -> str:
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
            stderr=subprocess.DEVNULL, text=True
        )
        for line in out.splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1] or "Wi-Fi"
        dev_out = subprocess.check_output(
            ["nmcli", "-t", "-f", "TYPE,STATE", "dev"],
            stderr=subprocess.DEVNULL, text=True
        )
        for line in dev_out.splitlines():
            if ":connected" in line:
                return "Online"
        return "Offline"
    except Exception:
        return "N/D"

@app.get("/", response_class=HTMLResponse)
def index():
    return (BASE_DIR / "index.html").read_text(encoding="utf-8")

@app.get("/api/status")
def status():
    bat = psutil.sensors_battery()
    bat_str = f"{int(bat.percent)}%" if bat else "AC"
    now = datetime.datetime.now().strftime("%H:%M")
    return {"battery": bat_str, "wifi": get_wifi_status(), "time": now}

@app.get("/api/chats")
def list_chats():
    files = sorted(CHATS_DIR.glob("*.md"), reverse=True)
    return [{"id": f.stem, "title": f.stem} for f in files[:25]]

@app.get("/api/chats/{chat_id}")
def read_chat(chat_id: str):
    path = CHATS_DIR / f"{chat_id}.md"
    if not path.exists():
        return {"content": ""}
    return {"content": path.read_text(encoding="utf-8")}


_MODELS_CACHE = None
_AUTH_SESSION = {"pid": None, "fd": None}
AGY_DIR = HOME / ".gemini" / "antigravity-cli"
AGY_TOKEN = AGY_DIR / "antigravity-oauth-token"


class AuthCodeRequest(BaseModel):
    code: str


@app.get("/api/agy/auth/status")
def agy_auth_status():
    env = os.environ.copy()
    env["PATH"] = f"{HOME / '.local/bin'}:{env.get('PATH', '')}"
    installed = subprocess.call(["which", "agy"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    return {"installed": installed, "authenticated": AGY_TOKEN.exists()}


@app.post("/api/agy/auth/login_start")
def agy_auth_login_start():
    # Clean previous pending auth session
    if _AUTH_SESSION["pid"]:
        try:
            os.kill(_AUTH_SESSION["pid"], 9)
        except OSError:
            pass
    if _AUTH_SESSION["fd"] is not None:
        try:
            os.close(_AUTH_SESSION["fd"])
        except OSError:
            pass

    agy_bin = HOME / ".local" / "bin" / "agy"
    if not agy_bin.exists():
        return {"ok": False, "error": "agy binary not found"}

    # Remove old token so agy prompts login flow
    if AGY_TOKEN.exists():
        AGY_TOKEN.unlink()

    pid, fd = pty.fork()
    if pid == 0:
        os.execv(str(agy_bin), ["agy"])

    _AUTH_SESSION["pid"] = pid
    _AUTH_SESSION["fd"] = fd
    buf = b""
    sent_enter = False
    start = time.time()
    url = None
    while time.time() - start < 15:
        if not sent_enter and time.time() - start > 2.2:
            os.write(fd, b"\r")
            sent_enter = True
        r, _, _ = select.select([fd], [], [], 0.25)
        if fd in r:
            try:
                buf += os.read(fd, 4096)
            except OSError:
                break
            text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", buf.decode("utf-8", errors="ignore"))
            m = re.search(r"─+\s*(https://accounts\.google\.com/.*?)─+", text, re.S)
            if m:
                url = re.sub(r"\s+", "", m.group(1))
                break

    if url:
        env = os.environ.copy()
        env.setdefault("DISPLAY", ":0")
        subprocess.Popen(["chromium", url], env=env)
        return {"ok": True, "url": url}
    return {"ok": False, "error": "Could not obtain OAuth URL from agy"}


@app.post("/api/agy/auth/login_code")
def agy_auth_login_code(req: AuthCodeRequest):
    fd = _AUTH_SESSION.get("fd")
    pid = _AUTH_SESSION.get("pid")
    if fd is None or not pid:
        return {"ok": False, "error": "No active login session. Run /login first."}

    os.write(fd, (req.code.strip() + "\r").encode())
    end = time.time() + 10
    while time.time() < end:
        if AGY_TOKEN.exists():
            break
        time.sleep(0.3)

    try:
        os.kill(pid, 9)
        os.close(fd)
    except OSError:
        pass
    _AUTH_SESSION["pid"] = None
    _AUTH_SESSION["fd"] = None

    if AGY_TOKEN.exists():
        cfg_path = AGY_DIR / "settings.json"
        if not cfg_path.exists():
            cfg_path.write_text(json.dumps({
                "agentMode": "auto",
                "allowNonWorkspaceAccess": True,
                "artifactReviewPolicy": "always-proceed",
                "colorScheme": "dark",
                "model": "Gemini 4 Hydrogen (Medium)",
                "queuedMessages": "send-immediately",
                "toolPermission": "always-proceed",
                "trustedWorkspaces": [str(HOME)],
            }, indent=2), encoding="utf-8")
        return {"ok": True}
    return {"ok": False, "error": "Token exchange failed"}


@app.post("/api/agy/auth/logout")
def agy_auth_logout():
    if AGY_TOKEN.exists():
        AGY_TOKEN.unlink()
    return {"ok": True}


@app.get("/api/agy/models")
def agy_models():
    global _MODELS_CACHE
    if _MODELS_CACHE is not None:
        return _MODELS_CACHE
    env = os.environ.copy()
    env["PATH"] = f"{HOME / '.local/bin'}:{env.get('PATH', '')}"
    try:
        out = subprocess.check_output(["agy", "models"], env=env, text=True, stderr=subprocess.DEVNULL)
        items = []
        for line in out.splitlines():
            if "\t" in line:
                mid, label = line.split("\t", 1)
                items.append({"id": mid.strip(), "label": label.strip()})
        _MODELS_CACHE = items
        return items
    except Exception:
        return []

@app.post("/api/ask")
def ask(req: PromptRequest):
    prompt = req.prompt.strip()
    if prompt in ("/new", "/clear"):
        return {"chat_id": None, "reply": t("new_chat")}

    if prompt.startswith("/model "):
        model_name = prompt.split(None, 1)[1].strip()
        cfg_path = HOME / ".gemini" / "antigravity-cli" / "settings.json"
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
            cfg["model"] = model_name
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            msg = f"Model set to `{model_name}`." if get_lang() == "en" else f"Modelo alterado para `{model_name}`."
            return {"chat_id": req.chat_id, "reply": msg}
        except Exception as e:
            return {"chat_id": req.chat_id, "reply": f"Error: {e}"}

    if prompt.startswith("/mode "):
        mode_val = prompt.split(None, 1)[1].strip()
        cfg_path = HOME / ".gemini" / "antigravity-cli" / "settings.json"
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
            cfg["agentMode"] = mode_val
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            msg = f"Mode set to `{mode_val}`." if get_lang() == "en" else f"Modo alterado para `{mode_val}`."
            return {"chat_id": req.chat_id, "reply": msg}
        except Exception as e:
            return {"chat_id": req.chat_id, "reply": f"Error: {e}"}

    chat_id = req.chat_id or datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    chat_file = CHATS_DIR / f"{chat_id}.md"

    with chat_file.open("a", encoding="utf-8") as f:
        f.write(f"\n### Utilizador\n{req.prompt}\n")

    # Deteta o agente CLI instalado (agy ou opencode), incluindo ~/.local/bin
    env = os.environ.copy()
    extra_bins = f"{HOME / '.local/bin'}:{HOME / '.opencode/bin'}"
    env["PATH"] = f"{extra_bins}:{env.get('PATH', '')}"

    agent_bin = None
    for candidate in ["agy", "opencode"]:
        found = subprocess.run(
            ["which", candidate], env=env, capture_output=True, text=True
        )
        if found.returncode == 0:
            agent_bin = found.stdout.strip()
            break

    if agent_bin:
        if Path(agent_bin).name == "opencode":
            cmd = [agent_bin, "run", req.prompt]
        elif prompt in ("/models", "/agents", "/mcp", "/help", "/changelog"):
            sub = prompt.lstrip("/")
            cmd = [agent_bin, sub, "list"] if sub == "mcp" else [agent_bin, sub]
        else:
            cmd = [agent_bin, "--mode", "auto", "--dangerously-skip-permissions"]
            if req.chat_id and prompt != "/usage":
                cmd.append("--continue")
            cmd.extend(["-p", req.prompt])
        proc = subprocess.run(cmd, cwd=str(HOME), env=env, capture_output=True, text=True)
        reply = proc.stdout.strip() or proc.stderr.strip() or "Concluído."
        if prompt == "/usage" and "\t" in reply:
            rows = [r.split("\t") for r in reply.splitlines() if "\t" in r]
            md = ["| Grupo | Limite | Restante | Reset |", "|---|---|---|---|"]
            for cols in rows:
                cols = (cols + ["", "", "", ""])[:4]
                md.append("| " + " | ".join(c.strip() for c in cols) + " |")
            reply = "\n".join(md)
        (LOGS_DIR / "last_action.log").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
    else:
        reply = (
            "⚠️ Nenhum agente CLI (`agy` ou `opencode`) encontrado no PATH.\n"
            "Instala e autentica o teu agente CLI na máquina para ativar a execução autónoma."
        )

    with chat_file.open("a", encoding="utf-8") as f:
        f.write(f"\n### AI-OS\n{reply}\n")

    return {"chat_id": chat_id, "reply": reply}


@app.post("/api/ask_stream")
def ask_stream(req: PromptRequest):
    prompt = req.prompt.strip()
    if prompt in ("/new", "/clear"):
        def _reset():
            yield json.dumps({"chat_id": None, "reply": t("new_chat"), "done": True}) + "\n"
        return StreamingResponse(_reset(), media_type="application/x-ndjson")

    chat_id = req.chat_id or datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    chat_file = CHATS_DIR / f"{chat_id}.md"
    with chat_file.open("a", encoding="utf-8") as f:
        f.write(f"\n### Utilizador\n{req.prompt}\n")

    env = os.environ.copy()
    extra_bins = f"{HOME / '.local/bin'}:{HOME / '.opencode/bin'}"
    env["PATH"] = f"{extra_bins}:{env.get('PATH', '')}"

    agent_bin = None
    for candidate in ["agy", "opencode"]:
        found = subprocess.run(["which", candidate], env=env, capture_output=True, text=True)
        if found.returncode == 0:
            agent_bin = found.stdout.strip()
            break

    def _stream():
        if not agent_bin:
            msg = "⚠️ Nenhum agente CLI (`agy` ou `opencode`) encontrado no PATH."
            yield json.dumps({"chat_id": chat_id, "reply": msg, "done": True}) + "\n"
            return

        if Path(agent_bin).name == "opencode" or prompt.startswith(("/model ", "/mode ")) or prompt in ("/usage", "/models", "/agents", "/mcp", "/help", "/changelog"):
            res = ask(req)
            yield json.dumps({"chat_id": res["chat_id"], "reply": res["reply"], "done": True}) + "\n"
            return

        cmd = [agent_bin, "--mode", "auto", "--dangerously-skip-permissions", "--output-format", "stream-json"]
        if req.chat_id:
            cmd.append("--continue")
        cmd.extend(["-p", req.prompt])

        proc = subprocess.Popen(
            cmd, cwd=str(HOME), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        full_reply = []
        final_text = ""
        for raw_line in proc.stdout:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                ev = json.loads(raw_line)
            except Exception:
                continue
            etype = ev.get("event")
            if etype == "step_update":
                su = ev.get("step_update", {})
                delta = su.get("text_delta")
                if delta:
                    full_reply.append(delta)
                    yield json.dumps({"delta": delta, "done": False}) + "\n"
            elif etype == "result":
                final_text = ev.get("result", {}).get("response", "").strip()

        proc.wait()
        reply = final_text or "".join(full_reply).strip() or proc.stderr.read().strip() or "Concluído."
        with chat_file.open("a", encoding="utf-8") as f:
            f.write(f"\n### AI-OS\n{reply}\n")
        (LOGS_DIR / "last_action.log").write_text(reply, encoding="utf-8")
        yield json.dumps({"chat_id": chat_id, "reply": reply, "done": True}) + "\n"

    return StreamingResponse(_stream(), media_type="application/x-ndjson")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
