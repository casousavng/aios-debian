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
  - Fixed 1-line bottom-docked input bar with vertical scroll (`Enter` sends, `Shift+Enter` newline, `Ctrl+↑/↓` prompt history, `Ctrl+H` saved chats).
  - **Lazy WebKit2GTK** Markdown renderer (~75 MiB RSS idle, 0 WebKit processes until first AI reply) with real-time SSE streaming (`/api/ask_stream`), **Copy**, and **Open in LiteMD** buttons.
  - **Separated Command Namespaces:**
    - `/` for **AGY CLI**: `/usage`, `/model `, `/mode `, `/models`, `/agents`, `/mcp`, `/new`, `/clear`, `/compact`, `/plan `, `/changelog`, `/help`, plus `@file` autocomplete from `~/Desktop`, `~/Documentos`, `~/Projetos`, `~/Temp`.
    - `#` for **AI-OS System**: `#chats`, `#clip` (15-item clipboard history), `#screenshot`, `#displays`, `#lang ` (`pt`/`en`), `#login`, `#logout`, `#update`, `#lock`, `#reboot`, `#poweroff`.
- **TopBar (`28px`) & Control Center:**
  - `◉` / `✦ AI...` live agent busy indicator, clickable open/minimized window switcher, live `PT`/`EN` language switch (with centered confirmation dialog), network status, battery, and clock.
  - **Control Popover:** Volume (`wpctl`), Brightness (`brightnessctl` / `xrandr`), active Podman container count, Wi-Fi network selector, Bluetooth toggle, **Detect Displays (`xrandr --auto`)**, and Lock Screen.
- **Desktop & Visual Design (`Openbox` + `PCManFM` + `picom`):**
  - Unified **AI-OS-Glass** dark slate + cyan-teal theme (`themerc`, `gtk.css`, `Papirus-Dark`, `Inter` & `JetBrains Mono` fonts, `Bibata-Modern-Classic` cursor).
  - Dynamic Cairo wave wallpaper (`wallpaper.py`) that shifts palette by time of day, reused on the lockscreen (`lock.sh` + `i3lock`).
  - Desktop icons support via `pcmanfm --desktop` with USB automount & Trash (`gvfs` + `udisks2`).
  - Graphical Polkit authentication (`lxpolkit`) and dark toast notifications (`dunst`).
- **Productivity & System Optimization:**
  - **Quick Screenshot to AI:** `Print` / `Super+Shift+S` / `#screenshot` saves `~/Temp/captura.png` and automatically attaches `@Temp/captura.png ` inside Spotlight.
  - **Native Window Tiling:** `Super+Left`, `Super+Right`, `Super+Up`, `Super+Down` via Openbox `MoveResizeTo`.
  - **Built-in Apps:** `Chromium`, **LiteMD** (`litemd.py`, default `.md` reader), **GPicView** (default image viewer), `xterm`.
  - **Lean Footprint:** `zram-tools` (LZ4), `earlyoom` (anti-freeze), `99norecommends` (APT without recommended/suggested bloat), `01_nodoc` (strips docs/manpages/non-PT-EN locales), `systemd-journald` capped at `50M`, `man-db.timer` disabled, `PipeWire` + `WirePlumber`, `Podman` rootless, `ufw` firewall, `openssh-server`.

### Keyboard Shortcuts
| Shortcut | Action |
| :--- | :--- |
| `Super+Space` / `Alt+Space` / `Ctrl+Space` | Focus Spotlight |
| `Esc` | Clear input & hide Spotlight results |
| `Enter` / `Shift+Enter` | Send prompt / Insert newline |
| `Ctrl+↑` / `Ctrl+↓` | Navigate prompt history |
| `Ctrl+H` | Open saved AI conversations |
| `Print` / `Super+Shift+S` | Capture screen & attach `@Temp/captura.png` to Spotlight |
| `Super+L` | Lock screen (`i3lock` with wallpaper) |
| `Super+←` / `Super+→` / `Super+↑` / `Super+↓` | Tile left / Tile right / Maximize / Restore |
| `Alt+Tab` / `Alt+F4` | Switch windows / Close active window |

### Installation & Configuration
#### Quick Install on Debian 13 (Netinst)
```bash
git clone https://github.com/casousavng/aios-debian.git
cd aios-debian
bash install-aios.sh
```
Reboot after installation. Log into `agy` directly from Spotlight with `#login` (browser opens Google OAuth; paste the `4/0...` code into Spotlight and press `Enter`).

#### Unattended ISO Build
```bash
bash build-iso.sh
```
Uses `preseed.cfg` to provision an unattended Debian 13 ARM64 installation with autologin on `tty1`, passwordless `sudo`, and `install-aios.sh`.

#### Key Configuration Files
- `spotlight/i18n.py`: Bilingual `PT-PT` / `EN` strings and live locale switching (`~/.ai-os/config.json`).
- `config/openbox/rc.xml`: Window margins (`top=28`), tiling & Spotlight shortcuts.
- `config/openbox/autostart`: Starts `picom`, `dunst`, `lxpolkit`, `pcmanfm --desktop`, `xss-lock` (10-min idle lock), `wallpaper.py`, and `spotlight_ui.py`.
- `config/01_nodoc` & `config/99norecommends`: Keeps Debian minimal across `apt` upgrades.
- `AGENTS.md`: System governance rules loaded by the agent.

---

<a id="português"></a>
## Português

### Visão Geral & Propósito
O **AI-OS Debian** é um sistema operativo minimalista e **AI-first** baseado em **Debian 13 (Trixie)**, pensado para usar o **Antigravity CLI (`agy`)** como interface principal do computador. Em vez de um ambiente gráfico pesado, combina uma base leve (**Openbox + GTK3 + picom**) com uma barra **Spotlight** estilo Apple Liquid Glass sempre acessível no fundo do ecrã.

Foi otimizado para correr rápido tanto em máquinas atuais como em hardware antigo ou VMs (~**405 MiB** RAM em idle, ~**2,9 GB** em disco, **776** pacotes), dando ao agente autonomia total (`--mode auto --dangerously-skip-permissions` com `sudo` sem password).

### Funcionalidades Principais
- **Spotlight AI (`spotlight/spotlight_ui.py` + `spotlight/server.py`):**
  - Barra fixa de 1 linha com scroll vertical (`Enter` envia, `Shift+Enter` quebra linha, `Ctrl+↑/↓` histórico, `Ctrl+H` conversas guardadas).
  - Renderização Markdown em **WebKit2GTK lazy** (~75 MiB RSS em idle, 0 processos WebKit até à 1.ª resposta) com streaming SSE (`/api/ask_stream`), botões **Copiar** e **Abrir no LiteMD**.
  - **Comandos separados por prefixo:**
    - `/` para **AGY CLI**: `/usage`, `/model `, `/mode `, `/models`, `/agents`, `/mcp`, `/new`, `/clear`, `/compact`, `/plan `, `/changelog`, `/help`, além de autocomplete `@ficheiro` em `~/Desktop`, `~/Documentos`, `~/Projetos`, `~/Temp`.
    - `#` para **Sistema AI-OS**: `#chats`, `#clip` (histórico de clipboard com 15 entradas), `#screenshot`, `#displays`, `#lang ` (`pt`/`en`), `#login`, `#logout`, `#update`, `#lock`, `#reboot`, `#poweroff`.
- **Barra de Topo (`28px`) & Centro de Controlo:**
  - Indicador `◉` / `✦ AI...` quando a IA está a trabalhar, lista clicável de janelas abertas/minimizadas, alternância instantânea `PT`/`EN` (com popup centrado de confirmação), estado de rede, bateria e relógio.
  - **Popover de Controlo:** Volume (`wpctl`), Brilho (`brightnessctl` / `xrandr`), contentores Podman ativos, ligação Wi-Fi, toggle Bluetooth, **Detetar Ecrãs (`xrandr --auto`)** e Bloquear Ecrã.
- **Desktop & Grafismo (`Openbox` + `PCManFM` + `picom`):**
  - Tema unificado **AI-OS-Glass** (`themerc`, `gtk.css`, `Papirus-Dark`, fontes `Inter` e `JetBrains Mono`, cursor `Bibata-Modern-Classic`).
  - Wallpaper dinâmico em Cairo (`wallpaper.py`) que muda consoante a hora do dia e é reutilizado no ecrã de bloqueio (`lock.sh` + `i3lock`).
  - Suporte a ícones no desktop (`pcmanfm --desktop`), automontagem USB e Lixo (`gvfs` + `udisks2`).
  - Autenticação gráfica Polkit (`lxpolkit`) e notificações escuras (`dunst`).
- **Produtividade & Otimização:**
  - **Captura Rápida para IA:** `Print` / `Super+Shift+S` / `#screenshot` grava `~/Temp/captura.png` e anexa `@Temp/captura.png ` direto no Spotlight.
  - **Window Tiling nativo:** `Super+Esquerda`, `Super+Direita`, `Super+Cima`, `Super+Baixo` no Openbox.
  - **Apps incluídas:** `Chromium`, **LiteMD** (`litemd.py`, leitor `.md` predefinido), **GPicView** (visualizador de imagens predefinido), `xterm`.
  - **Sistema enxuto:** `zram-tools` (LZ4), `earlyoom` (anti-freeze), `99norecommends`, `01_nodoc` (exclui docs/manpages/locales fora de PT/EN), `journald` limitado a `50M`, `man-db.timer` desativado, `PipeWire` + `WirePlumber`, `Podman` rootless, `ufw`, `openssh-server`.

### Atalhos de Teclado
| Atalho | Ação |
| :--- | :--- |
| `Super+Espaço` / `Alt+Espaço` / `Ctrl+Espaço` | Focar Spotlight |
| `Esc` | Limpar pesquisa e fechar resultados |
| `Enter` / `Shift+Enter` | Enviar pedido / Quebra de linha |
| `Ctrl+↑` / `Ctrl+↓` | Histórico de pedidos |
| `Ctrl+H` | Lista de conversas guardadas |
| `Print` / `Super+Shift+S` | Capturar ecrã e anexar `@Temp/captura.png` no Spotlight |
| `Super+L` | Bloquear ecrã (`i3lock` com wallpaper) |
| `Super+←` / `Super+→` / `Super+↑` / `Super+↓` | Metade esquerda / Metade direita / Maximizar / Restaurar |
| `Alt+Tab` / `Alt+F4` | Alternar janelas / Fechar janela ativa |

### Instalação & Configuração
#### Instalação Rápida em Debian 13 (Netinst)
```bash
git clone https://github.com/casousavng/aios-debian.git
cd aios-debian
bash install-aios.sh
```
Reinicia no fim. Para autenticar o `agy` sem terminal, escreve `#login` no Spotlight, autoriza no browser e cola o código `4/0...` no Spotlight + `Enter`.

#### Estrutura do Repositório
```text
aios-debian/
├── AGENTS.md                 # Regras de governação do agente
├── preseed.cfg               # Instalação automática Debian 13 ARM64
├── build-iso.sh              # Gera ISO instalável automática com preseed
├── install-aios.sh           # Provisionamento idempotente sobre Debian
├── docs/screenshots/         # Capturas de ecrã para documentação
├── config/
│   ├── 01_nodoc              # Exclui docs/manpages/locales fora PT/EN
│   ├── 99norecommends        # APT sem recomendações/sugestões
│   ├── dunstrc               # Notificações AI-OS
│   ├── gtk.css               # Tema GTK3 escuro unificado
│   ├── picom.conf            # Compositor (sombras suaves, fading rápido)
│   └── openbox/
│       ├── autostart         # Cursor, picom, dunst, lxpolkit, xss-lock, pcmanfm, Spotlight
│       ├── rc.xml            # Margem 28px, tiling Super+Setas, atalhos
│       └── themerc           # Tema de janelas AI-OS-Glass
└── spotlight/
    ├── server.py             # Backend FastAPI + SSE streaming para agy
    ├── spotlight_ui.py       # TopBar + Spotlight Apple Glass (GTK3/WebKit2 lazy)
    ├── i18n.py               # Localização PT-PT / EN
    ├── wallpaper.py          # Gerador de wallpaper dinâmico (Cairo)
    ├── litemd.py             # Leitor Markdown nativo
    ├── screenshot.sh         # Captura rápida -> @Temp/captura.png
    ├── lock.sh               # Bloqueio i3lock com wallpaper
    └── index.html            # Fallback web
```
