# src/routes/device.py
import uuid
from flask import Blueprint, jsonify, make_response, request, current_app
from ..utils.device import set_device_name

bp = Blueprint('device', __name__)

@bp.post('/accept-cookie')
def accept_cookie():
    session_id = str(uuid.uuid4())
    default_name = f"Device-{session_id[:6]}"
    set_device_name(session_id, default_name)
    resp = make_response(jsonify({'success': True, 'device_name': default_name}))
    resp.set_cookie(current_app.config['SESSION_COOKIE_NAME'], session_id, max_age=60*60*24*365*10)
    return resp

@bp.post('/change-device-name')
def change_device_name():
    sid = request.cookies.get(current_app.config['SESSION_COOKIE_NAME'])
    if not sid:
        return jsonify({'success': False, 'error': 'No session'}), 400
    data = request.get_json(force=True, silent=True) or {}
    new_name = (data.get('name') or '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'Name required'}), 400
    set_device_name(sid, new_name)
    return jsonify({'success': True, 'device_name': new_name})
