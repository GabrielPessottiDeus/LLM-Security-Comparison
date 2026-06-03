# ============================================================================
# Uso:
#   bash scripts/run_zap.sh <numero_caso> [baseline|full] [tag]
#
# Exemplos:
#   bash scripts/run_zap.sh 1 full gemini_python
#   bash scripts/run_zap.sh 2 full chatgpt_java
#   bash scripts/run_zap.sh 4 baseline claude_typescript
# ============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CASE_NUM="${1:-}"
SCAN_TYPE="${2:-full}"
TAG="${3:-}"

if [[ -z "$CASE_NUM" ]]; then
    echo "Uso: bash scripts/run_zap.sh <numero_caso> [baseline|full] [tag]"
    echo "Ex:  bash scripts/run_zap.sh 1 full gemini_python"
    exit 1
fi

ENDPOINTS_FILE="$ROOT/infra/endpoints.json"
if [[ ! -f "$ENDPOINTS_FILE" ]]; then
    echo "Arquivo de endpoints não encontrado: $ENDPOINTS_FILE"
    exit 1
fi

if ! command -v jq &>/dev/null; then
    echo "jq não está instalado. Rode: sudo dnf install -y jq"
    exit 1
fi

PORT="$(jq -r ".\"$CASE_NUM\".port" "$ENDPOINTS_FILE")"
CASE_NAME="$(jq -r ".\"$CASE_NUM\".name" "$ENDPOINTS_FILE")"
if [[ -z "$PORT" || "$PORT" == "null" ]]; then
    echo "Caso inválido: $CASE_NUM (use 1, 2, 3, 4 ou 5)"
    exit 1
fi
TARGET_URL="http://localhost:${PORT}"

case "$SCAN_TYPE" in
    baseline) ZAP_SCRIPT="zap-baseline.py" ;;
    full)     ZAP_SCRIPT="zap-full-scan.py" ;;
    *) echo "Tipo inválido: $SCAN_TYPE (use 'baseline' ou 'full')"; exit 1 ;;
esac

OUT_DIR="$ROOT/reports/dast"
mkdir -p "$OUT_DIR"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
NAME_BASE="zap_${SCAN_TYPE}_caso${CASE_NUM}"
[[ -n "$TAG" ]] && NAME_BASE="${NAME_BASE}_${TAG}"
NAME_BASE="${NAME_BASE}_${TIMESTAMP}"

echo "[zap] Caso $CASE_NUM ($CASE_NAME) — alvo: $TARGET_URL"
echo "[zap] Verificando se a aplicação responde..."
if ! curl -s -o /dev/null --max-time 5 "$TARGET_URL"; then
    FIRST_PATH="$(jq -r ".\"$CASE_NUM\".endpoints[0].path" "$ENDPOINTS_FILE")"
    if ! curl -s -o /dev/null --max-time 5 -X "$(jq -r ".\"$CASE_NUM\".endpoints[0].method" "$ENDPOINTS_FILE")" "${TARGET_URL}${FIRST_PATH}"; then
        echo "[zap] AVISO: aplicação não respondeu em $TARGET_URL"
        echo "[zap] Confirme que ela está rodando (em outro terminal):"
        case "$CASE_NUM" in
            1) echo "        bash scripts/run_app_python.sh codigos/caso01_auth/<ia>/python" ;;
            2) echo "        bash scripts/run_app_python.sh codigos/caso02_products/<ia>/python" ;;
            *) echo "        bash scripts/run_app_<lang>.sh codigos/casoXX_xxx/<ia>/<lang>" ;;
        esac
        exit 1
    fi
fi


URLS_FILE="$OUT_DIR/.${NAME_BASE}_urls.txt"
> "$URLS_FILE"
ENDPOINT_COUNT="$(jq -r ".\"$CASE_NUM\".endpoints | length" "$ENDPOINTS_FILE")"

echo "[zap] Pré-popula $ENDPOINT_COUNT endpoints conhecidos do caso $CASE_NUM..."

for i in $(seq 0 $((ENDPOINT_COUNT - 1))); do
    METHOD="$(jq -r ".\"$CASE_NUM\".endpoints[$i].method" "$ENDPOINTS_FILE")"
    PATH_EP="$(jq -r ".\"$CASE_NUM\".endpoints[$i].path" "$ENDPOINTS_FILE")"
    BODY="$(jq -c ".\"$CASE_NUM\".endpoints[$i].body // empty" "$ENDPOINTS_FILE")"
    CTYPE="$(jq -r ".\"$CASE_NUM\".endpoints[$i].content_type // empty" "$ENDPOINTS_FILE")"
    FORM_FILE="$(jq -r ".\"$CASE_NUM\".endpoints[$i].form_file // empty" "$ENDPOINTS_FILE")"
    FORM_FIELD="$(jq -r ".\"$CASE_NUM\".endpoints[$i].form_field // empty" "$ENDPOINTS_FILE")"

    URL="${TARGET_URL}${PATH_EP}"
    echo "$URL" >> "$URLS_FILE"

    if [[ "$METHOD" == "GET" ]]; then
        curl -s -o /dev/null --max-time 10 "$URL" || true

    elif [[ -n "$FORM_FILE" ]]; then
        TMP_UPLOAD="/tmp/${FORM_FILE}"
        echo "Arquivo de teste do ZAP $(date)" > "$TMP_UPLOAD"
        curl -s -o /dev/null --max-time 10 -X "$METHOD" \
            -F "${FORM_FIELD}=@${TMP_UPLOAD}" "$URL" || true
        rm -f "$TMP_UPLOAD"

    elif [[ "$CTYPE" == "application/json" ]]; then
        curl -s -o /dev/null --max-time 10 -X "$METHOD" \
            -H "Content-Type: application/json" \
            -d "$BODY" "$URL" || true

    elif [[ "$CTYPE" == "application/x-www-form-urlencoded" ]]; then
        FORM_DATA="$(echo "$BODY" | jq -r 'to_entries | map("\(.key)=\(.value|@uri)") | join("&")')"
        curl -s -o /dev/null --max-time 10 -X "$METHOD" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "$FORM_DATA" "$URL" || true
    fi
    echo "       [$METHOD] $PATH_EP"
done

echo "$TARGET_URL" >> "$URLS_FILE"

echo
echo "[zap] Iniciando $SCAN_TYPE scan..."
echo "[zap] Baseline ~1min, Full ~10-30min. Aguarde sem fechar este terminal."
echo

EXTRA_URLS="$(grep -v '^$' "$URLS_FILE" | sort -u | tr '\n' ' ')"

docker run --rm \
    --network host \
    -v "$OUT_DIR:/zap/wrk/:rw" \
    -t ghcr.io/zaproxy/zaproxy:stable \
    "$ZAP_SCRIPT" \
        -t "$TARGET_URL" \
        -r "${NAME_BASE}.html" \
        -J "${NAME_BASE}.json" \
        -x "${NAME_BASE}.xml" \
        -I \
        -z "-config spider.maxDuration=2 -config scanner.threadPerHost=5" \
        || true

rm -f "$URLS_FILE"

echo
echo "[zap] Relatórios gerados em $OUT_DIR/${NAME_BASE}.{html,json,xml}"

JSON_REPORT="$OUT_DIR/${NAME_BASE}.json"
if [[ -f "$JSON_REPORT" ]]; then
    if command -v jq &>/dev/null; then
        HIGH=$(jq '[.site[]?.alerts[]? | select(.riskcode=="3")] | length' "$JSON_REPORT" 2>/dev/null || echo "?")
        MED=$(jq  '[.site[]?.alerts[]? | select(.riskcode=="2")] | length' "$JSON_REPORT" 2>/dev/null || echo "?")
        LOW=$(jq  '[.site[]?.alerts[]? | select(.riskcode=="1")] | length' "$JSON_REPORT" 2>/dev/null || echo "?")
        INFO=$(jq '[.site[]?.alerts[]? | select(.riskcode=="0")] | length' "$JSON_REPORT" 2>/dev/null || echo "?")
        echo "[zap] Findings: HIGH=$HIGH  MEDIUM=$MED  LOW=$LOW  INFO=$INFO"
    fi
fi
echo "[zap] Para abrir o relatório HTML:"
echo "       xdg-open $OUT_DIR/${NAME_BASE}.html"