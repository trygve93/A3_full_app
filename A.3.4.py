from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import hashlib
import uuid
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ------------------- KONFIG -------------------
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB limit

DB_PATH = "app.db"

# Demo-brukere (byttes ut med ekte DB fra A.3.1)
USERS = {
    "admin": {"password": hashlib.sha256("admin".encode()).hexdigest(), "role": "admin"},
    "teacher": {"password": hashlib.sha256("teacher".encode()).hexdigest(), "role": "teacher"},
    "student": {"password": hashlib.sha256("student".encode()).hexdigest(), "role": "student"},
}


# ------------------- DATABASE -------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        filename TEXT NOT NULL,
        upload_time TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def save_file_metadata(username, filename):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO files (username, filename, upload_time) VALUES (?, ?, ?)",
                (username, filename, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


# ------------------- AUTH -------------------
def _unauthorized():
    resp = jsonify({"message": "Not authorized"})
    resp.status_code = 401
    resp.headers["WWW-Authenticate"] = 'Basic realm="Upload Area"'
    return resp

def _check_auth(required_roles=None):
    auth = request.authorization
    if not auth:
        return None

    user = USERS.get(auth.username)
    if not user:
        return None

    # Sjekk passord (SHA-256 hash for demo)
    if hashlib.sha256(auth.password.encode()).hexdigest() != user["password"]:
        return None

    # Sjekk rolle
    if required_roles and user["role"] not in required_roles:
        return None

    return {"username": auth.username, "role": user["role"]}


# ------------------- HJELPEFUNKSJONER -------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------- ROUTES -------------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Secure File Upload & Download API"}), 200


# ---- UPLOAD (kun admin/lærer) ----
@app.route('/upload', methods=['POST'])
def upload_file():
    user = _check_auth(required_roles=["admin", "teacher"])
    if not user:
        return _unauthorized()

    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "Invalid file type"}), 400
    if not (file.mimetype or "").lower().startswith("image/"):
        return jsonify({"message": "Invalid content type"}), 400

    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit('.', 1)[1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_name))
    save_file_metadata(user["username"], new_name)

    return jsonify({
        "message": "File uploaded successfully",
        "filename": new_name
    }), 201


# ---- DOWNLOAD (alle roller, student kun egne filer) ----
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    user = _check_auth(required_roles=["admin", "teacher", "student"])
    if not user:
        return _unauthorized()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT username FROM files WHERE filename=?", (filename,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"message": "File not found"}), 404

    owner_username = row[0]

    if user["role"] == "student" and user["username"] != owner_username:
        return jsonify({"message": "Access denied"}), 403

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


# ---- DELETE (kun admin/lærer) ----
@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    user = _check_auth(required_roles=["admin", "teacher"])
    if not user:
        return _unauthorized()

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM files WHERE filename=?", (filename,))
        conn.commit()
        conn.close()

        return jsonify({"message": "File deleted"}), 200
    else:
        return jsonify({"message": "File not found"}), 404


# ---- LIST (kun admin/lærer) ----
@app.route('/files', methods=['GET'])
def list_files():
    user = _check_auth(required_roles=["admin", "teacher"])
    if not user:
        return _unauthorized()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT username, filename, upload_time FROM files")
    rows = cur.fetchall()
    conn.close()

    return jsonify([{"username": r[0], "filename": r[1], "upload_time": r[2]} for r in rows]), 200


# ------------------- MAIN -------------------
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    init_db()
    app.run(debug=True)
