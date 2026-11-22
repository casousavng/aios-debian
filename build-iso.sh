#!/usr/bin/env bash
set -euo pipefail

# Gera uma ISO Debian 13 Netinst com preseed.cfg embutido (instalação automática AI-OS)
# Requer: xorriso, cpio, gzip (em Linux/Debian ou macOS com xorriso)

ISO_IN="${1:-debian-13.8.0-arm64-netinst.iso}"
ISO_OUT="${2:-aios-debian-13.8-arm64.iso}"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "=== [1/4] Extrair ISO base: $ISO_IN ==="
xorriso -osirrox on -indev "$ISO_IN" -extract / "$WORKDIR/iso"
chmod -R u+w "$WORKDIR/iso"

echo "=== [2/4] Injetar preseed.cfg no initrd ==="
INITRD="$WORKDIR/iso/install.a64/initrd.gz"
gzip -d "$INITRD"
(cd "$(dirname "$0")" && echo "preseed.cfg" | cpio -H newc -o -A -F "${INITRD%.gz}")
gzip -9 "${INITRD%.gz}"

echo "=== [3/4] Configurar GRUB automático ==="
sed -i.bak 's|linux    /install.a64/vmlinuz  --- quiet|linux    /install.a64/vmlinuz  auto=true priority=critical file=/preseed.cfg --- quiet|' "$WORKDIR/iso/boot/grub/grub.cfg"
rm -f "$WORKDIR/iso/boot/grub/grub.cfg.bak"

echo "=== [4/4] Gerar ISO final: $ISO_OUT ==="
xorriso -as mkisofs \
  -r -V "AIOS_DEBIAN_ARM64" \
  -o "$ISO_OUT" \
  -J -joliet-long \
  -e boot/grub/efi.img -no-emul-boot \
  "$WORKDIR/iso"

echo "=== Concluído: $ISO_OUT ==="
