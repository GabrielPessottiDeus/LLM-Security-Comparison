const mysql = require('mysql2/promise');
require('dotenv').config();

async function initDb() {
    const connection = await mysql.createConnection({
        host: process.env.DB_HOST,
        port: process.env.DB_PORT,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD
    });

    await connection.query(`CREATE DATABASE IF NOT EXISTS \`${process.env.DB_NAME}\``);
    await connection.end();

    const pool = mysql.createPool({
        host: process.env.DB_HOST,
        port: process.env.DB_PORT,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_NAME,
        waitForConnections: true,
        connectionLimit: 10,
        queueLimit: 0
    });

    await pool.query(`
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL
        )
    `);

    const [rows] = await pool.query('SELECT COUNT(*) as count FROM products');
    if (rows[0].count === 0) {
        await pool.query(`
            INSERT INTO products (name, description, price) VALUES
            ('Notebook Ultra', 'Notebook com 16GB RAM e SSD 512GB', 4500.00),
            ('Smartphone Alpha', 'Smartphone tela AMOLED 120Hz', 2300.00),
            ('Teclado Mecânico', 'Teclado switch blue RGB', 350.00),
            ('Mouse Gamer', 'Mouse com sensor óptico 16000 DPI', 200.00),
            ('Monitor 27 Pol', 'Monitor IPS Full HD 144Hz', 1200.00)
        `);
    }

    return pool;
}

module.exports = { initDb };