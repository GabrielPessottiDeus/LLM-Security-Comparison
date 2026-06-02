#!/usr/bin/env bash
# Para o MySQL. Use --wipe para destruir o volume e começar do zero
# (útil entre testes de IAs diferentes para garantir dados limpos).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../infra" && pwd)"
cd "$INFRA_DIR"

if [[ "${1:-}" == "--wipe" ]]; then
    echo "[mysql] Parando e REMOVENDO o volume (dados serão perdidos)..."
    docker compose down -v
else
    echo "[mysql] Parando containers (volume preservado)..."
    docker compose down
fi
