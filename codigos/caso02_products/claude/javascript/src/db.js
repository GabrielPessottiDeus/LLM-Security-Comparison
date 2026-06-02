const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '3306'),
  user: process.env.DB_USER || 'appuser',
  password: process.env.DB_PASSWORD || 'apppass',
  database: process.env.DB_NAME || 'caso02_products',
  waitForConnections: true,
  connectionLimit: 10,
});

async function initialize() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS products (
      id INT PRIMARY KEY AUTO_INCREMENT,
      name VARCHAR(255) NOT NULL,
      description TEXT,
      price DECIMAL(10, 2) NOT NULL
    )
  `);

  const [rows] = await pool.query('SELECT COUNT(*) AS count FROM products');
  if (rows[0].count === 0) {
    await pool.query(`
      INSERT INTO products (name, description, price) VALUES
        ('Notebook Pro', 'Laptop de alto desempenho com 16GB RAM', 4999.99),
        ('Mouse Wireless', 'Mouse sem fio com bateria recarregável', 149.90),
        ('Teclado Mecânico', 'Teclado mecânico RGB switches blue', 349.00),
        ('Monitor 4K', 'Monitor UHD 27 polegadas 144Hz', 2199.00),
        ('Headset Gamer', 'Headset surround 7.1 com microfone', 299.90)
    `);
  }
}

module.exports = { pool, initialize };
