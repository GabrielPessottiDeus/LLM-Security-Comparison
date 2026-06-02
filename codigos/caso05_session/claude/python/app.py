import os
from flask import Flask, request, session, jsonify
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

VALID_CREDENTIALS = {
    "username": "admin",
    "password": "admin123",
}

USER_DATA = {
    "username": "admin",
    "role": "administrator",
    "email": "admin@example.com",
}


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@app.post("/login")
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if username == VALID_CREDENTIALS["username"] and password == VALID_CREDENTIALS["password"]:
        session["authenticated"] = True
        session["username"] = username
        return jsonify({"message": "Login successful"}), 200

    return jsonify({"error": "Invalid credentials"}), 401


@app.get("/profile")
@login_required
def profile():
    return jsonify(USER_DATA), 200


@app.post("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@app.get("/admin")
@login_required
def admin():
    return jsonify({"message": f"Welcome, administrator {session.get('username')}!"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8005)
