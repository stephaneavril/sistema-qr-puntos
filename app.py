from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('scan_points.db')
    conn.row_factory = sqlite3.Row
    return conn

# Página principal
@app.route('/')
def home():
    return render_template('index.html')

# Escaneo de QR
@app.route('/scan', methods=['POST'])
def scan_qr():
    data = request.get_json()
    qr_code = data.get('qr_code')
    puntos = data.get('puntos')

    # Validación básica
    if not qr_code or not isinstance(puntos, int):
        return jsonify({'error': 'Datos inválidos ❌'}), 400

    # Validar formato y rango
    if not qr_code.startswith("codigo_qr_"):
        return jsonify({'error': 'Formato de QR inválido ❌'}), 400

    try:
        numero = int(qr_code.split("_")[-1])
    except ValueError:
        return jsonify({'error': 'QR inválido ❌'}), 400

    if numero < 1 or numero > 50:
        return jsonify({'error': f'QR {qr_code} fuera de rango (1-50) ❌'}), 400

    # Conexión a la base
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar si fue escaneado hace menos de 1 minuto
    cursor.execute("SELECT timestamp FROM scans WHERE qr_code = ? ORDER BY timestamp DESC LIMIT 1", (qr_code,))
    last_scan = cursor.fetchone()

    if last_scan:
        last_time = datetime.fromisoformat(last_scan["timestamp"])
        now = datetime.now()
        if now - last_time < timedelta(minutes=1):
            segundos_restantes = 60 - int((now - last_time).total_seconds())
            conn.close()
            return jsonify({'error': f'⏱️ Este código ya fue escaneado. Intenta en {segundos_restantes}s'}), 429

    # Crear usuario si no existe
    cursor.execute("SELECT * FROM users WHERE qr_code = ?", (qr_code,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (qr_code, username, points) VALUES (?, ?, 0)", (qr_code, qr_code))
        conn.commit()

    # Sumar puntos
    cursor.execute("UPDATE users SET points = points + ? WHERE qr_code = ?", (puntos, qr_code))

    # Registrar escaneo
    cursor.execute("INSERT INTO scans (qr_code, timestamp) VALUES (?, ?)", (qr_code, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return jsonify({'message': f'✅ ¡Se agregaron {puntos} puntos al código {qr_code}!'})

# Ranking individual
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

@app.route('/ranking_general')
def ranking_general():
    return render_template('ranking.html')

@app.route('/reset', methods=['POST'])
def reset_all():
    data = request.get_json()
    token = data.get("token")
    
    # 🔐 Cambia esto por tu clave personal
    TOKEN_SECRETO = "soybatman"

    if token != TOKEN_SECRETO:
        return jsonify({'error': 'Token inválido ❌'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM scans")
    conn.commit()
    conn.close()

    return jsonify({'message': '✅ Todos los datos han sido eliminados correctamente'})

@app.route('/admin_panel')
def admin_panel():
    return render_template('admin_panel.html')


if __name__ == '__main__':
    app.run(debug=True)
