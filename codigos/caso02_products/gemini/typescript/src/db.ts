import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config();

export const pool = mysql.createPool({
    host: process.env.DB_HOST,
    port: Number(process.env.DB_PORT),
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

export async function initDB() {
    const createTableQuery = `
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL
        )
    `;
    await pool.query(createTableQuery);

    const [rows]: any = await pool.query('SELECT COUNT(*) as count FROM products');
    
    if (rows[0].count === 0) {
        const insertQuery = `
            INSERT INTO products (name, description, price) VALUES
            ('Notebook Pro', 'Notebook com 16GB RAM e SSD 512GB', 4500.00),
            ('Smartphone X', 'Smartphone tela AMOLED 128GB', 2100.00),
            ('Monitor Ultra', 'Monitor Ultrawide 29 polegadas', 1350.00),
            ('Teclado Mecânico', 'Teclado switch brown RGB', 350.00),
            ('Mouse Gamer', 'Mouse com 10000 DPI', 180.00)
        `;
        await pool.query(insertQuery);
        console.log('Database initialized with 5 sample products.');
    }
}