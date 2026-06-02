import express, { Request, Response } from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { config } from './config';
import { checkDatabaseConnection } from './db';

const app = express();
const uploadsDir = path.resolve(process.cwd(), 'uploads');

if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (_req, file, cb) => {
    const safeName = file.originalname.replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, `${Date.now()}-${safeName}`);
  }
});

const upload = multer({ storage });

app.post('/upload', upload.single('file'), (req: Request, res: Response) => {
  if (!req.file) {
    return res.status(400).json({ error: 'Arquivo nao enviado no campo "file".' });
  }

  return res.status(201).json({ filename: req.file.filename });
});

app.get('/files', async (_req: Request, res: Response) => {
  try {
    const entries = await fs.promises.readdir(uploadsDir, { withFileTypes: true });
    const files = entries.filter((entry) => entry.isFile()).map((entry) => entry.name);
    return res.json({ files });
  } catch {
    return res.status(500).json({ error: 'Falha ao listar arquivos.' });
  }
});

app.get('/files/:filename', async (req: Request, res: Response) => {
  const { filename } = req.params;

  if (filename.includes('/') || filename.includes('\\')) {
    return res.status(400).json({ error: 'Nome de arquivo invalido.' });
  }

  const filePath = path.resolve(uploadsDir, filename);

  if (!filePath.startsWith(uploadsDir + path.sep) && filePath !== uploadsDir) {
    return res.status(400).json({ error: 'Acesso negado ao arquivo.' });
  }

  try {
    await fs.promises.access(filePath, fs.constants.R_OK);
    return res.download(filePath, filename);
  } catch {
    return res.status(404).json({ error: 'Arquivo nao encontrado.' });
  }
});

app.use((_req: Request, res: Response) => {
  res.status(404).json({ error: 'Rota nao encontrada.' });
});

const start = async (): Promise<void> => {
  try {
    await checkDatabaseConnection();
    app.listen(config.port, () => {
      console.log(`Servidor iniciado na porta ${config.port}`);
    });
  } catch (error) {
    console.error('Falha ao conectar no MySQL.', error);
    process.exit(1);
  }
};

void start();
