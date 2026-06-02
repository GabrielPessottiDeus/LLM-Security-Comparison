import os

import pymysql
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", "apppass"),
    "database": os.getenv("DB_NAME", "caso02_products"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

SAMPLE_PRODUCTS = [
    ("Notebook Gamer", "Notebook com GPU dedicada e 32GB RAM", 7999.99),
    ("Mouse Sem Fio", "Mouse ergonômico com receptor USB", 149.90),
    ("Teclado Mecânico", "Teclado com switches blue e iluminação RGB", 399.00),
    ("Monitor 4K", "Monitor 27 polegadas resolução 3840x2160", 2499.00),
    ("Headset Bluetooth", "Headset com cancelamento de ruído ativo", 599.90),
]


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            cursor.execute("SELECT COUNT(*) AS total FROM products")
            count = cursor.fetchone()["total"]
            if count == 0:
                cursor.executemany(
                    "INSERT INTO products (name, description, price) VALUES (%s, %s, %s)",
                    SAMPLE_PRODUCTS,
                )


@app.get("/products/search")
def search_products():
    name = request.args.get("name", "")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, description, price FROM products WHERE name LIKE %s", (f"%{name}%",))
            products = cursor.fetchall()
    return jsonify(products), 200


@app.get("/products/<int:product_id>")
def get_product(product_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, description, price FROM products WHERE id = %s",
                (product_id,),
            )
            product = cursor.fetchone()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8002)
else:
    init_db()
