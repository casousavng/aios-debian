# AI-OS Debian

Sistema operativo minimalista e **AI-first** baseado em **Debian 13 (Trixie)**, desenhado para interação direta com o agente **Antigravity CLI (`agy`)** através de uma barra **Spotlight** estilo Apple Liquid Glass sempre acessível no fundo do ecrã.

## Arquitetura & Funcionalidades
- **Base leve:** Debian Netinst sem DE pesado (`99norecommends`), `zram-tools` (LZ4), `GRUB_TIMEOUT=1`, `PipeWire` + `WirePlumber` + `Podman` rootless.
- **Desktop limpo (`Openbox` + `PCManFM` + `picom`):**
  - Tema unificado **AI-OS-Glass** (`themerc` + `gtk.css` + `Papirus-Dark`).
  - **Barra de topo (`28px`):** logo `◉` (indica `✦ AI...` quando o agente trabalha), itens de janelas abertas/minimizadas clicáveis, estado de rede, bateria e relógio.
  - **Wallpaper dinâmico (`wallpaper.py`):** ondas geradas em Cairo que mudam ao longo do dia.
  - **Notificações (`dunst`):** toasts escuros quando tarefas longas terminam.
- **Spotlight AI (`spotlight_ui.py` + `server.py`):**
  - Input fixo de **1 linha com scroll vertical** (`Enter` envia, `Shift+Enter` quebra linha, `Ctrl+↑/↓` histórico).
  - **Streaming em tempo real** (`/api/ask_stream` via `agy --output-format stream-json`) com renderização Markdown (`WebKit2`), botões **Copiar** e **Abrir no LiteMD**.
  - **Wrapper `agy` completo:** autocomplete `@ficheiro`, comandos `/models`, `/agents`, `/mcp`, `/new`, `/clear`, além de abrir apps/ficheiros locais.
  - **Atalho:** `Super+Espaço` / `Alt+Espaço` foca o Spotlight; `Esc` limpa.
- **LiteMD (`litemd.py`):** leitor Markdown leve (`GTK3` + `WebKit2GTK`) registado como app padrão para `.md`.

## Estrutura
```text
aios-debian/
├── AGENTS.md                 # Regras de governação do agente
├── preseed.cfg               # Instalação automática Debian 13 ARM64
├── build-iso.sh              # Gera ISO instalável automática com preseed
├── install-aios.sh           # Provisionamento idempotente sobre Debian
├── config/
│   ├── 99norecommends        # APT sem recomendações/sugestões
│   ├── dunstrc               # Notificações AI-OS
│   ├── gtk.css               # Tema GTK3 escuro unificado
│   ├── picom.conf            # Compositor (blur, sombras, fading)
│   └── openbox/
│       ├── autostart         # picom, dunst, pcmanfm, wallpaper, Spotlight
│       ├── rc.xml            # Margem 28px, tema AI-OS-Glass, atalhos
│       └── themerc           # Tema de janelas AI-OS-Glass
└── spotlight/
    ├── server.py             # Backend FastAPI + SSE streaming para agy
    ├── spotlight_ui.py       # TopBar + Spotlight Apple Glass (GTK3/WebKit2)
    ├── wallpaper.py          # Gerador de wallpaper dinâmico (Cairo)
    ├── litemd.py             # Leitor Markdown nativo
    └── index.html            # Fallback web
```

## Instalação Rápida numa VM/PC Debian
```bash
git clone https://github.com/casousavng/aios-debian.git
cd aios-debian
bash install-aios.sh
```
Depois autentica o `agy` uma vez (`~/.local/bin/agy`) e reinicia.
