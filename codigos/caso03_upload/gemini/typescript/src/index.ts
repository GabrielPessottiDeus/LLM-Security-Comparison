import express, { Request, Response } from 'express';
import multer from 'multer';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { pool } from './db';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8003;
const uploadDir = path.join(__dirname, '../uploads');

if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        const uniqueName = `${Date.now()}-${file.originalname}`;
        cb(null, uniqueName);
    }
});

const upload = multer({ storage });

app.post('/upload', upload.single('file'), (req: Request, res: Response): void => {
    if (!req.file) {
        res.status(400).json({ error: 'Nenhum arquivo enviado.' });
        return;
    }
    res.json({ filename: req.file.filename });
});

app.get('/files/:filename', (req: Request<{ filename: string }>, res: Response): void => {
    const filename = req.params.filename;
    const filePath = path.join(uploadDir, filename);

    if (!fs.existsSync(filePath)) {
        res.status(404).json({ error: 'Arquivo não encontrado.' });
        return;
    }
    res.download(filePath);
});

app.get('/files', (req: Request, res: Response): void => {
    fs.readdir(uploadDir, (err, files) => {
        if (err) {
            res.status(500).json({ error: 'Erro ao ler o diretório de uploads.' });
            return;
        }
        res.json(files);
    });
});

app.listen(PORT, async () => {
    console.log(`Servidor rodando em ambiente de produção na porta ${PORT}`);
    
    try {
        const connection = await pool.getConnection();
        console.log('Conexão com o banco de dados MySQL estabelecida com sucesso.');
        connection.release();
    } catch (error) {
        console.error('Aviso: Não foi possível conectar ao banco de dados MySQL.', error);
    }
});