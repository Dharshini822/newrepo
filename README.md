# SignAI — AI-Powered Multilingual Sign Language Communication System
**Sign. Translate. Connect.**

A production-grade, full-stack AI SaaS application for real-time sign language recognition, live webcam frame inference with on-canvas landmark mesh rendering, single image detection, dataset curation with directory traversal (Zip Slip) security, dual-tier Tamil & English translation, browser text-to-speech audio synthesis, and persistent SQLite event history.

Developed as a BTech AI & Data Science capstone project.

---

## 🌟 Key Architecture & Features

### 1. Modern AI SaaS Dashboard
- **Color Palette:** Pure White, Navy (`#0a1128`, `#101f42`), Electric Blue (`#2563eb`), and Cyan (`#06b6d4`).
- **Layout:** Responsive 8-view Single Page Application (SPA) with fixed sidebar navigation and fluid animations.
- **Theme Toggle:** Dark and Light mode toggle with persistent state saved in browser `localStorage`.
- **System Telemetry:** Live backend connectivity badge and active model state indicator.

### 2. Interactive Live Webcam Recognition
- **Real Browser Webcam API:** Uses `navigator.mediaDevices.getUserMedia` with permission requested only upon clicking **Start Camera**.
- **Real-Time Landmark Mesh:** Renders 21 skeletal hand landmarks and connecting bone vectors directly onto an HTML5 overlay canvas.
- **Throttled Inference Loop:** Processes webcam frames at ~3.1 FPS (320 ms intervals) to ensure instantaneous predictions without overloading system CPU.
- **Confidence Meter:** Dynamic color-coded confidence percentage bar and raw score breakdown.
- **Automatic Audio Playback:** Instant text-to-speech translation trigger for detected signs.
- **Safe Stream Lifecycle:** Full stream track release and canvas clearing on **Stop Camera** or view navigation.

### 3. Dedicated Image Upload & Inference
- **File Support:** PNG, JPG, JPEG, and WEBP formats with drag-and-drop or file browser picker.
- **Validation:** Enforces 100 MB max request size and image MIME/header verification.
- **Instant Preview & Detection:** Displays the uploaded image, draws MediaPipe landmark points over detected hands, shows the predicted sign, confidence, and target language translation.

### 4. Safe Dataset Manager
- **ZIP Dataset Import:** Safely extracts multi-class ZIP archives with strict Zip Slip directory traversal (`..`) protection and file extension validation.
- **Single Sample Upload:** Add individual images into structured class folders (`dataset/train/<class>/` and `dataset/validation/<class>/`).
- **Interactive Analytics:** Real-time class distribution metrics and image counts.
- **Sample Gallery:** Visual browser showing image filenames, sizes, and direct sample deletion.
- **Manifest Export:** Generates an exportable JSON dataset manifest.

### 5. AI Engine & Background Training
- **Landmark Feature Extraction:** MediaPipe Tasks `HandLandmarker` extracting 21 3D landmarks (63 features) normalized to wrist origin and maximum span for scale and translation invariance.
- **Classifier:** `SignLandmarkClassifier` (an ensemble of k-NN with k=5 and Cosine/Euclidean Centroid Softmax) outputting calibrated confidence probabilities. Runs in <1 ms with zero DLL dependencies.
- **Asynchronous Background Training:** Background thread execution preventing UI lockups, with real-time progress bar (0–100%) and streaming terminal logs.
- **Comprehensive Evaluation:** Generates overall accuracy, weighted F1-score, confusion matrix, and per-class precision/recall metrics saved in `models/model_metadata.json`.
- **Honest AI Status:** Returns `"Model not configured"` when models or weights are missing—never invents fake predictions or scores.

### 6. Dual-Tier Translation & Audio Synthesis
- **Verified ISL Glossary:** Offline dictionary for core Indian Sign Language glosses (greetings, courtesies, responses, questions, and A–Z alphabet finger spelling) with authentic Tamil translations and phonetic pronunciations (e.g. `HELLO` → `வணக்கம்` / *Vanakkam*, `THANK YOU` → `நன்றி` / *Nandri*).
- **Online Deep-Translator Fallback:** Automatic fallback for complex sentences using `deep-translator`.
- **Browser Text-to-Speech (TTS):** Web Speech API (`window.speechSynthesis`) supporting Tamil (`ta-IN`) and English (`en-US`) with speech rate controls.

### 7. SQLite Recognition History
- **Persistent Storage:** Stored in `backend/database/signai.db`.
- **Event Logging:** Records timestamp, recognized sign, confidence score, target language, translation, and detection source (`camera`, `upload`, or `manual`).
- **Management:** Source filtering, single-entry deletion, and full history clearing with confirmation dialog.

---

## 📁 Project Directory Structure

```
SignAI/
├── app.py                      # Unified server entry point (API + Frontend SPA)
├── config.py                   # Central paths, security limits, DB location
├── requirements.txt            # Python dependencies
├── README.md                   # Full system documentation
├── test_app.py                 # Automated test suite (12 unit & integration tests)
│
├── backend/
│   ├── app.py                  # Secondary backend entry point (forwarder)
│   ├── database/
│   │   └── signai.db           # Persistent SQLite database
│   ├── routes/
│   │   ├── status_routes.py    # /api/status, /api/health, /api/model/status
│   │   ├── predict_routes.py   # /api/predict/image, /api/predict/frame, /api/predict
│   │   ├── dataset_routes.py   # /api/dataset/upload-image, /api/dataset/upload-zip, manifest
│   │   ├── train_routes.py     # /api/train/start, /api/train/status, /api/train
│   │   ├── translate_routes.py # /api/translate, /api/translate/glossary
│   │   └── history_routes.py   # /api/history, /api/history/add, /api/history/clear
│   ├── services/
│   │   ├── hand_detector.py    # MediaPipe Tasks HandLandmarker service
│   │   ├── classifier.py       # Pure NumPy SignLandmarkClassifier
│   │   ├── model_service.py    # Inference, model reloading, confidence scoring
│   │   ├── training_service.py # Background training thread & evaluation
│   │   ├── dataset_service.py  # Safe zip extraction, validation, distribution stats
│   │   ├── translation_service.py # Verified ISL glossary + deep-translator fallback
│   │   └── db_service.py       # SQLite connection and queries
│   └── utils/
│       └── security.py         # Path traversal & image validation security
│
├── dataset/                    # Training and validation dataset storage
│   ├── train/                  # e.g., dataset/train/HELLO/, dataset/train/A/
│   └── validation/             # e.g., dataset/validation/HELLO/
│
├── models/                     # Trained models & MediaPipe assets
│   ├── hand_landmarker.task    # MediaPipe hand landmark model (7.8 MB)
│   ├── sign_model.joblib       # Serialized landmark classifier
│   └── model_metadata.json     # Supported classes, accuracy, confusion matrix
│
├── training/
│   ├── train.py                # Standalone CLI training script
│   ├── evaluate.py             # Standalone model evaluation script
│   ├── capture_samples.py      # Camera capture tool to record dataset images
│   └── create_starter_data.py  # Generates initial calibrated model & starter dataset
│
├── uploads/                    # Temporary staging for uploads
│
└── frontend/                   # Modern AI SaaS Dashboard
    ├── index.html              # Single Page Dashboard with 8 functional modules
    ├── css/
    │   ├── style.css           # Modern SaaS theme (navy, blue, cyan, white)
    │   └── responsive.css      # Fluid layouts for desktop, tablet, and mobile
    └── js/
        ├── app.js              # Routing, state management, toasts, telemetry
        ├── camera.js           # Browser webcam, landmark canvas mesh, throttled inference
        ├── upload.js           # Drag & drop image upload and detection
        ├── dataset.js          # Dataset manager: ZIP/image upload, distribution charts
        ├── translation.js      # English & Tamil translation and Web Speech TTS
        ├── history.js          # SQLite recognition event history display and filters
        └── model_status.js     # Model diagnostics, metrics, one-click training trigger
```

---

## ⚡ Quick Start & Installation

### Step 1: Open Terminal in the Project Directory
```powershell
cd C:\Users\bhava\Desktop\SignAI
```

### Step 2: Set Up Virtual Environment (Recommended)
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt (CMD)
# python -m venv .venv
# .venv\Scripts\activate.bat

# macOS / Linux
# python3 -m venv .venv
# source .venv/bin/activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application
```powershell
python app.py
```
*(You can also run `python backend/app.py`)*

The server starts on `http://127.0.0.1:5000`. Open this address in your web browser. The backend automatically serves the full interactive SaaS dashboard and all REST API endpoints.

---

## 🧪 Running Automated Tests

Run the comprehensive 12-test suite:
```powershell
python test_app.py
```

Tests cover:
- System health and API connectivity (`/api/status`, `/api/health`)
- Active model configuration and class verification (`/api/model/status`)
- Verified ISL glossary and online translation (`/api/translate`)
- ISL glossary dictionary listing (`/api/translate/glossary`)
- Dataset statistics calculation (`/api/dataset/stats`, `/api/dataset`)
- Dataset manifest generation (`/api/dataset/manifest`)
- SQLite recognition history lifecycle (`/api/history/add`, `/api/history`, `/api/history/<id>`, `/api/history/clear`)
- Webcam frame prediction with empty and landmark frames (`/api/predict/frame`)
- Model training status polling (`/api/train/status`)

---

## 📖 Module-by-Module User Guide

### 1. Live Camera Recognition
1. Click **Live Camera** in the sidebar.
2. Select your preferred target translation language (Tamil or English).
3. Click **Start Camera** (the browser will prompt for camera permission).
4. Hold one hand inside the central guide frame.
5. As soon as your hand is detected:
   - Green skeletal landmark points and connecting lines appear on your hand.
   - The recognized sign and its Tamil/English translation display instantly.
   - The confidence meter updates in real time.
   - The audio icon allows re-speaking the translation using browser Text-to-Speech.
6. Click **Stop Camera** when finished to immediately release the camera device.

### 2. Image Upload Detection
1. Click **Image Upload** in the sidebar.
2. Drag and drop any sign image (`.png`, `.jpg`, `.jpeg`, `.webp`) or click **Browse Files**.
3. The selected image will preview with its filename and file size.
4. Click **Run Sign Inference**.
5. The model detects hand landmarks, predicts the sign class, calculates the confidence score, and displays the Tamil/English translation.

### 3. Dataset Manager
1. Click **Dataset Manager** in the sidebar.
2. **Importing ZIP Datasets:**
   - Arrange folders by sign name (e.g., `A/img1.jpg`, `B/img2.jpg`, `HELLO/img3.jpg`).
   - Drag and drop the `.zip` archive into the ZIP dropzone.
   - Files are securely extracted, validated, and placed into `dataset/train/<class>/`.
3. **Uploading Individual Images:**
   - Enter the sign label (e.g. `HELLO`, `YES`, `NO`, `A`, `B`, `C`).
   - Choose an image file and click **Upload Labelled Image**.
4. **Capturing from Webcam (CLI Tool):**
   - Run: `python training/capture_samples.py --sign HELLO --count 25`
   - Press **SPACE** to record 25 photos directly into `dataset/train/HELLO/`.
5. **Managing & Exporting:**
   - Inspect class distribution bars and sample counts.
   - Browse sample thumbnails and delete any incorrectly labelled images.
   - Click **Export Manifest** to download a structured JSON manifest of the entire dataset.

### 4. Model Training & Diagnostics
1. Click **Model Status** in the sidebar.
2. View current algorithm details, number of supported classes, training date, accuracy score, and confusion matrix.
3. To retrain with your latest dataset images:
   - Click **Start Model Training** in the dashboard, or run `python training/train.py` from the terminal.
   - The real-time progress bar (0–100%) and live log stream will display the training progress.
   - MediaPipe extracts 63-dimensional features from every image.
   - Data is split into 80% training and 20% validation sets.
   - The newly trained model is saved to `models/sign_model.joblib` and automatically reloaded by the API.

### 5. Multilingual Translation & TTS
1. Click **Translation** in the sidebar.
2. Type any word, sentence, or sign name.
3. Select your target language (**Tamil** or **English**).
4. Click **Translate Text** to view the translation, phonetic pronunciation, and provider used (Verified ISL Dictionary or Deep-Translator).
5. Click **Speak Audio** to hear natural speech using the Web Speech API (`speechSynthesis`).
6. Browse the built-in **Indian Sign Language Glossary** table to explore verified signs, Tamil translations, and phonetic pronunciations.

### 6. Recognition History
1. Click **History** in the sidebar.
2. View all past recognition events with timestamp, detection source (`CAMERA`, `UPLOAD`, or `MANUAL`), detected sign, confidence score, and translation.
3. Filter entries by source using the dropdown.
4. Delete specific events or click **Clear All History** to reset the SQLite database log.

---

## 🔒 Security & Safe File Handling

- **Zip Slip directory traversal protection:** Validates all archive file paths against canonical base paths before extraction.
- **Strict File Type Validation:** Accepts only valid image extensions (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`).
- **File Size Limits:** Max 100 MB request ceiling to protect against denial-of-service memory exhausts.
- **Sanitized Filenames:** All filenames are sanitized to prevent illegal characters and filesystem escapes.
- **Decoupled Architecture:** Inference and training run in memory and separate threads; client-side code never exposes secrets or sensitive keys.

---

## ⚠️ Known Boundaries & Honest AI Disclaimers

1. **Static Gesture vs. Continuous ISL:** This system classifies static hand poses and single-frame gestures. Full Indian Sign Language sentence translation involves two-handed continuous signing, facial expressions, and grammar that require temporal video models (e.g. LSTM/Transformers).
2. **Lighting and Camera Positioning:** Accurate MediaPipe landmark detection requires good lighting and hand visibility without heavy occlusion or motion blur.
3. **Third-Party Translation Services:** Online fallback translation uses `deep-translator` and requires an internet connection. If offline, the built-in verified ISL glossary remains operational.
4. **Browser Voice Availability:** Tamil TTS playback depends on whether your operating system/browser includes a Tamil speech synthesis voice. If absent, the audio synthesis falls back gracefully or notifies the user.

---

## 📜 Deliverables Summary

- **Source Code:** Complete modular Python Flask backend and HTML5/CSS3/ES6 frontend in `C:\Users\bhava\Desktop\SignAI`.
- **Pre-trained Calibrated Model:** Included in `models/` with 7 initial classes (`HELLO`, `YES`, `NO`, `THANKS`, `A`, `B`, `C`).
- **MediaPipe Task Assets:** Pre-configured `models/hand_landmarker.task`.
- **Automated Tests:** 12 passing test cases in `test_app.py`.
#   S i g n A I  
 #   S i g n A I  
 #   S i g n A I  
 