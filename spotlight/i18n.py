"""Lightweight bilingual (PT-PT / EN) localization for AI-OS."""
import json
import os
import re
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
        "displays_short": "Detetar Ecrãs",
        "displays_ok": "Configuração de ecrãs atualizada (`xrandr --auto`).",
        "lock_btn": "Bloquear Ecrã (Super+L)",
        "lock_short": "Bloquear",
        "reboot_btn": "Reiniciar",
        "poweroff_btn": "Desligar",
        "tz_btn": "Data / Hora",
        "tz_title": "Data, Hora & Fuso Horário",
        "tz_ntp": "Sincronizar automaticamente (NTP)",
        "tz_dt_lbl": "Data e Hora (AAAA-MM-DD HH:MM):",
        "tz_zone_lbl": "Fuso Horário:",
        "tz_ok": "Fuso horário definido para **{tz}** (NTP ativo).",
        "sec_audio_display": "Som & Ecrã",
        "sec_conn": "Ligações",
        "sec_sys": "Sistema",
        "slash_tz": "Alterar fuso horário e relógio (timedatectl)",
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
        "slash_apps": "Listar todas as aplicações instaladas",
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
        "slash_kb": "Alternar layout de teclado (pt / us / es / fr / gb)",
        "kb_changed": "Layout de teclado alterado para **{layout}**.",
        "apps_btn": "Apps",
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
        "prof_fast": ("Rápido", "Hydrogen/Flash Medium · execução direta"),
        "prof_deep": ("Profundo", "Modelo High · análise complexa"),
        "prof_plan": ("Só Planear", "Planeia antes sem alterar ficheiros"),
        "prof_set": "Perfil AI alterado para **{name}** (`{model}`).",
        "font_small": ("Letra Pequena (12px)", "Texto compacto nas respostas"),
        "font_normal": ("Letra Normal (13px)", "Tamanho predefinido das respostas"),
        "font_large": ("Letra Grande (15px)", "Leitura mais confortável"),
        "font_set": "Tamanho da letra alterado para **{px}px**.",
        "settings_title": "Definições AI-OS",
        "settings_ai": "Agente AI",
        "settings_ui": "Chat &amp; Idioma",
        "settings_ui_tab": "Chat & Idioma",
        "settings_sys": "Sistema",
        "close_btn": "Fechar",
        "slash_settings": "Abrir janela de definições do AI-OS",
        "slash_help": "Mostrar ajuda do agy CLI",
        "activate_model": "Ativar modelo ({id})",
        "litemd_open": "Abrir",
        "litemd_empty": "# LiteMD\n\nClica em **Abrir** para escolher um ficheiro `.md`.",
        "confirm_danger_title": "Confirmar ação sensível",
        "confirm_danger_body": "Este pedido pode alterar ou remover ficheiros, pacotes ou estado crítico do sistema:\n\n«{prompt}»\n\nQueres mesmo executar?",
        "confirm_danger_btn": "Confirmar e Executar",
        "action_cancelled": "Ação cancelada pelo utilizador.",
        "danger_blocked": "⚠️ Ação sensível bloqueada: requer confirmação explícita.",
        "slash_remind": "Agendar lembrete (ex: #remind 10m pausa)",
        "remind_ok": "Lembrete agendado para daqui a **{when}**: {msg}",
        "remind_usage": "Uso: `#remind 10m Mensagem` (aceita `s`, `m`, `h`).",
        "slash_notif": "Histórico de notificações e lembretes",
        "notif_empty": "Sem notificações registadas.",
        "slash_reminders": "Ver e gerir lembretes e crons ativos",
        "reminders_empty": "Sem lembretes nem automações cron ativas.",
        "reminder_deleted": "Agendamento removido.",
        "bell_tip": "Lembretes, crons e notificações",
        "bell_sched_hdr": "Lembretes & Crons",
        "bell_notif_hdr": "Notificações recentes",
        "bell_tab_notif": "Notificações",
        "bell_tab_auto": "Automações",
        "bell_clear": "Limpar",
        "new_chat_btn": "Novo chat",
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
        "displays_short": "Displays",
        "displays_ok": "Display layout updated (`xrandr --auto`).",
        "lock_btn": "Lock Screen (Super+L)",
        "lock_short": "Lock",
        "reboot_btn": "Reboot",
        "poweroff_btn": "Power Off",
        "tz_btn": "Date / Time",
        "tz_title": "Date, Time & Timezone",
        "tz_ntp": "Automatic time (NTP)",
        "tz_dt_lbl": "Date & Time (YYYY-MM-DD HH:MM):",
        "tz_zone_lbl": "Timezone:",
        "tz_ok": "Timezone set to **{tz}** (NTP enabled).",
        "sec_audio_display": "Audio & Display",
        "sec_conn": "Connections",
        "sec_sys": "System",
        "slash_tz": "Change timezone and clock (timedatectl)",
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
        "slash_apps": "List all installed applications",
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
        "slash_kb": "Switch keyboard layout (pt / us / es / fr / gb)",
        "kb_changed": "Keyboard layout set to **{layout}**.",
        "apps_btn": "Apps",
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
        "prof_fast": ("Fast", "Hydrogen/Flash Medium · direct execution"),
        "prof_deep": ("Deep", "High model · complex reasoning"),
        "prof_plan": ("Plan Only", "Plans first without editing files"),
        "prof_set": "AI profile set to **{name}** (`{model}`).",
        "font_small": ("Small Text (12px)", "Compact chat text"),
        "font_normal": ("Normal Text (13px)", "Default chat text size"),
        "font_large": ("Large Text (15px)", "Larger, easier reading"),
        "font_set": "Chat font size set to **{px}px**.",
        "settings_title": "AI-OS Settings",
        "settings_ai": "AI Agent",
        "settings_ui": "Chat &amp; Language",
        "settings_ui_tab": "Chat & Language",
        "settings_sys": "System",
        "close_btn": "Close",
        "slash_settings": "Open AI-OS settings window",
        "slash_help": "Show agy CLI help",
        "activate_model": "Activate model ({id})",
        "litemd_open": "Open",
        "litemd_empty": "# LiteMD\n\nClick **Open** to choose a `.md` file.",
        "confirm_danger_title": "Confirm sensitive action",
        "confirm_danger_body": "This request may modify or delete files, packages, or critical system state:\n\n\"{prompt}\"\n\nProceed anyway?",
        "confirm_danger_btn": "Confirm & Run",
        "action_cancelled": "Action cancelled by user.",
        "danger_blocked": "⚠️ Sensitive action blocked: explicit confirmation required.",
        "slash_remind": "Schedule reminder (e.g. #remind 10m break)",
        "remind_ok": "Reminder scheduled in **{when}**: {msg}",
        "remind_usage": "Usage: `#remind 10m Message` (supports `s`, `m`, `h`).",
        "slash_notif": "Notifications & reminders history",
        "notif_empty": "No notifications recorded yet.",
        "slash_reminders": "View and manage active reminders & crons",
        "reminders_empty": "No active reminders or cron automations.",
        "reminder_deleted": "Schedule removed.",
        "bell_tip": "Reminders, crons & notifications",
        "bell_sched_hdr": "Reminders & Crons",
        "bell_notif_hdr": "Recent notifications",
        "bell_tab_notif": "Notifications",
        "bell_tab_auto": "Automations",
        "bell_clear": "Clear",
        "new_chat_btn": "New Chat",
    },
}


def get_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def update_config(**kwargs):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = get_config()
    data.update(kwargs)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


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
            f"pkill -x nemo-desktop; LANG={sys_locale} LC_ALL={sys_locale} setsid nemo-desktop </dev/null >/dev/null 2>&1 & sleep 0.6; python3 /opt/ai-os/spotlight/wallpaper.py",
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


_DANGER_PATTERNS = (
    ("destructive_delete", re.compile(r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\b|\b(apagar|eliminar|deletar|delete|remove|wipe|shred)\s+(tudo|all|disco|disk|sistema|system|pasta\s+home|/\w*)", re.I)),
    ("disk_format", re.compile(r"\b(mkfs|fdisk|parted|wipefs|dd\s+if=|formatar)\b", re.I)),
    ("power_action", re.compile(r"\b(reboot|poweroff|shutdown|halt|reiniciar(\s+o)?\s+(sistema|pc|vm|máquina)|desligar(\s+o)?\s+(sistema|pc|vm|máquina))\b", re.I)),
    ("pkg_remove", re.compile(r"\b(apt(-get)?\s+(remove|purge|autoremove)|dpkg\s+--(remove|purge)|desinstalar|uninstall)\b", re.I)),
    ("sys_security", re.compile(r"\b(chmod\s+-R\s+777|chown\s+-R|ufw\s+disable|iptables\s+-F|userdel|visudo|systemctl\s+(stop|disable))\b", re.I)),
)


def is_dangerous_prompt(prompt: str) -> str | None:
    p = (prompt or "").strip()
    if not p or p in ("/new", "/clear", "/models", "/agents", "/mcp", "/help", "/changelog", "/usage", "/update"):
        return None
    for reason, pat in _DANGER_PATTERNS:
        if pat.search(p):
            return reason
    return None


def human_cron(schedule: str, lang: str | None = None) -> str:
    lang = lang or get_lang()
    parts = (schedule or "").strip().split()
    if len(parts) != 5:
        return schedule
    m, h, dom, mon, dow = parts
    pt = lang == "pt"
    if parts == ["*", "*", "*", "*", "*"]:
        return "Todos os minutos" if pt else "Every minute"
    if m.startswith("*/") and h == "*" and dom == "*" and mon == "*" and dow == "*":
        n = m[2:]
        return f"A cada {n} min" if pt else f"Every {n} min"
    if m.isdigit() and h == "*" and dom == "*" and mon == "*" and dow == "*":
        return f"De hora a hora (:{int(m):02d})" if pt else f"Hourly (:{int(m):02d})"
    if m.isdigit() and h.startswith("*/") and dom == "*" and mon == "*" and dow == "*":
        n = h[2:]
        return f"A cada {n}h (:{int(m):02d})" if pt else f"Every {n}h (:{int(m):02d})"
    if m.isdigit() and h.isdigit() and dom == "*" and mon == "*":
        hhmm = f"{int(h):02d}:{int(m):02d}"
        if dow == "*":
            return f"Todos os dias às {hhmm}" if pt else f"Daily at {hhmm}"
        if dow == "1-5":
            return f"Dias úteis às {hhmm}" if pt else f"Weekdays at {hhmm}"
        days_pt = {"0": "Domingo", "7": "Domingo", "1": "Segunda", "2": "Terça", "3": "Quarta", "4": "Quinta", "5": "Sexta", "6": "Sábado"}
        days_en = {"0": "Sunday", "7": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday", "4": "Thursday", "5": "Friday", "6": "Saturday"}
        dname = (days_pt if pt else days_en).get(dow)
        if dname:
            return f"{dname} às {hhmm}" if pt else f"{dname} at {hhmm}"
    if m.isdigit() and h.isdigit() and dom.isdigit() and mon.isdigit() and dow == "*":
        hhmm = f"{int(h):02d}:{int(m):02d}"
        return f"{int(dom):02d}/{int(mon):02d} às {hhmm}" if pt else f"{int(mon):02d}/{int(dom):02d} at {hhmm}"
    return schedule
