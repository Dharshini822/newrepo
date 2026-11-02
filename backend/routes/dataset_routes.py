import os
import shutil
from flask import Blueprint, request, jsonify, send_file
import config
from backend.services.dataset_service import DatasetService
from backend.utils.security import is_safe_path, sanitize_name

dataset_bp = Blueprint("dataset", __name__)

@dataset_bp.route("/dataset", methods=["GET"])
def get_dataset():
    stats = DatasetService.get_stats()
    samples_data = DatasetService.list_samples(limit=500)
    samples_list = [
        {"name": s["filename"], "label": s["class_name"], "path": s["relative_path"], "split": s["split"]}
        for s in samples_data.get("samples", [])
    ]
    return jsonify({"success": True, "stats": stats, "samples": samples_list})

@dataset_bp.route("/dataset/stats", methods=["GET"])
def get_dataset_stats():
    stats = DatasetService.get_stats()
    return jsonify({"success": True, "stats": stats})

@dataset_bp.route("/dataset/upload-image", methods=["POST"])
@dataset_bp.route("/dataset/image", methods=["POST"])
def upload_single_image():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "Empty filename."}), 400

    class_name = request.form.get("class_name") or request.form.get("label", "UNLABELED")
    split = request.form.get("split", "train")

    try:
        result = DatasetService.add_single_sample(file, class_name=class_name, split=split)
        return jsonify({
            "success": True,
            "message": f"Image stored for class '{result.get('class_name')}'. Verify label before training.",
            "sample": result,
            "stats": DatasetService.get_stats()
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@dataset_bp.route("/dataset/upload-zip", methods=["POST"])
@dataset_bp.route("/dataset/zip", methods=["POST"])
def upload_zip_dataset():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No ZIP file uploaded."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "Empty filename."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".zip":
        return jsonify({"success": False, "error": "Only .zip archive files are supported."}), 400

    default_split = request.form.get("default_split", "train")

    os.makedirs(config.UPLOADS_DIR, exist_ok=True)
    temp_zip_path = os.path.join(config.UPLOADS_DIR, f"upload_{file.filename}")
    file.save(temp_zip_path)

    try:
        result = DatasetService.process_zip_dataset(temp_zip_path, default_split=default_split)
        return jsonify({
            "success": True,
            "message": f"Imported {result.get('organized_count', 0)} image(s). Review class labels before training.",
            "result": result,
            "stats": DatasetService.get_stats()
        })
    except Exception as e:
        if os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except OSError:
                pass
        return jsonify({"success": False, "error": str(e)}), 400

@dataset_bp.route("/dataset/samples", methods=["GET"])
def list_samples():
    class_name = request.args.get("class_name")
    split = request.args.get("split")
    limit = int(request.args.get("limit", 40))
    offset = int(request.args.get("offset", 0))

    data = DatasetService.list_samples(class_name=class_name, split=split, limit=limit, offset=offset)
    return jsonify({"success": True, "data": data})

@dataset_bp.route("/dataset/label", methods=["PATCH"])
def relabel_sample():
    data = request.get_json(silent=True) or {}
    rel_path = data.get("relative_path") or data.get("path")
    new_label = sanitize_name(data.get("label") or data.get("class_name", ""))
    if not rel_path or not new_label:
        return jsonify({"success": False, "error": "Both path and new label are required."}), 400
    try:
        clean_rel = rel_path.replace("\\", "/").lstrip("/")
        src = os.path.abspath(os.path.join(config.DATASET_DIR, clean_rel))
        if not is_safe_path(config.DATASET_DIR, src) or not os.path.isfile(src):
            return jsonify({"success": False, "error": "Sample file not found."}), 404
        
        parts = clean_rel.split("/")
        split = parts[0] if parts[0] in {"train", "validation"} else "train"
        dest_dir = os.path.join(config.DATASET_DIR, split, new_label)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, os.path.basename(src))
        shutil.move(src, dest)
        return jsonify({"success": True, "message": f"Sample relabeled to {new_label}.", "stats": DatasetService.get_stats()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@dataset_bp.route("/dataset/delete-sample", methods=["POST"])
@dataset_bp.route("/dataset/sample", methods=["DELETE"])
def delete_sample():
    data = request.get_json(silent=True) or {}
    rel_path = data.get("relative_path") or data.get("path") or request.args.get("path")
    if not rel_path:
        return jsonify({"success": False, "error": "relative_path is required."}), 400

    try:
        deleted = DatasetService.delete_sample(rel_path)
        return jsonify({"success": deleted, "message": "Sample deleted.", "stats": DatasetService.get_stats()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@dataset_bp.route("/dataset/manifest", methods=["GET"])
def get_manifest():
    manifest = DatasetService.generate_manifest()
    return jsonify(manifest)

@dataset_bp.route("/dataset/sample-image/<path:relative_path>", methods=["GET"])
def get_sample_image(relative_path):
    target_path = os.path.abspath(os.path.join(config.DATASET_DIR, relative_path.replace("\\", "/")))
    if not is_safe_path(config.DATASET_DIR, target_path) or not os.path.isfile(target_path):
        return jsonify({"error": "File not found or unsafe path."}), 404
    return send_file(target_path)
