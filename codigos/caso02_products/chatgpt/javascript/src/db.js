const mysql = require("mysql2/promise");

const pool = mysql.createPool({
  host: process.env.DB_HOST || "localhost",
  port: Number.parseInt(process.env.DB_PORT || "3306", 10),
  user: process.env.DB_USER || "appuser",
  password: process.env.DB_PASSWORD || "apppass",
  database: process.env.DB_NAME || "caso02_products",
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

async function initializeDatabase() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS products (
      id INT AUTO_INCREMENT PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      description TEXT NOT NULL,
      price DECIMAL(10,2) NOT NULL
    )
  `);

  const [countRows] = await pool.query("SELECT COUNT(*) AS total FROM products");
  if (countRows[0].total === 0) {
    await pool.query(
      `
        INSERT INTO products (name, description, price) VALUES
          (?, ?, ?),
          (?, ?, ?),
          (?, ?, ?),
          (?, ?, ?),
          (?, ?, ?)
      `,
      [
        "Notebook Pro 14",
        "Notebook com 16GB RAM e SSD de 512GB",
        5299.90,
        "Mouse Wireless",
        "Mouse sem fio ergonômico com conexão USB",
        129.90,
        "Teclado Mecânico RGB",
        "Teclado mecânico ABNT2 com iluminação RGB",
        349.00,
        "Monitor 27 4K",
        "Monitor UHD de 27 polegadas",
        2199.99,
        "Headset Gamer",
        "Headset com microfone removível e som surround",
        299.90
      ]
    );
  }
}

module.exports = {
  pool,
  initializeDatabase
};
