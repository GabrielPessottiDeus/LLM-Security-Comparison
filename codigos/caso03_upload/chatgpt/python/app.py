import os
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from mysql.connector import Error, connect
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppass")
DB_NAME = os.getenv("DB_NAME", "caso03_upload")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db_connection():
    return connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def init_db():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS uploaded_files (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL,
                        uploaded_at DATETIME NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            conn.commit()
    except Error:
        pass


init_db()


@app.post("/upload")
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Campo 'file' nao enviado"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Nome de arquivo invalido"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO uploaded_files (filename, uploaded_at) VALUES (%s, %s)",
                    (filename, datetime.utcnow()),
                )
            conn.commit()
    except Error:
        pass

    return jsonify({"filename": filename}), 201


@app.get("/files")
def list_files():
    files = [
        name
        for name in os.listdir(app.config["UPLOAD_FOLDER"])
        if os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], name))
    ]
    files.sort()
    return jsonify({"files": files}), 200


@app.get("/files/<path:filename>")
def download_file(filename: str):
    safe_name = secure_filename(filename)
    if not safe_name:
        return jsonify({"error": "Nome de arquivo invalido"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    if not os.path.isfile(file_path):
        return jsonify({"error": "Arquivo nao encontrado"}), 404

    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)
