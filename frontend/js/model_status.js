/**
 * SignAI — Model Diagnostics & Training Controller
 * Model State Inspection, Hyperparameter Tuning & Real-Time Training Log Stream
 */

class ModelStatusModule {
  constructor() {
    this.pollInterval = null;
    this.init();
  }

  init() {
    const trainBtn = document.getElementById("start-train-btn");
    if (trainBtn) {
      trainBtn.addEventListener("click", () => this.startTraining());
    }

    this.loadStatus();
  }

  async loadStatus() {
    try {
      const res = await fetch("/api/model/status");
      const data = await res.json();

      const badge = document.getElementById("model-diag-badge");
      const badgeText = document.getElementById("model-diag-badge-text");
      const archEl = document.getElementById("model-diag-arch");
      const dateEl = document.getElementById("model-diag-date");
      const accEl = document.getElementById("model-diag-acc");
      const f1El = document.getElementById("model-diag-f1");
      const samplesEl = document.getElementById("model-diag-samples");
      const classesList = document.getElementById("model-supported-classes-list");

      if (data.configured) {
        if (badge) badge.className = "status-pill online";
        if (badgeText) badgeText.textContent = "Active & Ready";
        if (archEl) archEl.textContent = data.algorithm || "RandomForestClassifier";
        if (dateEl) dateEl.textContent = data.trained_at || "—";
        if (accEl) accEl.textContent = data.accuracy ? `${(data.accuracy * 100).toFixed(1)}%` : "N/A";
        if (f1El) f1El.textContent = data.f1_score ? data.f1_score.toFixed(3) : "N/A";
        if (samplesEl) samplesEl.textContent = (data.training_samples || 0) + (data.validation_samples || 0);

        if (classesList) {
          if (!data.classes || data.classes.length === 0) {
            classesList.innerHTML = `<span style="color: var(--text-dim); font-size: 0.82rem;">No classes recorded</span>`;
          } else {
            classesList.innerHTML = data.classes.map(c => `
              <div class="class-chip">
                <span>${c}</span>
              </div>
            `).join("");
          }
        }
      } else {
        if (badge) badge.className = "status-pill warning";
        if (badgeText) badgeText.textContent = "Not Configured";
        if (archEl) archEl.textContent = "RandomForest (Uninitialized)";
        if (dateEl) dateEl.textContent = "Not trained yet";
        if (accEl) accEl.textContent = "—";
        if (f1El) f1El.textContent = "—";
        if (samplesEl) samplesEl.textContent = "0";

        if (classesList) {
          classesList.innerHTML = `<span style="color: var(--accent-amber); font-size: 0.82rem;">No model configured. Add training data in Dataset Manager and click 'Train Model Now'.</span>`;
        }
      }

    } catch (err) {
      console.warn("Could not load model status:", err);
    }
  }

  async startTraining() {
    const treesInput = document.getElementById("train-trees");
    const depthInput = document.getElementById("train-depth");
    const trainBtn = document.getElementById("start-train-btn");
    const logBox = document.getElementById("training-terminal-logs");

    const nTrees = parseInt(treesInput?.value || "100", 10);
    const mDepth = parseInt(depthInput?.value || "15", 10);

    try {
      if (trainBtn) {
        trainBtn.disabled = true;
        trainBtn.innerHTML = `<span>Training in progress...</span>`;
      }

      if (logBox) {
        logBox.innerHTML = `<div class="log-entry">[Init] Requesting backend training pipeline...</div>`;
      }

      const res = await fetch("/api/train/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ n_estimators: nTrees, max_depth: mDepth })
      });

      const data = await res.json();
      if (!data.success) {
        if (trainBtn) {
          trainBtn.disabled = false;
          trainBtn.innerHTML = `<span>Train Model Now</span>`;
        }
        window.app.showToast(data.error || "Failed to start training.", "error");
        if (logBox) {
          logBox.innerHTML += `<div class="log-entry error">[FAILED] ${data.error}</div>`;
        }
        return;
      }

      window.app.showToast("Training pipeline started in background.", "info");

      // Poll progress every 750ms
      if (this.pollInterval) clearInterval(this.pollInterval);
      this.pollInterval = setInterval(() => this.pollTrainingProgress(), 750);

    } catch (err) {
      if (trainBtn) {
        trainBtn.disabled = false;
        trainBtn.innerHTML = `<span>Train Model Now</span>`;
      }
      window.app.showToast("Error starting training.", "error");
    }
  }

  async pollTrainingProgress() {
    const trainBtn = document.getElementById("start-train-btn");
    const stepEl = document.getElementById("train-progress-step");
    const pctEl = document.getElementById("train-progress-pct");
    const barEl = document.getElementById("train-progress-bar");
    const logBox = document.getElementById("training-terminal-logs");

    try {
      const res = await fetch("/api/train/status");
      const status = await res.json();

      if (stepEl) stepEl.textContent = `Status: ${status.current_step}`;
      if (pctEl) pctEl.textContent = `${status.progress}%`;
      if (barEl) barEl.style.width = `${status.progress}%`;

      // Render terminal logs
      if (logBox && status.logs && status.logs.length > 0) {
        logBox.innerHTML = status.logs.map(line => {
          let cls = "log-entry";
          if (line.includes("ERROR") || line.includes("Failed")) cls += " error";
          if (line.includes("SUCCESS") || line.includes("completed")) cls += " success";
          return `<div class="${cls}">${line}</div>`;
        }).join("");
        logBox.scrollTop = logBox.scrollHeight;
      }

      // Check completion
      if (!status.is_training) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;

        if (trainBtn) {
          trainBtn.disabled = false;
          trainBtn.innerHTML = `<span>Train Model Now</span>`;
        }

        if (status.error) {
          window.app.showToast(`Training failed: ${status.error}`, "error");
        } else if (status.progress >= 95) {
          window.app.showToast("Model trained and loaded successfully!", "success");
          this.loadStatus();
          window.app.checkSystemStatus();
          window.app.loadDashboardStats();
        }
      }

    } catch (err) {
      console.warn("Polling error:", err);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.modelStatusModule = new ModelStatusModule();
});
