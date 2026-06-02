const express = require('express');
const session = require('express-session');

const app = express();
const PORT = 8005;

const VALID_USERNAME = 'admin';
const VALID_PASSWORD = 'admin123';

const sessionSecret = process.env.SESSION_SECRET;
if (!sessionSecret) {
  throw new Error('SESSION_SECRET is required in production.');
}

app.set('trust proxy', 1);
app.use(express.json());

app.use(
  session({
    name: 'sid',
    secret: sessionSecret,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge: 30 * 60 * 1000
    }
  })
);

function requireAuth(req, res, next) {
  if (!req.session || !req.session.user) {
    return res.status(401).json({ error: 'Nao autorizado' });
  }
  next();
}

app.post('/login', (req, res) => {
  const { username, password } = req.body || {};

  if (!username || !password) {
    return res.status(400).json({ error: 'username e password sao obrigatorios' });
  }

  if (username !== VALID_USERNAME || password !== VALID_PASSWORD) {
    return res.status(401).json({ error: 'Credenciais invalidas' });
  }

  req.session.regenerate((err) => {
    if (err) {
      return res.status(500).json({ error: 'Falha ao iniciar sessao' });
    }

    req.session.user = {
      id: 1,
      username: VALID_USERNAME,
      role: 'admin'
    };

    return res.status(200).json({ message: 'Login realizado com sucesso' });
  });
});

app.get('/profile', requireAuth, (req, res) => {
  res.status(200).json({ user: req.session.user });
});

app.post('/logout', requireAuth, (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ error: 'Falha ao encerrar sessao' });
    }

    res.clearCookie('sid');
    return res.status(200).json({ message: 'Logout realizado com sucesso' });
  });
});

app.get('/admin', requireAuth, (req, res) => {
  res.status(200).json({ message: `Bem-vindo, administrador ${req.session.user.username}` });
});

app.use((req, res) => {
  res.status(404).json({ error: 'Rota nao encontrada' });
});

app.listen(PORT, () => {
  console.log(`Servidor em execucao na porta ${PORT}`);
});
