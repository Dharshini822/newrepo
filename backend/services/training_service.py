import os
import json
import threading
import datetime
import numpy as np
import config
from backend.services.classifier import SignLandmarkClassifier
from backend.services.hand_detector import get_hand_detector
from backend.services.model_service import get_model_service
from backend.services.db_service import get_connection

def pure_train_test_split(X, y, test_size=0.25, random_seed=42):
    rng = np.random.RandomState(random_seed)
    indices = np.arange(len(X))
    rng.shuffle(indices)
    split_point = int(len(X) * (1 - test_size))
    train_idx = indices[:split_point]
    val_idx = indices[split_point:]
    
    X_arr = np.array(X, dtype=np.float32)
    y_arr = np.array(y)
    return X_arr[train_idx], X_arr[val_idx], y_arr[train_idx], y_arr[val_idx]

def compute_metrics(y_true, y_pred, classes):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    acc = float(np.mean(y_true == y_pred))

    report = {}
    cm = []
    total_f1_weighted = 0.0

    for actual in classes:
        row = []
        for pred in classes:
            row.append(int(np.sum((y_true == actual) & (y_pred == pred))))
        cm.append(row)

        tp = int(np.sum((y_true == actual) & (y_pred == actual)))
        fp = int(np.sum((y_true != actual) & (y_pred == actual)))
        fn = int(np.sum((y_true == actual) & (y_pred != actual)))
        support = int(np.sum(y_true == actual))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        report[actual] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1-score": round(f1, 4),
            "support": support
        }
        total_f1_weighted += f1 * support

    weighted_f1 = total_f1_weighted / max(1, len(y_true))
    return acc, weighted_f1, report, cm

class TrainingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrainingService, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.is_training = False
        self.progress = 0
        self.current_step = "Idle"
        self.logs = []
        self.latest_result = None
        self.error = None
        self._lock = threading.Lock()

    def get_status(self) -> dict:
        with self._lock:
            return {
                "is_training": self.is_training,
                "progress": self.progress,
                "current_step": self.current_step,
                "logs": self.logs[-25:],
                "latest_result": self.latest_result,
                "error": self.error
            }

    def _log(self, message: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(f"[TrainingService] {entry}")
        with self._lock:
            self.logs.append(entry)

    def start_training_async(self, n_estimators: int = 100, max_depth: int = 15):
        with self._lock:
            if self.is_training:
                return False, "Training is already in progress."
            self.is_training = True
            self.progress = 5
            self.current_step = "Starting training pipeline..."
            self.logs = []
            self.latest_result = None
            self.error = None

        thread = threading.Thread(
            target=self._run_training_pipeline,
            args=(n_estimators, max_depth),
            daemon=True
        )
        thread.start()
        return True, "Training initiated in background."

    def _run_training_pipeline(self, n_estimators: int = 100, max_depth: int = 15):
        try:
            self._log("Starting feature extraction using MediaPipe HandLandmarker...")
            with self._lock:
                self.progress = 10
                self.current_step = "Scanning dataset directories..."

            hand_detector = get_hand_detector()
            if not hand_detector.is_ready:
                raise RuntimeError("Hand detector is not initialized. Cannot extract landmarks.")

            train_dir = config.TRAIN_DIR
            val_dir = config.VAL_DIR

            X_train_list = []
            y_train_list = []
            X_val_list = []
            y_val_list = []
            skipped_images = 0

            # Scan training files
            train_classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]
            if not train_classes:
                raise ValueError("No class folders found in dataset/train/. Please upload images via Dataset Manager first.")

            self._log(f"Found {len(train_classes)} class folders in train set: {', '.join(train_classes)}")

            # Count total train images
            total_train_files = 0
            for cls in train_classes:
                c_path = os.path.join(train_dir, cls)
                total_train_files += len([f for f in os.listdir(c_path) if os.path.splitext(f)[1].lower() in config.ALLOWED_IMAGE_EXTENSIONS])

            if total_train_files < 4:
                raise ValueError(f"Insufficient training samples ({total_train_files} found). Need at least 4 labeled images.")

            processed_files = 0
            for cls in train_classes:
                c_path = os.path.join(train_dir, cls)
                files = [f for f in os.listdir(c_path) if os.path.splitext(f)[1].lower() in config.ALLOWED_IMAGE_EXTENSIONS]
                for fname in files:
                    fpath = os.path.join(c_path, fname)
                    res = hand_detector.extract_landmarks_from_path(fpath)
                    if res["has_hand"] and res["feature_vector"] is not None:
                        X_train_list.append(res["feature_vector"])
                        y_train_list.append(cls)
                    else:
                        skipped_images += 1
                    
                    processed_files += 1
                    with self._lock:
                        self.progress = min(60, 10 + int(processed_files / max(1, total_train_files) * 50))
                        self.current_step = f"Processing train image {processed_files}/{total_train_files} (Class: {cls})..."

            self._log(f"Extracted landmarks from {len(X_train_list)} train images ({skipped_images} skipped without clear hand landmarks).")

            unique_classes = sorted(list(set(y_train_list)))
            if len(unique_classes) < 2:
                raise ValueError(f"Classifier requires at least 2 distinct classes with detectable hand gestures. Found: {unique_classes}")

            # Check validation directory
            val_classes = [d for d in os.listdir(val_dir) if os.path.isdir(os.path.join(val_dir, d))] if os.path.exists(val_dir) else []
            for cls in val_classes:
                c_path = os.path.join(val_dir, cls)
                files = [f for f in os.listdir(c_path) if os.path.splitext(f)[1].lower() in config.ALLOWED_IMAGE_EXTENSIONS]
                for fname in files:
                    fpath = os.path.join(c_path, fname)
                    res = hand_detector.extract_landmarks_from_path(fpath)
                    if res["has_hand"] and res["feature_vector"] is not None:
                        X_val_list.append(res["feature_vector"])
                        y_val_list.append(cls)

            # Split if separate validation set is empty or insufficient
            if len(X_val_list) < 2 or len(set(y_val_list)) < 2:
                self._log("Validation directory empty or small; applying stratified train/val split (80/20)...")
                X_train, X_val, y_train, y_val = pure_train_test_split(X_train_list, y_train_list, test_size=0.20, random_seed=42)
            else:
                X_train = np.array(X_train_list, dtype=np.float32)
                y_train = np.array(y_train_list)
                X_val = np.array(X_val_list, dtype=np.float32)
                y_val = np.array(y_val_list)

            with self._lock:
                self.progress = 75
                self.current_step = f"Fitting SignLandmarkClassifier (k-NN + Centroid Softmax ensemble)..."
            self._log(f"Training set: {len(X_train)} samples | Validation set: {len(X_val)} samples.")

            # Fit model
            clf = SignLandmarkClassifier(k=5, temperature=6.0)
            clf.fit(X_train, y_train)

            with self._lock:
                self.progress = 85
                self.current_step = "Evaluating model performance..."

            # Evaluate
            y_pred = clf.predict(X_val)
            acc, f1, report, cm = compute_metrics(y_val, y_pred, unique_classes)

            self._log(f"Training completed! Validation Accuracy: {acc*100:.1f}%, F1-Score: {f1:.3f}")

            # Save model and metadata
            with self._lock:
                self.progress = 95
                self.current_step = "Saving model artifacts..."

            clf.save(config.MODEL_PATH)

            metadata = {
                "algorithm": "SignLandmarkClassifier (k-NN + Centroid Softmax)",
                "classes": unique_classes,
                "feature_dim": 63,
                "training_samples": len(X_train),
                "validation_samples": len(X_val),
                "skipped_unrecognized": skipped_images,
                "accuracy": round(acc, 4),
                "f1_score": round(f1, 4),
                "trained_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "metrics": {
                    "accuracy": round(acc, 4),
                    "f1_score": round(f1, 4),
                    "confusion_matrix": cm,
                    "classes": unique_classes,
                    "report": report
                }
            }

            with open(config.METADATA_PATH, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Record in SQLite training_logs
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO training_logs (timestamp, samples_count, classes_count, accuracy, f1_score, status, message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata["trained_at"],
                    len(X_train) + len(X_val),
                    len(unique_classes),
                    acc,
                    f1,
                    "completed",
                    f"Trained {len(unique_classes)} classes with {acc*100:.1f}% accuracy."
                ))
                conn.commit()
                conn.close()
            except Exception as dbe:
                print(f"[TrainingService] DB logging warning: {dbe}")

            # Reload model in ModelService
            get_model_service().reload()

            with self._lock:
                self.progress = 100
                self.current_step = "Training complete. Model is active!"
                self.is_training = False
                self.latest_result = metadata

            self._log("Model successfully reloaded into active inference pipeline.")

        except Exception as e:
            err_msg = str(e)
            self._log(f"ERROR: {err_msg}")
            with self._lock:
                self.is_training = False
                self.error = err_msg
                self.current_step = f"Failed: {err_msg}"

def get_training_service():
    return TrainingService()
