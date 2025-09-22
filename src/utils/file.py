import os, hashlib
from werkzeug.utils import secure_filename

TEXT_EXTS = {'txt','md','log','csv','json','xml','yaml','yml','ini','cfg'}
IMAGE_EXTS = {'jpg','jpeg','png','gif','bmp','webp'}
PDF_EXTS   = {'pdf'}
PPT_EXTS   = {'ppt','pptx'}
XLS_EXTS   = {'xls','xlsx'}

MAX_DISPLAY_LEN = 10

def allowed_file(filename):
    return '.' in filename

def ext_of(filename):
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

def get_file_type(filename):
    ext = ext_of(filename)
    if ext in IMAGE_EXTS: return 'image'
    if ext in PDF_EXTS:   return 'pdf'
    if ext in TEXT_EXTS:  return 'text'
    if ext in PPT_EXTS:   return 'ppt'
    if ext in XLS_EXTS:   return 'xls'
    return 'other'

def shorten_name(name, limit=MAX_DISPLAY_LEN):
    name = name.strip()
    if len(name) <= limit:
        return name
    prefix = name[:limit//2-2]
    suffix = name[-(limit//2-1):]
    return f"{prefix}…{suffix}"

def content_hash(file_storage):
    """Tính SHA256 nội dung file (stream) mà không giữ file tạm lớn trong RAM."""
    # đảm bảo con trỏ về đầu
    file_storage.stream.seek(0)
    h = hashlib.sha256()
    chunk = file_storage.stream.read(8192)
    total = 0
    while chunk:
        h.update(chunk)
        total += len(chunk)
        chunk = file_storage.stream.read(8192)
    file_storage.stream.seek(0)
    return h.hexdigest(), total

def safe_filename(original):
    return secure_filename(original) or 'file'
