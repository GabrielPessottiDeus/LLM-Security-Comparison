const express = require("express");
const productsRouter = require("./routes/products");
const { initializeDatabase } = require("./db");

const app = express();
const PORT = 8002;

app.use(express.json());
app.use("/products", productsRouter);

app.use((req, res) => {
  res.status(404).json({ error: "Rota não encontrada." });
});

initializeDatabase()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`API iniciada na porta ${PORT}`);
    });
  })
  .catch((error) => {
    console.error("Falha ao inicializar aplicação:", error);
    process.exit(1);
  });
