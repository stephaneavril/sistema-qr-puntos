# init_teams.py
"""
Crea la tabla 'teams' (si no existe) e inserta los equipos por defecto.
Ejecútalo una sola vez:   python init_teams.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("scan_points.db")

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# 1️⃣  Asegúrate de que la tabla exista
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS teams (
        id        INTEGER PRIMARY KEY,
        team_name TEXT NOT NULL UNIQUE
    )
    """
)

# 2️⃣  Inserta los equipos por defecto
equipos = [
    (1, "Equipo A"),
    (2, "Equipo B"),
    (3, "Equipo C"),
    (4, "Equipo D"),
]
cur.executemany(
    "INSERT OR IGNORE INTO teams (id, team_name) VALUES (?, ?)",
    equipos,
)

conn.commit()
conn.close()
print("✅  Equipos creados / actualizados correctamente.")
