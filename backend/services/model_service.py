import os
import json
import pickle
import numpy as np
import config
from backend.services.classifier import SignLandmarkClassifier

class ModelService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.model = None
        self.metadata = {}
        self.is_loaded = False
        self.reload()

    def reload(self):
        """Reloads model and metadata from disk if available."""
        self.model = None
        self.metadata = {}
        self.is_loaded = False

        if os.path.exists(config.MODEL_PATH) and os.path.exists(config.METADATA_PATH):
            try:
                # Load with pickle
                with open(config.MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)

                with open(config.METADATA_PATH, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

                self.is_loaded = True
                print(f"[ModelService] Model loaded successfully with classes: {self.metadata.get('classes', [])}")
            except Exception as e:
                print(f"[ModelService] Error loading model from disk: {e}")
                self.is_loaded = False
        else:
            print("[ModelService] No trained model found on disk. Status: Model not configured.")

    def get_status(self) -> dict:
        """Returns current model status, metadata, and supported classes."""
        if not self.is_loaded:
            return {
                "configured": False,
                "status": "Model not configured",
                "message": "No trained model found. Upload dataset or train a model to enable recognition.",
                "model_path": config.MODEL_PATH,
                "classes": [],
                "supported_classes": [],
                "num_classes": 0,
                "metrics": None
            }

        return {
            "configured": True,
            "status": "Active & Ready",
            "algorithm": self.metadata.get("algorithm", "SignLandmarkClassifier (k-NN + Centroid Softmax)"),
            "classes": self.metadata.get("classes", []),
            "supported_classes": self.metadata.get("classes", []),
            "num_classes": len(self.metadata.get("classes", [])),
            "trained_at": self.metadata.get("trained_at", "Unknown"),
            "training_samples": self.metadata.get("training_samples", 0),
            "validation_samples": self.metadata.get("validation_samples", 0),
            "accuracy": self.metadata.get("accuracy", None),
            "f1_score": self.metadata.get("f1_score", None),
            "feature_dim": self.metadata.get("feature_dim", 63),
            "metrics": self.metadata.get("metrics", {})
        }

    def predict(self, feature_vector: list[float]) -> dict:
        """
        Runs prediction on a 63-dimensional normalized hand landmark vector.
        """
        if not self.is_loaded or self.model is None:
            return {
                "success": False,
                "sign": None,
                "confidence": 0.0,
                "error": "Model not configured. Train a model first via the Dataset Manager or Model Status page."
            }

        if not feature_vector or len(feature_vector) != 63:
            return {
                "success": False,
                "sign": None,
                "confidence": 0.0,
                "error": f"Invalid feature vector length (expected 63, got {len(feature_vector) if feature_vector else 0})."
            }

        try:
            X = np.array([feature_vector], dtype=np.float32)
            classes = list(self.model.classes_)
            
            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba(X)[0]
                best_idx = int(np.argmax(probs))
                best_class = str(classes[best_idx])
                confidence = float(probs[best_idx])
                all_scores = {str(cls_name): round(float(prob), 4) for cls_name, prob in zip(classes, probs)}
            else:
                pred = self.model.predict(X)[0]
                best_class = str(pred)
                confidence = 1.0
                all_scores = {best_class: 1.0}

            return {
                "success": True,
                "sign": best_class,
                "confidence": round(confidence, 4),
                "all_scores": all_scores
            }
        except Exception as e:
            print(f"[ModelService] Prediction error: {e}")
            return {
                "success": False,
                "sign": None,
                "confidence": 0.0,
                "error": f"Inference failure: {str(e)}"
            }

def get_model_service():
    return ModelService()
