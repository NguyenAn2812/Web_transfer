# src/utils/db.py
import sqlite3
from flask import g
from flask import current_app as app

DB_PATH = 'app.db'  # có thể giữ như cũ

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db(flask_app):
    with flask_app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS devices (
            session_id TEXT PRIMARY KEY,
            device_name TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            display_name TEXT,
            title TEXT,
            uploader_id TEXT,
            uploader_name TEXT,
            is_public INTEGER,
            receiver_id TEXT,
            upload_time TEXT,
            file_path TEXT,
            file_type TEXT,
            file_hash TEXT,
            file_size INTEGER,
            folder TEXT DEFAULT 'root'   -- NEW
        )''')

        # index/unique để chống trùng nội dung:
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_files_file_hash ON files(file_hash)')
        db.commit()

def teardown_appcontext(app):
    app.teardown_appcontext(close_connection)
