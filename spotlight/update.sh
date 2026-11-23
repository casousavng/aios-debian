#!/bin/bash
set -e
notify-send "AI-OS" "A atualizar sistema Debian e AI-OS..." 2>/dev/null || true
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo apt-get autoremove --purge -y
sudo apt-get clean
if [ -d /opt/ai-os/repo/.git ]; then
    sudo git -C /opt/ai-os/repo pull --ff-only || true
    sudo cp /opt/ai-os/repo/spotlight/*.py /opt/ai-os/repo/spotlight/*.sh /opt/ai-os/repo/spotlight/*.html /opt/ai-os/spotlight/
    sudo chmod +x /opt/ai-os/spotlight/*.py /opt/ai-os/spotlight/*.sh
fi
notify-send "AI-OS" "Atualização concluída." 2>/dev/null || true
