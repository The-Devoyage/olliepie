import sqlite3
import os

def get_db_connection():
    db = os.getenv('DATABASE_URL')

    if not db:
        print("No database URL found. Exiting get_db_connection function.")
        exit()

    if db.startswith("sqlite://"):
        db = db[9:]

    conn = sqlite3.connect(db)
    c = conn.cursor()

    return conn, c

