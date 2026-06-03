# Reseta os dados de um caso específico (drop + recreate do banco).
# Útil quando se troca de IA/linguagem testada para garantir estado limpo.
#
# Uso:  bash scripts/reset_db.sh <numero_do_caso>
#       bash scripts/reset_db.sh 1     # reseta caso01_auth
#       bash scripts/reset_db.sh all   # reseta todos 
set -euo pipefail

CASE="${1:-}"
if [[ -z "$CASE" ]]; then
    echo "Uso: bash scripts/reset_db.sh <1|2|3|4|5|all>"
    exit 1
fi

run_sql() {
    docker exec -i llm-sec-mysql mysql -uroot -prootpass <<EOF
$1
EOF
}

reset_case() {
    case "$1" in
        1) DB="caso01_auth"     ;;
        2) DB="caso02_products" ;;
        3) DB="caso03_upload"   ;;
        4) DB="caso04_comments" ;;
        5) DB="caso05_session"  ;;
        *) echo "Caso inválido: $1"; exit 1 ;;
    esac

    echo "[reset] Recriando banco $DB..."
    run_sql "DROP DATABASE IF EXISTS $DB; CREATE DATABASE $DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON $DB.* TO 'appuser'@'%'; FLUSH PRIVILEGES;"

    # Reaplica schema + seed do init para esse banco
    case "$1" in
        1) run_sql "USE $DB; CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL);" ;;
        2) run_sql "USE $DB;
            CREATE TABLE products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, description TEXT, price DECIMAL(10,2) NOT NULL);
            INSERT INTO products (name, description, price) VALUES
              ('Notebook Dell Inspiron','Notebook 15.6 polegadas, 16GB RAM, SSD 512GB',4599.90),
              ('Mouse Logitech MX Master','Mouse sem fio ergonômico',499.00),
              ('Teclado Mecânico Keychron','Teclado mecânico switch brown, layout ABNT2',789.50),
              ('Monitor LG UltraWide','Monitor 29 polegadas 2560x1080 IPS',1899.00),
              ('Webcam Logitech C920','Webcam Full HD 1080p',649.00);" ;;
        4) run_sql "USE $DB; CREATE TABLE comments (id INT AUTO_INCREMENT PRIMARY KEY, author VARCHAR(255) NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);" ;;
    esac
    echo "[reset] $DB OK."
}

if [[ "$CASE" == "all" ]]; then
    for i in 1 2 3 4 5; do reset_case "$i"; done
else
    reset_case "$CASE"
fi
