#!/usr/bin/env bash
# ============================================================================
# run_app_node.sh — instala deps, builda (se TS) e sobe uma app Node.
#
# Uso:  bash scripts/run_app_node.sh codigos/caso01_auth/claude/javascript
#       bash scripts/run_app_node.sh codigos/caso01_auth/claude/typescript
#
# O script:
#   1) Detecta o caso pelo caminho e exporta variáveis DB_* no ambiente
#      (a app pode lê-las via process.env)
#   2) Instala deps (npm install)
#   3) Se for TS com script "build" no package.json -> compila
#   4) Roda:
#      - npm start (se houver script "start")
#      - npx ts-node <entry> (se for TS sem start)
#      - node <entry> (se for JS sem start)
# ============================================================================
set -euo pipefail

TARGET="${1:-}"
[[ -z "$TARGET" ]] && { echo "Uso: bash scripts/run_app_node.sh <pasta>"; exit 1; }
[[ ! -d "$TARGET" ]] && { echo "Pasta inexistente: $TARGET"; exit 1; }
[[ ! -f "$TARGET/package.json" ]] && { echo "package.json não encontrado em $TARGET"; exit 1; }

# ----------------------------------------------------------------------------
# 1) Detecta o caso pelo caminho e exporta as credenciais do banco
# ----------------------------------------------------------------------------
TARGET_ABS="$(cd "$TARGET" && pwd)"
CASE_DIR_NAME=""
for part in $(echo "$TARGET_ABS" | tr '/' '\n'); do
    if [[ "$part" =~ ^caso0[0-9]_ ]]; then
        CASE_DIR_NAME="$part"
        break
    fi
done

if [[ -z "$CASE_DIR_NAME" ]]; then
    echo "[node] AVISO: não detectei o caso (esperava 'caso0X_xxx' no caminho)."
else
    export DB_HOST="localhost"
    export DB_PORT="3306"
    export DB_USER="appuser"
    export DB_PASSWORD="apppass"
    export DB_NAME="$CASE_DIR_NAME"
    echo "[node] Variáveis de ambiente do banco exportadas (DB_NAME=$DB_NAME)"
fi

cd "$TARGET"

# ----------------------------------------------------------------------------
# 2) Dependências
# ----------------------------------------------------------------------------
echo "[node] Instalando dependências..."
npm install --no-audit --no-fund --loglevel=error

# Helper: verifica se um script existe no package.json
has_script() {
    node -e "
        try {
            const p = require('./package.json');
            process.exit(p.scripts && p.scripts['$1'] ? 0 : 1);
        } catch (e) { process.exit(1); }
    "
}

# ----------------------------------------------------------------------------
# 3) Build (apenas para projetos TypeScript com script "build")
# ----------------------------------------------------------------------------
if [[ -f tsconfig.json ]] && has_script build; then
    echo "[node] Projeto TypeScript detectado. Rodando 'npm run build'..."
    npm run build
fi

# ----------------------------------------------------------------------------
# 4) Executa a app
# ----------------------------------------------------------------------------
if has_script start; then
    echo "[node] Executando 'npm start'..."
    exec npm start
fi

# Sem script start: detecta entry
ENTRY=""
for cand in src/index.ts src/server.ts src/app.ts index.ts server.ts app.ts \
            src/index.js src/server.js src/app.js index.js server.js app.js \
            dist/index.js dist/server.js dist/app.js; do
    [[ -f "$cand" ]] && { ENTRY="$cand"; break; }
done
[[ -z "$ENTRY" ]] && { echo "[node] Nenhum arquivo de entrada encontrado."; exit 1; }

if [[ "$ENTRY" == *.ts ]]; then
    if ! [ -x "node_modules/.bin/ts-node" ]; then
        echo "[node] Instalando ts-node + tipos..."
        npm install --no-save --no-audit --no-fund ts-node typescript @types/node
    fi
    echo "[node] Executando $ENTRY com ts-node..."
    exec npx ts-node "$ENTRY"
else
    echo "[node] Executando $ENTRY ..."
    exec node "$ENTRY"
fi