from flask import Blueprint, request, jsonify
from backend.services.training_service import get_training_service

train_bp = Blueprint("train", __name__)

@train_bp.route("/train", methods=["POST"])
@train_bp.route("/train/start", methods=["POST"])
def start_training():
    data = request.get_json(silent=True) or {}
    n_estimators = int(data.get("n_estimators", 100))
    max_depth = int(data.get("max_depth", 15))

    training_service = get_training_service()
    started, msg = training_service.start_training_async(n_estimators=n_estimators, max_depth=max_depth)

    if not started:
        return jsonify({"success": False, "error": msg}), 409

    return jsonify({"success": True, "message": msg})

@train_bp.route("/train/status", methods=["GET"])
def get_training_status():
    training_service = get_training_service()
    status = training_service.get_status()
    return jsonify(status)
