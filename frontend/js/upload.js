/**
 * SignAI — Image Upload & Detection Controller
 * Drag & Drop, File Validation, Image Preview, Inference & Audio
 */

class UploadModule {
  constructor() {
    this.selectedFile = null;
    this.init();
  }

  init() {
    const dropzone = document.getElementById("upload-dropzone");
    const fileInput = document.getElementById("image-file-input");
    const detectBtn = document.getElementById("detect-sign-btn");
    const speakBtn = document.getElementById("upload-speak-btn");

    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());

      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });

      dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
      });

      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          this.handleFileSelection(e.dataTransfer.files[0]);
        }
      });

      fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
          this.handleFileSelection(e.target.files[0]);
        }
      });
    }

    if (detectBtn) {
      detectBtn.addEventListener("click", () => this.detectSignFromImage());
    }

    if (speakBtn) {
      speakBtn.addEventListener("click", () => {
        const transEl = document.getElementById("upload-res-trans");
        const lang = window.app ? window.app.targetLanguage : "ta";
        if (transEl && window.translationModule) {
          const text = transEl.textContent.replace("Translation:", "").trim();
          if (text && text !== "—") {
            window.translationModule.speakText(text, lang);
          }
        }
      });
    }
  }

  handleFileSelection(file) {
    const allowed = ["image/png", "image/jpeg", "image/webp", "image/jpg"];
    if (!allowed.includes(file.type)) {
      window.app.showToast("Unsupported file type. Please upload PNG, JPG, or WEBP.", "error");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      window.app.showToast("Image is too large. Maximum size is 10MB.", "error");
      return;
    }

    this.selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
      const previewImg = document.getElementById("selected-image-preview");
      const previewWrapper = document.getElementById("image-preview-wrapper");
      const infoText = document.getElementById("image-info-text");

      if (previewImg) previewImg.src = e.target.result;
      if (previewWrapper) previewWrapper.style.display = "block";
      if (infoText) {
        const sizeKb = Math.round(file.size / 1024);
        infoText.textContent = `${file.name} (${sizeKb} KB)`;
      }

      // Hide previous result
      const emptyState = document.getElementById("upload-empty-state");
      const resultPanel = document.getElementById("upload-result-panel");
      if (emptyState) emptyState.style.display = "block";
      if (resultPanel) resultPanel.style.display = "none";
    };
    reader.readAsDataURL(file);
  }

  async detectSignFromImage() {
    if (!this.selectedFile) {
      window.app.showToast("Please select an image file first.", "warning");
      return;
    }

    const detectBtn = document.getElementById("detect-sign-btn");
    const emptyState = document.getElementById("upload-empty-state");
    const resultPanel = document.getElementById("upload-result-panel");
    const originalBtnHtml = detectBtn ? detectBtn.innerHTML : "";

    try {
      if (detectBtn) {
        detectBtn.disabled = true;
        detectBtn.innerHTML = `<span>Processing...</span>`;
      }

      const formData = new FormData();
      formData.append("file", this.selectedFile);
      formData.append("target_lang", window.app ? window.app.targetLanguage : "ta");
      formData.append("save_history", "true");

      const res = await fetch("/api/predict/image", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (detectBtn) {
        detectBtn.disabled = false;
        detectBtn.innerHTML = originalBtnHtml;
      }

      if (!data.success) {
        if (data.has_hand === false) {
          window.app.showToast(data.message || "No hand gesture detected in image.", "warning");
        } else if (data.model_configured === false) {
          window.app.showToast(data.message || "Model not configured.", "warning");
        } else {
          window.app.showToast(data.error || "Recognition failed.", "error");
        }
        return;
      }

      // Display real prediction results
      if (emptyState) emptyState.style.display = "none";
      if (resultPanel) resultPanel.style.display = "block";

      const signEl = document.getElementById("upload-res-sign");
      const transEl = document.getElementById("upload-res-trans");
      const pronounceEl = document.getElementById("upload-res-pronounce");
      const confValEl = document.getElementById("upload-confidence-val");
      const confFillEl = document.getElementById("upload-confidence-fill");
      const presenceEl = document.getElementById("upload-hand-presence");
      const handednessEl = document.getElementById("upload-handedness");
      const dbStatusEl = document.getElementById("upload-db-log-status");

      const pct = Math.round((data.confidence || 0) * 100);

      if (signEl) signEl.textContent = data.sign || "—";
      if (transEl) transEl.textContent = `Translation: ${data.translation?.translated || '—'}`;
      if (pronounceEl) pronounceEl.textContent = data.translation?.pronunciation ? `(${data.translation.pronunciation})` : "";
      if (confValEl) confValEl.textContent = `${pct}%`;
      if (confFillEl) confFillEl.style.width = `${pct}%`;
      if (presenceEl) presenceEl.textContent = "Detected (21 Landmarks extracted)";
      if (handednessEl) handednessEl.textContent = data.handedness || "Right";
      if (dbStatusEl) dbStatusEl.textContent = data.history_id ? `Recorded to SQLite (ID #${data.history_id})` : "Not recorded";

      window.app.showToast(`Sign detected: ${data.sign} (${pct}% confidence)`, "success");
      window.app.loadDashboardStats();

    } catch (err) {
      console.error("Prediction error:", err);
      if (detectBtn) {
        detectBtn.disabled = false;
        detectBtn.innerHTML = originalBtnHtml;
      }
      window.app.showToast("Server error during sign prediction.", "error");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.uploadModule = new UploadModule();
});
