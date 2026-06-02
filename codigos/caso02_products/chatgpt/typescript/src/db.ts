import mysql from 'mysql2/promise';

export const pool = mysql.createPool({
  host: process.env.DB_HOST ?? 'localhost',
  port: Number(process.env.DB_PORT ?? 3306),
  user: process.env.DB_USER ?? 'appuser',
  password: process.env.DB_PASSWORD ?? 'apppass',
  database: process.env.DB_NAME ?? 'caso02_products',
  waitForConnections: true,
  connectionLimit: 10
});

type CountRow = {
  count: number;
};

export async function initDatabase(): Promise<void> {
  await pool.execute(`
    CREATE TABLE IF NOT EXISTS products (
      id INT PRIMARY KEY AUTO_INCREMENT,
      name VARCHAR(255) NOT NULL,
      description TEXT NOT NULL,
      price DECIMAL(10, 2) NOT NULL
    )
  `);

  const [rows] = await pool.query<(mysql.RowDataPacket & CountRow)[]>(
    'SELECT COUNT(*) AS count FROM products'
  );
  const count = Number(rows[0]?.count ?? 0);

  if (count === 0) {
    await pool.execute(`
      INSERT INTO products (name, description, price) VALUES
      ('Notebook Pro 15', 'Notebook de alta performance com 32GB RAM e SSD de 1TB', 7599.90),
      ('Mouse Wireless', 'Mouse sem fio ergonômico com bateria recarregável', 189.90),
      ('Teclado Mecânico RGB', 'Teclado mecânico com switches blue e iluminação RGB', 429.00),
      ('Monitor 27 4K', 'Monitor 27 polegadas UHD com painel IPS', 2399.00),
      ('Headset Gamer', 'Headset com áudio surround 7.1 e microfone removível', 649.90)
    `);
  }
}
