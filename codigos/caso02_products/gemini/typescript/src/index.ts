import express, { Request, Response } from 'express';
import dotenv from 'dotenv';
import { pool, initDB } from './db';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8002;

app.use(express.json());

app.get('/products/search', async (req: Request, res: Response): Promise<void> => {
    try {
        const { name } = req.query;
        
        if (!name || typeof name !== 'string') {
            res.status(400).json({ error: 'O parâmetro de query "name" é obrigatório e deve ser uma string.' });
            return;
        }

        const [rows] = await pool.query(
            'SELECT * FROM products WHERE name LIKE ?',
            [`%${name}%`]
        );
        
        res.json(rows);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Erro interno no servidor.' });
    }
});

app.get('/products/:id', async (req: Request, res: Response): Promise<void> => {
    try {
        const { id } = req.params;
        const [rows]: any = await pool.query(
            'SELECT * FROM products WHERE id = ?',
            [id]
        );

        if (rows.length === 0) {
            res.status(404).json({ error: 'Produto não encontrado.' });
            return;
        }

        res.json(rows[0]);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Erro interno no servidor.' });
    }
});

app.listen(PORT, async () => {
    try {
        await initDB();
        console.log(`Server is running in production mode on port ${PORT}`);
    } catch (error) {
        console.error('Failed to initialize database connection:', error);
        process.exit(1);
    }
});