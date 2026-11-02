import os
import sys
import platform
import datetime
import zipfile
from flask import Blueprint, jsonify, send_file
from backend.services.model_service import get_model_service
from backend.services.db_service import get_system_stats
from backend.services.hand_detector import get_hand_detector
import config

status_bp = Blueprint("status", __name__)

def create_project_zip():
    zip_path = os.path.join(config.BASE_DIR, "SignAI_FullStack_Website.zip")
    exclude_dirs = {"__pycache__", ".venv", ".git", ".idea", ".vscode", "venv", "env"}
    exclude_extensions = {".pyc", ".zip"}

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(config.BASE_DIR):
            rel_root = os.path.relpath(root, config.BASE_DIR)
            parts = set(rel_root.replace("\\", "/").split("/"))
            if parts.intersection(exclude_dirs):
                continue
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if os.path.splitext(file)[1].lower() in exclude_extensions:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, config.BASE_DIR)
                zipf.write(full_path, arcname=os.path.join("SignAI", rel_path))
    return zip_path

@status_bp.route("/status", methods=["GET"])
@status_bp.route("/health", methods=["GET"])
def get_status():
    model_service = get_model_service()
    hand_detector = get_hand_detector()
    return jsonify({
        "status": "online",
        "app_name": "SignAI — Sign. Translate. Connect.",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hand_detector_ready": hand_detector.is_ready,
        "model_configured": model_service.is_loaded
    })

@status_bp.route("/model/status", methods=["GET"])
def get_model_status():
    model_service = get_model_service()
    return jsonify(model_service.get_status())

@status_bp.route("/system/stats", methods=["GET"])
def get_stats():
    stats = get_system_stats()
    return jsonify({
        "success": True,
        "stats": stats,
        "environment": {
            "os": platform.platform(),
            "python_version": sys.version.split()[0],
            "framework": "Flask 3.1.3",
            "ml_engine": "MediaPipe Tasks + Scikit-Learn"
        }
    })

@status_bp.route("/download-project", methods=["GET"])
@status_bp.route("/download", methods=["GET"])
def download_project_zip():
    zip_path = create_project_zip()
    return send_file(
        zip_path,
        as_attachment=True,
        download_name="SignAI_FullStack_Website.zip",
        mimetype="application/zip"
    )
