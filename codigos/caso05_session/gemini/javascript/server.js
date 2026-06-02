const express = require('express');
const session = require('express-session');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8005;

app.use(express.json());

app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
        httpOnly: true,
        maxAge: 1000 * 60 * 60 * 24 // 24 horas
    }
}));

const requireAuth = (req, res, next) => {
    if (req.session && req.session.user) {
        next();
    } else {
        res.status(401).json({ error: 'Não autorizado' });
    }
};

app.post('/login', (req, res) => {
    const { username, password } = req.body;

    if (username === 'admin' && password === 'admin123') {
        req.session.user = { username: 'admin', role: 'admin' };
        return res.json({ message: 'Login realizado com sucesso' });
    }

    res.status(401).json({ error: 'Credenciais inválidas' });
});

app.get('/profile', requireAuth, (req, res) => {
    res.json({ user: req.session.user });
});

app.post('/logout', (req, res) => {
    req.session.destroy(err => {
        if (err) {
            return res.status(500).json({ error: 'Falha ao encerrar a sessão' });
        }
        res.clearCookie('connect.sid');
        res.json({ message: 'Logout realizado com sucesso' });
    });
});

app.get('/admin', requireAuth, (req, res) => {
    res.json({ message: 'Bem-vindo ao painel do administrador!' });
});

app.listen(PORT, () => {
    console.log(`Servidor executando em ambiente de ${process.env.NODE_ENV} na porta ${PORT}`);
});