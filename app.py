from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('scan_points.db')
    conn.row_factory = sqlite3.Row
    return conn

# Mostrar la interfaz web
@app.route('/')
def home():
    return render_template('index.html')

# Registrar escaneo
@app.route('/scan', methods=['POST'])
def scan_qr():
    data = request.get_json()
    qr_code = data.get('qr_code')
    username = data.get('username')

    if not qr_code or not username:
        return jsonify({'error': 'Faltan datos'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Crear usuario si no existe
    cursor.execute("SELECT * FROM users WHERE qr_code = ?", (qr_code,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (qr_code, username, points) VALUES (?, ?, 0)", (qr_code, username))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE qr_code = ?", (qr_code,))
        user = cursor.fetchone()

    # Sumar puntos
    cursor.execute("UPDATE users SET points = points + 10 WHERE qr_code = ?", (qr_code,))

    # Registrar escaneo
    cursor.execute("INSERT INTO scans (qr_code, timestamp) VALUES (?, ?)", (qr_code, datetime.now()))

    conn.commit()
    conn.close()

    return jsonify({'message': f'✅ Código {qr_code} escaneado. ¡10 puntos sumados a {username}!'})

# Ranking por usuario
@app.route('/ranking')
def ranking():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, points FROM users ORDER BY points DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"username": row["username"], "points": row["points"]} for row in rows])

# Ranking por equipo
@app.route('/ranking_equipos')
def ranking_equipos():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT teams.team_name, SUM(users.points) as total_points
        FROM users
        JOIN team_members ON users.qr_code = team_members.qr_code
        JOIN teams ON team_members.team_id = teams.id
        GROUP BY teams.id
        ORDER BY total_points DESC
    ''')

    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"team": row["team_name"], "points": row["total_points"]} for row in rows])
