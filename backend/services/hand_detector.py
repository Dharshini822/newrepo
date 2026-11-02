import os
import urllib.request
import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import config

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
TASK_PATH = os.path.join(config.MODELS_DIR, "hand_landmarker.task")

class HandDetector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HandDetector, cls).__new__(cls)
            cls._instance._init_detector()
        return cls._instance

    def _init_detector(self):
        self.detector = None
        self.is_ready = False
        try:
            # Ensure task model is present
            if not os.path.exists(TASK_PATH) or os.path.getsize(TASK_PATH) == 0:
                print(f"[HandDetector] Downloading MediaPipe hand_landmarker.task to {TASK_PATH}...")
                os.makedirs(os.path.dirname(TASK_PATH), exist_ok=True)
                urllib.request.urlretrieve(MODEL_URL, TASK_PATH)
            
            base_options = python.BaseOptions(model_asset_path=TASK_PATH)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            self.is_ready = True
            print("[HandDetector] MediaPipe HandLandmarker initialized successfully.")
        except Exception as e:
            print(f"[HandDetector] Error initializing HandLandmarker: {e}")
            self.detector = None
            self.is_ready = False

    def extract_landmarks_from_bgr(self, bgr_image: np.ndarray):
        """
        Extracts 21 3D hand landmarks from a BGR numpy image.
        Returns:
            dict with:
                'has_hand': bool,
                'landmarks': list of {'x': float, 'y': float, 'z': float},
                'feature_vector': list of float (63 values) or None,
                'handedness': 'Right' | 'Left' | 'Unknown'
        """
        if not self.is_ready or self.detector is None or bgr_image is None:
            return {"has_hand": False, "landmarks": [], "feature_vector": None, "handedness": "Unknown"}

        try:
            rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
            result = self.detector.detect(mp_image)

            if not result.hand_landmarks or len(result.hand_landmarks) == 0:
                return {"has_hand": False, "landmarks": [], "feature_vector": None, "handedness": "Unknown"}

            # Take the primary hand detected
            hand_landmarks = result.hand_landmarks[0]
            raw_pts = [{"x": float(lm.x), "y": float(lm.y), "z": float(lm.z)} for lm in hand_landmarks]

            # Determine handedness if available
            handedness = "Right"
            if result.handedness and len(result.handedness) > 0:
                handedness = result.handedness[0][0].category_name

            # Compute normalized, translation- and scale-invariant 63-dim feature vector
            wrist_x, wrist_y, wrist_z = raw_pts[0]["x"], raw_pts[0]["y"], raw_pts[0]["z"]
            
            # Translate relative to wrist
            shifted_pts = []
            max_dist = 0.0
            for pt in raw_pts:
                dx = pt["x"] - wrist_x
                dy = pt["y"] - wrist_y
                dz = pt["z"] - wrist_z
                dist = np.sqrt(dx * dx + dy * dy + dz * dz)
                if dist > max_dist:
                    max_dist = dist
                shifted_pts.append((dx, dy, dz))

            # Scale normalization
            if max_dist < 1e-6:
                max_dist = 1.0

            normalized_vector = []
            for dx, dy, dz in shifted_pts:
                normalized_vector.extend([float(dx / max_dist), float(dy / max_dist), float(dz / max_dist)])

            return {
                "has_hand": True,
                "landmarks": raw_pts,
                "feature_vector": normalized_vector,
                "handedness": handedness
            }
        except Exception as e:
            print(f"[HandDetector] Detection error: {e}")
            return {"has_hand": False, "landmarks": [], "feature_vector": None, "handedness": "Unknown"}

    def extract_landmarks_from_path(self, image_path: str):
        if not os.path.exists(image_path):
            return {"has_hand": False, "landmarks": [], "feature_vector": None, "handedness": "Unknown"}
        bgr = cv2.imread(image_path)
        if bgr is None:
            return {"has_hand": False, "landmarks": [], "feature_vector": None, "handedness": "Unknown"}
        return self.extract_landmarks_from_bgr(bgr)

# Global singleton helper
def get_hand_detector():
    return HandDetector()
