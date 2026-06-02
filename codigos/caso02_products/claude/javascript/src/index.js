const express = require('express');
const { initialize } = require('./db');
const productsRouter = require('./routes/products');

const app = express();
const PORT = 8002;

app.use(express.json());
app.use('/products', productsRouter);

initialize()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error('Failed to initialize database:', err);
    process.exit(1);
  });
