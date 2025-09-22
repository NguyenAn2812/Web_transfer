# src/routes/main.py
from flask import Blueprint, render_template, request, current_app
from ..utils.device import get_device_name

bp = Blueprint('main', __name__)

@bp.get('/')
def index():
    sid = request.cookies.get(current_app.config['SESSION_COOKIE_NAME'])
    device_name = get_device_name(sid) if sid else None
    return render_template('index.html', has_session=sid is not None, device_name=device_name)
