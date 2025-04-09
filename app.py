from flask import Flask, request, jsonify, render_template
from flask_cors import CORS  # 👈 Importa la extensión
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 👈 Esto permite que tu HTML se comunique con Flask

# Función para conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect('scan_points.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ruta para escanear un QR y sumar puntos
@app.route('/scan', methods=['POST'])
def scan_qr():
    data = request.get_json()

    username = data.get('username')
    qr_code = data.get('qr_code')

    if not username or not qr_code:
        return jsonify({'error': 'Faltan datos'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Buscar usuario o crearlo si no existe
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (username, points) VALUES (?, ?)", (username, 0))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

    user_id = user["id"]

    # Verificar si ya escaneó ese código
    cursor.execute("SELECT * FROM scans WHERE user_id = ? AND qr_code_id = ?", (user_id, qr_code))
    already_scanned = cursor.fetchone()

    if already_scanned:
        conn.close()
        return jsonify({'message': 'Este código ya fue escaneado por este usuario'}), 200

    # Registrar escaneo y sumar puntos
    cursor.execute("INSERT OR IGNORE INTO qrcodes (id) VALUES (?)", (qr_code,))
    cursor.execute("INSERT INTO scans (user_id, qr_code_id, timestamp) VALUES (?, ?, ?)", (user_id, qr_code, datetime.now()))
    cursor.execute("UPDATE users SET points = points + 10 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Puntos sumados exitosamente ✅'}), 200

# Ruta para ver puntos de un usuario
@app.route('/points/<username>', methods=['GET'])
def get_points(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT points FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({'username': username, 'points': row[0]})
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404

@app.route('/ranking')
def ranking():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    ranking = [{"username": row[0], "points": row[1]} for row in rows]
    return jsonify(ranking)

# Iniciar el servidor
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
