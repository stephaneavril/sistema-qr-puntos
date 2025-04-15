import sqlite3

DB_PATH = "scan_points.db"  # Cambia esto si tu archivo está en otra ruta

def preparar_base():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Agrega columnas 'nombre' y 'apellido' a users si no existen
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN nombre TEXT")
        print("✔️ Columna 'nombre' agregada")
    except sqlite3.OperationalError:
        print("ℹ️ La columna 'nombre' ya existe")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN apellido TEXT")
        print("✔️ Columna 'apellido' agregada")
    except sqlite3.OperationalError:
        print("ℹ️ La columna 'apellido' ya existe")

    # Crear tabla teams
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL
        )
    """)
    print("✔️ Tabla 'teams' verificada/creada")

    # Crear tabla team_members
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            qr_code TEXT NOT NULL,
            FOREIGN KEY (team_id) REFERENCES teams (id),
            FOREIGN KEY (qr_code) REFERENCES users (qr_code)
        )
    """)
    print("✔️ Tabla 'team_members' verificada/creada")

    # Insertar equipos si no existen
    cursor.execute("SELECT COUNT(*) FROM teams")
    if cursor.fetchone()[0] == 0:
        equipos = [('Equipo A',), ('Equipo B',), ('Equipo C',), ('Equipo D',)]
        cursor.executemany("INSERT INTO teams (team_name) VALUES (?)", equipos)
        print("✔️ Equipos A-D insertados")
    else:
        print("ℹ️ Ya existen equipos en la tabla")

    conn.commit()
    conn.close()
    print("✅ Base de datos lista")

if __name__ == "__main__":
    preparar_base()
