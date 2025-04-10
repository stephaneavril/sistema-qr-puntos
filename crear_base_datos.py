import sqlite3

def crear_base_datos():
    conn = sqlite3.connect('scan_points.db')
    cursor = conn.cursor()

    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT UNIQUE,
            username TEXT,
            points INTEGER DEFAULT 0
        )
    ''')

    # Tabla de escaneos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT,
            timestamp TEXT
        )
    ''')

    # Tabla de equipos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT
        )
    ''')

    # Tabla de miembros de equipo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            qr_code TEXT,
            team_id INTEGER
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Base de datos creada con las nuevas tablas.")

crear_base_datos()
