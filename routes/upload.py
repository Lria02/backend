# backend/routes/upload.py

from flask import Blueprint, request, jsonify
from extract.extractor import extract_text_from_file
import tempfile
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        file.save(tmp)
        tmp_path = tmp.name

    text = extract_text_from_file(tmp_path)
    os.remove(tmp_path)
    return jsonify({"text": text[:500]})
