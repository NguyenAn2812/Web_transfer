# src/app.py
import os
from flask import Flask, send_from_directory, current_app
from .utils.db import init_db
from .routes.main import bp as main_bp
from .routes.device import bp as device_bp
from .routes.file import bp as file_bp

def create_app():
    app = Flask(__name__, static_folder=None, template_folder='../templates')

    # 1) Đọc biến môi trường hoặc mặc định 'uploads'
    upload_root = os.environ.get('UPLOAD_FOLDER', 'uploads')
    # 2) Nếu là đường dẫn tương đối, ép về tuyệt đối tại gốc project (ra ngoài 'src')
    if not os.path.isabs(upload_root):
        # app.root_path = .../Web_transfer/src
        project_root = os.path.abspath(os.path.join(app.root_path, '..'))
        upload_root = os.path.abspath(os.path.join(project_root, upload_root))
    app.config['UPLOAD_FOLDER'] = upload_root

    app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024
    app.config['SESSION_COOKIE_NAME'] = 'web_transfer_sid'

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    init_db(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(file_bp)

    # Route phục vụ file tĩnh đã upload
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
