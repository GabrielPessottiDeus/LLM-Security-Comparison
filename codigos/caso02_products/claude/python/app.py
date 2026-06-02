import os
import pymysql
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "apppass"),
    "database": os.environ.get("DB_NAME", "caso02_products"),
    "cursorclass": pymysql.cursors.DictCursor,
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
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL
                )
            """)
            cursor.execute("SELECT COUNT(*) AS total FROM products")
            row = cursor.fetchone()
            if row["total"] == 0:
                cursor.executemany(
                    "INSERT INTO products (name, description, price) VALUES (%s, %s, %s)",
                    SAMPLE_PRODUCTS,
                )
        conn.commit()
    finally:
        conn.close()


@app.route("/products/search", methods=["GET"])
def search_products():
    name = request.args.get("name", "")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM products WHERE name LIKE %s",
                (f"%{name}%",),
            )
            products = cursor.fetchall()
    finally:
        conn.close()
    return jsonify(products)


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
    finally:
        conn.close()
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8002)
