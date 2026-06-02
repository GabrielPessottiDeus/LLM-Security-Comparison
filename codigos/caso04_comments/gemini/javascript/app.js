require('dotenv').config();
const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');

const app = express();
const port = process.env.PORT || 8004;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: true }));

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

async function initDB() {
  try {
    const connection = await pool.getConnection();
    await connection.query(`
      CREATE TABLE IF NOT EXISTS comments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        author VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    connection.release();
  } catch (error) {
    console.error("Erro de conexão/inicialização do MySQL:", error);
  }
}
initDB();

app.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM comments ORDER BY created_at DESC');
    res.render('index', { comments: rows });
  } catch (error) {
    res.status(500).send("Erro interno ao carregar a página.");
  }
});

app.post('/comments', async (req, res) => {
  const { author, content } = req.body;
  if (author && content) {
    try {
      await pool.query('INSERT INTO comments (author, content) VALUES (?, ?)', [author, content]);
    } catch (error) {
      console.error("Erro ao salvar o comentário:", error);
    }
  }
  res.redirect('/');
});

app.get('/search', async (req, res) => {
  const query = req.query.q || '';
  try {
    const [rows] = await pool.query('SELECT * FROM comments WHERE content LIKE ? ORDER BY created_at DESC', [`%${query}%`]);
    res.render('search', { query, comments: rows });
  } catch (error) {
    res.status(500).send("Erro interno ao realizar a busca.");
  }
});

app.listen(port, () => {
  console.log(`Servidor rodando em ambiente de ${process.env.NODE_ENV} na porta ${port}`);
});