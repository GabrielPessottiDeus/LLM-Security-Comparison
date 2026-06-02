#!/usr/bin/env bash
# ============================================================================
# setup_fedora.sh  (v2 — idempotente)
#
# Instala tudo o que é necessário no Fedora para:
#   - Rodar as aplicações geradas pelas LLMs (Python, Java, Node)
#   - Rodar as ferramentas SAST localmente (Bandit, Semgrep, SpotBugs, ESLint)
#   - Rodar Docker (para MySQL e OWASP ZAP)
#
# Mudanças nesta versão:
#   - Tolera pacotes já instalados (não aborta o script)
#   - Detecta o JDK disponível em vez de exigir java-17-openjdk
#   - Pode ser rodado várias vezes sem problema
#
# Uso:  bash scripts/setup_fedora.sh
# ============================================================================
set -uo pipefail   # removido o -e proposital: queremos continuar mesmo se um passo falhar

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[setup]${NC} $*"; }
warn() { echo -e "${YELLOW}[setup]${NC} $*"; }
err()  { echo -e "${RED}[setup]${NC} $*"; }

if [[ $EUID -eq 0 ]]; then
    err "Não rode como root. O script chama sudo quando necessário."
    exit 1
fi

# Instala um pacote só se ele não estiver instalado. Não falha se faltar.
dnf_install_if_missing() {
    local pkg="$1"
    if rpm -q "$pkg" &>/dev/null; then
        log "  já instalado: $pkg"
    else
        if sudo dnf -y install "$pkg" &>/dev/null; then
            log "  instalado:    $pkg"
        else
            warn "  indisponível ou erro: $pkg (continuando)"
        fi
    fi
}

log "==> Atualizando metadados do dnf..."
sudo dnf -y makecache >/dev/null 2>&1 || warn "makecache falhou (continuando)"

# ----------------------------------------------------------------------------
# 1) Ferramentas base
# ----------------------------------------------------------------------------
log "==> Instalando ferramentas base..."
for pkg in git curl wget jq unzip tar which gcc gcc-c++ make \
           python3 python3-pip python3-virtualenv \
           maven nodejs npm ca-certificates; do
    dnf_install_if_missing "$pkg"
done

# ----------------------------------------------------------------------------
# 2) JDK — tenta 17 primeiro; se não houver, aceita qualquer JDK instalado
# ----------------------------------------------------------------------------
log "==> Verificando JDK..."
if command -v javac &>/dev/null; then
    JDK_VERSION="$(javac -version 2>&1 | awk '{print $2}')"
    log "  JDK já presente: $JDK_VERSION ($(which javac))"
else
    log "  Nenhum JDK detectado. Tentando instalar..."
    # Tenta nesta ordem: 17 (Spring Boot 3 oficial), 21 (LTS), latest
    for jdk_pkg in java-17-openjdk-devel java-21-openjdk-devel java-latest-openjdk-devel; do
        if sudo dnf -y install "$jdk_pkg" &>/dev/null; then
            log "  instalado: $jdk_pkg"
            break
        fi
    done
    if ! command -v javac &>/dev/null; then
        err "Não foi possível instalar nenhum JDK automaticamente."
        err "Instale manualmente: sudo dnf install java-latest-openjdk-devel"
    fi
fi

# ----------------------------------------------------------------------------
# 3) Docker
# ----------------------------------------------------------------------------
if ! command -v docker &>/dev/null; then
    log "==> Instalando Docker (repositório oficial)..."
    sudo dnf -y install dnf-plugins-core || true
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo || true
    sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin || true
    sudo systemctl enable --now docker || warn "falha ao iniciar serviço docker"
    sudo usermod -aG docker "$USER" || true
    warn "Você foi adicionado ao grupo 'docker'. Faça LOGOUT/LOGIN (ou rode 'newgrp docker') antes de continuar."
else
    log "==> Docker já instalado: $(docker --version)"
    # Garante que o serviço está rodando
    if ! systemctl is-active --quiet docker; then
        sudo systemctl start docker || warn "falha ao iniciar serviço docker"
    fi
    # Garante que o usuário está no grupo
    if ! groups | grep -q docker; then
        sudo usermod -aG docker "$USER" || true
        warn "Você foi adicionado ao grupo 'docker'. Faça LOGOUT/LOGIN ou rode 'newgrp docker'."
    fi
fi

# ----------------------------------------------------------------------------
# 4) Python tools (Bandit + Semgrep)
# ----------------------------------------------------------------------------
log "==> Verificando Bandit e Semgrep..."
if ! command -v pipx &>/dev/null; then
    log "  Instalando pipx..."
    python3 -m pip install --user --break-system-packages pipx >/dev/null 2>&1 || \
        python3 -m pip install --user pipx >/dev/null 2>&1
    python3 -m pipx ensurepath >/dev/null 2>&1 || true
fi
export PATH="$HOME/.local/bin:$PATH"

if ! command -v bandit &>/dev/null; then
    log "  Instalando bandit via pipx..."
    pipx install bandit >/dev/null 2>&1 || warn "  falha ao instalar bandit"
else
    log "  bandit já instalado: $(bandit --version 2>&1 | head -1)"
fi

if ! command -v semgrep &>/dev/null; then
    log "  Instalando semgrep via pipx..."
    pipx install semgrep >/dev/null 2>&1 || warn "  falha ao instalar semgrep"
else
    log "  semgrep já instalado: $(semgrep --version)"
fi

# ----------------------------------------------------------------------------
# 5) SpotBugs + find-sec-bugs
# ----------------------------------------------------------------------------
SPOTBUGS_VERSION="4.8.6"
FINDSECBUGS_VERSION="1.14.0"
SPOTBUGS_HOME="$HOME/tools/spotbugs-${SPOTBUGS_VERSION}"

# Salva diretório atual para voltar depois (cd /tmp quebrava caminhos relativos)
SETUP_CWD="$(pwd)"

if [[ ! -x "$SPOTBUGS_HOME/bin/spotbugs" ]]; then
    log "==> Baixando SpotBugs ${SPOTBUGS_VERSION}..."
    mkdir -p "$HOME/tools"
    (cd /tmp && \
        curl -fL -o spotbugs.tgz \
            "https://github.com/spotbugs/spotbugs/releases/download/${SPOTBUGS_VERSION}/spotbugs-${SPOTBUGS_VERSION}.tgz" && \
        tar -xzf spotbugs.tgz -C "$HOME/tools/" && \
        rm -f spotbugs.tgz)
    if [[ -x "$SPOTBUGS_HOME/bin/spotbugs" ]]; then
        chmod +x "$SPOTBUGS_HOME/bin/spotbugs"
        log "  SpotBugs instalado em $SPOTBUGS_HOME"
    else
        err "  falha ao baixar/instalar SpotBugs"
    fi
else
    log "==> SpotBugs já instalado em $SPOTBUGS_HOME"
fi

FINDSECBUGS_JAR="$SPOTBUGS_HOME/plugin/findsecbugs-plugin.jar"
# Remove jar antigo se vazio (de tentativas anteriores que falharam)
[[ -f "$FINDSECBUGS_JAR" && ! -s "$FINDSECBUGS_JAR" ]] && rm -f "$FINDSECBUGS_JAR"

if [[ ! -f "$FINDSECBUGS_JAR" && -d "$SPOTBUGS_HOME/plugin" ]]; then
    log "==> Baixando plugin find-sec-bugs ${FINDSECBUGS_VERSION} do Maven Central..."
    # URL do Maven Central (releases do GitHub não incluem o JAR pronto a partir da 1.12)
    if curl -fL -o "$FINDSECBUGS_JAR" \
        "https://repo1.maven.org/maven2/com/h3xstream/findsecbugs/findsecbugs-plugin/${FINDSECBUGS_VERSION}/findsecbugs-plugin-${FINDSECBUGS_VERSION}.jar"; then
        log "  find-sec-bugs instalado"
    else
        err "  falha ao baixar find-sec-bugs"
    fi
elif [[ -f "$FINDSECBUGS_JAR" ]]; then
    log "==> find-sec-bugs já instalado"
fi

# Volta para o diretório original do projeto antes dos próximos passos
cd "$SETUP_CWD"

# PATH no ~/.bashrc
if [[ -d "$SPOTBUGS_HOME/bin" ]] && ! grep -q "spotbugs-${SPOTBUGS_VERSION}/bin" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo ""
        echo "# SpotBugs (instalado pelo setup_fedora.sh do trabalho de LLM SAST)"
        echo "export SPOTBUGS_HOME=\"$SPOTBUGS_HOME\""
        echo "export PATH=\"\$SPOTBUGS_HOME/bin:\$PATH\""
    } >> "$HOME/.bashrc"
    warn "SpotBugs adicionado ao ~/.bashrc. Rode 'source ~/.bashrc' ou abra um novo terminal."
fi
export SPOTBUGS_HOME="$SPOTBUGS_HOME"
export PATH="$SPOTBUGS_HOME/bin:$PATH"

# ----------------------------------------------------------------------------
# 6) ESLint + plugins
# ----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ESLINT_BIN="$PROJECT_ROOT/sast-configs/node_modules/.bin/eslint"
if [[ ! -x "$ESLINT_BIN" ]]; then
    log "==> Instalando ESLint + plugins de segurança em sast-configs/..."
    (cd "$PROJECT_ROOT/sast-configs" && npm install --no-audit --no-fund 2>&1 | tail -5)
else
    log "==> ESLint já instalado em sast-configs/node_modules"
fi

# ----------------------------------------------------------------------------
# 7) Resumo
# ----------------------------------------------------------------------------
echo
log "==> Versões instaladas:"
echo
printf "  Python:    "; python3 --version 2>&1 | head -1
printf "  Java:      "; java -version 2>&1 | head -1 || echo "(não detectado)"
printf "  javac:     "; javac -version 2>&1 | head -1 || echo "(não detectado)"
printf "  Maven:     "; mvn -v 2>&1 | head -1 || echo "(não detectado)"
printf "  Node:      "; node --version 2>&1 || echo "(não detectado)"
printf "  npm:       "; npm --version 2>&1 || echo "(não detectado)"
printf "  Docker:    "; docker --version 2>&1 || echo "(não detectado ou precisa logout/login)"
printf "  Bandit:    "; bandit --version 2>&1 | head -1 || echo "(não detectado)"
printf "  Semgrep:   "; semgrep --version 2>&1 | head -1 || echo "(não detectado)"
printf "  SpotBugs:  "; [[ -x "$SPOTBUGS_HOME/bin/spotbugs" ]] && echo "instalado em $SPOTBUGS_HOME" || echo "(não detectado)"
printf "  ESLint:    "; [[ -x "$ESLINT_BIN" ]] && "$ESLINT_BIN" --version || echo "(não detectado)"
echo
log "Setup concluído!"
echo "  1) Se acabou de instalar Docker: faça logout/login (ou: newgrp docker)"
echo "  2) Suba o MySQL:      bash scripts/start_mysql.sh"
echo "  3) Cole códigos das LLMs em codigos/casoXX_xxx/<ia>/<linguagem>/"
echo "  4) Rode os SAST:      bash scripts/run_all_sast.sh"
echo "  5) Para DAST:         suba a app desejada e rode bash scripts/run_zap.sh <porta>"