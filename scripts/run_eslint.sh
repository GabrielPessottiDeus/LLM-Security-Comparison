#!/usr/bin/env bash
# ============================================================================
# run_eslint.sh — analisa JS/TS com ESLint + plugins de segurança
#
# Uso:
#   bash scripts/run_eslint.sh <caminho_codigo_js_ou_ts> [nome_relatorio]
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
    echo "Uso: bash scripts/run_eslint.sh <caminho_codigo>"
    exit 1
fi
[[ ! -d "$TARGET" ]] && { echo "Diretório não existe: $TARGET"; exit 1; }

# Caminho absoluto do alvo (ESLint precisa para o --resolve-plugins-relative-to)
TARGET_ABS="$(cd "$TARGET" && pwd)"

REPORT_NAME="${2:-$(echo "$TARGET" | sed -E 's|^codigos/||;s|/|_|g')}"
OUT_DIR="$ROOT/reports/sast/eslint"
mkdir -p "$OUT_DIR"

ESLINT_CONFIG="$ROOT/sast-configs/.eslintrc.cjs"
ESLINT_BIN="$ROOT/sast-configs/node_modules/.bin/eslint"

if [[ ! -x "$ESLINT_BIN" ]]; then
    echo "Erro: ESLint não instalado. Rode 'bash scripts/setup_fedora.sh' primeiro."
    exit 1
fi

echo "[eslint] Analisando $TARGET ..."
# --no-eslintrc para ignorar qualquer .eslintrc do próprio código da LLM
# --resolve-plugins-relative-to garante que os plugins sejam buscados em sast-configs/
"$ESLINT_BIN" \
    --no-eslintrc \
    --config "$ESLINT_CONFIG" \
    --resolve-plugins-relative-to "$ROOT/sast-configs" \
    --ext .js,.jsx,.ts,.tsx,.mjs,.cjs \
    --format json \
    --output-file "$OUT_DIR/${REPORT_NAME}.json" \
    --ignore-pattern "node_modules/" \
    --ignore-pattern "dist/" \
    --ignore-pattern "build/" \
    "$TARGET_ABS" || true

"$ESLINT_BIN" \
    --no-eslintrc \
    --config "$ESLINT_CONFIG" \
    --resolve-plugins-relative-to "$ROOT/sast-configs" \
    --ext .js,.jsx,.ts,.tsx,.mjs,.cjs \
    --format stylish \
    --ignore-pattern "node_modules/" \
    --ignore-pattern "dist/" \
    --ignore-pattern "build/" \
    "$TARGET_ABS" > "$OUT_DIR/${REPORT_NAME}.txt" 2>&1 || true

echo "[eslint] Relatórios:"
echo "  $OUT_DIR/${REPORT_NAME}.json"
echo "  $OUT_DIR/${REPORT_NAME}.txt"
