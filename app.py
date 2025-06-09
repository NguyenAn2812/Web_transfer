import os
import uuid
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, send_file, abort, g
from datetime import datetime

app = Flask(__name__)
DB_PATH = 'app.db'
UPLOAD_FOLDER = 'uploads'
SESSION_COOKIE_NAME = 'session_id'

# --- DB helpers ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
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
            file_type TEXT
        )''')
        db.commit()

init_db()

# --- Device helpers ---
def get_device_name(session_id):
    db = get_db()
    cur = db.execute('SELECT device_name FROM devices WHERE session_id=?', (session_id,))
    row = cur.fetchone()
    return row['device_name'] if row else None

def set_device_name(session_id, name):
    db = get_db()
    if get_device_name(session_id):
        db.execute('UPDATE devices SET device_name=? WHERE session_id=?', (name, session_id))
    else:
        db.execute('INSERT INTO devices (session_id, device_name) VALUES (?, ?)', (session_id, name))
    db.commit()

def get_all_devices(exclude_id=None):
    db = get_db()
    if exclude_id:
        cur = db.execute('SELECT session_id, device_name FROM devices WHERE session_id != ?', (exclude_id,))
    else:
        cur = db.execute('SELECT session_id, device_name FROM devices')
    return {row['session_id']: row['device_name'] for row in cur.fetchall()}

# --- File helpers ---
def allowed_file(filename):
    return '.' in filename

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']: return 'image'
    if ext in ['pdf']: return 'pdf'
    if ext in ['txt', 'md', 'log', 'csv']: return 'text'
    return 'other'

# --- Routes ---
@app.route('/accept-cookie', methods=['POST'])
def accept_cookie():
    session_id = str(uuid.uuid4())
    default_name = f"Device-{session_id[:6]}"
    set_device_name(session_id, default_name)
    resp = make_response(jsonify({'success': True, 'device_name': default_name}))
    resp.set_cookie(SESSION_COOKIE_NAME, session_id, max_age=60*60*24*365*10)
    return resp

@app.route('/change-device-name', methods=['POST'])
def change_device_name():
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return jsonify({'success': False, 'error': 'No session'}), 400
    data = request.get_json()
    new_name = data.get('name', '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'Name required'}), 400
    set_device_name(session_id, new_name)
    return jsonify({'success': True, 'device_name': new_name})

@app.route('/')
def index():
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    device_name = get_device_name(session_id) if session_id else None
    return render_template('index.html', has_session=session_id is not None, device_name=device_name)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    device_name = get_device_name(session_id) if session_id else None
    devices = get_all_devices(exclude_id=session_id)
    if request.method == 'POST':
        file = request.files.get('file')
        mode = request.form.get('mode')
        receiver = request.form.get('receiver')
        display_name = request.form.get('display_name')
        title = request.form.get('title')
        if not file or not mode:
            return render_template('upload.html', has_session=session_id is not None, device_name=device_name, devices=devices, session_id=session_id, error='Thiếu thông tin')
        if not display_name:
            display_name = file.filename
        if not title:
            title = file.filename
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        file_type = get_file_type(file.filename)
        db = get_db()
        db.execute('''INSERT INTO files (filename, display_name, title, uploader_id, uploader_name, is_public, receiver_id, upload_time, file_path, file_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (file.filename, display_name, title, session_id, device_name, 1 if mode=='public' else 0, receiver if mode=='private' and receiver else None, datetime.now().isoformat(), file_path, file_type))
        db.commit()
        return redirect(url_for('files'))
    return render_template('upload.html', has_session=session_id is not None, device_name=device_name, devices=devices, session_id=session_id)

@app.route('/files')
def files():
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    device_name = get_device_name(session_id) if session_id else None
    db = get_db()
    cur = db.execute('''SELECT * FROM files WHERE is_public=1 OR receiver_id=? ORDER BY id DESC''', (session_id,))
    files = cur.fetchall()
    return render_template('files.html', has_session=session_id is not None, device_name=device_name, files=files, session_id=session_id)

@app.route('/download/<int:file_id>')
def download(file_id):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    db = get_db()
    cur = db.execute('''SELECT * FROM files WHERE (is_public=1 OR receiver_id=?) ORDER BY id DESC''', (session_id,))
    files = cur.fetchall()
    if 0 <= file_id < len(files):
        file = files[file_id]
        file_path = file['file_path']
        if file_path and os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=file['filename'])
    return abort(404)

@app.route('/delete/<int:file_id>')
def delete_file(file_id):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    db = get_db()
    cur = db.execute('''SELECT * FROM files WHERE (is_public=1 OR receiver_id=?) ORDER BY id DESC''', (session_id,))
    files = cur.fetchall()
    if 0 <= file_id < len(files):
        file = files[file_id]
        if file['uploader_id'] == session_id:
            file_path = file['file_path']
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            db.execute('DELETE FROM files WHERE id=?', (file['id'],))
            db.commit()
    return redirect(url_for('files'))

@app.route('/preview/<int:file_id>')
def preview_file(file_id):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    db = get_db()
    cur = db.execute('''SELECT * FROM files WHERE (is_public=1 OR receiver_id=?) ORDER BY id DESC''', (session_id,))
    files = cur.fetchall()
    if 0 <= file_id < len(files):
        file = files[file_id]
        file_type = file['file_type']
        file_path = file['file_path']
        if file_type == 'image':
            return f'<img src="/{file_path}" style="max-width:100vw;max-height:65vh;object-fit:contain;display:block;margin:auto">'
        elif file_type == 'pdf':
            return f'<embed src="/{file_path}" type="application/pdf" width="100%" height="600px">'
        elif file_type == 'text':
            with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
                content = f.read(2000)
            return f'<pre style="max-height:600px;overflow:auto">{content}</pre>'
        else:
            return 'Previewing this file is not supported.'
    return abort(404)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 