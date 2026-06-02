import mysql from 'mysql2/promise';

export const pool = mysql.createPool({
  host: process.env.DB_HOST ?? 'localhost',
  port: Number(process.env.DB_PORT ?? 3306),
  user: process.env.DB_USER ?? 'appuser',
  password: process.env.DB_PASSWORD ?? 'apppass',
  database: process.env.DB_NAME ?? 'caso02_products',
  waitForConnections: true,
  connectionLimit: 10,
});

export async function initDatabase(): Promise<void> {
  await pool.execute(`
    CREATE TABLE IF NOT EXISTS products (
      id INT PRIMARY KEY AUTO_INCREMENT,
      name VARCHAR(255) NOT NULL,
      description TEXT,
      price DECIMAL(10, 2) NOT NULL
    )
  `);

  const [rows] = await pool.execute('SELECT COUNT(*) as count FROM products');
  const count = (rows as { count: number }[])[0].count;

  if (count === 0) {
    await pool.execute(`
      INSERT INTO products (name, description, price) VALUES
        ('Notebook Pro 15', 'Notebook de alta performance com tela de 15 polegadas', 4999.99),
        ('Mouse Wireless', 'Mouse sem fio com autonomia de 12 meses', 129.90),
        ('Teclado Mecânico RGB', 'Teclado mecânico com iluminação RGB e switches blue', 349.00),
        ('Monitor 27" 4K', 'Monitor UHD 4K com painel IPS e taxa de atualização 144Hz', 2199.00),
        ('Headset Gamer', 'Headset com som surround 7.1 e microfone com cancelamento de ruído', 599.90)
    `);
  }
}
