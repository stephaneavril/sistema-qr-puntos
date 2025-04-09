import sqlite3

def crear_base_datos():
    conn = sqlite3.connect('scan_points.db')
    cursor = conn.cursor()

    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            points INTEGER DEFAULT 0
        )
    ''')

    # Tabla de códigos QR
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qrcodes (
            id TEXT PRIMARY KEY
        )
    ''')

    # Tabla de escaneos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            user_id INTEGER,
            qr_code_id TEXT,
            timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Base de datos creada con éxito")

crear_base_datos()
