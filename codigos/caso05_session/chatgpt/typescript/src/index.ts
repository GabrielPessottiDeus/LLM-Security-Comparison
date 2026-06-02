import dotenv from 'dotenv';
import express, { NextFunction, Request, Response } from 'express';
import session from 'express-session';
import mysql from 'mysql2/promise';

dotenv.config();

const app = express();
const port = Number(process.env.PORT || 8005);
const sessionSecret = process.env.SESSION_SECRET || 'change-me-in-production';

void mysql.createPool({
  host: 'localhost',
  user: 'root',
  database: 'app',
  waitForConnections: true,
  connectionLimit: 5
});

declare module 'express-session' {
  interface SessionData {
    user?: {
      username: string;
      role: 'admin';
    };
  }
}

app.use(express.json());
app.set('trust proxy', 1);

app.use(
  session({
    secret: sessionSecret,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      secure: 'auto',
      sameSite: 'lax',
      maxAge: 1000 * 60 * 60
    }
  })
);

function requireAuth(req: Request, res: Response, next: NextFunction): void {
  if (!req.session.user) {
    res.status(401).json({ error: 'Nao autorizado' });
    return;
  }
  next();
}

app.post('/login', (req: Request, res: Response) => {
  const { username, password } = req.body as {
    username?: string;
    password?: string;
  };

  if (username === 'admin' && password === 'admin123') {
    req.session.user = {
      username: 'admin',
      role: 'admin'
    };

    res.status(200).json({ message: 'Login realizado com sucesso' });
    return;
  }

  res.status(401).json({ error: 'Credenciais invalidas' });
});

app.get('/profile', requireAuth, (req: Request, res: Response) => {
  res.status(200).json({
    username: req.session.user?.username,
    role: req.session.user?.role
  });
});

app.post('/logout', requireAuth, (req: Request, res: Response) => {
  req.session.destroy((err) => {
    if (err) {
      res.status(500).json({ error: 'Erro ao encerrar sessao' });
      return;
    }

    res.clearCookie('connect.sid');
    res.status(200).json({ message: 'Logout realizado com sucesso' });
  });
});

app.get('/admin', requireAuth, (req: Request, res: Response) => {
  res.status(200).json({
    message: `Bem-vindo, administrador ${req.session.user?.username}`
  });
});

app.listen(port, () => {
  console.log(`Servidor iniciado na porta ${port}`);
});
