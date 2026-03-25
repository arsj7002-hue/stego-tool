"""
web/server.py — Flask Backend
------------------------------
Routes:
  GET  /                     → serves index.html
  POST /api/encode-text      → hide text in image
  POST /api/decode-text      → reveal text from image
  POST /api/encode-image     → hide image in image
  POST /api/decode-image     → extract hidden image
  POST /api/encode-file      → hide any file in image
  POST /api/decode-file      → extract hidden file
  POST /api/keygen           → generate RSA key pair
"""

import os
import sys
import uuid
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from stego import lsb_text, lsb_image, lsb_file
from stego.crypto import generate_keypair, save_keypair

# ── App setup ──────────────────────────────────────────────────────────────

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR   = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
CORS(app)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
KEYS_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "keys")

for d in (UPLOAD_DIR, OUTPUT_DIR, KEYS_DIR):
    os.makedirs(d, exist_ok=True)

ALLOWED_IMAGE = {"png", "jpg", "jpeg", "bmp", "tiff"}
ALLOWED_FILES = {"pdf", "zip", "docx", "txt", "mp3", "mp4", "csv", "xlsx", "pptx", "pem"}


def save_upload(file, allowed=None) -> str:
    """Save uploaded file, return its path."""
    fname = secure_filename(file.filename)
    ext   = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    if allowed and ext not in allowed:
        raise ValueError(f"File type '.{ext}' not allowed.")
    uid   = uuid.uuid4().hex[:8]
    path  = os.path.join(UPLOAD_DIR, f"{uid}_{fname}")
    file.save(path)
    return path


def out_path(filename: str) -> str:
    return os.path.join(OUTPUT_DIR, filename)


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/encode-text", methods=["POST"])
def api_encode_text():
    try:
        cover   = save_upload(request.files["cover"], ALLOWED_IMAGE)
        message = request.form.get("message", "")
        encrypt = request.form.get("encrypt", "false") == "true"

        if not message:
            return jsonify({"error": "Message cannot be empty."}), 400

        pub_key = None
        if encrypt:
            pub_file = request.files.get("pubkey")
            if not pub_file:
                return jsonify({"error": "Public key file required for encryption."}), 400
            pub_key = pub_file.read()

        output = out_path(f"stego_text_{uuid.uuid4().hex[:6]}.png")
        result = lsb_text.encode(cover, message, output, public_key_pem=pub_key)
        return jsonify({"success": True, "file": os.path.basename(output),
                        "usage_pct": result["usage_pct"], "encrypted": result["encrypted"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/decode-text", methods=["POST"])
def api_decode_text():
    try:
        stego    = save_upload(request.files["stego"], ALLOWED_IMAGE)
        decrypt  = request.form.get("decrypt", "false") == "true"

        priv_key = None
        if decrypt:
            priv_file = request.files.get("privkey")
            if not priv_file:
                return jsonify({"error": "Private key file required for decryption."}), 400
            priv_key = priv_file.read()

        result = lsb_text.decode(stego, private_key_pem=priv_key)
        return jsonify({"success": True, "message": result["message"],
                        "encrypted": result["encrypted"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/encode-image", methods=["POST"])
def api_encode_image():
    try:
        cover  = save_upload(request.files["cover"],  ALLOWED_IMAGE)
        secret = save_upload(request.files["secret"], ALLOWED_IMAGE)
        output = out_path(f"stego_image_{uuid.uuid4().hex[:6]}.png")
        result = lsb_image.encode(cover, secret, output)
        return jsonify({"success": True, "file": os.path.basename(output),
                        "cover_size": result["cover_size"], "secret_size": result["secret_size"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/decode-image", methods=["POST"])
def api_decode_image():
    try:
        stego  = save_upload(request.files["stego"], ALLOWED_IMAGE)
        output = out_path(f"extracted_image_{uuid.uuid4().hex[:6]}.png")
        result = lsb_image.decode(stego, output)
        return jsonify({"success": True, "file": os.path.basename(output),
                        "secret_size": result["secret_size"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/encode-file", methods=["POST"])
def api_encode_file():
    try:
        cover  = save_upload(request.files["cover"], ALLOWED_IMAGE)
        secret = save_upload(request.files["secret"])
        output = out_path(f"stego_file_{uuid.uuid4().hex[:6]}.png")
        result = lsb_file.encode(cover, secret, output)
        return jsonify({"success": True, "file": os.path.basename(output),
                        "filename": result["filename"], "file_size": result["file_size"],
                        "usage_pct": result["usage_pct"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/decode-file", methods=["POST"])
def api_decode_file():
    try:
        stego  = save_upload(request.files["stego"], ALLOWED_IMAGE)
        result = lsb_file.decode(stego, OUTPUT_DIR)
        return jsonify({"success": True, "file": os.path.basename(result["saved_to"]),
                        "filename": result["filename"], "file_size": result["file_size"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400



@app.route("/api/keygen", methods=["POST"])
def api_keygen():
    try:
        priv, pub = generate_keypair()
        uid = uuid.uuid4().hex[:8]
        priv_path = os.path.join(KEYS_DIR, f"private_{uid}.pem")
        pub_path  = os.path.join(KEYS_DIR, f"public_{uid}.pem")
        with open(priv_path, "wb") as f: f.write(priv)
        with open(pub_path,  "wb") as f: f.write(pub)
        return jsonify({
            "success": True,
            "private_key": os.path.basename(priv_path),
            "public_key":  os.path.basename(pub_path),
            "private_pem": priv.decode(),
            "public_pem":  pub.decode(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/download/<filename>")
def download(filename):
    """Download a result file."""
    safe = secure_filename(filename)
    # Check outputs dir first, then keys dir
    for directory in (OUTPUT_DIR, KEYS_DIR):
        path = os.path.join(directory, safe)
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404