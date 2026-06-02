import { Router, Request, Response } from 'express';
import { pool } from '../db';

const router = Router();

router.get('/search', async (req: Request, res: Response): Promise<void> => {
  const name = req.query.name as string | undefined;

  if (!name) {
    res.status(400).json({ error: 'Query parameter "name" is required' });
    return;
  }

  const [rows] = await pool.execute(
    'SELECT * FROM products WHERE name LIKE ?',
    [`%${name}%`]
  );

  res.json(rows);
});

router.get('/:id', async (req: Request, res: Response): Promise<void> => {
  const id = Number(req.params.id);

  if (!Number.isInteger(id) || id <= 0) {
    res.status(400).json({ error: 'Invalid product id' });
    return;
  }

  const [rows] = await pool.execute(
    'SELECT * FROM products WHERE id = ?',
    [id]
  );

  const products = rows as unknown[];

  if (products.length === 0) {
    res.status(404).json({ error: 'Product not found' });
    return;
  }

  res.json(products[0]);
});

export default router;
