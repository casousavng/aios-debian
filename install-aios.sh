#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/6] Configurar APT sem pacotes recomendados e locales PT/EN ==="
sudo cp config/99norecommends /etc/apt/apt.conf.d/99norecommends
sudo sed -i 's/^# *pt_PT.UTF-8 UTF-8/pt_PT.UTF-8 UTF-8/' /etc/locale.gen
sudo locale-gen pt_PT.UTF-8 en_US.UTF-8
sudo apt-get update

echo "=== [2/6] Instalar Xorg, Openbox, PCManFM, Spotlight GTK3 e utilitários de sistema ==="
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  xorg xinit openbox pcmanfm picom wmctrl x11-xserver-utils papirus-icon-theme librsvg2-common \
  python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 python3-markdown spice-vdagent \
  network-manager cups brightnessctl pipewire wireplumber dunst libnotify-bin podman ufw i3lock \
  python3 python3-fastapi python3-uvicorn python3-psutil \
  curl git libglib2.0-bin xterm zram-tools

echo "=== [3/6] Criar estrutura de pastas do AI-OS ==="
mkdir -p "$HOME/Desktop" "$HOME/Documentos" "$HOME/Projetos" "$HOME/Temp"
mkdir -p "$HOME/.ai-os/chats" "$HOME/.ai-os/logs" "$HOME/.config/openbox"

cp AGENTS.md "$HOME/AGENTS.md"
sudo cp AGENTS.md /etc/AGENTS.md
cp config/openbox/autostart "$HOME/.config/openbox/autostart"
cp config/openbox/rc.xml "$HOME/.config/openbox/rc.xml"
cp config/picom.conf "$HOME/.config/picom.conf"
mkdir -p "$HOME/.config/dunst"
cp config/dunstrc "$HOME/.config/dunst/dunstrc"
chmod +x "$HOME/.config/openbox/autostart"

mkdir -p "$HOME/.themes/AI-OS-Glass/openbox-3"
cp config/openbox/themerc "$HOME/.themes/AI-OS-Glass/openbox-3/themerc"

mkdir -p "$HOME/.config/gtk-3.0"
cp config/gtk.css "$HOME/.config/gtk-3.0/gtk.css"
cat << 'EOF' > "$HOME/.config/gtk-3.0/settings.ini"
[Settings]
gtk-icon-theme-name=Papirus-Dark
gtk-application-prefer-dark-theme=1
EOF
echo 'gtk-icon-theme-name="Papirus-Dark"' > "$HOME/.gtkrc-2.0"

echo "=== [4/6] Instalar aplicação Spotlight ==="
sudo mkdir -p /opt/ai-os/spotlight
sudo cp spotlight/server.py spotlight/index.html spotlight/spotlight_ui.py spotlight/wallpaper.py spotlight/litemd.py spotlight/i18n.py /opt/ai-os/spotlight/
sudo chmod +x /opt/ai-os/spotlight/spotlight_ui.py /opt/ai-os/spotlight/wallpaper.py /opt/ai-os/spotlight/litemd.py
sudo ln -sf /opt/ai-os/spotlight/litemd.py /usr/local/bin/litemd
sudo tee /usr/share/applications/litemd.desktop >/dev/null << 'EOF'
[Desktop Entry]
Name=LiteMD
Comment=Leitor Markdown leve para AI-OS
Exec=litemd %f
Icon=text-x-generic
Terminal=false
Type=Application
MimeType=text/markdown;text/x-markdown;
Categories=Utility;Office;
EOF
xdg-mime default litemd.desktop text/markdown text/x-markdown

echo "=== [5/6] Configurar serviço systemd (user) para o backend do Spotlight ==="
mkdir -p "$HOME/.config/systemd/user"
cat << 'EOF' > "$HOME/.config/systemd/user/aios-spotlight.service"
[Unit]
Description=AI-OS Spotlight Backend
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/ai-os/spotlight/server.py
Restart=always
WorkingDirectory=%h

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now aios-spotlight.service
sudo loginctl enable-linger "$USER"

echo "=== [6/6] Configurar Autologin no TTY1 e arranque direto do Xorg ==="
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
cat << EOF | sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF

if ! grep -q "exec startx" "$HOME/.profile"; then
  cat << 'EOF' >> "$HOME/.profile"

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec startx
fi
EOF
fi

echo "exec openbox-session" > "$HOME/.xinitrc"
echo "=== Instalação concluída! Reinicia a máquina para entrar no AI-OS. ==="
