import express, { Request, Response } from 'express';
import bcrypt from 'bcrypt';
import { RowDataPacket } from 'mysql2';
import pool, { initDb } from './db';

type AuthBody = {
  username?: string;
  password?: string;
};

const app = express();
app.use(express.json());

const PORT = 8001;
const SALT_ROUNDS = 12;

app.post('/register', async (req: Request<{}, {}, AuthBody>, res: Response): Promise<void> => {
  const { username, password } = req.body;

  if (!username || !password) {
    res.status(400).json({ success: false, message: 'username e password sao obrigatorios' });
    return;
  }

  try {
    const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS);
    await pool.execute('INSERT INTO users (username, password) VALUES (?, ?)', [username, hashedPassword]);
    res.status(201).json({ success: true, message: 'usuario cadastrado com sucesso' });
  } catch (error: any) {
    if (error?.code === 'ER_DUP_ENTRY') {
      res.status(409).json({ success: false, message: 'username ja existe' });
      return;
    }
    res.status(500).json({ success: false, message: 'erro interno do servidor' });
  }
});

app.post('/login', async (req: Request<{}, {}, AuthBody>, res: Response): Promise<void> => {
  const { username, password } = req.body;

  if (!username || !password) {
    res.status(400).json({ success: false, message: 'username e password sao obrigatorios' });
    return;
  }

  try {
    const [rows] = await pool.execute<RowDataPacket[]>('SELECT password FROM users WHERE username = ?', [username]);

    if (rows.length === 0) {
      res.status(401).json({ success: false, message: 'falha na autenticacao' });
      return;
    }

    const valid = await bcrypt.compare(password, rows[0].password as string);

    if (!valid) {
      res.status(401).json({ success: false, message: 'falha na autenticacao' });
      return;
    }

    res.status(200).json({ success: true, message: 'autenticacao realizada com sucesso' });
  } catch {
    res.status(500).json({ success: false, message: 'erro interno do servidor' });
  }
});

initDb()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Servidor executando na porta ${PORT}`);
    });
  })
  .catch((error) => {
    console.error('Falha ao inicializar o banco de dados:', error);
    process.exit(1);
  });
