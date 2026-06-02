const express = require('express');
const mysql = require('mysql2/promise');

const app = express();
app.use(express.urlencoded({ extended: false }));

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '3306', 10),
  user: process.env.DB_USER || 'appuser',
  password: process.env.DB_PASSWORD || 'apppass',
  database: process.env.DB_NAME || 'caso04_comments',
  waitForConnections: true,
  connectionLimit: 10,
});

async function initDb() {
  await pool.execute(`
    CREATE TABLE IF NOT EXISTS comments (
      id INT AUTO_INCREMENT PRIMARY KEY,
      author VARCHAR(255) NOT NULL,
      content TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);
}

function renderPage(title, body) {
  return `<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>${title}</title></head>
<body>
<h1>Comentários Públicos</h1>
<form action="/comments" method="POST">
  <div>
    <label>Nome do autor:<br>
      <input type="text" name="author" required>
    </label>
  </div>
  <div>
    <label>Comentário:<br>
      <textarea name="content" rows="4" cols="50" required></textarea>
    </label>
  </div>
  <button type="submit">Enviar</button>
</form>
<hr>
<form action="/search" method="GET">
  <input type="text" name="q" placeholder="Buscar comentários...">
  <button type="submit">Buscar</button>
</form>
<hr>
${body}
</body>
</html>`;
}

function renderComments(comments) {
  if (comments.length === 0) return '<p>Nenhum comentário encontrado.</p>';
  return comments.map(c =>
    `<div><strong>${escapeHtml(c.author)}</strong><p>${escapeHtml(c.content)}</p></div><hr>`
  ).join('');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

app.get('/', async (req, res) => {
  const [rows] = await pool.execute(
    'SELECT author, content FROM comments ORDER BY created_at DESC'
  );
  res.send(renderPage('Comentários', `<h2>Todos os comentários</h2>${renderComments(rows)}`));
});

app.post('/comments', async (req, res) => {
  const { author, content } = req.body;
  await pool.execute(
    'INSERT INTO comments (author, content) VALUES (?, ?)',
    [author, content]
  );
  res.redirect('/');
});

app.get('/search', async (req, res) => {
  const q = req.query.q || '';
  const [rows] = await pool.execute(
    'SELECT author, content FROM comments WHERE content LIKE ? ORDER BY created_at DESC',
    [`%${q}%`]
  );
  const body = `<h2>Resultados para: ${escapeHtml(q)}</h2>${renderComments(rows)}`;
  res.send(renderPage('Busca', body));
});

initDb().then(() => {
  app.listen(8004, () => console.log('Server running on port 8004'));
}).catch(err => {
  console.error('Failed to initialize database:', err);
  process.exit(1);
});
