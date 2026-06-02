import express from 'express';
import { initDatabase } from './db';
import productsRouter from './routes/products';

const app = express();
const PORT = 8002;

app.use(express.json());
app.use('/products', productsRouter);

async function main(): Promise<void> {
  await initDatabase();
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

main().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
