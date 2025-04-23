from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# ✅ Primero defines la función
def inicializar_base_si_falta():
    conn = sqlite3.connect('scan_points.db')
    cursor = conn.cursor()

    # Crear tablas si no existen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            qr_code TEXT PRIMARY KEY,
            username TEXT,
            points INTEGER,
            nombre TEXT,
            apellido TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            qr_code TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_usado TEXT,
            qr_code_destino TEXT,
            puntos_asignados INTEGER,
            timestamp TEXT
        )
    """)

    # Insertar equipos si aún no existen
    cursor.execute("SELECT COUNT(*) FROM teams")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO teams (team_name) VALUES (?)", [
            ("Equipo A",),
            ("Equipo B",),
            ("Equipo C",),
            ("Equipo D",)
        ])

    conn.commit()
    conn.close()

# ✅ Luego la llamas
inicializar_base_si_falta()

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

    token_usado = request.headers.get("X-User-Token")
    cursor.execute(
    "INSERT INTO scan_logs (token_usado, qr_code_destino, puntos_asignados, timestamp) VALUES (?, ?, ?, ?)",
    (token_usado, qr_code, puntos, datetime.now().isoformat())
)

    conn.commit()
    conn.close()

    return jsonify({'message': f'✅ ¡Se agregaron {puntos} puntos al código {qr_code}!'})

# Ranking individual
@app.route('/ranking')
def ranking():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.qr_code, u.nombre, u.apellido, u.points, t.team_name
        FROM users u
        LEFT JOIN team_members tm ON u.qr_code = tm.qr_code
        LEFT JOIN teams t ON tm.team_id = t.id
        ORDER BY u.points DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    def nombre_completo(row):
        nombre = row["nombre"] or ""
        apellido = row["apellido"] or ""
        full = f"{nombre} {apellido}".strip()
        return full if full else row["qr_code"]

    return jsonify([
        {
            "username": nombre_completo(row),
            "points": row["points"],
            "team": row["team_name"] or "Sin equipo"
        } for row in rows
    ])

# Ranking por equipo
@app.route('/ranking_equipos')
def ranking_equipos():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.team_name, COALESCE(SUM(u.points), 0) AS total_points
        FROM teams t
        LEFT JOIN team_members tm ON t.id = tm.team_id
        LEFT JOIN users u ON tm.qr_code = u.qr_code
        GROUP BY t.id
        ORDER BY total_points DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "team": row["team_name"],
            "points": row["total_points"]
        } for row in rows
    ])

@app.route('/ranking_general')
def ranking_general():
    conn   = get_db_connection()
    cursor = conn.cursor()

    # ---------- PARTICIPANTES ----------
    cursor.execute("""
        SELECT u.qr_code, u.nombre, u.apellido, u.points
        FROM users u
        ORDER BY u.points DESC
    """)
    usuarios = cursor.fetchall()

    participantes = [
        (
            idx + 1,
            (row["nombre"] or "") + " " + (row["apellido"] or "") or row["qr_code"],
            row["points"]
        )
        for idx, row in enumerate(usuarios)
    ]

    # ---------- EQUIPOS ----------
    cursor.execute("""
        SELECT t.team_name, COALESCE(SUM(u.points),0) AS total_points
        FROM teams t
        LEFT JOIN team_members tm ON t.id = tm.team_id
        LEFT JOIN users u ON tm.qr_code = u.qr_code
        GROUP BY t.id
        ORDER BY total_points DESC
    """)
    filas_equipo = cursor.fetchall()
    conn.close()

    equipos = [
        (idx + 1, row["team_name"], row["total_points"])
        for idx, row in enumerate(filas_equipo)
    ]

    return render_template(
        "ranking.html",
        participantes=participantes,
        equipos=equipos
    )

@app.route('/registrar_participante', methods=['POST'])
def registrar_participante():
    data = request.get_json()
    qr = data.get("qr")
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    equipo_id = data.get("equipo_id")

    if not qr or not nombre or not apellido or not equipo_id:
        return jsonify({"error": "Faltan datos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifica si existe
    cursor.execute("SELECT * FROM users WHERE qr_code = ?", (qr,))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET nombre = ?, apellido = ? WHERE qr_code = ?", (nombre, apellido, qr))
    else:
        cursor.execute("INSERT INTO users (qr_code, username, points, nombre, apellido) VALUES (?, ?, 0, ?, ?)", (qr, qr, nombre, apellido))

    # Vincular al equipo
    cursor.execute("SELECT * FROM team_members WHERE qr_code = ?", (qr,))
    if cursor.fetchone():
        cursor.execute("UPDATE team_members SET team_id = ? WHERE qr_code = ?", (equipo_id, qr))
    else:
        cursor.execute("INSERT INTO team_members (team_id, qr_code) VALUES (?, ?)", (equipo_id, qr))

    conn.commit()
    conn.close()

    return jsonify({"message": "✅ Participante registrado correctamente"})

@app.route('/eliminar_participante', methods=['POST'])
def eliminar_participante():
    data = request.get_json()
    qr = data.get("qr")

    if not qr:
        return jsonify({"error": "Falta código QR"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM team_members WHERE qr_code = ?", (qr,))
    cursor.execute("DELETE FROM scans WHERE qr_code = ?", (qr,))
    cursor.execute("DELETE FROM users WHERE qr_code = ?", (qr,))

    conn.commit()
    conn.close()

    return jsonify({"message": f"✅ Participante '{qr}' eliminado correctamente"})

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

@app.route('/log_scans')
def log_scans():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.token_usado, l.qr_code_destino, u.nombre, u.apellido, l.puntos_asignados, l.timestamp
        FROM scan_logs l
        LEFT JOIN users u ON l.qr_code_destino = u.qr_code
        ORDER BY l.timestamp DESC
        LIMIT 100
    """)
    registros = cursor.fetchall()
    conn.close()
    return render_template("log_scans.html", registros=registros)

from flask import send_file
import pandas as pd
import io

@app.route('/descargar_log_scans')
def descargar_log_scans():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.token_usado, l.qr_code_destino, u.nombre, u.apellido, l.puntos_asignados, l.timestamp
        FROM scan_logs l
        LEFT JOIN users u ON l.qr_code_destino = u.qr_code
        ORDER BY l.timestamp DESC
    """)
    registros = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(registros, columns=["token_usado", "qr_code_destino", "nombre", "apellido", "puntos_asignados", "timestamp"])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Escaneos')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="log_scans.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)
