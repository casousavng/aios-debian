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
