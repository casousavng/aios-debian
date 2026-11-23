# Constituição do Sistema Operativo (AI-OS) — `AGENTS.md`

Este repositório define o protótipo **AI-OS Debian**: um sistema operativo minimalista baseado em Debian Netinst onde o ambiente gráfico é 100% limpo (Openbox sem barras ou painéis, apenas pastas e ficheiros geridos pelo PCManFM) e toda a interação, configuração de hardware e criação de ficheiros é orquestrada por uma janela **Spotlight** sempre acessível ligada a um agente CLI (`agy` ou `opencode`).

## 1. Arquitetura Base
- **SO Base:** Debian 12/13 Netinst (sem Desktop Environment pré-instalado), com `APT::Install-Recommends "false";` e `APT::Install-Suggests "false";`.
- **Arranque:** Autologin no `tty1` via `systemd` (`getty@tty1.service`) -> `startx` automático no `~/.profile`.
- **Camada Gráfica:** `xorg` + `openbox` (zero barras/painéis) + `pcmanfm --desktop` (ícones/pastas no ambiente de trabalho).
- **Interface Principal (Spotlight):** Aplicação web local (`FastAPI` + HTML/JS) corrida em janela flutuante/app (`chromium --app=http://localhost:8765`), com histórico de conversas em Markdown (`~/.ai-os/chats/`), indicadores de bateria/Wi-Fi/hora e atalho global `Super+Espaço`.

## 2. Regras de Gestão de Ficheiros e Pastas
- **Estrutura padrão da Home:**
  - `~/Desktop` — Trabalho ativo do dia e ficheiros que o utilizador quer ver no ecrã.
  - `~/Documentos` — Ficheiros Markdown finais, relatórios, guiões e documentação.
  - `~/Projetos` — Código, repositórios, ambientes Docker e testes estruturados.
  - `~/Temp` — Experiências rápidas e rascunhos descartáveis.
- **Proibição de Poluição:** NUNCA cries ficheiros soltos na raiz da home (`~/`) nem na raiz do sistema (`/`).
- **Regra de Criação Imediata:** Quando o utilizador pedir explicitamente para criar ou editar um ficheiro (em `~/Desktop`, `~/Documentos`, `~/Projetos` ou `~/Temp`), executa imediatamente sem pedir confirmação prévia, usando nomes em `kebab-case` (ex: `~/Desktop/lista-compras-continente.md`).
- **Apagar com Segurança:** Nunca uses `rm -rf` fora de `~/Temp`. Move sempre ficheiros apagados para a reciclagem (`gio trash <ficheiro>`).

## 3. Regras de Sistema, Hardware e Pacotes
- **Nível Verde (Execução Imediata, Zero Perguntas):**
  - Diagnóstico e leitura: ver estado da bateria, rede Wi-Fi (`nmcli`), impressoras (`lpstat`), espaço em disco (`df -h`), RAM (`free -h`), processos e logs.
  - Criar ou editar ficheiros dentro de `~/Desktop`, `~/Documentos`, `~/Projetos` e `~/Temp`.
- **Nível Amarelo (Executa ou Resume em 1 Linha):**
  - Instalar pacotes via `apt` ou configurar hardware/rede (`lpadmin`, `nmcli`, `bluetoothctl`, `brightnessctl`).
  - Sempre que instalares ferramentas pontuais ou servidores de teste, dá preferência a contentores Docker isolados em vez de sujar o sistema anfitrião.
- **Nível Vermelho (Bloqueio e Alerta Explícito):**
  - Alterações críticas em `/etc/fstab`, particionamento de discos ou regras de firewall/rede permanentes sem confirmação explícita.

## 4. Estilo de Resposta no Spotlight
- Sê conciso, direto e orientado à ação.
- Não despejes logs extensos no chat do Spotlight; guarda o output técnico completo em `~/.ai-os/logs/last_action.log` e mostra apenas o resultado resumido ou a pergunta de confirmação.

## 5. Instruções para Provisionamento Remoto (`ssh aios-dev`)
Quando ligado à VM de desenvolvimento Debian (`aios-dev`), o agente deve:
1. Verificar a arquitetura (`uname -m`) e confirmar que `/etc/apt/apt.conf.d/99norecommends` está ativo.
2. Copiar os ficheiros deste repositório (`install-aios.sh`, `config/`, `spotlight/`, `AGENTS.md`) para a VM e executar `bash install-aios.sh`.
3. Validar que o serviço `aios-spotlight.service` (systemd user) está ativo e que o Openbox arranca limpo no `tty1`.

## 6. Browser Agent Web (`aios-web` via Chromium CDP)
Quando o utilizador pedir para abrir um site, ler conteúdo web, preencher formulários ou clicar em botões no navegador, **executa obrigatoriamente passo a passo via `aios-web`** (não digas que não tens acesso ao browser):
1. `aios-web open "<URL>"` — Abre o Chromium (com CDP `127.0.0.1:9222` no `DISPLAY=:0`) e navega para o URL.
2. `aios-web wait "<selector>" [seg]` — Aguarda elementos dinâmicos (SPAs/AJAX) aparecerem.
3. `aios-web dom` — Lê título, texto visível e elementos interativos (incl. `iframes` e Shadow DOM) com `[data-aios-id="N"]`.
4. `aios-web fill '<selector>' '<valor>'` / `aios-web click '<selector>'` / `aios-web press Enter` / `aios-web scroll down`.
5. `aios-web tabs` e `aios-web tab <idx>` — Lista e alterna entre abas abertas (`target="_blank"`).
6. `aios-web screenshot [path]` — Captura o ecrã do browser para análise.
7. `aios-web dom` — Volta a ler o DOM após ações para confirmar o resultado real.

## 7. Ferramentas Nativas, APIs e MCP
- **Chromium CDP global:** `/etc/chromium.d/aios-cdp` ativa `--remote-debugging-port=9222 --remote-debugging-address=127.0.0.1` em qualquer janela Chromium (para `aios-web` ou servidores MCP de browser).
- **API local do SO:** `http://127.0.0.1:8765` (`aios-spotlight.service`) expõe estado, Wi-Fi, áudio (`wpctl`), Bluetooth e modelos `agy`.
- **Contentores & MCPs isolados:** `podman` rootless está pronto para correr servidores MCP ou ferramentas sem sujar o sistema.
- **GUI fora do browser:** usa `xdotool` (`DISPLAY=:0`) + `scrot` quando precisares de interagir com janelas nativas X11.
- **PDFs e JSON locais:** usa `pdftotext <ficheiro.pdf> -` e `jq` para leitura rápida.
- **Lembretes e tarefas agendadas:** usa `cron` (`crontab`) com `DISPLAY=:0 notify-send "AI-OS" "<mensagem>"`.
