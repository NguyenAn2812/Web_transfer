from .db import get_db

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
