# AI-OS Debian

> **Um sistema operativo desktop AI-first construído de raiz sobre Debian 13 (Trixie) Netinst** — concebido para eliminar ruído visual, menus redundantes e sobrecarga de recursos, colocando um **Spotlight nativo** e um **agente autónomo abstraído** no centro de toda a operação diária.

**Propósito do Projeto:** Explorar o conceito de sistema operativo com IA embutida que as grandes tecnológicas começaram a construir, mas com uma abordagem acessível — tirando partido de uma **subscrição mensal de baixo custo** para dar a **máquinas com poucos recursos** todo um ecossistema conectado (ficheiros locais, browser real, automações `cron`, containers e controlo de hardware).

[![Debian 13 Trixie](https://img.shields.io/badge/Debian-13%20Trixie-A81D33?logo=debian&logoColor=white)](https://www.debian.org/)
[![Openbox](https://img.shields.io/badge/WM-Openbox-2A2E37)](http://openbox.org/)
[![GTK3 + WebKit2](https://img.shields.io/badge/UI-GTK3%20%2B%20WebKit2-4A86CF)](https://gtk.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Podman](https://img.shields.io/badge/Containers-Podman%20Rootless-892CA0?logo=podman&logoColor=white)](https://podman.io/)

![AI-OS Live Demo](docs/screenshots/demo.gif)

[Português (PT-PT)](#-versão-em-português) | [English](#-english-version)

---

## 🇵🇹 Versão em Português

### 1. Filosofia & Decisões de Arquitetura (O Quê e Porquê)

Cada componente deste sistema foi escolhido para maximizar **agilidade, previsibilidade e baixo consumo** (~439 MB RAM em idle):

| Camada | Escolha | Porquê esta decisão |
|---|---|---|
| **Base do SO** | **Debian 13 Netinst** + `APT::Install-Recommends "false"` + `01_nodoc` | Controlo cirúrgico do que entra no disco: zero pacotes supérfluos, zero documentação/manpages pesadas, arranque direto em `tty1` para sessão gráfica. |
| **Memória & Estabilidade** | `zram-tools` (LZ4) + `earlyoom` + `journald` limitado (`50M`) | Mantém o sistema responsivo em VMs e portáteis com pouca RAM, evitando congelamentos por OOM ou crescimento silencioso de logs. |
| **Gestor de Janelas** | **Openbox** + `picom` (XRender) + `_NET_WM_STRUT_PARTIAL` | Ultraleve, configurável por XML (`rc.xml`), com tiling por teclado, resistência de bordas para proteger a barra superior e transparências suaves sem depender de aceleração 3D. |
| **Ambiente de Trabalho** | **Nemo** (`nemo-desktop`) + `feh` + `Papirus-Dark` | Ícones reais no Desktop com posicionamento livre (`gvfsd-metadata`) e drag-and-drop fluido para dentro do Spotlight; `feh` pinta a root window X11 com o wallpaper dinâmico Cairo. |
| **Interface Principal** | **GTK3 + WebKit2GTK** (`spotlight_ui.py`) | Em vez de Electron ou separadores de browser, uma janela nativa ancorada em baixo (`720px`), transparente, com streaming Markdown em WebKit2 e zero latência de arranque. |
| **Motor AI Abstraído** | **FastAPI** (`127.0.0.1:8765`) + Wrapper de Agente CLI | O utilizador interage apenas com o **AI-OS** (perfis *Rápido / Profundo / Só Planear*, login Google, streaming, guardrails). O motor CLI fica encapsulado por baixo, permitindo evoluir modelos sem mudar a experiência. |
| **Automações & Lembretes** | **`crontab` nativo** + `threading.Timer` (**Zero Polling**) | Em vez de loops Python a ler o disco de X em X segundos, os lembretes únicos usam timers em memória e as recorrências usam o `cron` do próprio Linux — consumo de CPU praticamente nulo em repouso. |
| **Leitor & Editor de Docs** | **LiteMD** (`litemd.py`) | Um único utilitário leve (`GTK3 + WebKit2`) registado como predefinido para Markdown e texto plano, alternando instantaneamente entre leitura estilizada e edição (`Ctrl+E` / `Ctrl+S`). |
| **Browser & Automação Web** | **Chromium** com CDP (`127.0.0.1:9222`) + `aios-web` | Permite ao assistente abrir páginas, ler DOM (incluindo `iframes` e Shadow DOM), preencher formulários e tirar screenshots diretamente no browser real do utilizador. |
| **Isolamento de Ferramentas** | **Podman Rootless** + `ufw` + `i3lock` | Serviços e servidores MCP correm isolados sem sujar o sistema anfitrião; firewall e bloqueio instantâneo vêm ativos de raiz. |

#### Métricas Medidas em Produção (VM Debian 13 Trixie, 2 GB RAM)

| Métrica | Valor Medido | Detalhe Técnico |
|---|---|---|
| **RAM em Idle (`free -m`)** | **439 MB** | De 1967 MB totais (`1527 MB` livres, `0 MB` swap `zram` usado) |
| **Disco / ROM (`df -h /`)** | **3.1 GB** | Sistema Debian 13 completo + desktop + stack AI-OS (`796` pacotes `dpkg`) |
| **Pegada do AI-OS (`/opt/ai-os`)** | **680 KB** | Todo o código Python/Bash/UI do sistema operativo |
| **Tempo de Arranque (`systemd-analyze`)** | **2.44s** | `532ms` kernel + `1.910s` userspace (`graphical.target` em `1.825s`) |
| **Consumo AI CLI em Idle** | **0 MB / 0% CPU** | Agente CLI só arranca sob pedido no prompt; automações usam `crontab` + `threading.Timer` (zero polling) |
| **Backend AI (`server.py`)** | **57.5 MB** RSS | FastAPI local (`127.0.0.1:8765`), gestor de crons, portas e estado |
| **UI Nativa (`spotlight_ui.py`)** | **82.8 MB** RSS | GTK3 + WebKit2GTK (TopBar + Popovers + Spotlight) sem overhead de Electron |
| **Sessão Desktop (`openbox` + `picom` + `dunst` + `nemo-desktop`)** | **78.4 MB** RSS | `17.2 MB` + `4.8 MB` + `10.3 MB` + `46.1 MB` combinados |

---

### 2. Galeria do Sistema

| Ambiente de Trabalho & Spotlight | Saúde do SO (`#health`) |
| :---: | :---: |
| ![Desktop](docs/screenshots/desktop.png) | ![Spotlight Health](docs/screenshots/spotlight-health.png) |

| Painel de Controlo (Hover) | Sino: Notificações & Automações |
| :---: | :---: |
| ![Control Popover](docs/screenshots/control-popover.png) | ![Bell Popover](docs/screenshots/bell-popover.png) |

| Definições AI-OS (`#settings`) | LiteMD (Leitor & Editor Markdown) |
| :---: | :---: |
| ![Settings](docs/screenshots/settings.png) | ![LiteMD](docs/screenshots/litemd.png) |

---

### 3. Guia Completo de Funcionalidades

#### Spotlight & Chat AI
- **Lançador Universal**: pesquisa simultânea de aplicações instaladas, ações rápidas do sistema, projetos em `~/Projetos` e ficheiros em profundidade (`~/Desktop`, `~/Documentos`, `~/Projetos`, `~/Downloads`).
- **Chat em Streaming**:
  - Respostas renderizadas a 100% de largura (sem bordas aninhadas), indicador vivo pulsante durante execução de ferramentas e botão `■` para interromper a qualquer momento.
  - Botão `Copiar` por resposta e por bloco de código; links externos abrem diretamente no **Chromium** e `.md` locais abrem no **LiteMD**.
  - Barra de controlo rápido: **`Novo chat`** (feedback temporário de 2,5s no placeholder), **`A-` / `A+`** (8–18px sincronizado ao vivo com as Definições) e **`Abrir no LiteMD`**.
  - Recolhe automaticamente ao clicar fora ou com `Escape`, preservando a conversa no botão `▲` para retomar depois (`Ctrl+H` lista histórico de conversas).
- **Anexos Multimodais**:
  - **`@ficheiros`**: autocomplete recursivo ao escrever `@`.
  - **Drag & Drop**: arrastar ficheiros do Desktop ou Nemo para a barra anexa-os como `@caminho` sem mover os originais.
  - **`Ctrl+V` de Imagem / `Print`**: cola screenshots diretamente no pedido para análise visual.
- **Guardrail de Segurança**: pedidos destrutivos (`rm -rf`, formatação de disco, remoção de pacotes, `reboot`/`poweroff`, alterações críticas de permissões/serviços) exigem confirmação explícita via modal seguro (foco padrão em *Cancelar*) e bloqueio na API.

#### Barra Superior (`AITopBar`) & Popovers por Hover
- **Workspaces (`1–4`) & Janelas Abertas**: alternância por clique, atalho ou scroll do rato; menu esquerdo **AI-OS** lista janelas por workspace com foco rápido e botão **`×`** para fechar diretamente.
- **Sino (Notificações & Automações)**:
  - Mostra na barra apenas a contagem de **notificações** registadas.
  - Popover com duas abas: **Notificações** (histórico + botão **`DND`** ligado ao `dunstctl` + *Limpar*) e **Automações** (lembretes e crons em linguagem legível como `Todos os dias às 09:00`, com **Pausar/Retomar** e **Remover**).
- **Painel de Controlo (Hardware & Sistema)**:
  - **Som & Ecrã**: sliders de volume (`wpctl`) e brilho (`brightnessctl`/`xrandr`), mais seleção de saída de áudio.
  - **Ligações**: redes Wi-Fi (`nmcli`) e Bluetooth (`bluetoothctl`).
  - **Sistema**: gestor de resoluções `xrandr`, bloqueio (`i3lock`), reiniciar, desligar e estado Podman/teclado, além de ajuste de **Data/Hora & Timezone**.

#### Automações (`cron`) & Lembretes
- **Por Comando (`#remind`)**: `#remind 10m Pausa` (aceita `s`, `m`, `h`) ou `#reminders` / `#crons` para listar e gerir.
- **Por Linguagem Natural no Chat**: basta pedir *"todos os dias às 09:00 verifica X"* ou *"daqui a 3 minutos abre o site Y e cria um resumo no Desktop"*. O sistema cria a entrada no `crontab` (`run_cron.sh`), mantém o chat principal limpo (auto-reset de sessão efémera) e entrega notificações persistentes até o utilizador as fechar.

#### Comandos Rápidos do Sistema (`#`) e Assistente (`/`)

| Comando | Função |
|---|---|
| `#health` | Estado ao vivo de `server.py`, `nemo-desktop`, `dunst`, `picom`, `cron`, disco `/` e RAM |
| `#ports` | Lista portas TCP em escuta e containers **Podman** com opção de paragem segura |
| `#proj` | Lista projetos em `~/Projetos` (com branch Git) e abre Terminal dentro da pasta |
| `#grep <termo>` | Pesquisa texto dentro de ficheiros em `~/Documentos`, `~/Desktop` e `~/Projetos` |
| `#clip` | Histórico de clipboard com **Snippets fixados (`[Pin]`)** |
| `#keys` | Folha rápida de todos os atalhos de teclado e rato |
| `#displays` | Seletor gráfico de resolução e monitores (`xrandr`) |
| `#settings` | Janela centrada de Definições (Perfis AI, Sessão/Consumo, Fonte, Idioma, Teclado, Sistema) |
| `#audit` / `#notif` | Registo de auditoria de ações da IA e histórico de notificações |
| `#apps` / `#chats` | Lista completa de apps instaladas / Conversas guardadas (`Ctrl+H`) |
| `#lang` / `#kb` / `#tz` | Alternar idioma (`pt`/`en`), teclado (`pt`/`us`/`es`/`fr`/`gb`) ou fuso horário |
| `#update` / `#lock` | Atualização com validação + rollback atómico (`update.sh`) / Bloqueio (`i3lock`) |
| `/model`, `/mode`, `/usage` | Seleção de modelo, modo (`auto`, `accept-edits`, `plan`) e consumo |

#### Atalhos de Teclado & Rato

| Atalho | Ação |
|---|---|
| `Super+Espaço` / `Alt+Espaço` | Focar Spotlight |
| `Super+T` | Abrir Terminal (`xterm`) |
| `Super+L` | Bloquear ecrã (`i3lock`) |
| `Super+1..4` | Mudar de Workspace |
| `Super+Shift+1..4` | Mover janela ativa para Workspace e acompanhar |
| `Super+← / → / ↑ / ↓` | Encaixar à esquerda/direita ou maximizar janela |
| `Alt+Arrastar` / `Alt+F4` | Mover ou fechar qualquer janela |
| `Print` / `Super+Shift+S` | Captura de ecrã anexada ao Spotlight |
| `Ctrl+H` / `Ctrl+V` | Histórico de chats / Colar imagem no pedido |
| `XF86Audio*` / `XF86MonBrightness*` | Volume e brilho com OSD persistente (`dunst`) |

---

### 4. Estrutura, Instalação & Build ISO

```text
├── .github/workflows/
│   └── build-iso.yml        # GitHub Actions: build ISO amd64 + Release
├── build-live-iso.sh        # Gera ISO Live + Instalador híbrida (amd64, zero credenciais)
├── build-iso.sh             # Gera ISO Netinst autónoma (preseed)
├── preseed.cfg              # Instalação autónoma Debian Netinst
├── install-aios.sh          # Provisionamento completo do sistema
├── AGENTS.md                # Constituição, regras e ferramentas do agente
├── config/
│   ├── openbox/             # autostart, rc.xml, themerc
│   ├── dunstrc              # Notificações persistentes (timeout=0 critical)
│   ├── picom.conf           # Compositor XRender leve
│   ├── litemd.desktop       # Associação MIME para Markdown & Texto
│   ├── aios-cdp             # Flags Chromium CDP (127.0.0.1:9222)
│   └── 01_nodoc, 99norecommends
├── spotlight/
│   ├── spotlight_ui.py      # TopBar, Popovers, Settings, Spotlight GTK3+WebKit2
│   ├── server.py            # Backend FastAPI (127.0.0.1:8765), streaming, crons, ports
│   ├── i18n.py              # Localização PT-PT/EN, guardrails & human_cron()
│   ├── litemd.py            # Leitor & Editor Markdown/Texto GTK3+WebKit2
│   ├── web_agent.py         # CLI aios-web via Chromium CDP
│   ├── wallpaper.py         # Wallpaper dinâmico Cairo + feh + gsettings
│   ├── gestures.py          # Gestos touchpad (libinput)
│   ├── run_cron.sh          # Executor de automações crontab
│   └── lock.sh, screenshot.sh, update.sh
└── tests/
    └── test_smoke.py        # Suite unittest (compilação, shell, XML, i18n, guardrails, cron)
```

```bash
# Provisionar numa máquina Debian 12/13 limpa:
git clone https://github.com/casousavng/aios-debian.git
cd aios-debian && bash install-aios.sh

# Validar suite de testes:
python3 -m unittest discover -s tests -v
```

---

## 🇬🇧 English Version

**Project Purpose:** Explore the AI-embedded operating system paradigm pioneered by tech giants, but built for accessibility — leveraging an **affordable monthly AI subscription** to give **low-resource machines** a complete, connected ecosystem (local files, real browser automation, `cron` schedules, containers, and hardware controls).

### 1. Philosophy & Architecture Decisions (What & Why)

Every component is chosen to maximize **responsiveness, predictability, and low resource usage** (~439 MB RAM at idle):

| Layer | Choice | Why this decision |
|---|---|---|
| **OS Base** | **Debian 13 Netinst** + `APT::Install-Recommends "false"` + `01_nodoc` | Surgical control over disk footprint: zero bloat packages, zero heavy docs/manpages, direct boot on `tty1` into graphical session. |
| **Memory & Stability** | `zram-tools` (LZ4) + `earlyoom` + capped `journald` (`50M`) | Keeps VMs and low-RAM laptops snappy, preventing OOM freezes and silent log growth. |
| **Window Manager** | **Openbox** + `picom` (XRender) + `_NET_WM_STRUT_PARTIAL` | Ultra-lightweight XML configuration (`rc.xml`), keyboard tiling, edge resistance protecting the top bar, and smooth transparency without 3D acceleration. |
| **Desktop Environment** | **Nemo** (`nemo-desktop`) + `feh` + `Papirus-Dark` | Real Desktop icons with free positioning (`gvfsd-metadata`) and fluid drag-and-drop into Spotlight; `feh` paints the X11 root window with the dynamic Cairo wallpaper. |
| **Primary Interface** | **GTK3 + WebKit2GTK** (`spotlight_ui.py`) | Instead of Electron or browser tabs, a native bottom-docked transparent bar (`720px`) with WebKit2 Markdown streaming and zero startup latency. |
| **Abstracted AI Engine** | **FastAPI** (`127.0.0.1:8765`) + CLI Agent Wrapper | Users interact solely with **AI-OS** (*Fast / Deep / Plan Only* profiles, Google login, streaming, guardrails). The underlying CLI engine stays encapsulated so models can evolve without changing UX. |
| **Automations & Reminders** | **Native `crontab`** + `threading.Timer` (**Zero Polling**) | Instead of Python loops polling disk every few seconds, one-shot reminders use in-memory timers and recurring jobs use Linux `cron` — near-zero idle CPU usage. |
| **Docs Reader & Editor** | **LiteMD** (`litemd.py`) | Single lightweight utility (`GTK3 + WebKit2`) registered as default for Markdown and plain text, toggling instantly between styled reading and editing (`Ctrl+E` / `Ctrl+S`). |
| **Browser & Web Automation** | **Chromium** with CDP (`127.0.0.1:9222`) + `aios-web` | Lets the assistant open pages, inspect DOM (including `iframes` and Shadow DOM), fill forms, and capture screenshots in the user's real browser. |
| **Tool Isolation** | **Podman Rootless** + `ufw` + `i3lock` | Services and MCP servers run isolated without polluting the host; firewall and instant screen lock are enabled out of the box. |

#### Measured System Footprint (Debian 13 Trixie VM, 2 GB RAM)

| Metric | Measured Value | Technical Detail |
|---|---|---|
| **Idle RAM (`free -m`)** | **439 MB** | Out of 1967 MB total (`1527 MB` available, `0 MB` `zram` swap used) |
| **Disk / ROM (`df -h /`)** | **3.1 GB** | Full Debian 13 OS + desktop + AI-OS stack (`796` `dpkg` packages) |
| **AI-OS Footprint (`/opt/ai-os`)** | **680 KB** | Entire Python/Bash/UI codebase of the desktop environment |
| **Boot Time (`systemd-analyze`)** | **2.44s** | `532ms` kernel + `1.910s` userspace (`graphical.target` in `1.825s`) |
| **AI CLI Idle Overhead** | **0 MB / 0% CPU** | CLI agent spawns on-demand per prompt only; schedules use `crontab` + `threading.Timer` (zero polling) |
| **AI Backend (`server.py`)** | **57.5 MB** RSS | Local FastAPI (`127.0.0.1:8765`), cron manager, ports, and system state |
| **Native UI (`spotlight_ui.py`)** | **82.8 MB** RSS | GTK3 + WebKit2GTK (TopBar + Popovers + Spotlight) with zero Electron overhead |
| **Desktop Stack (`openbox` + `picom` + `dunst` + `nemo-desktop`)** | **78.4 MB** RSS | `17.2 MB` + `4.8 MB` + `10.3 MB` + `46.1 MB` combined |

---

### 2. System Gallery

| Desktop & Spotlight | OS Health (`#health`) |
| :---: | :---: |
| ![Desktop](docs/screenshots/desktop.png) | ![Spotlight Health](docs/screenshots/spotlight-health.png) |

| Control Panel (Hover) | Bell: Notifications & Automations |
| :---: | :---: |
| ![Control Popover](docs/screenshots/control-popover.png) | ![Bell Popover](docs/screenshots/bell-popover.png) |

| AI-OS Settings (`#settings`) | LiteMD (Markdown Reader & Editor) |
| :---: | :---: |
| ![Settings](docs/screenshots/settings.png) | ![LiteMD](docs/screenshots/litemd.png) |

---

### 3. Complete Feature Guide

#### Spotlight & AI Chat
- **Universal Launcher**: Simultaneous search across installed apps, quick system actions, projects in `~/Projetos`, and deep file search (`~/Desktop`, `~/Documentos`, `~/Projetos`, `~/Downloads`).
- **Streaming Chat**:
  - Full-width rendered replies (no nested borders), pulsing live indicator during tool execution, and `■` stop button at any time.
  - `Copy` button per reply and per code block; external links open directly in **Chromium** and local `.md` files open in **LiteMD**.
  - Quick toolbar: **`New chat`** (2.5s temporary placeholder feedback), **`A-` / `A+`** (8–18px live-synced with Settings), and **`Open in LiteMD`**.
  - Auto-collapses on outside click or `Escape`, preserving the conversation under the `▲` toggle (`Ctrl+H` opens saved chat history).
- **Multimodal Attachments**:
  - **`@files`**: recursive autocomplete when typing `@`.
  - **Drag & Drop**: drag files from Desktop or Nemo into the bar to attach as `@path` without moving originals.
  - **`Ctrl+V` Image / `Print`**: paste screenshots directly into prompts for visual analysis.
- **Safety Guardrail**: destructive prompts (`rm -rf`, disk formatting, package removal, `reboot`/`poweroff`, critical permission/service changes) require explicit confirmation via a safe modal (default focus on *Cancel*) plus API-level blocking.

#### Top Bar (`AITopBar`) & Hover Popovers
- **Workspaces (`1–4`) & Open Windows**: switch by click, shortcut, or mouse scroll; left **AI-OS** menu lists open windows per workspace with quick focus and **`×`** close button.
- **Bell (Notifications & Automations)**:
  - Top bar badge shows only **notification** count.
  - Two-tab popover: **Notifications** (history + **`DND`** toggle wired to `dunstctl` + *Clear*) and **Automations** (reminders and crons in human-readable labels like `Every day at 09:00`, with **Pause/Resume** and **Remove**).
- **Control Panel (Hardware & System)**:
  - **Audio & Display**: volume (`wpctl`) and brightness (`brightnessctl`/`xrandr`) sliders plus audio sink selector.
  - **Connections**: Wi-Fi (`nmcli`) and Bluetooth (`bluetoothctl`).
  - **System**: `xrandr` display resolution picker, screen lock (`i3lock`), reboot, shutdown, Podman/keyboard status, plus **Date/Time & Timezone** configuration.

#### Automations (`cron`) & Reminders
- **Command (`#remind`)**: `#remind 10m Break` (supports `s`, `m`, `h`) or `#reminders` / `#crons` to list and manage.
- **Natural Language in Chat**: simply ask *"every day at 09:00 check X"* or *"in 3 minutes open site Y and save a summary to Desktop"*. The system creates the `crontab` entry (`run_cron.sh`), keeps the main chat clean (ephemeral session auto-reset), and delivers sticky notifications until dismissed.

#### Quick System Commands (`#`) & Assistant (`/`)

| Command | Function |
|---|---|
| `#health` | Live status of `server.py`, `nemo-desktop`, `dunst`, `picom`, `cron`, `/` disk & RAM |
| `#ports` | Lists listening TCP ports and **Podman** containers with safe stop action |
| `#proj` | Lists projects in `~/Projetos` (with Git branch) and opens Terminal inside folder |
| `#grep <term>` | Searches text inside files across `~/Documentos`, `~/Desktop`, and `~/Projetos` |
| `#clip` | Clipboard history with **pinned Snippets (`[Pin]`)** |
| `#keys` | Quick cheatsheet of all keyboard and mouse shortcuts |
| `#displays` | Graphical monitor & resolution switcher (`xrandr`) |
| `#settings` | Centered Settings window (AI Profiles, Session/Usage, Font, Language, Keyboard, System) |
| `#audit` / `#notif` | AI action audit log and notification history |
| `#apps` / `#chats` | Full installed apps list / Saved conversations (`Ctrl+H`) |
| `#lang` / `#kb` / `#tz` | Switch language (`pt`/`en`), keyboard (`pt`/`us`/`es`/`fr`/`gb`), or timezone |
| `#update` / `#lock` | Validated update with atomic rollback (`update.sh`) / Screen lock (`i3lock`) |
| `/model`, `/mode`, `/usage` | Model selector, execution mode (`auto`, `accept-edits`, `plan`), and usage |

#### Keyboard & Mouse Shortcuts

| Shortcut | Action |
|---|---|
| `Super+Space` / `Alt+Space` | Focus Spotlight |
| `Super+T` | Open Terminal (`xterm`) |
| `Super+L` | Lock screen (`i3lock`) |
| `Super+1..4` | Switch Workspace |
| `Super+Shift+1..4` | Move active window to Workspace and follow |
| `Super+← / → / ↑ / ↓` | Snap left/right or maximize window |
| `Alt+Drag` / `Alt+F4` | Move or close any window |
| `Print` / `Super+Shift+S` | Capture screenshot attached to Spotlight |
| `Ctrl+H` / `Ctrl+V` | Chat history / Paste image into prompt |
| `XF86Audio*` / `XF86MonBrightness*` | Volume and brightness with persistent OSD (`dunst`) |

---

### 4. Structure, Installation & Live ISO Build

```text
├── .github/workflows/
│   └── build-iso.yml        # GitHub Actions: build amd64 ISO + Release
├── build-live-iso.sh        # Builds hybrid Live + Installer ISO (amd64, zero credentials)
├── build-iso.sh             # Builds unattended Debian Netinst ISO (preseed)
├── preseed.cfg              # Unattended Debian Netinst configuration
├── install-aios.sh          # Full system provisioning script
├── AGENTS.md                # Agent constitution, rules, and tools
├── config/
│   ├── openbox/             # autostart, rc.xml, themerc
│   ├── dunstrc              # Persistent notifications (timeout=0 critical)
│   ├── picom.conf           # Lightweight XRender compositor
│   ├── litemd.desktop       # MIME associations for Markdown & Plain Text
│   ├── aios-cdp             # Chromium CDP flags (127.0.0.1:9222)
│   └── 01_nodoc, 99norecommends
├── spotlight/
│   ├── spotlight_ui.py      # TopBar, Popovers, Settings, Spotlight GTK3+WebKit2
│   ├── server.py            # FastAPI backend (127.0.0.1:8765), streaming, crons, ports
│   ├── i18n.py              # PT-PT/EN localization, guardrails & human_cron()
│   ├── litemd.py            # Markdown/Text Reader & Editor GTK3+WebKit2
│   ├── web_agent.py         # aios-web CLI via Chromium CDP
│   ├── wallpaper.py         # Dynamic Cairo wallpaper + feh + gsettings
│   ├── gestures.py          # Touchpad gestures (libinput)
│   ├── run_cron.sh          # Crontab automation runner
│   └── lock.sh, screenshot.sh, update.sh
└── tests/
    └── test_smoke.py        # unittest suite (compile, shell, XML, i18n, guardrails, cron)
```

```bash
# Provision on a clean Debian 12/13 machine:
git clone https://github.com/casousavng/aios-debian.git
cd aios-debian && bash install-aios.sh

# Run test suite:
python3 -m unittest discover -s tests -v

# Build a shareable Live + Installer amd64 ISO (inside Debian Trixie):
sudo bash build-live-iso.sh
```
