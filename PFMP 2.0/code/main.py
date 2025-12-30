import os
import sys
import json
import mimetypes
import webbrowser
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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({"columns": []}, f, ensure_ascii=False, indent=2)

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"columns": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify(load_data())

@app.route('/api/save-all', methods=['POST'])
def save_all():
    data = request.json
    save_data(data)
    return jsonify(success=True)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(success=False, msg="No file"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, msg="No filename"), 400
    
    filename = secure_filename(file.filename)
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(UPLOAD_FOLDER, new_filename)):
        new_filename = f"{base}({counter}){ext}"
        counter += 1
    
    file.save(os.path.join(UPLOAD_FOLDER, new_filename))
    return jsonify(success=True, filename=new_filename, url=f"/download/{new_filename}")

@app.route('/download/<path:filename>')
def download_file(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    port = 5006
    url = f"http://127.0.0.1:{port}"
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open(url)
    app.run(port=port, debug=False)
