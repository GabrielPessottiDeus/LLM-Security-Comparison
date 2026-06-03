-- CASO 01 - autenticação (tabela users) 
USE caso01_auth;
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- CASO 02 - produtos (tabela products + seed)
USE caso02_products;
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL
);

INSERT INTO products (name, description, price) VALUES
    ('Notebook Dell Inspiron',  'Notebook 15.6 polegadas, 16GB RAM, SSD 512GB', 4599.90),
    ('Mouse Logitech MX Master','Mouse sem fio ergonômico',                      499.00),
    ('Teclado Mecânico Keychron','Teclado mecânico switch brown, layout ABNT2',  789.50),
    ('Monitor LG UltraWide',    'Monitor 29 polegadas 2560x1080 IPS',           1899.00),
    ('Webcam Logitech C920',    'Webcam Full HD 1080p',                          649.00);


-- CASO 04 - comentários (tabela comments)
USE caso04_comments;
CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author  VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Caso 03 não precisa de tabela (só upload em disco).
-- Caso 05 não precisa de tabela (credencial admin/admin123 é fixa no código).
