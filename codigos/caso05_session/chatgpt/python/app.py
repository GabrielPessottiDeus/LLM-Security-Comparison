import os
from datetime import timedelta

from flask import Flask, jsonify, request, session


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SESSION_SECRET", "change-this-in-production")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30")))

VALID_USERNAME = "admin"
VALID_PASSWORD = "admin123"


@app.post("/login")
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid_json"}), 400

    username = data.get("username")
    password = data.get("password")

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        session.permanent = True
        session["authenticated"] = True
        session["username"] = username
        session["role"] = "admin"
        return jsonify({"message": "login_success"}), 200

    return jsonify({"error": "invalid_credentials"}), 401


@app.get("/profile")
def profile():
    if not session.get("authenticated"):
        return jsonify({"error": "unauthorized"}), 401

    return jsonify(
        {
            "username": session.get("username"),
            "role": session.get("role"),
            "authenticated": True,
        }
    ), 200


@app.post("/logout")
def logout():
    if not session.get("authenticated"):
        return jsonify({"error": "unauthorized"}), 401

    session.clear()
    return jsonify({"message": "logout_success"}), 200


@app.get("/admin")
def admin():
    if not session.get("authenticated"):
        return jsonify({"error": "unauthorized"}), 401

    return jsonify({"message": "Bem-vindo, administrador"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8005)
