import express, { Request, Response, NextFunction } from 'express';
import session from 'express-session';

declare module 'express-session' {
  interface SessionData {
    user: {
      username: string;
    };
  }
}

const app = express();
const PORT = 8005;

app.use(express.json());

app.use(
  session({
    secret: process.env.SESSION_SECRET || 'segredo_padrao_para_desenvolvimento',
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: process.env.NODE_ENV === 'production' && process.env.HTTPS_ENABLED === 'true',
      maxAge: 3600000 
    }
  })
);

const requireAuth = (req: Request, res: Response, next: NextFunction) => {
  if (req.session && req.session.user) {
    next();
  } else {
    res.status(401).json({ error: 'Não autorizado.' });
  }
};

app.post('/login', (req: Request, res: Response) => {
  const { username, password } = req.body;

  if (username === 'admin' && password === 'admin123') {
    req.session.user = { username };
    return res.status(200).json({ message: 'Autenticado com sucesso.' });
  }

  return res.status(401).json({ error: 'Credenciais inválidas.' });
});

app.get('/profile', requireAuth, (req: Request, res: Response) => {
  return res.status(200).json({ user: req.session.user });
});

app.post('/logout', (req: Request, res: Response) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ error: 'Erro ao encerrar a sessão.' });
    }
    res.clearCookie('connect.sid');
    return res.status(200).json({ message: 'Logout realizado com sucesso.' });
  });
});

app.get('/admin', requireAuth, (req: Request, res: Response) => {
  return res.status(200).json({ message: 'Bem-vindo ao painel do administrador!' });
});

app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});