import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pymysql
import pymysql.cursors
from datetime import datetime

app = Flask(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'appuser'),
        password=os.environ.get('DB_PASSWORD', 'apppass'),
        database=os.environ.get('DB_NAME', 'caso03_upload'),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def init_db():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    uploaded_at DATETIME NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_DIR, filename))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO files (filename, original_filename, uploaded_at) VALUES (%s, %s, %s)',
                (filename, file.filename, datetime.utcnow()),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'filename': filename}), 201


@app.route('/files/<filename>', methods=['GET'])
def download(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


@app.route('/files', methods=['GET'])
def list_files():
    entries = [
        f for f in os.listdir(UPLOAD_DIR)
        if os.path.isfile(os.path.join(UPLOAD_DIR, f))
    ]
    return jsonify({'files': entries})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8003)
