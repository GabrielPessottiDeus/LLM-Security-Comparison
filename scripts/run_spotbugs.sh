#!/usr/bin/env bash
# ============================================================================
# run_spotbugs.sh — analisa código Java com SpotBugs + find-sec-bugs
#
# SpotBugs analisa BYTECODE compilado (.class/.jar). Por isso o script
# primeiro compila o projeto Maven (mvn compile) antes de analisar.
#
# Uso:
#   bash scripts/run_spotbugs.sh <caminho_codigo_java> [nome_relatorio]
#
# Recursos chave:
#   1) Detecta Java 21 automaticamente (Java 25 não é suportado por SpotBugs 4.8.6)
#   2) Compila o código com 'mvn clean compile'
#   3) **Resolve o classpath completo via maven-dependency-plugin** e passa
#      todas as bibliotecas (Spring, Hibernate, BCrypt, etc.) como
#      auxClasspath para o SpotBugs. Isso permite que o detector "enxergue"
#      o código de bibliotecas e detecte vulnerabilidades sutis como SQL
#      injection através de Spring Data JPA, taint tracking entre
#      controllers e repositories, etc.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Detecta Java 21 (preferido). SpotBugs 4.8.6 não analisa bytecode do Java 25.
JAVA21_HOME="$(ls -d /usr/lib/jvm/java-21-openjdk* 2>/dev/null | head -1 || true)"
if [[ -n "$JAVA21_HOME" && -x "$JAVA21_HOME/bin/java" ]]; then
    export JAVA_HOME="$JAVA21_HOME"
    export PATH="$JAVA_HOME/bin:$PATH"
    echo "[spotbugs] Usando Java 21: $JAVA_HOME"
else
    echo "[spotbugs] AVISO: Java 21 não encontrado."
    echo "[spotbugs] SpotBugs pode falhar se o bytecode foi gerado por Java 24+."
    echo "[spotbugs] Instale: sudo dnf install -y java-21-openjdk-devel"
fi

# SpotBugs home
if [[ -z "${SPOTBUGS_HOME:-}" ]]; then
    SPOTBUGS_HOME="$(ls -d "$HOME"/tools/spotbugs-* 2>/dev/null | sort -V | tail -1 || true)"
fi
if [[ -z "${SPOTBUGS_HOME:-}" || ! -x "$SPOTBUGS_HOME/bin/spotbugs" ]]; then
    echo "Erro: SpotBugs não encontrado. Rode 'bash scripts/setup_fedora.sh' primeiro."
    exit 1
fi

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
    echo "Uso: bash scripts/run_spotbugs.sh <caminho_codigo_java>"
    exit 1
fi
[[ ! -d "$TARGET" ]] && { echo "Diretório não existe: $TARGET"; exit 1; }

REPORT_NAME="${2:-$(echo "$TARGET" | sed -E 's|^codigos/||;s|/|_|g')}"
OUT_DIR="$ROOT/reports/sast/spotbugs"
mkdir -p "$OUT_DIR"

if [[ ! -f "$TARGET/pom.xml" ]]; then
    echo "[spotbugs] AVISO: $TARGET não tem pom.xml. Pulando."
    exit 0
fi

# ----------------------------------------------------------------------------
# 1) Compila o projeto (clean garante bytecode consistente com Java 21)
# ----------------------------------------------------------------------------
echo "[spotbugs] Compilando projeto (mvn clean compile)..."
(cd "$TARGET" && mvn -q clean compile)

CLASSES_DIR="$TARGET/target/classes"
if [[ ! -d "$CLASSES_DIR" ]]; then
    echo "[spotbugs] Erro: $CLASSES_DIR não existe após compilação."
    exit 1
fi

# ----------------------------------------------------------------------------
# 2) Resolve auxClasspath via maven-dependency-plugin
#
# O maven-dependency-plugin:build-classpath gera uma string com todos os JARs
# de dependências resolvidas pelo Maven (Spring, Hibernate, MySQL connector,
# BCrypt, Jackson, Tomcat embarcado, etc.). Passando isso como -auxclasspath,
# o SpotBugs consegue resolver tipos do Spring e fazer análises mais profundas
# (especialmente taint tracking para SQL injection, XSS, etc.).
# ----------------------------------------------------------------------------
echo "[spotbugs] Resolvendo classpath de dependências (Spring, etc.)..."
CLASSPATH_FILE="$(mktemp)"
(cd "$TARGET" && mvn -q dependency:build-classpath \
    -Dmdep.outputFile="$CLASSPATH_FILE" \
    -Dmdep.pathSeparator=: 2>/dev/null) || true

AUX_CLASSPATH=""
if [[ -s "$CLASSPATH_FILE" ]]; then
    AUX_CLASSPATH="$(cat "$CLASSPATH_FILE")"
    DEPS_COUNT=$(echo "$AUX_CLASSPATH" | tr ':' '\n' | wc -l)
    echo "[spotbugs]   $DEPS_COUNT JARs de dependências resolvidos"
else
    echo "[spotbugs]   AVISO: não consegui resolver classpath. Análise será mais superficial."
fi
rm -f "$CLASSPATH_FILE"

# ----------------------------------------------------------------------------
# 3) Roda SpotBugs com auxClasspath
# ----------------------------------------------------------------------------
echo "[spotbugs] Analisando bytecode em $CLASSES_DIR ..."

AUX_FLAG=""
[[ -n "$AUX_CLASSPATH" ]] && AUX_FLAG="-auxclasspath $AUX_CLASSPATH"

# Versão XML (para o agregador)
"$SPOTBUGS_HOME/bin/spotbugs" \
    -textui \
    -effort:max \
    -low \
    -pluginList "$SPOTBUGS_HOME/plugin/findsecbugs-plugin.jar" \
    -include "$ROOT/sast-configs/spotbugs-include.xml" \
    $AUX_FLAG \
    -xml:withMessages \
    -output "$OUT_DIR/${REPORT_NAME}.xml" \
    "$CLASSES_DIR" 2>&1 | grep -v "DetectorFactoryCollection\|already registered factory\|WARNING:" || true

# Versão TXT (legível por humano) — captura sem o ruído dos warnings de plugin
"$SPOTBUGS_HOME/bin/spotbugs" \
    -textui \
    -effort:max \
    -low \
    -pluginList "$SPOTBUGS_HOME/plugin/findsecbugs-plugin.jar" \
    -include "$ROOT/sast-configs/spotbugs-include.xml" \
    $AUX_FLAG \
    "$CLASSES_DIR" 2>&1 | grep -v "DetectorFactoryCollection\|already registered factory\|May.*PM\|WARNING:" > "$OUT_DIR/${REPORT_NAME}.txt" || true

# Conta achados
BUG_COUNT=$(grep -c "^[HML] [A-Z]" "$OUT_DIR/${REPORT_NAME}.txt" 2>/dev/null || echo 0)

echo
echo "[spotbugs] Relatórios:"
echo "  $OUT_DIR/${REPORT_NAME}.xml"
echo "  $OUT_DIR/${REPORT_NAME}.txt"
echo "[spotbugs] Total de achados: $BUG_COUNT"