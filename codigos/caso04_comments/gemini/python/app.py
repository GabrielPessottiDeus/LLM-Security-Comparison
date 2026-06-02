import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "apppass")
DB_NAME = os.environ.get("DB_NAME", "caso04_comments")

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/', methods=['GET'])
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, author, content, created_at FROM comments ORDER BY created_at DESC")
        comments = cursor.fetchall()
    conn.close()
    return render_template('index.html', comments=comments)

@app.route('/comments', methods=['POST'])
def add_comment():
    author = request.form.get('author')
    content = request.form.get('content')
    
    if author and content:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO comments (author, content) VALUES (%s, %s)",
                (author, content)
            )
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search():
    query_term = request.args.get('q', '')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, author, content, created_at FROM comments WHERE content LIKE %s ORDER BY created_at DESC",
            (f"%{query_term}%",)
        )
        comments = cursor.fetchall()
    conn.close()
    return render_template('search.html', query=query_term, comments=comments)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004)