import express, { Request, Response } from 'express';
import pool, { initDb } from './db';
import { homePage, searchPage, Comment } from './templates';

const app = express();
const PORT = 8004;

app.use(express.urlencoded({ extended: false }));

app.get('/', async (_req: Request, res: Response) => {
  const [rows] = await pool.execute(
    'SELECT id, author, content, created_at FROM comments ORDER BY created_at DESC'
  );
  res.send(homePage(rows as Comment[]));
});

app.post('/comments', async (req: Request, res: Response) => {
  const { author, content } = req.body as { author: string; content: string };
  await pool.execute(
    'INSERT INTO comments (author, content) VALUES (?, ?)',
    [author, content]
  );
  res.redirect('/');
});

app.get('/search', async (req: Request, res: Response) => {
  const q = (req.query.q as string) || '';
  const [rows] = await pool.execute(
    'SELECT id, author, content, created_at FROM comments WHERE content LIKE ? ORDER BY created_at DESC',
    [`%${q}%`]
  );
  res.send(searchPage(q, rows as Comment[]));
});

async function main() {
  await initDb();
  app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

main().catch((err) => {
  console.error('Failed to start:', err);
  process.exit(1);
});
