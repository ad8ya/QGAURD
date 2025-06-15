from flask import Blueprint, jsonify, request

api = Blueprint('api', __name__)

@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@api.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    # Save the file or process it as needed
    return jsonify({"message": "File uploaded successfully"}), 201

@api.route('/scan', methods=['POST'])
def scan_code():
    # Logic for scanning code would go here
    return jsonify({"message": "Code scanning initiated"}), 202