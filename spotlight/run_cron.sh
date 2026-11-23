#!/bin/bash
# AI-OS native cron job runner: run_cron.sh <id> <kind:notify|ask|cmd> <base64_payload>
ID="${1:-unknown}"
KIND="${2:-notify}"
B64="${3:-}"
PAYLOAD=$(printf '%s' "$B64" | base64 -d 2>/dev/null || true)

export DISPLAY="${DISPLAY:-:0}"
UID_NUM=$(id -u)
if [ -S "/run/user/${UID_NUM}/bus" ]; then
    export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${UID_NUM}/bus"
fi

NOTIF_LOG="$HOME/.ai-os/notifications.log"
mkdir -p "$HOME/.ai-os"
TS=$(date "+%Y-%m-%d %H:%M:%S")

case "$KIND" in
    notify)
        printf '%s | AI-OS Cron | %s\n' "$TS" "${PAYLOAD:0:160}" >> "$NOTIF_LOG"
        notify-send -u critical -t 0 "AI-OS Cron" "$PAYLOAD" 2>/dev/null || true
        ;;
    ask)
        BODY=$(python3 -c 'import json,sys; print(json.dumps({"prompt": sys.argv[1], "confirmed": False}))' "$PAYLOAD")
        REPLY=$(curl -s -X POST http://127.0.0.1:8765/api/ask -H "Content-Type: application/json" -d "$BODY" | jq -r '.reply // "Concluído."' 2>/dev/null || echo "Erro backend")
        printf '%s\n' "$REPLY" > "$HOME/.ai-os/logs/last_cron.log"
        CLEAN=$(python3 -c 'import re,sys; s=re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",sys.argv[1]); s=re.sub(r"[#*`]+","",s); s=" ".join(s.splitlines()[0].split()) if s.strip() else "Concluída."; print(s[:95])' "$REPLY")
        printf '%s | AI-OS Auto | %s\n' "$TS" "$CLEAN" >> "$NOTIF_LOG"
        notify-send -u critical -t 0 "AI-OS Automação concluída" "$CLEAN" 2>/dev/null || true
        ;;
    cmd)
        OUT=$(bash -lc "$PAYLOAD" 2>&1 | tail -n 3 | tr '\n' ' ' | cut -c1-160)
        printf '%s | AI-OS Cmd (%s) | %s\n' "$TS" "$ID" "${OUT:-ok}" >> "$NOTIF_LOG"
        ;;
esac
