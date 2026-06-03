# ============================================================================
# run_app_python.sh — sobe um app Python/Flask de uma pasta de código.
#
# Uso:  bash scripts/run_app_python.sh codigos/caso01_auth/claude/python
#
# O script:
#   1) Detecta o caso a partir do caminho (caso01_auth, caso02_products, etc.)
#   2) Exporta DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME no ambiente
#      antes de subir a app. Isso permite que o código gerado pelas LLMs
#      obtenha credenciais via os.environ em vez de hardcoded, mantendo
#      o experimento metodologicamente mais limpo.
#   3) Cria um venv local, instala requirements.txt
#   4) Detecta o arquivo principal e roda
# ============================================================================
set -euo pipefail

TARGET="${1:-}"
[[ -z "$TARGET" ]] && { echo "Uso: bash scripts/run_app_python.sh <pasta>"; exit 1; }
[[ ! -d "$TARGET" ]] && { echo "Pasta inexistente: $TARGET"; exit 1; }

TARGET_ABS="$(cd "$TARGET" && pwd)"
CASE_DIR_NAME=""
for part in $(echo "$TARGET_ABS" | tr '/' '\n'); do
    if [[ "$part" =~ ^caso0[0-9]_ ]]; then
        CASE_DIR_NAME="$part"
        break
    fi
done

if [[ -z "$CASE_DIR_NAME" ]]; then
    echo "[py] AVISO: não detectei o caso (esperava 'caso0X_xxx' no caminho)."
    echo "[py] As variáveis DB_* não serão exportadas. A app pode não conectar."
else
    export DB_HOST="localhost"
    export DB_PORT="3306"
    export DB_USER="appuser"
    export DB_PASSWORD="apppass"
    export DB_NAME="$CASE_DIR_NAME"
    echo "[py] Variáveis de ambiente do banco exportadas (DB_NAME=$DB_NAME)"
fi

cd "$TARGET"

if [[ ! -d .venv ]]; then
    echo "[py] Criando venv..."
    python3 -m venv .venv
fi

source .venv/bin/activate

if [[ -f requirements.txt ]]; then
    echo "[py] Instalando dependências..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
fi

ENTRY=""
for cand in app.py main.py server.py run.py wsgi.py; do
    [[ -f "$cand" ]] && { ENTRY="$cand"; break; }
done
if [[ -z "$ENTRY" ]]; then
    ENTRY="$(ls *.py 2>/dev/null | head -1 || true)"
fi
[[ -z "$ENTRY" ]] && { echo "[py] Nenhum .py encontrado para executar."; exit 1; }

echo "[py] Executando $ENTRY ..."
echo "[py] (Ctrl+C para parar)"
exec python "$ENTRY"