#!/bin/bash
set -e
notify-send "AI-OS" "A atualizar sistema Debian e AI-OS..." 2>/dev/null || true
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo apt-get autoremove --purge -y
sudo apt-get clean
if [ -d /opt/ai-os/repo/.git ]; then
    sudo git -C /opt/ai-os/repo pull --ff-only || true
    # Validate staged files before deploying
    for py in /opt/ai-os/repo/spotlight/*.py; do
        python3 -m py_compile "$py"
    done
    for sh in /opt/ai-os/repo/spotlight/*.sh; do
        bash -n "$sh"
    done
    sudo rm -rf /opt/ai-os/spotlight.bak
    sudo cp -a /opt/ai-os/spotlight /opt/ai-os/spotlight.bak
    if ! (
        sudo cp /opt/ai-os/repo/spotlight/*.py /opt/ai-os/repo/spotlight/*.sh /opt/ai-os/repo/spotlight/*.html /opt/ai-os/spotlight/ &&
        sudo chmod +x /opt/ai-os/spotlight/*.py /opt/ai-os/spotlight/*.sh &&
        sudo python3 -m py_compile /opt/ai-os/spotlight/*.py
    ); then
        sudo rm -rf /opt/ai-os/spotlight
        sudo mv /opt/ai-os/spotlight.bak /opt/ai-os/spotlight
        notify-send -u critical "AI-OS" "Erro na atualização: rollback aplicado." 2>/dev/null || true
        exit 1
    fi
fi
notify-send "AI-OS" "Atualização concluída." 2>/dev/null || true
