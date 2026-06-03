# ===========================================================================
# compila e sobe um app Spring Boot.
#
# Uso:  bash scripts/run_app_java.sh codigos/caso01_auth/claude/java
# ===========================================================================
set -euo pipefail

TARGET="${1:-}"
[[ -z "$TARGET" ]] && { echo "Uso: bash scripts/run_app_java.sh <pasta>"; exit 1; }
[[ ! -d "$TARGET" ]] && { echo "Pasta inexistente: $TARGET"; exit 1; }
[[ ! -f "$TARGET/pom.xml" ]] && { echo "pom.xml não encontrado em $TARGET"; exit 1; }


TARGET_ABS="$(cd "$TARGET" && pwd)"
CASE_DIR_NAME=""
for part in $(echo "$TARGET_ABS" | tr '/' '\n'); do
    if [[ "$part" =~ ^caso0[0-9]_ ]]; then
        CASE_DIR_NAME="$part"
        break
    fi
done

if [[ -z "$CASE_DIR_NAME" ]]; then
    echo "[java] AVISO: não detectei o caso (esperava 'caso0X_xxx' no caminho)."
else
    export DB_HOST="localhost"
    export DB_PORT="3306"
    export DB_USER="appuser"
    export DB_PASSWORD="apppass"
    export DB_NAME="$CASE_DIR_NAME"
    echo "[java] Variáveis de ambiente do banco exportadas (DB_NAME=$DB_NAME)"
fi

JAVA21_HOME="$(ls -d /usr/lib/jvm/java-21-openjdk* 2>/dev/null | head -1 || true)"
if [[ -n "$JAVA21_HOME" && -x "$JAVA21_HOME/bin/java" ]]; then
    export JAVA_HOME="$JAVA21_HOME"
    export PATH="$JAVA_HOME/bin:$PATH"
    echo "[java] Usando Java 21: $JAVA_HOME"
else
    echo "[java] AVISO: Java 21 não encontrado. Usando default do sistema:"
    java -version 2>&1 | head -1
fi

cd "$TARGET"
echo "[java] Compilando e iniciando Spring Boot..."
echo "[java] (Ctrl+C para parar)"
exec mvn spring-boot:run