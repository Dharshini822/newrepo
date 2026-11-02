import os
import sys
import json
import pickle
import numpy as np

# Add parent directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from backend.services.classifier import SignLandmarkClassifier
from backend.services.hand_detector import get_hand_detector
from backend.services.training_service import compute_metrics

def evaluate():
    print("===============================================================")
    print("  SignAI: Model Evaluation Tool")
    print("===============================================================")

    if not os.path.exists(config.MODEL_PATH) or not os.path.exists(config.METADATA_PATH):
        print(f"[ERROR] No trained model found at {config.MODEL_PATH}.")
        print("Please train a model first using: python training/train.py")
        sys.exit(1)

    with open(config.METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    print(f"Model Algorithm:    {meta.get('algorithm')}")
    print(f"Trained Date:       {meta.get('trained_at')}")
    print(f"Classes:            {', '.join(meta.get('classes', []))}")
    print(f"Recorded Accuracy:  {meta.get('accuracy', 0)*100:.2f}%\n")

    with open(config.MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    detector = get_hand_detector()

    val_dir = config.VAL_DIR
    classes = [d for d in os.listdir(val_dir) if os.path.isdir(os.path.join(val_dir, d))]
    
    if not classes:
        print("[INFO] No images in dataset/validation/. Evaluating on dataset/train/...")
        val_dir = config.TRAIN_DIR
        classes = [d for d in os.listdir(val_dir) if os.path.isdir(os.path.join(val_dir, d))]

    X_test = []
    y_test = []

    print(f"Extracting features from: {val_dir} ...")
    for cls in classes:
        cls_p = os.path.join(val_dir, cls)
        for fname in os.listdir(cls_p):
            if os.path.splitext(fname)[1].lower() in config.ALLOWED_IMAGE_EXTENSIONS:
                img_path = os.path.join(cls_p, fname)
                res = detector.extract_landmarks_from_path(img_path)
                if res["has_hand"] and res["feature_vector"] is not None:
                    X_test.append(res["feature_vector"])
                    y_test.append(cls)

    if not X_test:
        print("[INFO] No external image files found in dataset folders.")
        print(f"Loaded model is ready with supported classes: {meta.get('classes')}")
        return

    y_pred = model.predict(X_test)
    acc, f1, report, cm = compute_metrics(y_test, y_pred, meta.get("classes", []))
    print(f"\nEvaluation on {len(X_test)} samples:")
    print(f"Overall Accuracy: {acc*100:.2f}%")
    print(f"Weighted F1-Score: {f1:.4f}\n")
    print("Classification Report:")
    for cls, metrics in report.items():
        print(f"  {cls:12s} - Precision: {metrics['precision']:.3f}, Recall: {metrics['recall']:.3f}, F1: {metrics['f1-score']:.3f} (support: {metrics['support']})")

if __name__ == "__main__":
    evaluate()
