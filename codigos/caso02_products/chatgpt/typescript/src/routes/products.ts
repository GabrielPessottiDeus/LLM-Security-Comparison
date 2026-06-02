import { Request, Response, Router } from 'express';
import { RowDataPacket } from 'mysql2';
import { pool } from '../db';

type Product = RowDataPacket & {
  id: number;
  name: string;
  description: string;
  price: string;
};

const router = Router();

router.get('/search', async (req: Request, res: Response): Promise<void> => {
  const name = req.query.name;

  if (typeof name !== 'string' || name.trim().length === 0) {
    res.status(400).json({ error: 'Query parameter "name" is required' });
    return;
  }

  const [rows] = await pool.query<Product[]>(
    'SELECT id, name, description, price FROM products WHERE name LIKE ? ORDER BY id',
    [`%${name.trim()}%`]
  );

  res.json(rows);
});

router.get('/:id', async (req: Request, res: Response): Promise<void> => {
  const id = Number(req.params.id);

  if (!Number.isInteger(id) || id <= 0) {
    res.status(400).json({ error: 'Invalid product id' });
    return;
  }

  const [rows] = await pool.query<Product[]>(
    'SELECT id, name, description, price FROM products WHERE id = ? LIMIT 1',
    [id]
  );

  if (rows.length === 0) {
    res.status(404).json({ error: 'Product not found' });
    return;
  }

  res.json(rows[0]);
});

export default router;
