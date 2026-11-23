#!/usr/bin/env python3
import base64
import fcntl
import json
import os
import pty
import re
import select
import struct
import subprocess
import termios
import threading
import time
import uuid
import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import psutil
import uvicorn
from i18n import get_lang, is_dangerous_prompt, t

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
    confirmed: bool = False

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
    notif_count = len(NOTIF_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()) if NOTIF_LOG.exists() else 0
    return {"battery": bat_str, "wifi": get_wifi_status(), "time": now, "alerts": notif_count}

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
_AUTH_SESSION = {"pid": None, "fd": None, "browser_pid": None}
AGY_DIR = HOME / ".gemini" / "antigravity-cli"
AGY_TOKEN = AGY_DIR / "antigravity-oauth-token"


class AuthCodeRequest(BaseModel):
    code: str


class WifiConnectRequest(BaseModel):
    ssid: str
    password: str = ""


@app.get("/api/net/wifi")
def list_wifi():
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi", "list"],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        )
        seen = set()
        nets = []
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[1] and parts[1] not in seen:
                seen.add(parts[1])
                nets.append({"active": parts[0] == "yes", "ssid": parts[1], "signal": parts[2]})
        return nets[:6]
    except Exception:
        return []


@app.post("/api/net/wifi")
def connect_wifi(req: WifiConnectRequest):
    cmd = ["nmcli", "dev", "wifi", "connect", req.ssid]
    if req.password:
        cmd.extend(["password", req.password])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {"ok": proc.returncode == 0, "msg": proc.stdout.strip() or proc.stderr.strip()}


@app.post("/api/net/bt_toggle")
def toggle_bt():
    try:
        show = subprocess.check_output(["bluetoothctl", "show"], text=True, stderr=subprocess.DEVNULL)
        powered = "Powered: yes" in show
        subprocess.run(["bluetoothctl", "power", "off" if powered else "on"], capture_output=True)
        return {"ok": True, "powered": not powered}
    except Exception:
        return {"ok": False, "powered": False}


class AudioSinkRequest(BaseModel):
    id: int


class BtDeviceRequest(BaseModel):
    mac: str


@app.get("/api/audio/sinks")
def list_audio_sinks():
    try:
        out = subprocess.check_output(["wpctl", "status"], text=True, stderr=subprocess.DEVNULL, timeout=3)
        sinks = []
        in_sinks = False
        for line in out.splitlines():
            if "Sinks:" in line:
                in_sinks = True
                continue
            if in_sinks:
                if not line.strip() or ("Sources:" in line or "Filters:" in line or "Streams:" in line or "Video" in line):
                    break
                m = re.search(r"([*])?\s*(\d+)\.\s+(.+?)\s*(?:\[vol:|$)", line)
                if m:
                    sinks.append({"default": bool(m.group(1)), "id": int(m.group(2)), "name": m.group(3).strip()})
        return sinks[:6]
    except Exception:
        return []


@app.post("/api/audio/default")
def set_audio_default(req: AudioSinkRequest):
    proc = subprocess.run(["wpctl", "set-default", str(req.id)], capture_output=True)
    return {"ok": proc.returncode == 0}


@app.get("/api/bt/devices")
def list_bt_devices():
    try:
        out = subprocess.check_output(["bluetoothctl", "devices", "Paired"], text=True, stderr=subprocess.DEVNULL, timeout=3)
        devs = []
        for line in out.splitlines():
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0] == "Device":
                mac, name = parts[1], parts[2]
                info = subprocess.check_output(["bluetoothctl", "info", mac], text=True, stderr=subprocess.DEVNULL, timeout=2)
                devs.append({"mac": mac, "name": name, "connected": "Connected: yes" in info})
        return devs[:5]
    except Exception:
        return []


@app.post("/api/bt/connect")
def connect_bt_device(req: BtDeviceRequest):
    try:
        info = subprocess.check_output(["bluetoothctl", "info", req.mac], text=True, stderr=subprocess.DEVNULL, timeout=2)
        action = "disconnect" if "Connected: yes" in info else "connect"
        proc = subprocess.run(["bluetoothctl", action, req.mac], capture_output=True, text=True, timeout=8)
        return {"ok": proc.returncode == 0, "connected": action == "connect"}
    except Exception:
        return {"ok": False}


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
        child_env = os.environ.copy()
        child_env["TERM"] = "xterm-256color"
        child_env["COLUMNS"] = "120"
        child_env["LINES"] = "40"
        os.execve(str(agy_bin), ["agy"], child_env)

    _AUTH_SESSION["pid"] = pid
    _AUTH_SESSION["fd"] = fd
    try:
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
    except OSError:
        pass
    buf = b""
    sent_enter = False
    start = time.time()
    url = None
    while time.time() - start < 20:
        r, _, _ = select.select([fd], [], [], 0.2)
        if fd in r:
            try:
                buf += os.read(fd, 4096)
            except OSError:
                break
            text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", buf.decode("utf-8", errors="ignore"))
            if not sent_enter and ("Select login method" in text or "Google OAuth" in text):
                time.sleep(0.2)
                os.write(fd, b"\r")
                sent_enter = True
            osc = re.search(r"(https://accounts\.google\.com/[^\s\x07\x1b]+)", text)
            if osc and "state=" in osc.group(1):
                url = osc.group(1)
                break
            m = re.search(r"─+\s*(https://accounts\.google\.com/.*?)─+", text, re.S)
            if m:
                url = re.sub(r"\s+", "", m.group(1))
                break
        elif not sent_enter and time.time() - start > 4.0:
            os.write(fd, b"\r")
            sent_enter = True

    if url:
        env = os.environ.copy()
        env.setdefault("DISPLAY", ":0")
        bproc = subprocess.Popen(["chromium", url], env=env)
        _AUTH_SESSION["browser_pid"] = bproc.pid
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
    if _AUTH_SESSION.get("browser_pid"):
        try:
            os.kill(_AUTH_SESSION["browser_pid"], 15)
        except OSError:
            pass
        _AUTH_SESSION["browser_pid"] = None

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


class ProfileRequest(BaseModel):
    profile: str


@app.post("/api/agy/profile")
def set_agy_profile(req: ProfileRequest):
    prof = req.profile.lower()
    env = os.environ.copy()
    env["PATH"] = f"{HOME / '.local/bin'}:/usr/local/bin:{env.get('PATH', '')}"
    models = []
    try:
        out = subprocess.check_output(["agy", "models"], env=env, text=True, stderr=subprocess.DEVNULL, timeout=5)
        for line in out.splitlines():
            if "\t" in line:
                models.append(line.split("\t", 1)[1].strip())
    except Exception:
        pass

    def _pick(prefs):
        for p in prefs:
            for m in models:
                if p.lower() in m.lower():
                    return m
        return None

    cfg_path = HOME / ".gemini" / "antigravity-cli" / "settings.json"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    if prof == "deep":
        chosen = _pick(["hydrogen (high)", "neon (high)", "(high)"])
        mode = "auto"
    elif prof == "plan":
        chosen = _pick(["hydrogen (medium)", "flash (medium)", "(medium)"])
        mode = "plan"
    else:
        prof = "fast"
        chosen = _pick(["hydrogen (medium)", "flash (medium)", "(medium)"])
        mode = "auto"

    if chosen:
        cfg["model"] = chosen
    cfg["agentMode"] = mode
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return {"ok": True, "profile": prof, "model": cfg.get("model", ""), "mode": mode}


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

    if is_dangerous_prompt(prompt) and not req.confirmed:
        _write_audit(req.prompt, ["guardrail"], "blocked")
        return {"chat_id": req.chat_id, "requires_confirmation": True, "reply": t("danger_blocked")}

    if prompt == "/update":
        upd_cmd = (
            "sudo apt-get update && "
            "sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y && "
            "sudo apt-get autoremove -y && sudo apt-get clean"
        )
        proc = subprocess.run(["bash", "-lc", upd_cmd], capture_output=True, text=True)
        summary = "\n".join(proc.stdout.strip().splitlines()[-12:]) or proc.stderr.strip()
        return {"chat_id": req.chat_id, "reply": f"```\n{summary}\n```"}

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
            "⚠️ Motor do Assistente AI-OS não encontrado no sistema.\n"
            "Instala e autentica o motor de agente na máquina para ativar a execução autónoma."
        )

    with chat_file.open("a", encoding="utf-8") as f:
        f.write(f"\n### AI-OS\n{reply}\n")
    _write_audit(req.prompt, [], "ok" if agent_bin else "no-agent")

    return {"chat_id": chat_id, "reply": reply}


def _write_audit(prompt: str, tools: list, status: str):
    try:
        audit_file = HOME / ".ai-os" / "audit.log"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        one_line = " ".join(prompt.split())[:140]
        t_str = ",".join(dict.fromkeys(tools)) if tools else "-"
        with audit_file.open("a", encoding="utf-8") as af:
            af.write(f"{ts} | {status} | {t_str} | {one_line}\n")
    except Exception:
        pass


_ACTIVE_PROC = {"proc": None}


@app.post("/api/ask_stop")
def ask_stop():
    proc = _ACTIVE_PROC.get("proc")
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            return {"ok": True, "stopped": True}
        except Exception:
            pass
    return {"ok": True, "stopped": False}


@app.post("/api/ask_stream")
def ask_stream(req: PromptRequest):
    prompt = req.prompt.strip()
    if prompt in ("/new", "/clear"):
        def _reset():
            yield json.dumps({"chat_id": None, "reply": t("new_chat"), "done": True}) + "\n"
        return StreamingResponse(_reset(), media_type="application/x-ndjson")

    if is_dangerous_prompt(prompt) and not req.confirmed:
        _write_audit(req.prompt, ["guardrail"], "blocked")
        def _blocked():
            yield json.dumps({"chat_id": req.chat_id, "requires_confirmation": True, "reply": t("danger_blocked"), "done": True}) + "\n"
        return StreamingResponse(_blocked(), media_type="application/x-ndjson")

    chat_id = req.chat_id or datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    chat_file = CHATS_DIR / f"{chat_id}.md"

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
            msg = "⚠️ Motor do Assistente AI-OS não encontrado no sistema."
            yield json.dumps({"chat_id": chat_id, "reply": msg, "done": True}) + "\n"
            return

        if Path(agent_bin).name == "opencode" or prompt.startswith(("/model ", "/mode ")) or prompt in ("/usage", "/models", "/agents", "/mcp", "/help", "/changelog", "/update"):
            res = ask(req)
            yield json.dumps({"chat_id": res["chat_id"], "reply": res["reply"], "done": True}) + "\n"
            return

        with chat_file.open("a", encoding="utf-8") as f:
            f.write(f"\n### Utilizador\n{req.prompt}\n")

        cfg_mode = "auto"
        try:
            s_file = HOME / ".gemini" / "antigravity-cli" / "settings.json"
            if s_file.exists():
                cfg_mode = json.loads(s_file.read_text(encoding="utf-8")).get("agentMode", "auto")
        except Exception:
            pass
        cmd = [agent_bin, "--mode", cfg_mode, "--dangerously-skip-permissions", "--output-format", "stream-json"]
        if req.chat_id:
            cmd.append("--continue")
        cmd.extend(["-p", req.prompt])

        before_sched = {it.get("id") for it in _load_reminders()} | {it.get("id") for it in list_crons()}
        proc = subprocess.Popen(
            cmd, cwd=str(HOME), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        _ACTIVE_PROC["proc"] = proc
        full_reply = []
        final_text = ""
        used_tools = []
        try:
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
                    stype = su.get("step_type", "")
                    delta = su.get("text_delta")
                    if delta:
                        full_reply.append(delta)
                        yield json.dumps({"delta": delta, "done": False}) + "\n"
                    elif stype and stype not in ("user_input", "agent_response") and not full_reply:
                        tool_name = su.get("tool_name") or stype
                        used_tools.append(tool_name)
                        yield json.dumps({"status": tool_name, "done": False}) + "\n"
                    elif su.get("tool_name"):
                        used_tools.append(su.get("tool_name"))
                elif etype == "result":
                    final_text = ev.get("result", {}).get("response", "").strip()

            rc = proc.wait()
        finally:
            if _ACTIVE_PROC.get("proc") is proc:
                _ACTIVE_PROC["proc"] = None
        reply = final_text or "".join(full_reply).strip() or proc.stderr.read().strip() or "Concluído."
        after_sched = {it.get("id") for it in _load_reminders()} | {it.get("id") for it in list_crons()}
        ephemeral = bool(after_sched - before_sched)
        if ephemeral and not req.chat_id:
            try:
                chat_file.unlink(missing_ok=True)
            except OSError:
                pass
        else:
            with chat_file.open("a", encoding="utf-8") as f:
                f.write(f"\n### AI-OS\n{reply}\n")
        (LOGS_DIR / "last_action.log").write_text(reply, encoding="utf-8")
        _write_audit(req.prompt, used_tools, f"rc={rc}")
        yield json.dumps({"chat_id": None if ephemeral else chat_id, "ephemeral": ephemeral, "reply": reply, "done": True}) + "\n"

    return StreamingResponse(_stream(), media_type="application/x-ndjson")


REMINDERS_FILE = HOME / ".ai-os" / "reminders.json"
NOTIF_LOG = HOME / ".ai-os" / "notifications.log"
_REM_LOCK = threading.Lock()
_TIMERS: dict[str, threading.Timer] = {}


class ReminderRequest(BaseModel):
    delay_seconds: int = 60
    message: str


class CronRequest(BaseModel):
    schedule: str
    kind: str = "notify"  # notify | ask | cmd
    payload: str
    label: str = ""


def _log_notif(title: str, body: str):
    try:
        NOTIF_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with NOTIF_LOG.open("a", encoding="utf-8") as nf:
            nf.write(f"{ts} | {title} | {' '.join(body.split())[:160]}\n")
    except Exception:
        pass


def _load_reminders() -> list:
    try:
        if REMINDERS_FILE.exists():
            return json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_reminders(items: list):
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REMINDERS_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _fire_reminder(rid: str):
    msg = None
    with _REM_LOCK:
        _TIMERS.pop(rid, None)
        items = _load_reminders()
        kept = []
        for it in items:
            if it.get("id") == rid:
                msg = it.get("message", "Lembrete")
            else:
                kept.append(it)
        _save_reminders(kept)
    if msg is not None:
        _log_notif("AI-OS Lembrete", msg)
        try:
            env = os.environ.copy()
            env.setdefault("DISPLAY", ":0")
            subprocess.Popen(["notify-send", "-u", "critical", "-t", "0", "AI-OS Lembrete", msg], env=env)
        except Exception:
            pass


def _schedule_timer(item: dict):
    rid = item.get("id")
    if not rid:
        return
    delay = max(0.5, float(item.get("fire_at", 0)) - time.time())
    old = _TIMERS.pop(rid, None)
    if old:
        old.cancel()
    tm = threading.Timer(delay, _fire_reminder, args=(rid,))
    tm.daemon = True
    _TIMERS[rid] = tm
    tm.start()


def _schedule_all_reminders():
    with _REM_LOCK:
        items = _load_reminders()
    for it in items:
        if not it.get("done"):
            _schedule_timer(it)


@app.get("/api/reminders")
def list_reminders():
    with _REM_LOCK:
        return _load_reminders()


@app.post("/api/reminders")
def create_reminder(req: ReminderRequest):
    delay = max(1, min(int(req.delay_seconds), 86400 * 30))
    item = {
        "id": uuid.uuid4().hex[:8],
        "fire_at": time.time() + delay,
        "message": req.message.strip()[:240],
        "done": False,
    }
    with _REM_LOCK:
        items = _load_reminders()
        items.append(item)
        _save_reminders(items)
    _schedule_timer(item)
    return {"ok": True, "reminder": item}


@app.delete("/api/reminders/{rid}")
def delete_reminder(rid: str):
    with _REM_LOCK:
        tm = _TIMERS.pop(rid, None)
        if tm:
            tm.cancel()
        items = [it for it in _load_reminders() if it.get("id") != rid]
        _save_reminders(items)
    return {"ok": True}


def _read_crontab() -> list[str]:
    proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    return proc.stdout.splitlines()


def _write_crontab(lines: list[str]):
    body = ("\n".join(lines).rstrip() + "\n") if lines else ""
    subprocess.run(["crontab", "-"], input=body, text=True, check=True)


@app.get("/api/crons")
def list_crons():
    out = []
    for line in _read_crontab():
        m = re.match(r"^(#PAUSED\s+)?(\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+.*?#\s*aios-cron:([a-f0-9]+):(\w+):(.*)$", line.strip())
        if m:
            out.append({
                "id": m.group(3),
                "schedule": m.group(2),
                "kind": m.group(4),
                "label": m.group(5).strip(),
                "paused": bool(m.group(1)),
            })
    return out


@app.post("/api/crons")
def create_cron(req: CronRequest):
    sched = " ".join(req.schedule.strip().split())
    if len(sched.split()) != 5 or any(c in sched for c in ("\n", "\r", ";", "&", "|")):
        return {"ok": False, "error": "Invalid 5-field cron expression"}
    kind = req.kind if req.kind in ("notify", "ask", "cmd") else "notify"
    cid = uuid.uuid4().hex[:8]
    b64 = base64.b64encode(req.payload.strip().encode("utf-8")).decode("ascii")
    label = " ".join((req.label or req.payload).split())[:60].replace("\n", " ")
    entry = f"{sched} /opt/ai-os/spotlight/run_cron.sh {cid} {kind} {b64} # aios-cron:{cid}:{kind}:{label}"
    lines = [l for l in _read_crontab() if l.strip()]
    lines.append(entry)
    _write_crontab(lines)
    return {"ok": True, "cron": {"id": cid, "schedule": sched, "kind": kind, "label": label}}


@app.post("/api/crons/{cid}/toggle")
def toggle_cron(cid: str):
    tag = f"# aios-cron:{cid}:"
    new_lines = []
    paused = False
    for l in _read_crontab():
        if tag in l:
            s = l.lstrip()
            if s.startswith("#PAUSED "):
                l = s[len("#PAUSED "):]
                paused = False
            else:
                l = "#PAUSED " + s
                paused = True
        new_lines.append(l)
    _write_crontab(new_lines)
    return {"ok": True, "paused": paused}


@app.delete("/api/crons/{cid}")
def delete_cron(cid: str):
    tag = f"# aios-cron:{cid}:"
    lines = [l for l in _read_crontab() if tag not in l]
    _write_crontab(lines)
    return {"ok": True}


@app.get("/api/notifications")
def list_notifications():
    if not NOTIF_LOG.exists():
        return []
    return NOTIF_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()[-30:]


@app.delete("/api/notifications")
def clear_notifications():
    try:
        if NOTIF_LOG.exists():
            NOTIF_LOG.unlink()
    except OSError:
        pass
    return {"ok": True}


if __name__ == "__main__":
    _schedule_all_reminders()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
