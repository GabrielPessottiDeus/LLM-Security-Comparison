const path = require('path');
const express = require('express');
const { pool, initDb } = require('./db');

const app = express();
const PORT = 8004;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: false }));

app.get('/', async (req, res, next) => {
  try {
    const [comments] = await pool.execute(
      'SELECT id, author, content, created_at FROM comments ORDER BY created_at DESC, id DESC'
    );
    res.render('index', { comments });
  } catch (error) {
    next(error);
  }
});

app.post('/comments', async (req, res, next) => {
  try {
    const author = (req.body.author || '').trim();
    const content = (req.body.content || '').trim();

    if (!author || !content) {
      return res.status(400).send('Campos author e content sao obrigatorios.');
    }

    await pool.execute('INSERT INTO comments (author, content) VALUES (?, ?)', [author, content]);
    res.redirect('/');
  } catch (error) {
    next(error);
  }
});

app.get('/search', async (req, res, next) => {
  try {
    const q = (req.query.q || '').trim();
    let comments = [];

    if (q) {
      const [rows] = await pool.execute(
        'SELECT id, author, content, created_at FROM comments WHERE content LIKE ? ORDER BY created_at DESC, id DESC',
        [`%${q}%`]
      );
      comments = rows;
    }

    res.render('search', { q, comments });
  } catch (error) {
    next(error);
  }
});

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).send('Erro interno do servidor.');
});

(async () => {
  try {
    await initDb();
    app.listen(PORT, () => {
      console.log(`Servidor rodando na porta ${PORT}`);
    });
  } catch (error) {
    console.error('Falha ao iniciar aplicacao:', error);
    process.exit(1);
  }
})();
