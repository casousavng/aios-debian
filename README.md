# AI-OS Debian

[English](#english) · [Português](#portugu%C3%AAs)

![AI-OS Debian Desktop](docs/screenshots/desktop.png)

---

<a id="english"></a>
## English

### Overview & Vision
**AI-OS Debian** is a minimalist, **AI-first** operating system built on **Debian 13 (Trixie)**, designed around the **Antigravity CLI (`agy`)** as the primary way to interact with your computer. Instead of a heavy desktop environment, it pairs a lean **Openbox + GTK3 + picom** workspace with a persistent Apple Liquid Glass **Spotlight** bar at the bottom of the screen.

It is built to run fast on both modern machines and older hardware/VMs (~**405 MiB** RAM at idle, ~**2.9 GB** disk footprint, **776** packages), while giving the AI agent full autonomous control (`--mode auto --dangerously-skip-permissions` with passwordless `sudo`).

### Core Features
- **Spotlight AI (`spotlight/spotlight_ui.py` + `spotlight/server.py`):**
  - Fixed 1-line bottom-docked input bar; long prompts (`>54` chars or `Shift+Enter`) pop up an editable **draft card** above sharing the exact same `Gtk.TextBuffer`.
  - **Continuous Chat UI (`Lazy WebKit2GTK`):** Real-time SSE streaming (`/api/ask_stream`), right-aligned cyan user bubbles & left-aligned AI bubbles (460px max height), **Stop (`■`)** button (`/api/ask_stop`), **`/new`**, **Copy**, and **Open in LiteMD** (opens the full conversation `.md`).
  - **Persistent `Chat` & `Apps` Buttons:** `Apps` opens a visual list of all installed applications; `Chat` appears whenever an active conversation exists (persisted across reboots via `last_chat_id` in `~/.ai-os/config.json`).
  - **Separated Command Namespaces:**
    - `/` for **AGY CLI**: `/usage`, `/login`, `/logout`, `/model `, `/mode `, `/models`, `/agents`, `/mcp`, `/new`, `/clear`, `/compact`, `/plan `, `/changelog`, `/help`, plus `@file` autocomplete from `~/Desktop`, `~/Documentos`, `~/Projetos`, `~/Temp`.
    - `#` for **AI-OS System**: `#chats`, `#audit` (AI action audit log), `#clip` (15-item clipboard history), `#screenshot`, `#displays`, `#lang ` (`pt`/`en`), `#kb ` (`pt`/`us`/`es`/`fr`/`gb`), `#update` (deterministic `apt` + repo sync), `#lock`, `#reboot`, `#poweroff`.
- **Browser Agent (`spotlight/web_agent.py` -> `aios-web`):**
  - Lightweight **Chromium CDP** automation (`127.0.0.1:9222` via `python3-websockets`, 0 MB idle RAM).
  - Lets `agy` open sites, read interactive DOM elements (`[data-aios-id="N"]`), fill inputs/checkboxes/selects, click buttons, and verify results step by step (`AGENTS.md`).
- **TopBar (`28px`) & Control Center:**
  - `◉` / `✦ AI...` live agent busy indicator, clickable **4-Desktop switcher** (`Desktop 1..4` with `•` occupancy dots + `WindowsPopover` grouped by Desktop), horizontal scroll workspace switching, live `PT`/`EN` toggle (with centered confirmation), network/battery/clock, and low-battery alerts (`15%` / `5%` critical).
  - **Control Popover:** Volume (`wpctl`), **Audio Output switcher** (`wpctl` sinks), Brightness (`brightnessctl` / `xrandr`), Podman container count, Wi-Fi network selector, **Bluetooth toggle & paired devices**, **Detect Displays (`xrandr --auto`)**, and Lock Screen.
- **Desktop, Gestures & Visual Design (`Openbox` + `PCManFM` + `picom`):**
  - Unified **AI-OS-Glass** theme (`themerc`, `gtk.css`, `Papirus-Dark`, `Inter` & `JetBrains Mono` fonts, `Bibata-Modern-Classic` cursor).
  - Dynamic Cairo wave wallpaper (`wallpaper.py`) reused on the lockscreen (`lock.sh` + `i3lock` + `xss-lock` 10-min idle lock).
  - **3-Finger Touchpad Gestures (`gestures.py`):** 3-finger swipe left/right switches Desktops; 3-finger swipe up focuses Spotlight (`libinput-tools`).
  - **Native Window Tiling:** `Super+Left`, `Super+Right`, `Super+Up`, `Super+Down`.
  - **Quick Screenshot to AI:** `Print` / `Super+Shift+S` / `#screenshot` saves `~/Temp/captura.png` and auto-attaches `@Temp/captura.png ` in Spotlight.
  - **First-Boot OOBE:** Centered welcome dialog if `agy` is not yet signed in (language selector + 1-click `/login`).
  - **Built-in Apps & Lean Footprint:** `Chromium`, **LiteMD** (`litemd.py`), **GPicView**, `xterm`, `PCManFM` (`gvfs` + `udisks2`), `lxpolkit`, `dunst`, `PipeWire` + `WirePlumber`, `Podman` rootless, `ufw`, `zram-tools` (LZ4), `earlyoom`, `99norecommends`, `01_nodoc`, `journald` `50M` cap.

### Keyboard Shortcuts
| Shortcut | Action |
| :--- | :--- |
| `Super+Space` / `Alt+Space` / `Ctrl+Space` | Focus Spotlight |
| `Esc` | Clear input & close Spotlight pane |
| `Enter` / `Shift+Enter` | Send prompt / Insert newline |
| `Ctrl+↑` / `Ctrl+↓` | Navigate prompt history |
| `Ctrl+H` | Open saved AI conversations |
| `Print` / `Super+Shift+S` | Capture screen & attach `@Temp/captura.png` to Spotlight |
| `Super+L` | Lock screen (`i3lock` with wallpaper) |
| `Super+1..4` / `Ctrl+Alt+←/→` / `3-finger swipe` | Switch virtual Desktops (`Desktop 1..4`) |
| `Super+←` / `Super+→` / `Super+↑` / `Super+↓` | Tile left / Tile right / Maximize / Restore |
| `Alt+Tab` / `Alt+F4` | Switch windows / Close active window |

### Installation & Configuration
```bash
git clone https://github.com/casousavng/aios-debian.git
cd aios-debian
bash install-aios.sh
```
Reboot after installation. On first boot, the OOBE dialog lets you choose `PT`/`EN` and sign in via `/login` (browser opens Google OAuth; paste the `4/0...` code into Spotlight and press `Enter`).

---

<a id="português"></a>
## Português

### Visão Geral & Propósito
O **AI-OS Debian** é um sistema operativo minimalista e **AI-first** baseado em **Debian 13 (Trixie)**, pensado para usar o **Antigravity CLI (`agy`)** como interface principal do computador. Em vez de um ambiente gráfico pesado, combina uma base leve (**Openbox + GTK3 + picom**) com uma barra **Spotlight** estilo Apple Liquid Glass sempre acessível no fundo do ecrã.

Foi otimizado para correr rápido tanto em máquinas atuais como em hardware antigo ou VMs (~**405 MiB** RAM em idle, ~**2,9 GB** em disco, **776** pacotes), dando ao agente autonomia total (`--mode auto --dangerously-skip-permissions` com `sudo` sem password).

### Funcionalidades Principais
- **Spotlight AI (`spotlight/spotlight_ui.py` + `spotlight/server.py`):**
  - Barra fixa de 1 linha; prompts longos (`>54` chars ou `Shift+Enter`) abrem um **card editável** acima com o mesmo `Gtk.TextBuffer`.
  - **Chat Contínuo (`WebKit2GTK` lazy):** Streaming SSE em tempo real (`/api/ask_stream`), balões do utilizador à direita (ciano) e da IA à esquerda (slate, até `460px`), botão **Stop (`■`)** (`/api/ask_stop`), **`/new`**, **Copiar** e **Abrir no LiteMD** (abre o `.md` completo da conversa).
  - **Botões `Apps` e `Chat`:** `Apps` lista todas as aplicações instaladas; `Chat` reabre a conversa ativa mesmo após `Esc` ou reboot (`last_chat_id` em `~/.ai-os/config.json`).
  - **Comandos separados por prefixo:**
    - `/` para **AGY CLI**: `/usage`, `/login`, `/logout`, `/model `, `/mode `, `/models`, `/agents`, `/mcp`, `/new`, `/clear`, `/compact`, `/plan `, `/changelog`, `/help`, além de autocomplete `@ficheiro`.
    - `#` para **Sistema AI-OS**: `#chats`, `#audit` (registo de auditoria da IA), `#clip` (histórico de clipboard com 15 entradas), `#screenshot`, `#displays`, `#lang ` (`pt`/`en`), `#kb ` (`pt`/`us`/`es`/`fr`/`gb`), `#update` (atualização determinística `apt` + repo), `#lock`, `#reboot`, `#poweroff`.
- **Browser Agent (`spotlight/web_agent.py` -> `aios-web`):**
  - Automação leve via **Chromium CDP** (`127.0.0.1:9222` com `python3-websockets`, `0 MB` RAM em idle).
  - Permite ao `agy` abrir sites, ler o DOM (`[data-aios-id="N"]`), preencher campos/checkboxes/selects, clicar em botões e confirmar resultados (`AGENTS.md`).
- **Barra de Topo (`28px`) & Centro de Controlo:**
  - Indicador `◉` / `✦ AI...`, seletor de **4 Desktops** (`Desktop 1..4` com `•` de ocupação + `WindowsPopover` agrupado por Desktop), scroll horizontal na barra/desktop, toggle `PT`/`EN`, rede/bateria/hora e alertas de bateria fraca (`15%` / `5%` crítico).
  - **Popover de Controlo:** Volume (`wpctl`), **Seletor de Saída de Áudio**, Brilho (`brightnessctl`/`xrandr`), contentores Podman, Wi-Fi, **Bluetooth toggle & dispositivos emparelhados**, **Detetar Ecrãs (`xrandr --auto`)** e Bloquear Ecrã.
- **Desktop, Gestos & Grafismo (`Openbox` + `PCManFM` + `picom`):**
  - Tema unificado **AI-OS-Glass** (`themerc`, `gtk.css`, `Papirus-Dark`, fontes `Inter` e `JetBrains Mono`, cursor `Bibata-Modern-Classic`).
  - Wallpaper dinâmico em Cairo (`wallpaper.py`) reutilizado no `i3lock` (`lock.sh` + `xss-lock`).
  - **Gestos 3 Dedos (`gestures.py`):** 3 dedos esquerda/direita troca de Desktop; 3 dedos cima foca o Spotlight.
  - **Window Tiling (`Super+Setas`):** metade esquerda/direita, maximizar e restaurar.
  - **Captura Rápida (`Print` / `Super+Shift+S` / `#screenshot`):** grava `~/Temp/captura.png` e anexa `@Temp/captura.png ` no Spotlight.
  - **OOBE 1.º Arranque:** popup centrado para escolher `PT`/`EN` e fazer `/login` caso o `agy` ainda não esteja autenticado.
  - **Base Enxuta:** `Chromium`, `LiteMD`, `GPicView`, `xterm`, `PCManFM` (`gvfs` + `udisks2`), `lxpolkit`, `dunst`, `PipeWire` + `WirePlumber`, `Podman`, `ufw`, `zram-tools`, `earlyoom`, `99norecommends`, `01_nodoc`, `journald` (`50M`).

### Atalhos de Teclado
| Atalho | Ação |
| :--- | :--- |
| `Super+Espaço` / `Alt+Espaço` / `Ctrl+Espaço` | Focar Spotlight |
| `Esc` | Limpar input e fechar painel |
| `Enter` / `Shift+Enter` | Enviar pedido / Quebra de linha |
| `Ctrl+↑` / `Ctrl+↓` | Histórico de pedidos |
| `Ctrl+H` | Lista de conversas guardadas |
| `Print` / `Super+Shift+S` | Capturar ecrã e anexar `@Temp/captura.png` no Spotlight |
| `Super+L` | Bloquear ecrã (`i3lock` com wallpaper) |
| `Super+1..4` / `Ctrl+Alt+←/→` / `3 dedos` | Alternar Desktops (`Desktop 1..4`) |
| `Super+←` / `Super+→` / `Super+↑` / `Super+↓` | Metade esquerda / Metade direita / Maximizar / Restaurar |
| `Alt+Tab` / `Alt+F4` | Alternar janelas / Fechar janela ativa |

### Instalação & Estrutura
```bash
git clone https://github.com/casousavng/aios-debian.git
cd aios-debian
bash install-aios.sh
```
```text
aios-debian/
├── AGENTS.md                 # Regras de governação do agente + aios-web
├── preseed.cfg               # Instalação automática Debian 13 ARM64
├── build-iso.sh              # Gera ISO instalável automática com preseed
├── install-aios.sh           # Provisionamento idempotente sobre Debian
├── docs/screenshots/         # Capturas de ecrã
├── config/
│   ├── 01_nodoc              # Exclui docs/manpages/locales fora PT/EN
│   ├── 99norecommends        # APT sem recomendações/sugestões
│   ├── dunstrc               # Notificações AI-OS
│   ├── gtk.css               # Tema GTK3 escuro unificado
│   ├── picom.conf            # Compositor
│   └── openbox/              # autostart, rc.xml, themerc
└── spotlight/
    ├── server.py             # Backend FastAPI + SSE + audit + áudio/BT
    ├── spotlight_ui.py       # TopBar + Spotlight + Chat contínuo
    ├── web_agent.py          # Browser Agent Chromium CDP (aios-web)
    ├── gestures.py           # Gestos 3 dedos (libinput-tools)
    ├── i18n.py               # Localização PT-PT / EN + config persistente
    ├── wallpaper.py          # Wallpaper dinâmico Cairo
    ├── litemd.py             # Leitor Markdown nativo
    ├── screenshot.sh         # Captura rápida -> @Temp/captura.png
    ├── lock.sh               # Bloqueio i3lock com wallpaper
    ├── update.sh             # Atualização determinística (#update)
    └── index.html            # Fallback web
```
