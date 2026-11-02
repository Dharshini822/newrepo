from flask import Blueprint, request, jsonify
from backend.services.translation_service import translate_text, get_glossary_list

translate_bp = Blueprint("translate", __name__)

@translate_bp.route("/translate", methods=["POST"])
def translate_endpoint():
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"success": False, "error": "Field 'text' is required."}), 400

    text = data.get("text", "")
    target_lang = data.get("target_lang") or data.get("target", "ta")

    result = translate_text(text, target_lang=target_lang)
    return jsonify({
        "success": True,
        "result": result,
        "translation": result.get("translated", ""),
        "target": target_lang
    })

@translate_bp.route("/translate/glossary", methods=["GET"])
def glossary_endpoint():
    glossary = get_glossary_list()
    return jsonify({"success": True, "glossary": glossary})
