# ===========================================================================
# run_bandit.sh — analisa código Python com Bandit
#
# Uso:
#   bash scripts/run_bandit.sh <caminho_codigo> [nome_relatorio]
# Exemplo:
#   bash scripts/run_bandit.sh codigos/caso01_auth/claude/python
# ===========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
    echo "Uso: bash scripts/run_bandit.sh <caminho_codigo>"
    exit 1
fi
[[ ! -d "$TARGET" ]] && { echo "Diretório não existe: $TARGET"; exit 1; }

REPORT_NAME="${2:-$(echo "$TARGET" | sed -E 's|^codigos/||;s|/|_|g')}"
OUT_DIR="$ROOT/reports/sast/bandit"
mkdir -p "$OUT_DIR"

echo "[bandit] Analisando $TARGET ..."
bandit -r "$TARGET" \
    -ll -ii \
    -f json -o "$OUT_DIR/${REPORT_NAME}.json" \
    --exclude '**/venv/**,**/.venv/**,**/__pycache__/**' \
    || true

bandit -r "$TARGET" \
    -ll -ii \
    -f txt -o "$OUT_DIR/${REPORT_NAME}.txt" \
    --exclude '**/venv/**,**/.venv/**,**/__pycache__/**' \
    || true

echo "[bandit] Relatórios:"
echo "  $OUT_DIR/${REPORT_NAME}.json"
echo "  $OUT_DIR/${REPORT_NAME}.txt"
