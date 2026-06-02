const express = require("express");
const { pool } = require("../db");

const router = express.Router();

router.get("/search", async (req, res) => {
  const { name } = req.query;

  if (!name || typeof name !== "string" || name.trim() === "") {
    return res.status(400).json({ error: 'Query string "name" is obrigatória.' });
  }

  try {
    const [rows] = await pool.query(
      "SELECT id, name, description, price FROM products WHERE name LIKE ? ORDER BY id ASC",
      [`%${name}%`]
    );
    return res.json(rows);
  } catch (error) {
    return res.status(500).json({ error: "Erro ao buscar produtos." });
  }
});

router.get("/:id", async (req, res) => {
  const id = Number.parseInt(req.params.id, 10);
  if (Number.isNaN(id) || id <= 0) {
    return res.status(400).json({ error: "ID inválido." });
  }

  try {
    const [rows] = await pool.query(
      "SELECT id, name, description, price FROM products WHERE id = ?",
      [id]
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: "Produto não encontrado." });
    }
    return res.json(rows[0]);
  } catch (error) {
    return res.status(500).json({ error: "Erro ao buscar produto." });
  }
});

module.exports = router;
