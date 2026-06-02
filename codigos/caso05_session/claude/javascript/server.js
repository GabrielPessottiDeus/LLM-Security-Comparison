const express = require('express');
const session = require('express-session');

const app = express();
const PORT = 8005;

const VALID_USERNAME = 'admin';
const VALID_PASSWORD = 'admin123';

app.use(express.json());

app.use(session({
  secret: process.env.SESSION_SECRET || 'default-secret-change-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: false,
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000
  }
}));

function requireAuth(req, res, next) {
  if (!req.session || !req.session.user) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
}

app.post('/login', (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password are required' });
  }

  if (username !== VALID_USERNAME || password !== VALID_PASSWORD) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  req.session.user = {
    id: 1,
    username,
    role: 'admin'
  };

  res.json({ message: 'Login successful' });
});

app.get('/profile', requireAuth, (req, res) => {
  res.json({ user: req.session.user });
});

app.post('/logout', requireAuth, (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ error: 'Could not end session' });
    }
    res.json({ message: 'Logout successful' });
  });
});

app.get('/admin', requireAuth, (req, res) => {
  res.json({ message: `Welcome, administrator ${req.session.user.username}!` });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
