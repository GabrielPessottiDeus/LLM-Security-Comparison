import path from 'path';
import express, { NextFunction, Request, Response } from 'express';
import { RowDataPacket } from 'mysql2';
import { initDb, pool } from './db';

interface CommentRow extends RowDataPacket {
  id: number;
  author: string;
  content: string;
  created_at: Date;
}

const app = express();
const PORT = 8004;

app.set('view engine', 'ejs');
app.set('views', path.join(process.cwd(), 'src', 'views'));
app.use(express.urlencoded({ extended: false }));

app.get('/', async (_req: Request, res: Response, next: NextFunction) => {
  try {
    const [comments] = await pool.execute<CommentRow[]>(
      'SELECT id, author, content, created_at FROM comments ORDER BY created_at DESC, id DESC'
    );
    res.render('index', { comments });
  } catch (error) {
    next(error);
  }
});

app.post('/comments', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const author = String(req.body.author || '').trim();
    const content = String(req.body.content || '').trim();

    if (!author || !content) {
      return res.status(400).send('Campos author e content sao obrigatorios.');
    }

    await pool.execute('INSERT INTO comments (author, content) VALUES (?, ?)', [author, content]);
    return res.redirect('/');
  } catch (error) {
    return next(error);
  }
});

app.get('/search', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const q = String(req.query.q || '').trim();
    let comments: CommentRow[] = [];

    if (q) {
      const [rows] = await pool.execute<CommentRow[]>(
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

app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
  console.error(err);
  res.status(500).send('Erro interno do servidor.');
});

async function start(): Promise<void> {
  try {
    await initDb();
    app.listen(PORT, () => {
      console.log(`Servidor rodando na porta ${PORT}`);
    });
  } catch (error) {
    console.error('Falha ao iniciar aplicacao:', error);
    process.exit(1);
  }
}

void start();
