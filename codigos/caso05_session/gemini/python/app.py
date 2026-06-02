import os
from flask import Flask, request, jsonify, session
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_change_in_production')
app.config['SESSION_COOKIE_HTTPONLY'] = True

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Credenciais ausentes"}), 400
        
    if data['username'] == 'admin' and data['password'] == 'admin123':
        session['user'] = data['username']
        return jsonify({"message": "Login realizado com sucesso"}), 200
        
    return jsonify({"error": "Credenciais inválidas"}), 401

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    return jsonify({
        "username": session['user'],
        "status": "ativo"
    }), 200

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"message": "Logout realizado com sucesso"}), 200

@app.route('/admin', methods=['GET'])
@login_required
def admin():
    return jsonify({"message": "Bem-vindo ao administrador, admin!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8005, debug=False)