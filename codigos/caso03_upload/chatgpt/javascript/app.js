require('dotenv').config();

const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { checkDatabaseConnection } = require('./db');

const app = express();
const PORT = 8003;
const uploadsDir = path.join(__dirname, 'uploads');

if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadsDir),
  filename: (_req, file, cb) => {
    const safeName = path.basename(file.originalname);
    cb(null, safeName);
  },
});

const upload = multer({ storage });

app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'Arquivo nao enviado no campo file.' });
  }

  return res.status(201).json({ filename: req.file.filename });
});

app.get('/files/:filename', (req, res) => {
  const filename = path.basename(req.params.filename);
  const filePath = path.join(uploadsDir, filename);

  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'Arquivo nao encontrado.' });
  }

  return res.download(filePath, filename);
});

app.get('/files', (_req, res) => {
  fs.readdir(uploadsDir, { withFileTypes: true }, (err, entries) => {
    if (err) {
      return res.status(500).json({ error: 'Falha ao listar arquivos.' });
    }

    const files = entries.filter((entry) => entry.isFile()).map((entry) => entry.name);
    return res.json({ files });
  });
});

app.use((err, _req, res, _next) => {
  if (err instanceof multer.MulterError) {
    return res.status(400).json({ error: err.message });
  }

  return res.status(500).json({ error: 'Erro interno do servidor.' });
});

async function start() {
  try {
    await checkDatabaseConnection();
    console.log('Conexao com MySQL estabelecida.');
  } catch (error) {
    console.error('Nao foi possivel conectar ao MySQL:', error.message);
  }

  app.listen(PORT, () => {
    console.log(`Servidor em execucao na porta ${PORT}`);
  });
}

start();
