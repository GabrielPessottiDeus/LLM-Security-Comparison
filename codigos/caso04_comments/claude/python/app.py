import os
import pymysql
from flask import Flask, request, redirect, render_template, url_for

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "apppass"),
    "database": os.environ.get("DB_NAME", "caso04_comments"),
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def init_db():
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    author VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()


@app.route("/")
def index():
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, author, content, created_at FROM comments ORDER BY created_at DESC")
            comments = cur.fetchall()
    return render_template("index.html", comments=comments)


@app.route("/comments", methods=["POST"])
def add_comment():
    author = request.form.get("author", "").strip()
    content = request.form.get("content", "").strip()
    if author and content:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO comments (author, content) VALUES (%s, %s)",
                    (author, content),
                )
            conn.commit()
    return redirect(url_for("index"))


@app.route("/search")
def search():
    q = request.args.get("q", "")
    comments = []
    if q:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, author, content, created_at FROM comments WHERE content LIKE %s ORDER BY created_at DESC",
                    (f"%{q}%",),
                )
                comments = cur.fetchall()
    return render_template("search.html", comments=comments, query=q)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8004)
