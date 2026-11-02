/**
 * SignAI — Live Camera Controller
 * Real MediaDevices Webcam Stream, Canvas Landmark Overlay, Throttled Inference & Audio
 */

class CameraModule {
  constructor() {
    this.video = document.getElementById("webcam-video");
    this.canvas = document.getElementById("landmark-canvas");
    this.ctx = this.canvas ? this.canvas.getContext("2d") : null;
    this.stream = null;
    this.isProcessing = false;
    this.processInterval = null;
    this.lastSpokenSign = null;
    this.lastSpokenTime = 0;
    this.minConfidence = 0.65;
    this.fpsCounter = 0;
    this.fpsTimer = null;

    this.init();
  }

  init() {
    const startBtn = document.getElementById("start-cam-btn");
    const stopBtn = document.getElementById("stop-cam-btn");
    const speakBtn = document.getElementById("cam-speak-btn");
    const slider = document.getElementById("conf-threshold-slider");
    const sliderVal = document.getElementById("conf-threshold-val");

    if (startBtn) startBtn.addEventListener("click", () => this.startCamera());
    if (stopBtn) stopBtn.addEventListener("click", () => this.stopCamera());
    if (speakBtn) speakBtn.addEventListener("click", () => this.speakCurrentSign());

    if (slider) {
      slider.addEventListener("input", (e) => {
        this.minConfidence = parseInt(e.target.value, 10) / 100;
        if (sliderVal) sliderVal.textContent = `${e.target.value}%`;
      });
    }

    // Clean up camera stream when window unloads
    window.addEventListener("beforeunload", () => this.stopCamera());
  }

  async startCamera() {
    const startBtn = document.getElementById("start-cam-btn");
    const stopBtn = document.getElementById("stop-cam-btn");
    const placeholder = document.getElementById("camera-placeholder");
    const overlayStatus = document.getElementById("camera-overlay-status");

    try {
      if (overlayStatus) overlayStatus.textContent = "Requesting camera permission...";
      
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user"
        },
        audio: false
      });

      this.video.srcObject = this.stream;
      await this.video.play();

      // Configure overlay canvas sizing
      this.canvas.width = this.video.videoWidth || 640;
      this.canvas.height = this.video.videoHeight || 480;

      // Update UI state
      if (startBtn) startBtn.disabled = true;
      if (stopBtn) stopBtn.disabled = false;
      if (placeholder) placeholder.style.display = "none";
      if (overlayStatus) overlayStatus.textContent = "Webcam Active • Position hand inside guide box";

      window.app.showToast("Camera stream started successfully.", "success");

      // Start frame processing loop (every 320ms ~ 3.1 FPS to balance responsiveness & CPU)
      this.isProcessing = true;
      this.processInterval = setInterval(() => this.processCurrentFrame(), 320);

      // Start telemetry timer
      this.fpsTimer = setInterval(() => {
        const fpsEl = document.getElementById("cam-fps");
        if (fpsEl) fpsEl.textContent = `${this.fpsCounter * 2} FPS`;
        this.fpsCounter = 0;
      }, 500);

    } catch (err) {
      console.error("Camera access error:", err);
      if (startBtn) startBtn.disabled = false;
      if (stopBtn) stopBtn.disabled = true;
      if (placeholder) placeholder.style.display = "flex";

      let errorMsg = "Could not access webcam.";
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        errorMsg = "Camera permission was denied. Please allow camera access in your browser settings.";
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        errorMsg = "No webcam device was found on this computer.";
      } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
        errorMsg = "Camera hardware is currently in use by another application.";
      }
      if (overlayStatus) overlayStatus.textContent = errorMsg;
      window.app.showToast(errorMsg, "error");
    }
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.video) {
      this.video.srcObject = null;
    }

    if (this.processInterval) {
      clearInterval(this.processInterval);
      this.processInterval = null;
    }

    if (this.fpsTimer) {
      clearInterval(this.fpsTimer);
      this.fpsTimer = null;
    }

    this.isProcessing = false;
    this.clearCanvas();

    const startBtn = document.getElementById("start-cam-btn");
    const stopBtn = document.getElementById("stop-cam-btn");
    const placeholder = document.getElementById("camera-placeholder");
    const overlayStatus = document.getElementById("camera-overlay-status");
    const fpsEl = document.getElementById("cam-fps");

    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    if (placeholder) placeholder.style.display = "flex";
    if (overlayStatus) overlayStatus.textContent = "Camera Stopped • Click Start Camera";
    if (fpsEl) fpsEl.textContent = "0 FPS";

    this.resetDetectionDisplay();
  }

  async processCurrentFrame() {
    if (!this.isProcessing || !this.video || this.video.readyState !== 4) return;

    try {
      // Create off-screen canvas to capture frame
      const offscreen = document.createElement("canvas");
      offscreen.width = 320; // Downscale frame for fast transfer
      offscreen.height = 240;
      const oCtx = offscreen.getContext("2d");
      
      // Mirror image for proper alignment
      oCtx.save();
      oCtx.scale(-1, 1);
      oCtx.drawImage(this.video, -320, 0, 320, 240);
      oCtx.restore();

      const frameData = offscreen.toDataURL("image/jpeg", 0.65);
      const targetLang = document.getElementById("cam-target-lang")?.value || "ta";

      this.fpsCounter++;

      const res = await fetch("/api/predict/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          frame: frameData,
          target_lang: targetLang,
          log_history: true
        })
      });

      const data = await res.json();
      if (!data.success) {
        this.clearCanvas();
        return;
      }

      this.handleInferenceResult(data);

    } catch (err) {
      console.warn("Frame inference error:", err);
    }
  }

  handleInferenceResult(data) {
    const statusEl = document.getElementById("cam-detection-status");
    const signEl = document.getElementById("cam-result-sign");
    const transEl = document.getElementById("cam-result-trans");
    const pronounceEl = document.getElementById("cam-result-pronounce");
    const confValEl = document.getElementById("cam-confidence-val");
    const confFillEl = document.getElementById("cam-confidence-fill");
    const speakBtn = document.getElementById("cam-speak-btn");
    const landmarksCountEl = document.getElementById("cam-landmarks-count");
    const autoSpeak = document.getElementById("cam-auto-speak")?.checked;

    if (!data.has_hand) {
      this.clearCanvas();
      if (statusEl) statusEl.textContent = "Scanning for hand gestures...";
      if (landmarksCountEl) landmarksCountEl.textContent = "0 / 21";
      return;
    }

    // Hand detected! Draw landmarks
    if (landmarksCountEl) landmarksCountEl.textContent = "21 / 21";
    this.drawHandLandmarks(data.landmarks);

    // If model is not loaded
    if (data.model_configured === false) {
      if (statusEl) statusEl.textContent = "Hand Detected • Model not configured (Train in Model Status)";
      if (signEl) signEl.textContent = "NO MODEL";
      if (transEl) transEl.textContent = "Please upload or train a model";
      if (confValEl) confValEl.textContent = "0%";
      if (confFillEl) confFillEl.style.width = "0%";
      if (speakBtn) speakBtn.disabled = true;
      return;
    }

    // Model is loaded and returned a prediction!
    const confidence = data.confidence || 0;
    const sign = data.sign || "—";
    const translation = data.translation?.translated || "—";
    const pronunciation = data.translation?.pronunciation || "";

    const pct = Math.round(confidence * 100);

    if (confidence >= this.minConfidence) {
      if (statusEl) statusEl.textContent = `Gesture Detected (${data.handedness || 'Hand'})`;
      if (signEl) signEl.textContent = sign;
      if (transEl) transEl.textContent = `Translation: ${translation}`;
      if (pronounceEl) pronounceEl.textContent = pronunciation ? `(${pronunciation})` : "";
      if (confValEl) confValEl.textContent = `${pct}%`;
      if (confFillEl) confFillEl.style.width = `${pct}%`;
      if (speakBtn) speakBtn.disabled = false;

      // Auto-speech synthesis with 2-second debounce
      const now = Date.now();
      if (autoSpeak && confidence >= 0.80 && (sign !== this.lastSpokenSign || now - this.lastSpokenTime > 2500)) {
        this.speakCurrentSign();
        this.lastSpokenSign = sign;
        this.lastSpokenTime = now;
      }
    } else {
      if (statusEl) statusEl.textContent = `Uncertain gesture (${pct}% confidence)`;
      if (confValEl) confValEl.textContent = `${pct}%`;
      if (confFillEl) confFillEl.style.width = `${pct}%`;
    }
  }

  drawHandLandmarks(landmarks) {
    if (!this.ctx || !landmarks || landmarks.length === 0) return;
    this.clearCanvas();

    const w = this.canvas.width;
    const h = this.canvas.height;

    // Standard hand skeleton connections
    const connections = [
      [0,1],[1,2],[2,3],[3,4],        // Thumb
      [0,5],[5,6],[6,7],[7,8],        // Index
      [5,9],[9,10],[10,11],[11,12],   // Middle
      [9,13],[13,14],[14,15],[15,16], // Ring
      [13,17],[17,18],[18,19],[19,20],[0,17] // Pinky & Palm base
    ];

    // Draw skeleton lines
    this.ctx.strokeStyle = "rgba(0, 240, 255, 0.7)";
    this.ctx.lineWidth = 3;
    for (const [startIdx, endIdx] of connections) {
      if (landmarks[startIdx] && landmarks[endIdx]) {
        const x1 = landmarks[startIdx].x * w;
        const y1 = landmarks[startIdx].y * h;
        const x2 = landmarks[endIdx].x * w;
        const y2 = landmarks[endIdx].y * h;
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.stroke();
      }
    }

    // Draw landmark joints
    this.ctx.fillStyle = "#3B82F6";
    this.ctx.strokeStyle = "#FFFFFF";
    this.ctx.lineWidth = 1.5;
    for (const pt of landmarks) {
      const cx = pt.x * w;
      const cy = pt.y * h;
      this.ctx.beginPath();
      this.ctx.arc(cx, cy, 5, 0, 2 * Math.PI);
      this.ctx.fill();
      this.ctx.stroke();
    }
  }

  clearCanvas() {
    if (this.ctx && this.canvas) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  resetDetectionDisplay() {
    const statusEl = document.getElementById("cam-detection-status");
    const signEl = document.getElementById("cam-result-sign");
    const transEl = document.getElementById("cam-result-trans");
    const pronounceEl = document.getElementById("cam-result-pronounce");
    const confValEl = document.getElementById("cam-confidence-val");
    const confFillEl = document.getElementById("cam-confidence-fill");
    const speakBtn = document.getElementById("cam-speak-btn");

    if (statusEl) statusEl.textContent = "Camera stopped";
    if (signEl) signEl.textContent = "—";
    if (transEl) transEl.textContent = "Translation: —";
    if (pronounceEl) pronounceEl.textContent = "";
    if (confValEl) confValEl.textContent = "0%";
    if (confFillEl) confFillEl.style.width = "0%";
    if (speakBtn) speakBtn.disabled = true;
  }

  speakCurrentSign() {
    const transEl = document.getElementById("cam-result-trans");
    const targetLang = document.getElementById("cam-target-lang")?.value || "ta";
    if (!transEl) return;

    let text = transEl.textContent.replace("Translation:", "").trim();
    if (!text || text === "—") return;

    if (window.translationModule) {
      window.translationModule.speakText(text, targetLang);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.cameraModule = new CameraModule();
});
