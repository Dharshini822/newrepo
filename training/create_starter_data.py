import os
import sys
import json
import datetime
import numpy as np

# Add parent directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from backend.services.classifier import SignLandmarkClassifier
from backend.services.training_service import pure_train_test_split, compute_metrics
from backend.services.db_service import get_connection

def generate_base_hand_landmarks(gesture_type: str) -> np.ndarray:
    """
    Constructs a 21-landmark 3D coordinate array based on standard MediaPipe
    hand landmark topological geometry for common ISL gestures.
    Wrist is landmark 0 at (0, 0, 0).
    Coordinates are normalized relative to wrist.
    """
    pts = np.zeros((21, 3), dtype=np.float32)

    # Base palm landmarks (0: wrist, 1: thumb CMC, 5: index MCP, 9: middle MCP, 13: ring MCP, 17: pinky MCP)
    pts[0] = [0.0, 0.0, 0.0]
    pts[1] = [-0.15, -0.15, 0.0]
    pts[2] = [-0.25, -0.30, 0.0]
    pts[5] = [-0.10, -0.45, 0.0]
    pts[9] = [0.00, -0.48, 0.0]
    pts[13] = [0.10, -0.45, 0.0]
    pts[17] = [0.20, -0.40, 0.0]

    if gesture_type == "HELLO":  # Open 5 fingers spread
        pts[3] = [-0.35, -0.45, 0.0]; pts[4] = [-0.45, -0.60, 0.0]
        pts[6] = [-0.12, -0.65, 0.0]; pts[7] = [-0.14, -0.80, 0.0]; pts[8] = [-0.15, -0.95, 0.0]
        pts[10] = [0.00, -0.70, 0.0]; pts[11] = [0.00, -0.85, 0.0]; pts[12] = [0.00, -1.00, 0.0]
        pts[14] = [0.12, -0.65, 0.0]; pts[15] = [0.14, -0.80, 0.0]; pts[16] = [0.15, -0.95, 0.0]
        pts[18] = [0.22, -0.55, 0.0]; pts[19] = [0.25, -0.70, 0.0]; pts[20] = [0.28, -0.85, 0.0]

    elif gesture_type == "YES":  # Closed fist
        pts[3] = [-0.15, -0.35, 0.1]; pts[4] = [-0.05, -0.40, 0.1]
        pts[6] = [-0.10, -0.35, 0.1]; pts[7] = [-0.08, -0.28, 0.05]; pts[8] = [-0.08, -0.20, 0.0]
        pts[10] = [0.00, -0.37, 0.1]; pts[11] = [0.00, -0.28, 0.05]; pts[12] = [0.00, -0.20, 0.0]
        pts[14] = [0.10, -0.35, 0.1]; pts[15] = [0.08, -0.28, 0.05]; pts[16] = [0.08, -0.20, 0.0]
        pts[18] = [0.18, -0.32, 0.1]; pts[19] = [0.16, -0.26, 0.05]; pts[20] = [0.15, -0.20, 0.0]

    elif gesture_type == "NO":  # Index upright, others curled
        pts[3] = [-0.15, -0.35, 0.1]; pts[4] = [-0.05, -0.40, 0.1]
        pts[6] = [-0.10, -0.65, 0.0]; pts[7] = [-0.10, -0.80, 0.0]; pts[8] = [-0.10, -0.95, 0.0]
        pts[10] = [0.00, -0.37, 0.1]; pts[11] = [0.00, -0.28, 0.05]; pts[12] = [0.00, -0.20, 0.0]
        pts[14] = [0.10, -0.35, 0.1]; pts[15] = [0.08, -0.28, 0.05]; pts[16] = [0.08, -0.20, 0.0]
        pts[18] = [0.18, -0.32, 0.1]; pts[19] = [0.16, -0.26, 0.05]; pts[20] = [0.15, -0.20, 0.0]

    elif gesture_type == "THANKS":  # Flat palm angled outward
        pts[3] = [-0.20, -0.40, 0.0]; pts[4] = [-0.22, -0.55, 0.0]
        pts[6] = [-0.08, -0.60, 0.0]; pts[7] = [-0.08, -0.75, 0.0]; pts[8] = [-0.08, -0.90, 0.0]
        pts[10] = [0.00, -0.62, 0.0]; pts[11] = [0.00, -0.77, 0.0]; pts[12] = [0.00, -0.92, 0.0]
        pts[14] = [0.08, -0.60, 0.0]; pts[15] = [0.08, -0.75, 0.0]; pts[16] = [0.08, -0.90, 0.0]
        pts[18] = [0.16, -0.52, 0.0]; pts[19] = [0.16, -0.67, 0.0]; pts[20] = [0.16, -0.82, 0.0]

    elif gesture_type == "A":  # Fist with upright thumb on side
        pts[3] = [-0.20, -0.35, 0.0]; pts[4] = [-0.18, -0.50, 0.0]
        pts[6] = [-0.08, -0.32, 0.1]; pts[7] = [-0.06, -0.24, 0.05]; pts[8] = [-0.06, -0.18, 0.0]
        pts[10] = [0.00, -0.35, 0.1]; pts[11] = [0.00, -0.25, 0.05]; pts[12] = [0.00, -0.18, 0.0]
        pts[14] = [0.08, -0.33, 0.1]; pts[15] = [0.06, -0.24, 0.05]; pts[16] = [0.06, -0.18, 0.0]
        pts[18] = [0.16, -0.30, 0.1]; pts[19] = [0.14, -0.22, 0.05]; pts[20] = [0.14, -0.18, 0.0]

    elif gesture_type == "B":  # 4 fingers straight up, thumb folded
        pts[3] = [-0.05, -0.28, 0.1]; pts[4] = [0.02, -0.30, 0.1]
        pts[6] = [-0.08, -0.65, 0.0]; pts[7] = [-0.08, -0.80, 0.0]; pts[8] = [-0.08, -0.95, 0.0]
        pts[10] = [0.00, -0.68, 0.0]; pts[11] = [0.00, -0.84, 0.0]; pts[12] = [0.00, -0.98, 0.0]
        pts[14] = [0.08, -0.65, 0.0]; pts[15] = [0.08, -0.80, 0.0]; pts[16] = [0.08, -0.94, 0.0]
        pts[18] = [0.16, -0.58, 0.0]; pts[19] = [0.16, -0.72, 0.0]; pts[20] = [0.16, -0.86, 0.0]

    elif gesture_type == "C":  # Cupped 'C' hand
        pts[3] = [-0.25, -0.35, 0.0]; pts[4] = [-0.20, -0.50, 0.0]
        pts[6] = [-0.15, -0.50, 0.1]; pts[7] = [-0.10, -0.60, 0.15]; pts[8] = [-0.05, -0.65, 0.2]
        pts[10] = [-0.05, -0.52, 0.1]; pts[11] = [0.00, -0.62, 0.15]; pts[12] = [0.05, -0.66, 0.2]
        pts[14] = [0.05, -0.50, 0.1]; pts[15] = [0.10, -0.58, 0.15]; pts[16] = [0.15, -0.62, 0.2]
        pts[18] = [0.12, -0.42, 0.1]; pts[19] = [0.16, -0.50, 0.15]; pts[20] = [0.20, -0.55, 0.2]

    # Normalize relative to wrist and max span
    dists = np.linalg.norm(pts, axis=1)
    max_d = np.max(dists)
    if max_d > 1e-5:
        pts = pts / max_d

    return pts.flatten()

def generate_starter_dataset_and_model(samples_per_class: int = 50):
    classes = ["HELLO", "YES", "NO", "THANKS", "A", "B", "C"]
    print("===============================================================")
    print("  SignAI: Generating Calibration Dataset & Training Starter Model")
    print(f"  Classes: {', '.join(classes)}")
    print(f"  Samples per class: {samples_per_class}")
    print("===============================================================")

    np.random.seed(42)
    X = []
    y = []

    for cls in classes:
        base_vector = generate_base_hand_landmarks(cls)
        cls_dir = os.path.join(config.TRAIN_DIR, cls)
        os.makedirs(cls_dir, exist_ok=True)

        for _ in range(samples_per_class):
            noise = np.random.normal(0, 0.025, size=base_vector.shape)
            sample_vec = base_vector + noise
            X.append(sample_vec)
            y.append(cls)

    X = np.array(X, dtype=np.float32)
    y = np.array(y)

    X_train, X_val, y_train, y_val = pure_train_test_split(X, y, test_size=0.25, random_seed=42)

    print(f"Fitting SignLandmarkClassifier on {len(X_train)} training samples...")
    clf = SignLandmarkClassifier(k=5, temperature=6.0)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_val)
    acc, f1, rep, cm = compute_metrics(y_val, y_pred, classes)

    print(f"[SUCCESS] Starter Model Evaluation:")
    print(f"  Validation Accuracy: {acc*100:.2f}%")
    print(f"  Weighted F1-Score:   {f1:.4f}")

    os.makedirs(config.MODELS_DIR, exist_ok=True)
    clf.save(config.MODEL_PATH)

    metadata = {
        "algorithm": "SignLandmarkClassifier (k-NN + Centroid Softmax)",
        "classes": classes,
        "feature_dim": 63,
        "training_samples": len(X_train),
        "validation_samples": len(X_val),
        "accuracy": round(acc, 4),
        "f1_score": round(f1, 4),
        "trained_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": {
            "accuracy": round(acc, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm,
            "classes": classes,
            "report": rep
        }
    }

    with open(config.METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    try:
        from backend.services.db_service import init_db
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO training_logs (timestamp, samples_count, classes_count, accuracy, f1_score, status, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata["trained_at"],
            len(X),
            len(classes),
            acc,
            f1,
            "completed",
            "Initial calibration model generated for HELLO, YES, NO, THANKS, A, B, C."
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: could not insert into DB: {e}")

    print(f"\nModel saved to:    {config.MODEL_PATH}")
    print(f"Metadata saved to: {config.METADATA_PATH}")
    print("The SignAI live recognition pipeline is now active and ready to use!\n")

if __name__ == "__main__":
    generate_starter_dataset_and_model()
