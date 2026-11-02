from flask import Blueprint, request, jsonify
from backend.services.db_service import get_history, add_history_entry, clear_history, delete_history_entry

history_bp = Blueprint("history", __name__)

@history_bp.route("/history", methods=["GET"])
def list_history():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    source = request.args.get("source")
    
    entries = get_history(limit=limit, offset=offset, source=source)
    return jsonify({"success": True, "history": entries})

@history_bp.route("/history/add", methods=["POST"])
def add_manual_entry():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "No JSON payload provided."}), 400

    sign_detected = data.get("sign_detected", "").strip()
    if not sign_detected:
        return jsonify({"success": False, "error": "sign_detected is required."}), 400

    confidence = float(data.get("confidence", 1.0))
    target_lang = data.get("target_lang", "ta")
    translation = data.get("translation", sign_detected)
    source = data.get("source", "manual")

    entry = add_history_entry(sign_detected, confidence, target_lang, translation, source)
    return jsonify({"success": True, "entry": entry})

@history_bp.route("/history", methods=["DELETE"])
@history_bp.route("/history/clear", methods=["POST"])
def clear_all_history():
    clear_history()
    return jsonify({"success": True, "message": "History cleared successfully."})

@history_bp.route("/history/<int:entry_id>", methods=["DELETE"])
def delete_single_entry(entry_id: int):
    deleted = delete_history_entry(entry_id)
    return jsonify({"success": deleted})
