# ============================================================================
# run_semgrep.sh — analisa código com Semgrep usando rulesets de segurança
#
# Uso:
#   bash scripts/run_semgrep.sh <caminho_codigo> [nome_relatorio]
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
    echo "Uso: bash scripts/run_semgrep.sh <caminho_codigo>"
    exit 1
fi
[[ ! -d "$TARGET" ]] && { echo "Diretório não existe: $TARGET"; exit 1; }

REPORT_NAME="${2:-$(echo "$TARGET" | sed -E 's|^codigos/||;s|/|_|g')}"
OUT_DIR="$ROOT/reports/sast/semgrep"
mkdir -p "$OUT_DIR"

RULESETS=(
    "p/security-audit"
    "p/owasp-top-ten"
    "p/python"
    "p/flask"
    "p/java"
    "p/javascript"
    "p/typescript"
    "p/nodejs"
    "p/expressjs"
    "p/sql-injection"
    "p/xss"
    "p/secrets"
    "p/jwt"
)
CONFIG_ARGS=()
for r in "${RULESETS[@]}"; do CONFIG_ARGS+=("--config=$r"); done

echo "[semgrep] Analisando $TARGET com ${#RULESETS[@]} rulesets..."
semgrep "${CONFIG_ARGS[@]}" \
    --json -o "$OUT_DIR/${REPORT_NAME}.json" \
    --exclude=node_modules --exclude=venv --exclude=.venv --exclude=target \
    --exclude=dist --exclude=build --exclude=__pycache__ \
    --metrics=off \
    "$TARGET" || true

semgrep "${CONFIG_ARGS[@]}" \
    --text \
    --exclude=node_modules --exclude=venv --exclude=.venv --exclude=target \
    --exclude=dist --exclude=build --exclude=__pycache__ \
    --metrics=off \
    "$TARGET" > "$OUT_DIR/${REPORT_NAME}.txt" 2>&1 || true

echo "[semgrep] Relatórios:"
echo "  $OUT_DIR/${REPORT_NAME}.json"
echo "  $OUT_DIR/${REPORT_NAME}.txt"
