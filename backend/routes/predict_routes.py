import os
import base64
import numpy as np
import cv2
from flask import Blueprint, request, jsonify
import config
from backend.services.hand_detector import get_hand_detector
from backend.services.model_service import get_model_service
from backend.services.translation_service import translate_text
from backend.services.db_service import add_history_entry

predict_bp = Blueprint("predict", __name__)

@predict_bp.route("/predict", methods=["POST"])
@predict_bp.route("/predict/image", methods=["POST"])
def predict_image():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No image file provided."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "Empty filename."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in config.ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"success": False, "error": f"Unsupported file type '{ext}'. Allowed: PNG, JPG, JPEG, WEBP."}), 400

    target_lang = request.form.get("target_lang", "ta")
    save_history = request.form.get("save_history", "true").lower() == "true"

    try:
        # Read file into OpenCV BGR image
        in_memory = file.read()
        nparr = np.frombuffer(in_memory, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"success": False, "error": "Failed to decode image data."}), 400

        hand_detector = get_hand_detector()
        hand_res = hand_detector.extract_landmarks_from_bgr(img)

        if not hand_res["has_hand"]:
            return jsonify({
                "success": False,
                "has_hand": False,
                "sign": None,
                "confidence": 0.0,
                "message": "No hand gesture detected in the image. Please ensure your hand is centered, well-lit, and fingers are clearly visible."
            })

        model_service = get_model_service()
        if not model_service.is_loaded:
            return jsonify({
                "success": False,
                "has_hand": True,
                "model_configured": False,
                "sign": None,
                "landmarks": hand_res["landmarks"],
                "message": "Hand landmarks successfully captured, but no trained AI model is currently loaded. Go to Model Status or Dataset Manager to train your model."
            })

        pred_res = model_service.predict(hand_res["feature_vector"])
        if not pred_res["success"]:
            return jsonify({
                "success": False,
                "has_hand": True,
                "error": pred_res.get("error", "Inference error.")
            })

        sign_detected = pred_res["sign"]
        confidence = pred_res["confidence"]

        # Translate to target language
        trans_res = translate_text(sign_detected, target_lang=target_lang)

        # Save to SQLite history if requested
        history_id = None
        if save_history and confidence >= 0.3:
            h_entry = add_history_entry(
                sign_detected=sign_detected,
                confidence=confidence,
                target_lang=target_lang,
                translation=trans_res.get("translated", sign_detected),
                source="upload"
            )
            history_id = h_entry["id"]

        return jsonify({
            "success": True,
            "has_hand": True,
            "sign": sign_detected,
            "label": sign_detected,
            "confidence": confidence,
            "all_scores": pred_res.get("all_scores", {}),
            "translation": trans_res,
            "landmarks": hand_res["landmarks"],
            "handedness": hand_res["handedness"],
            "history_id": history_id
        })

    except Exception as e:
        print(f"[PredictRoutes] Image prediction error: {e}")
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

@predict_bp.route("/predict/frame", methods=["POST"])
def predict_frame():
    data = request.get_json(silent=True)
    if not data or "frame" not in data:
        return jsonify({"success": False, "error": "No frame data provided."}), 400

    frame_data = data["frame"]
    target_lang = data.get("target_lang", "ta")
    log_history = data.get("log_history", False)

    try:
        if "," in frame_data:
            frame_data = frame_data.split(",")[1]

        image_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"success": False, "error": "Unable to decode frame."}), 400

        hand_detector = get_hand_detector()
        hand_res = hand_detector.extract_landmarks_from_bgr(img)

        if not hand_res["has_hand"]:
            return jsonify({
                "success": True,
                "has_hand": False,
                "sign": None,
                "confidence": 0.0,
                "landmarks": []
            })

        model_service = get_model_service()
        if not model_service.is_loaded:
            return jsonify({
                "success": True,
                "has_hand": True,
                "model_configured": False,
                "sign": None,
                "confidence": 0.0,
                "landmarks": hand_res["landmarks"],
                "message": "Model not configured"
            })

        pred_res = model_service.predict(hand_res["feature_vector"])
        if not pred_res["success"]:
            return jsonify({
                "success": False,
                "has_hand": True,
                "error": pred_res.get("error", "Inference error.")
            })

        sign_detected = pred_res["sign"]
        confidence = pred_res["confidence"]

        trans_res = translate_text(sign_detected, target_lang=target_lang)

        if log_history and confidence >= 0.70:
            add_history_entry(
                sign_detected=sign_detected,
                confidence=confidence,
                target_lang=target_lang,
                translation=trans_res.get("translated", sign_detected),
                source="camera"
            )

        return jsonify({
            "success": True,
            "has_hand": True,
            "sign": sign_detected,
            "label": sign_detected,
            "confidence": confidence,
            "all_scores": pred_res.get("all_scores", {}),
            "translation": trans_res,
            "landmarks": hand_res["landmarks"],
            "handedness": hand_res["handedness"]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
