import os
import pymysql
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "apppass"),
    "database": os.environ.get("DB_NAME", "caso01_auth"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def init_db():
    conn = get_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL
                )
            """)
        conn.commit()


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"status": "error", "message": "username and password are required"}), 400

    username = data["username"].strip()
    password = data["password"]

    if not username or not password:
        return jsonify({"status": "error", "message": "username and password must not be empty"}), 400

    hashed = generate_password_hash(password)

    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed),
                )
            conn.commit()
    except pymysql.err.IntegrityError:
        return jsonify({"status": "error", "message": "username already exists"}), 409
    except Exception:
        return jsonify({"status": "error", "message": "internal server error"}), 500

    return jsonify({"status": "success", "message": "user registered"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"status": "error", "message": "username and password are required"}), 400

    username = data["username"].strip()
    password = data["password"]

    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT password FROM users WHERE username = %s",
                    (username,),
                )
                row = cursor.fetchone()
    except Exception:
        return jsonify({"status": "error", "message": "internal server error"}), 500

    if row is None or not check_password_hash(row["password"], password):
        return jsonify({"status": "error", "message": "invalid credentials"}), 401

    return jsonify({"status": "success", "message": "login successful"}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8001)
