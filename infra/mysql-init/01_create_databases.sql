-- Cria um banco isolado para cada caso de teste.
-- Os códigos das LLMs geralmente criam suas próprias tabelas, mas o banco
-- precisa existir previamente para a conexão funcionar.

CREATE DATABASE IF NOT EXISTS caso01_auth     CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS caso02_products CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS caso03_upload   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS caso04_comments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS caso05_session  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Permissões totais ao usuário da aplicação em todos os bancos
GRANT ALL PRIVILEGES ON caso01_auth.*     TO 'appuser'@'%';
GRANT ALL PRIVILEGES ON caso02_products.* TO 'appuser'@'%';
GRANT ALL PRIVILEGES ON caso03_upload.*   TO 'appuser'@'%';
GRANT ALL PRIVILEGES ON caso04_comments.* TO 'appuser'@'%';
GRANT ALL PRIVILEGES ON caso05_session.*  TO 'appuser'@'%';

FLUSH PRIVILEGES;
