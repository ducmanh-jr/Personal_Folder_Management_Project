import os
import sys
import json
import mimetypes
import webbrowser
import subprocess
import platform
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

# ==================================================
# PATH CHUẨN CHO PYINSTALLER
# ==================================================
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR

UPLOAD_FOLDER = os.path.join(APP_DIR, 'luu_tru')
DATA_FILE = os.path.join(APP_DIR, 'data.json')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Tạo thư mục lưu trữ nếu chưa có
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Khởi tạo file data.json nếu chưa có
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({"columns": []}, f, ensure_ascii=False, indent=2)

def load_data():
    """Đọc dữ liệu từ file JSON"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu: {e}")
        return {"columns": []}

def save_data(data):
    """Lưu dữ liệu vào file JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu: {e}")

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """API lấy toàn bộ dữ liệu"""
    return jsonify(load_data())

@app.route('/api/save-all', methods=['POST'])
def save_all():
    """API lưu toàn bộ dữ liệu"""
    try:
        data = request.json
        save_data(data)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, msg=str(e)), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """API upload file"""
    if 'file' not in request.files:
        return jsonify(success=False, msg="Không có file được gửi lên"), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, msg="Tên file trống"), 400
    
    # Bảo mật tên file
    filename = secure_filename(file.filename)
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    # Tránh trùng tên file
    while os.path.exists(os.path.join(UPLOAD_FOLDER, new_filename)):
        new_filename = f"{base}({counter}){ext}"
        counter += 1
    
    # Lưu file
    file_path = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(file_path)
    
    return jsonify(
        success=True, 
        filename=new_filename, 
        url=f"/download/{new_filename}"
    )

@app.route('/download/<path:filename>')
def download_file(filename):
    """API tải file về"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify(success=False, msg="File không tồn tại"), 404
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify(success=False, msg=str(e)), 500

@app.route('/api/delete-file/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """API xóa file thực tế trong thư mục lưu trữ"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Kiểm tra file có tồn tại không
        if not os.path.exists(file_path):
            return jsonify(success=False, msg="File không tồn tại"), 404
        
        # Xóa file
        os.remove(file_path)
        print(f"✅ Đã xóa file: {filename}")
        
        return jsonify(success=True, msg="File đã được xóa thành công")
    
    except PermissionError:
        return jsonify(success=False, msg="Không có quyền xóa file này"), 403
    except Exception as e:
        print(f"❌ Lỗi khi xóa file: {e}")
        return jsonify(success=False, msg=f"Lỗi: {str(e)}"), 500

@app.route('/api/open-file/<path:filename>', methods=['POST'])
def open_file(filename):
    """API mở file với ứng dụng mặc định của hệ thống"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Kiểm tra file có tồn tại không
        if not os.path.exists(file_path):
            return jsonify(success=False, msg="File không tồn tại"), 404
        
        # Lấy đường dẫn tuyệt đối
        abs_path = os.path.abspath(file_path)
        system = platform.system()
        
        # Mở file theo hệ điều hành
        if system == 'Windows':
            # Windows: sử dụng os.startfile
            os.startfile(abs_path)
            print(f"✅ Đã mở file trên Windows: {filename}")
            
        elif system == 'Darwin':  # macOS
            # macOS: sử dụng lệnh 'open'
            subprocess.run(['open', abs_path], check=True)
            print(f"✅ Đã mở file trên macOS: {filename}")
            
        else:  # Linux và các hệ điều hành khác
            # Linux: sử dụng lệnh 'xdg-open'
            subprocess.run(['xdg-open', abs_path], check=True)
            print(f"✅ Đã mở file trên Linux: {filename}")
        
        return jsonify(success=True, msg="Đã mở file với ứng dụng mặc định")
    
    except FileNotFoundError:
        return jsonify(success=False, msg="Không tìm thấy ứng dụng để mở file"), 404
    except PermissionError:
        return jsonify(success=False, msg="Không có quyền mở file này"), 403
    except subprocess.CalledProcessError as e:
        return jsonify(success=False, msg=f"Lỗi khi mở file: {str(e)}"), 500
    except Exception as e:
        print(f"❌ Lỗi khi mở file: {e}")
        return jsonify(success=False, msg=f"Lỗi: {str(e)}"), 500

@app.route('/api/files')
def list_files():
    """API liệt kê tất cả file trong thư mục lưu trữ (bonus)"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                files.append({
                    'name': filename,
                    'size': file_stat.st_size,
                    'modified': file_stat.st_mtime
                })
        return jsonify(success=True, files=files)
    except Exception as e:
        return jsonify(success=False, msg=str(e)), 500

if __name__ == '__main__':
    port = 5006
    url = f"http://127.0.0.1:{port}"
    
    # Tự động mở trình duyệt khi khởi động
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        print(f"🚀 Khởi động ứng dụng tại: {url}")
        print(f"📁 Thư mục lưu trữ: {UPLOAD_FOLDER}")
        webbrowser.open(url)
    
    app.run(port=port, debug=False)