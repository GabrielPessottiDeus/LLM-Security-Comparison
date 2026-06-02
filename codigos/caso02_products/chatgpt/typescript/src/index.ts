import express, { NextFunction, Request, Response } from 'express';
import { initDatabase } from './db';
import productsRouter from './routes/products';

const app = express();
const PORT = 8002;

app.use(express.json());
app.use('/products', productsRouter);

app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
  console.error('Unexpected error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

async function startServer(): Promise<void> {
  await initDatabase();
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

startServer().catch((err) => {
  console.error('Failed to start application:', err);
  process.exit(1);
});
