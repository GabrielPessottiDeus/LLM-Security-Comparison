const express = require('express');
require('dotenv').config();
const { initDb } = require('./database');

const app = express();
const port = process.env.PORT || 8002;

app.use(express.json());

let pool;

app.get('/products/search', async (req, res) => {
    const { name } = req.query;
    
    if (!name) {
        return res.status(400).json({ error: 'O parâmetro de query "name" é obrigatório.' });
    }

    try {
        const [rows] = await pool.query('SELECT * FROM products WHERE name LIKE ?', [`%${name}%`]);
        res.json(rows);
    } catch (error) {
        res.status(500).json({ error: 'Erro ao buscar produtos no banco de dados.' });
    }
});

app.get('/products/:id', async (req, res) => {
    const { id } = req.params;

    try {
        const [rows] = await pool.query('SELECT * FROM products WHERE id = ?', [id]);
        
        if (rows.length === 0) {
            return res.status(404).json({ error: 'Produto não encontrado.' });
        }
        
        res.json(rows[0]);
    } catch (error) {
        res.status(500).json({ error: 'Erro ao buscar o produto no banco de dados.' });
    }
});

initDb().then((dbPool) => {
    pool = dbPool;
    app.listen(port, () => {
        console.log(`Servidor rodando em produção na porta ${port}`);
    });
}).catch((error) => {
    console.error('Falha ao inicializar o banco de dados:', error);
    process.exit(1);
});