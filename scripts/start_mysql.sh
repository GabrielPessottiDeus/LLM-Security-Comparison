# Sobe o MySQL via docker-compose e aguarda ele ficar saudável.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../infra" && pwd)"

cd "$INFRA_DIR"
docker compose up -d

echo "[mysql] Aguardando o MySQL ficar saudável..."
for i in {1..60}; do
    status="$(docker inspect --format='{{.State.Health.Status}}' llm-sec-mysql 2>/dev/null || echo 'starting')"
    if [[ "$status" == "healthy" ]]; then
        echo "[mysql] Pronto! Acesso:"
        echo "  Host:     localhost"
        echo "  Porta:    3306"
        echo "  Root:     root / rootpass"
        echo "  App user: appuser / apppass"
        echo "  Bancos:   caso01_auth, caso02_products, caso03_upload, caso04_comments, caso05_session"
        exit 0
    fi
    sleep 1
done
echo "[mysql] Timeout aguardando saúde. Verifique: docker logs llm-sec-mysql"
exit 1
