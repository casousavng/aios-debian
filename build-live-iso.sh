#!/usr/bin/env bash
set -euo pipefail

# Builds a clean, bootable AI-OS Debian 13 (Trixie) amd64 Live + Installer hybrid ISO.
# Must be run on Debian/Linux (x86_64/amd64) with root privileges and `live-build`.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
ARCH="${ARCH:-amd64}"
DISTRO="${DISTRO:-trixie}"
ISO_OUT="${1:-$REPO_DIR/aios-debian-13-${ARCH}-live.iso}"
WORKDIR="$(mktemp -d /tmp/aios-lb.XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "=== [1/4] Preparing live-build workspace in $WORKDIR ==="
cd "$WORKDIR"

lb config \
  --architecture "$ARCH" \
  --distribution "$DISTRO" \
  --archive-areas "main contrib non-free-firmware" \
  --binary-images iso-hybrid \
  --bootloaders "syslinux,grub-efi" \
  --debian-installer live \
  --debian-installer-gui true \
  --iso-application "AI-OS Debian" \
  --iso-volume "AIOS_DEBIAN_LIVE" \
  --apt-recommends false \
  --memtest none \
  --bootappend-live "boot=live components quiet splash username=aios hostname=aios"

echo "=== [2/4] Configuring packages ==="
mkdir -p config/package-lists config/includes.chroot/opt/ai-os/spotlight \
  config/includes.chroot/etc/chromium.d \
  config/includes.chroot/etc/apt/apt.conf.d \
  config/includes.chroot/etc/apt/dpkg.cfg.d \
  config/includes.chroot/etc/skel/.config/openbox \
  config/includes.chroot/etc/skel/.config/dunst \
  config/includes.chroot/etc/skel/.config/gtk-3.0 \
  config/includes.chroot/etc/skel/.config/systemd/user \
  config/includes.chroot/etc/xdg/openbox \
  config/includes.chroot/etc/xdg/dunst \
  config/includes.chroot/usr/share/applications \
  config/hooks/live

cat << 'EOF' > config/package-lists/aios.list.chroot
linux-image-amd64
live-boot
live-config
live-config-systemd
calamares
calamares-settings-debian
xorg
xinit
openbox
nemo
cinnamon-l10n
feh
picom
wmctrl
x11-xserver-utils
papirus-icon-theme
librsvg2-common
chromium
xterm
dunst
libnotify-bin
i3lock
xss-lock
lxpolkit
podman
network-manager
wireplumber
pipewire-pulse
brightnessctl
scrot
xdotool
jq
poppler-utils
curl
ca-certificates
sudo
zram-tools
earlyoom
ufw
python3
python3-gi
python3-cairo
python3-fastapi
python3-uvicorn
python3-psutil
python3-markdown
gir1.2-gtk-3.0
gir1.2-webkit2-4.1
EOF

echo "=== [3/4] Copying AI-OS files & skel defaults (zero credentials) ==="
cp "$REPO_DIR/spotlight/"*.py "$REPO_DIR/spotlight/"*.sh "$REPO_DIR/spotlight/"*.html \
  config/includes.chroot/opt/ai-os/spotlight/
cp "$REPO_DIR/AGENTS.md" config/includes.chroot/etc/skel/AGENTS.md
cp "$REPO_DIR/config/01_nodoc" config/includes.chroot/etc/apt/dpkg.cfg.d/01_nodoc 2>/dev/null || true
cp "$REPO_DIR/config/99norecommends" config/includes.chroot/etc/apt/apt.conf.d/99norecommends
cp "$REPO_DIR/config/aios-cdp" config/includes.chroot/etc/chromium.d/aios-cdp
cp "$REPO_DIR/config/litemd.desktop" config/includes.chroot/usr/share/applications/litemd.desktop
cp "$REPO_DIR/config/openbox/"* config/includes.chroot/etc/skel/.config/openbox/
cp "$REPO_DIR/config/openbox/"* config/includes.chroot/etc/xdg/openbox/
cp "$REPO_DIR/config/picom.conf" config/includes.chroot/etc/skel/.config/picom.conf
cp "$REPO_DIR/config/dunstrc" config/includes.chroot/etc/skel/.config/dunst/dunstrc
cp "$REPO_DIR/config/dunstrc" config/includes.chroot/etc/xdg/dunst/dunstrc
cp "$REPO_DIR/config/gtk.css" config/includes.chroot/etc/skel/.config/gtk-3.0/gtk.css

cat << 'EOF' > config/includes.chroot/etc/skel/.xinitrc
#!/bin/sh
exec openbox-session
EOF
chmod +x config/includes.chroot/etc/skel/.xinitrc

cat << 'EOF' > config/includes.chroot/etc/skel/.profile
if [ -z "${DISPLAY:-}" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec startx
fi
EOF

cat << 'EOF' > config/includes.chroot/etc/skel/.config/systemd/user/aios-spotlight.service
[Unit]
Description=AI-OS Spotlight Backend
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/ai-os/spotlight/server.py
Restart=always
RestartSec=2

[Install]
WantedBy=default.target
EOF

cat << 'EOF' > config/hooks/live/010-aios-setup.chroot
#!/bin/sh
set -e
chmod +x /opt/ai-os/spotlight/*.py /opt/ai-os/spotlight/*.sh
ln -sf /opt/ai-os/spotlight/web_agent.py /usr/local/bin/aios-web
ln -sf /opt/ai-os/spotlight/litemd.py /usr/local/bin/litemd
update-desktop-database /usr/share/applications || true
mkdir -p /etc/skel/Desktop /etc/skel/Documentos /etc/skel/Projetos /etc/skel/Downloads /etc/skel/Temp
mkdir -p /etc/skel/.config/systemd/user/default.target.wants
ln -sf ../aios-spotlight.service /etc/skel/.config/systemd/user/default.target.wants/aios-spotlight.service
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat << 'GETTY' > /etc/systemd/system/getty@tty1.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin aios --noclear %I $TERM
GETTY
systemctl enable NetworkManager cron earlyoom || true
EOF
chmod +x config/hooks/live/010-aios-setup.chroot

echo "=== [4/4] Building hybrid ISO ==="
lb build
BUILT_ISO="$(ls -1 *.hybrid.iso 2>/dev/null | head -n1 || true)"
[ -n "$BUILT_ISO" ] || { echo "Error: hybrid ISO not produced"; exit 1; }
mv "$BUILT_ISO" "$ISO_OUT"
sha256sum "$ISO_OUT" > "${ISO_OUT}.sha256"
echo "=== Done: $ISO_OUT ==="
