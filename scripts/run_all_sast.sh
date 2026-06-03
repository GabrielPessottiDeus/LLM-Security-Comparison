# ============================================================================
# run_all_sast.sh — varre TODOS os códigos colados em codigos/ e roda
# automaticamente a ferramenta SAST apropriada para cada linguagem.
#
# Para cada pasta codigos/caso*/<ia>/<linguagem>/ que tiver código:
#   - python     -> Bandit + Semgrep
#   - java       -> SpotBugs + Semgrep
#   - javascript -> ESLint + Semgrep
#   - typescript -> ESLint + Semgrep
#
# Uso:  bash scripts/run_all_sast.sh
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

for s in run_bandit.sh run_semgrep.sh run_spotbugs.sh run_eslint.sh; do
    [[ -f "scripts/$s" ]] || { echo "Faltando scripts/$s"; exit 1; }
done

has_code() {
    local dir="$1"
    [[ -d "$dir" ]] || return 1
    find "$dir" -maxdepth 3 -type f \
        ! -path '*/node_modules/*' \
        ! -path '*/target/*' \
        ! -path '*/venv/*' \
        ! -path '*/.venv/*' \
        ! -name '.gitkeep' \
        | head -1 | grep -q . || return 1
}

TOTAL=0; SKIPPED=0
for case_dir in codigos/caso*/; do
    [[ -d "$case_dir" ]] || continue
    for ia_dir in "$case_dir"*/; do
        [[ -d "$ia_dir" ]] || continue
        for lang_dir in "$ia_dir"*/; do
            [[ -d "$lang_dir" ]] || continue
            lang="$(basename "$lang_dir")"
            target="${lang_dir%/}"

            if ! has_code "$target"; then
                SKIPPED=$((SKIPPED+1))
                continue
            fi
            TOTAL=$((TOTAL+1))

            echo
            echo "================================================================"
            echo "  Alvo: $target"
            echo "  Linguagem: $lang"
            echo "================================================================"

            case "$lang" in
                python)
                    bash scripts/run_bandit.sh  "$target" || true
                    bash scripts/run_semgrep.sh "$target" || true
                    ;;
                java)
                    bash scripts/run_spotbugs.sh "$target" || true
                    bash scripts/run_semgrep.sh  "$target" || true
                    ;;
                javascript|typescript)
                    bash scripts/run_eslint.sh   "$target" || true
                    bash scripts/run_semgrep.sh  "$target" || true
                    ;;
                *)
                    echo "Linguagem desconhecida: $lang (pulando)"
                    ;;
            esac
        done
    done
done

echo
echo "================================================================"
echo "  CONCLUÍDO: $TOTAL códigos analisados, $SKIPPED diretórios vazios pulados"
echo "  Relatórios em: $ROOT/reports/sast/"
echo "================================================================"
