from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import hashlib
import uuid
import os

app = Flask(__name__)

# Upload file:
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB limit


_USERNAME = "admin"
_PASSWORD_PLAIN = "admin"
_PASSWORD_SHA256 = hashlib.sha256(_PASSWORD_PLAIN.encode()).hexdigest()

def _unauthorized():
    resp = jsonify({"message": "Authentication required"})
    resp.status_code = 401
    resp.headers["WWW-Authenticate"] = 'Basic realm="Upload Area"'
    return resp

def _check_auth():
    auth = request.authorization
    if not auth:
        return False
    if auth.username != _USERNAME:
        return False
    return hashlib.sha256(auth.password.encode()).hexdigest() == _PASSWORD_SHA256

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Secure Image Upload API"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if not _check_auth():
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

    return jsonify({
        "message": "File uploaded successfully",
        "filename": new_name
    }), 201

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)


