import os

# Base directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "validation")
MODELS_DIR = os.path.join(BASE_DIR, "models")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DATABASE_DIR = os.path.join(BASE_DIR, "backend", "database")
DB_PATH = os.path.join(DATABASE_DIR, "signai.db")

MODEL_PATH = os.path.join(MODELS_DIR, "sign_model.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

# Server limits & security
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max request size (for dataset ZIPs)
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
ALLOWED_ARCHIVE_EXTENSIONS = {".zip"}

# Camera & Inference defaults
DEFAULT_CONFIDENCE_THRESHOLD = 0.60
TARGET_FRAME_WIDTH = 640
TARGET_FRAME_HEIGHT = 480

# Ensure essential runtime directories exist
for directory in [DATASET_DIR, TRAIN_DIR, VAL_DIR, MODELS_DIR, UPLOADS_DIR, DATABASE_DIR]:
    os.makedirs(directory, exist_ok=True)
