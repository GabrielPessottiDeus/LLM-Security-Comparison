import os
import pymysql
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppass")
DB_NAME = os.getenv("DB_NAME", "caso02_products")

def get_db_connection(use_database=True):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if use_database else None,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    conn = get_db_connection(use_database=False)
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.commit()
    conn.close()

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT,
                description TEXT,
                price DECIMAL(10, 2)
            )
        """)
        
        cursor.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()['count'] == 0:
            sample_products = [
                ("Notebook", "Notebook ultrafino de 15 polegadas", 4500.00),
                ("Smartphone", "Smartphone com câmera de 108MP", 2500.00),
                ("Monitor", "Monitor 4K de 27 polegadas", 1800.00),
                ("Teclado Mecânico", "Teclado mecânico RGB switch blue", 350.00),
                ("Mouse Sem Fio", "Mouse ergonômico com bateria recarregável", 150.00)
            ]
            cursor.executemany(
                "INSERT INTO products (name, description, price) VALUES (%s, %s, %s)",
                sample_products
            )
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

@app.route('/products/search', methods=['GET'])
def search_products():
    search_term = request.args.get('name', '')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM products WHERE name LIKE %s", (f"%{search_term}%",))
        products = cursor.fetchall()
    conn.close()
    return jsonify(products)

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
    conn.close()
    
    if product:
        return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)