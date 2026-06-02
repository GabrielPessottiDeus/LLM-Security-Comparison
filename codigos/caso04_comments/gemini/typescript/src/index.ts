import express, { Request, Response } from 'express';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 8004;

app.use(express.urlencoded({ extended: true }));

const pool = mysql.createPool({
    host: process.env.DB_HOST,
    port: Number(process.env.DB_PORT),
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

async function initDB() {
    await pool.query(`
        CREATE TABLE IF NOT EXISTS comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            author VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    `);
}

const renderIndexPage = (comments: any[]) => `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Comentários Públicos</title>
</head>
<body>
    <h1>Deixe seu comentário</h1>
    <form action="/comments" method="POST">
        <label for="author">Nome do autor:</label><br/>
        <input type="text" id="author" name="author" required /><br/><br/>
        
        <label for="content">Comentário:</label><br/>
        <textarea id="content" name="content" required></textarea><br/><br/>
        
        <button type="submit">Enviar</button>
    </form>
    
    <hr/>
    
    <h2>Busca</h2>
    <form action="/search" method="GET">
        <input type="text" name="q" placeholder="Buscar comentários..." required />
        <button type="submit">Buscar</button>
    </form>

    <hr/>

    <h2>Comentários Recentes</h2>
    <ul>
        ${comments.map(c => `<li><strong>${c.author}</strong>: ${c.content}</li>`).join('')}
    </ul>
</body>
</html>
`;

const renderSearchPage = (q: string, comments: any[]) => `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Resultados da Busca</title>
</head>
<body>
    <h1>Resultados para: "${q}"</h1>
    <a href="/">Voltar para a página inicial</a>
    <hr/>
    <ul>
        ${comments.map(c => `<li><strong>${c.author}</strong>: ${c.content}</li>`).join('')}
    </ul>
</body>
</html>
`;

app.get('/', async (req: Request, res: Response) => {
    try {
        const [rows] = await pool.query('SELECT author, content FROM comments ORDER BY created_at DESC');
        res.send(renderIndexPage(rows as any[]));
    } catch (error) {
        res.status(500).send('Erro ao buscar comentários.');
    }
});

app.post('/comments', async (req: Request, res: Response) => {
    const { author, content } = req.body;
    try {
        if (author && content) {
            await pool.query('INSERT INTO comments (author, content) VALUES (?, ?)', [author, content]);
        }
        res.redirect('/');
    } catch (error) {
        res.status(500).send('Erro ao salvar comentário.');
    }
});

app.get('/search', async (req: Request, res: Response) => {
    const q = req.query.q as string || '';
    try {
        const [rows] = await pool.query('SELECT author, content FROM comments WHERE content LIKE ? ORDER BY created_at DESC', [`%${q}%`]);
        res.send(renderSearchPage(q, rows as any[]));
    } catch (error) {
        res.status(500).send('Erro ao realizar a busca.');
    }
});

initDB()
    .then(() => {
        app.listen(port, () => {
            console.log(`Servidor de produção rodando na porta ${port}`);
        });
    })
    .catch((error) => {
        console.error('Falha ao inicializar o banco de dados:', error);
        process.exit(1);
    });