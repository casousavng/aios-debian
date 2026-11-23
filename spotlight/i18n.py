"""Lightweight bilingual (PT-PT / EN) localization for AI-OS."""
import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".ai-os" / "config.json"

STRINGS = {
    "pt": {
        "placeholder": "Pede algo, / para IA, # para sistema...",
        "open_windows": "Janelas Abertas",
        "no_windows": "Nenhuma janela aberta",
        "show_windows_tip": "Mostrar todas as janelas abertas",
        "volume": "Volume",
        "brightness": "Brilho",
        "podman_active": "Contentores Podman ativos: {n}",
        "podman_ready": "Podman pronto",
        "audio_out": "Saída de Áudio",
        "bt_devices": "Bluetooth",
        "update_started": "Atualização do sistema iniciada em segundo plano (`apt upgrade`).",
        "update_done": "Sistema atualizado com sucesso.",
        "update_fail": "Erro na atualização: {err}",
        "bat_low": "Bateria fraca ({pct}%). Liga o carregador.",
        "bat_crit": "Bateria crítica ({pct}%)! O sistema pode suspender em breve.",
        "displays_btn": "Detetar Ecrãs (xrandr)",
        "displays_ok": "Configuração de ecrãs atualizada (`xrandr --auto`).",
        "lock_btn": "Bloquear Ecrã (Super+L)",
        "copy": "Copiar",
        "open_litemd": "Abrir no LiteMD",
        "processing": "A processar pedido...",
        "ai_stopped": "Pedido cancelado.",
        "no_chats": "Ainda sem conversas guardadas.",
        "no_clip": "Histórico de clipboard vazio.",
        "clip_copied": "Copiado para o clipboard.",
        "saved_chat": "Conversa guardada",
        "done_notify": "Pedido concluído.",
        "new_chat": "Nova conversa agy iniciada.",
        "lang_changed": "Idioma alterado para **Português (PT-PT)**.",
        "lang_confirm_title": "Alterar Idioma do Sistema",
        "lang_confirm_msg": "Alterar o idioma reinicia o gestor de ficheiros e fecha janelas de pastas abertas. Continuar?",
        "cancel": "Cancelar",
        "confirm": "Continuar",
        "act_terminal": ("Terminal", "Abrir consola (xterm)"),
        "act_files": ("Ficheiros", "Abrir gestor de ficheiros (PCManFM)"),
        "act_browser": ("Navegador", "Abrir Chromium"),
        "act_sysinfo": ("Estado do Sistema", "Ver CPU, RAM e disco"),
        "act_sysinfo_prompt": "Mostra resumo rápido de CPU, RAM e disco desta máquina.",
        "act_lock": ("Bloquear Ecrã", "Bloquear sessão (Super+L)"),
        "act_reboot": ("Reiniciar VM", "Reiniciar o sistema"),
        "act_poweroff": ("Desligar VM", "Desligar o sistema"),
        "open_app": "Abrir aplicação ({cmd})",
        "attach_agy": "Anexar ao pedido agy",
        "slash_usage": "Ver limites e consumo atual da subscrição agy",
        "slash_model": "Escolher e ativar modelo do agy",
        "slash_mode": "Alternar modo de execução (auto, accept-edits, plan)",
        "slash_models": "Listar todos os modelos do agy",
        "slash_agents": "Listar agentes disponíveis no agy",
        "slash_mcp": "Listar servidores MCP configurados",
        "slash_new": "Iniciar nova conversa limpa",
        "slash_clear": "Limpar sessão atual do agy",
        "slash_compact": "Compactar contexto da conversa atual",
        "slash_plan": "Pedir plano antes de executar",
        "slash_chats": "Abrir lista de conversas guardadas (Ctrl+H)",
        "slash_audit": "Ver registo de auditoria das ações da IA",
        "audit_empty": "Ainda sem registos em `~/.ai-os/audit.log`.",
        "oobe_title": "Bem-vindo ao AI-OS",
        "oobe_msg": "O Antigravity CLI (agy) ainda não está autenticado.\nEscolhe o idioma e inicia sessão na tua conta Google:",
        "oobe_login": "Login AGY",
        "oobe_later": "Mais tarde",
        "slash_clip": "Histórico de clipboard (últimos textos copiados)",
        "slash_lock": "Bloquear ecrã imediatamente (Super+L)",
        "slash_screenshot": "Capturar ecrã e anexar ao Spotlight (Print)",
        "slash_displays": "Detetar monitores externos (xrandr --auto)",
        "slash_login": "Autenticar conta Google no agy CLI",
        "slash_logout": "Terminar sessão do agy CLI",
        "slash_update": "Atualizar sistema Debian, agy e AI-OS",
        "slash_lang": "Alternar idioma (pt / en)",
        "wifi_label": "Wi-Fi",
        "wifi_none": "Sem adaptador Wi-Fi ativo",
        "wifi_pw_prompt": "Password para {ssid}:",
        "bt_label": "Bluetooth",
        "step_tool": "A executar ferramenta ({tool})...",
        "step_thinking": "A pensar...",
        "login_started": "Browser aberto para login Google.\n\nDepois de autorizar, **cola o código `4/0...` aqui no Spotlight e prime Enter**.",
        "login_ok": "Autenticação **agy** concluída com sucesso!",
        "login_fail": "Falha na autenticação: {err}",
        "logout_ok": "Sessão **agy** terminada.",
        "slash_changelog": "Ver novidades da versão do agy",
        "slash_help": "Mostrar ajuda do agy CLI",
        "activate_model": "Ativar modelo ({id})",
        "litemd_open": "Abrir",
        "litemd_empty": "# LiteMD\n\nClica em **Abrir** para escolher um ficheiro `.md`.",
    },
    "en": {
        "placeholder": "Ask anything, / for AI, # for system...",
        "open_windows": "Open Windows",
        "no_windows": "No open windows",
        "show_windows_tip": "Show all open windows",
        "volume": "Volume",
        "brightness": "Brightness",
        "podman_active": "Active Podman containers: {n}",
        "podman_ready": "Podman ready",
        "audio_out": "Audio Output",
        "bt_devices": "Bluetooth",
        "update_started": "System update started in background (`apt upgrade`).",
        "update_done": "System updated successfully.",
        "update_fail": "Update failed: {err}",
        "bat_low": "Low battery ({pct}%). Plug in charger.",
        "bat_crit": "Critical battery ({pct}%)! System may suspend soon.",
        "displays_btn": "Detect Displays (xrandr)",
        "displays_ok": "Display layout updated (`xrandr --auto`).",
        "lock_btn": "Lock Screen (Super+L)",
        "copy": "Copy",
        "open_litemd": "Open in LiteMD",
        "processing": "Processing request...",
        "ai_stopped": "Request cancelled.",
        "no_chats": "No saved conversations yet.",
        "no_clip": "Clipboard history is empty.",
        "clip_copied": "Copied to clipboard.",
        "saved_chat": "Saved conversation",
        "done_notify": "Task completed.",
        "new_chat": "New agy conversation started.",
        "lang_changed": "Language switched to **English (EN)**.",
        "lang_confirm_title": "Switch System Language",
        "lang_confirm_msg": "Switching language restarts the file manager and closes open folder windows. Continue?",
        "cancel": "Cancel",
        "confirm": "Continue",
        "act_terminal": ("Terminal", "Open terminal (xterm)"),
        "act_files": ("Files", "Open file manager (PCManFM)"),
        "act_browser": ("Browser", "Open Chromium"),
        "act_sysinfo": ("System Status", "View CPU, RAM, and disk"),
        "act_sysinfo_prompt": "Show a quick summary of CPU, RAM, and disk on this machine.",
        "act_lock": ("Lock Screen", "Lock session (Super+L)"),
        "act_reboot": ("Reboot VM", "Restart the system"),
        "act_poweroff": ("Power Off VM", "Shut down the system"),
        "open_app": "Open application ({cmd})",
        "attach_agy": "Attach to agy prompt",
        "slash_usage": "Show current agy subscription limits and usage",
        "slash_model": "Choose and activate agy model",
        "slash_mode": "Switch execution mode (auto, accept-edits, plan)",
        "slash_models": "List all available agy models",
        "slash_agents": "List available agy agents",
        "slash_mcp": "List configured MCP servers",
        "slash_new": "Start a clean new conversation",
        "slash_clear": "Clear current agy session",
        "slash_compact": "Compact current conversation context",
        "slash_plan": "Request a plan before executing",
        "slash_chats": "Open saved conversations list (Ctrl+H)",
        "slash_audit": "View AI action audit log",
        "audit_empty": "No entries in `~/.ai-os/audit.log` yet.",
        "oobe_title": "Welcome to AI-OS",
        "oobe_msg": "Antigravity CLI (agy) is not signed in yet.\nChoose your language and sign in with Google:",
        "oobe_login": "Login AGY",
        "oobe_later": "Later",
        "slash_clip": "Clipboard history (recently copied texts)",
        "slash_lock": "Lock screen immediately (Super+L)",
        "slash_screenshot": "Capture screen and attach to Spotlight (Print)",
        "slash_displays": "Detect external monitors (xrandr --auto)",
        "slash_login": "Sign in Google account to agy CLI",
        "slash_logout": "Sign out of agy CLI",
        "slash_update": "Update Debian system, agy, and AI-OS",
        "slash_lang": "Switch language (pt / en)",
        "wifi_label": "Wi-Fi",
        "wifi_none": "No active Wi-Fi adapter",
        "wifi_pw_prompt": "Password for {ssid}:",
        "bt_label": "Bluetooth",
        "step_tool": "Running tool ({tool})...",
        "step_thinking": "Thinking...",
        "login_started": "Browser opened for Google sign-in.\n\nAfter authorizing, **paste the `4/0...` code here in Spotlight and press Enter**.",
        "login_ok": "**agy** authentication succeeded!",
        "login_fail": "Authentication failed: {err}",
        "logout_ok": "**agy** signed out.",
        "slash_changelog": "Show agy version changelog",
        "slash_help": "Show agy CLI help",
        "activate_model": "Activate model ({id})",
        "litemd_open": "Open",
        "litemd_empty": "# LiteMD\n\nClick **Open** to choose a `.md` file.",
    },
}


def get_lang() -> str:
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            lang = data.get("lang", "").lower()
            if lang in STRINGS:
                return lang
    except Exception:
        pass
    return "en" if os.environ.get("LANG", "").startswith("en") else "pt"


def set_lang(lang: str) -> str:
    lang = "en" if lang.lower().startswith("en") else "pt"
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    data["lang"] = lang
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    sys_locale = "pt_PT.UTF-8" if lang == "pt" else "en_US.UTF-8"
    os.environ["LANG"] = sys_locale
    os.environ["LC_ALL"] = sys_locale
    try:
        import subprocess
        subprocess.Popen(["sudo", "localectl", "set-locale", f"LANG={sys_locale}"])
        subprocess.Popen(
            f"pkill -x pcmanfm; LANG={sys_locale} LC_ALL={sys_locale} setsid pcmanfm --desktop </dev/null >/dev/null 2>&1 & sleep 0.6; python3 /opt/ai-os/spotlight/wallpaper.py",
            shell=True,
        )
    except Exception:
        pass
    return lang


def t(key: str, **kwargs):
    lang = get_lang()
    val = STRINGS.get(lang, STRINGS["pt"]).get(key, key)
    if isinstance(val, str) and kwargs:
        return val.format(**kwargs)
    return val
