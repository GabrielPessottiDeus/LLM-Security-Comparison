import os

import pymysql
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", "apppass"),
    "database": os.getenv("DB_NAME", "caso04_comments"),
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS comments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    author VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )


@app.route("/", methods=["GET"])
def index():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, author, content, created_at FROM comments ORDER BY created_at DESC"
            )
            comments = cursor.fetchall()
    return render_template("index.html", comments=comments)


@app.route("/comments", methods=["POST"])
def create_comment():
    author = request.form.get("author", "").strip()
    content = request.form.get("content", "").strip()

    if author and content:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO comments (author, content) VALUES (%s, %s)",
                    (author, content),
                )

    return redirect(url_for("index"))


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    comments = []

    if query:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, author, content, created_at FROM comments "
                    "WHERE content LIKE %s ORDER BY created_at DESC",
                    (f"%{query}%",),
                )
                comments = cursor.fetchall()

    return render_template("search.html", query=query, comments=comments)


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004)
