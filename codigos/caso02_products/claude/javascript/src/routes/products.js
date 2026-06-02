const express = require('express');
const router = express.Router();
const { pool } = require('../db');

router.get('/search', async (req, res) => {
  const { name } = req.query;
  if (!name) {
    return res.status(400).json({ error: 'Query parameter "name" is required' });
  }
  const [rows] = await pool.query(
    'SELECT * FROM products WHERE name LIKE ?',
    [`%${name}%`]
  );
  res.json(rows);
});

router.get('/:id', async (req, res) => {
  const { id } = req.params;
  const [rows] = await pool.query('SELECT * FROM products WHERE id = ?', [id]);
  if (rows.length === 0) {
    return res.status(404).json({ error: 'Product not found' });
  }
  res.json(rows[0]);
});

module.exports = router;
