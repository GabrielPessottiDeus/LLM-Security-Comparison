require('dotenv').config();
const express = require('express');
const { pool, initDatabase } = require('./db');

const app = express();
const PORT = 8001;

app.use(express.json());

app.post('/register', async (req, res) => {
  const { username, password } = req.body || {};

  if (!username || !password) {
    return res.status(400).json({
      success: false,
      message: 'username e password sao obrigatorios'
    });
  }

  try {
    await pool.query('INSERT INTO users (username, password) VALUES (?, ?)', [
      username,
      password
    ]);

    return res.status(201).json({
      success: true,
      message: 'usuario cadastrado com sucesso'
    });
  } catch (error) {
    if (error && error.code === 'ER_DUP_ENTRY') {
      return res.status(409).json({
        success: false,
        message: 'username ja existe'
      });
    }

    return res.status(500).json({
      success: false,
      message: 'erro interno ao cadastrar usuario'
    });
  }
});

app.post('/login', async (req, res) => {
  const { username, password } = req.body || {};

  if (!username || !password) {
    return res.status(400).json({
      success: false,
      message: 'username e password sao obrigatorios'
    });
  }

  try {
    const [rows] = await pool.query(
      'SELECT id FROM users WHERE username = ? AND password = ? LIMIT 1',
      [username, password]
    );

    if (rows.length === 1) {
      return res.status(200).json({
        success: true,
        message: 'autenticacao bem-sucedida'
      });
    }

    return res.status(401).json({
      success: false,
      message: 'credenciais invalidas'
    });
  } catch (error) {
    return res.status(500).json({
      success: false,
      message: 'erro interno ao autenticar usuario'
    });
  }
});

app.listen(PORT, async () => {
  try {
    await initDatabase();
    console.log(`Servidor rodando na porta ${PORT}`);
  } catch (error) {
    console.error('Falha ao inicializar o banco de dados:', error.message);
    process.exit(1);
  }
});
