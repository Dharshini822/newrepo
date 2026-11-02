/**
 * SignAI — App Core Controller
 * Navigation, View Routing, State Management, Toasts & Telemetry
 */

class SignAIApp {
  constructor() {
    this.currentView = "dashboard";
    this.targetLanguage = "ta";
    this.speechRate = 1.0;
    this.apiBase = "/api";
    this.init();
  }

  init() {
    this.bindNavigation();
    this.bindThemeToggle();
    this.bindGlobalLanguage();
    this.checkSystemStatus();
    this.loadDashboardStats();

    // Poll system status every 12 seconds
    setInterval(() => this.checkSystemStatus(), 12000);
  }

  bindNavigation() {
    const navLinks = document.querySelectorAll(".nav-link");
    navLinks.forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const view = link.getAttribute("data-view");
        this.switchView(view);
      });
    });
  }

  switchView(viewName) {
    if (!viewName) return;

    // Stop webcam if leaving camera view
    if (this.currentView === "camera" && viewName !== "camera" && window.cameraModule) {
      window.cameraModule.stopCamera();
    }

    // Update active nav link
    document.querySelectorAll(".nav-link").forEach(el => {
      if (el.getAttribute("data-view") === viewName) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    });

    // Update view section visibility
    document.querySelectorAll(".view-section").forEach(sec => {
      sec.classList.remove("active");
    });

    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) {
      targetSection.classList.add("active");
    }

    // Update page title
    const titles = {
      dashboard: "Dashboard Overview",
      camera: "Live Webcam Recognition",
      upload: "Image Upload & Detection",
      dataset: "Dataset Manager",
      translation: "Multilingual Translation & Glossary",
      history: "Recognition Event History",
      model: "Model Diagnostics & Training",
      settings: "Preferences & System Info"
    };

    const titleEl = document.getElementById("page-title");
    if (titleEl) {
      titleEl.textContent = titles[viewName] || "Dashboard";
    }

    this.currentView = viewName;

    // Trigger view-specific refreshes
    if (viewName === "dashboard") {
      this.loadDashboardStats();
    } else if (viewName === "dataset" && window.datasetModule) {
      window.datasetModule.loadStats();
      window.datasetModule.loadSamples();
    } else if (viewName === "history" && window.historyModule) {
      window.historyModule.loadHistory();
    } else if (viewName === "model" && window.modelStatusModule) {
      window.modelStatusModule.loadStatus();
    }
  }

  bindThemeToggle() {
    const btn = document.getElementById("theme-toggle-btn");
    if (!btn) return;

    btn.addEventListener("click", () => {
      document.body.classList.toggle("light-theme");
      const isLight = document.body.classList.contains("light-theme");
      localStorage.setItem("signai_theme", isLight ? "light" : "dark");
    });

    if (localStorage.getItem("signai_theme") === "light") {
      document.body.classList.add("light-theme");
    }
  }

  bindGlobalLanguage() {
    const langSelect = document.getElementById("global-lang-select");
    const camLang = document.getElementById("cam-target-lang");
    const settingsLang = document.getElementById("settings-default-lang");

    if (langSelect) {
      langSelect.addEventListener("change", (e) => {
        this.targetLanguage = e.target.value;
        if (camLang) camLang.value = this.targetLanguage;
        if (settingsLang) settingsLang.value = this.targetLanguage;
        this.showToast(`Target language set to: ${e.target.options[e.target.selectedIndex].text}`, "info");
      });
    }

    if (settingsLang) {
      settingsLang.addEventListener("change", (e) => {
        this.targetLanguage = e.target.value;
        if (langSelect) langSelect.value = this.targetLanguage;
        if (camLang) camLang.value = this.targetLanguage;
      });
    }
  }

  async checkSystemStatus() {
    try {
      const res = await fetch(`${this.apiBase}/status`);
      const data = await res.json();

      const backendPill = document.getElementById("backend-status-pill");
      const backendText = document.getElementById("backend-status-text");

      if (data.status === "online") {
        backendPill.className = "status-pill online";
        backendText.textContent = "Backend: Online";
      }

      // Check model status
      const modelRes = await fetch(`${this.apiBase}/model/status`);
      const modelData = await modelRes.json();

      const modelPill = document.getElementById("model-status-pill");
      const modelText = document.getElementById("model-status-text");
      const dashModel = document.getElementById("dash-model-status");
      const dashClasses = document.getElementById("dash-supported-classes");

      if (modelData.configured) {
        modelPill.className = "status-pill online";
        modelText.textContent = "Model: Active";
        if (dashModel) dashModel.textContent = "Active";
        if (dashClasses) dashClasses.textContent = modelData.num_classes || 0;
      } else {
        modelPill.className = "status-pill warning";
        modelText.textContent = "Model: Not Configured";
        if (dashModel) dashModel.textContent = "Not Configured";
        if (dashClasses) dashClasses.textContent = "0";
      }
    } catch (err) {
      const backendPill = document.getElementById("backend-status-pill");
      const backendText = document.getElementById("backend-status-text");
      if (backendPill && backendText) {
        backendPill.className = "status-pill offline";
        backendText.textContent = "Backend: Offline";
      }
    }
  }

  async loadDashboardStats() {
    try {
      // Load SQLite telemetry
      const res = await fetch(`${this.apiBase}/system/stats`);
      const json = await res.json();
      if (json.success && json.stats) {
        const totalDet = document.getElementById("dash-total-detections");
        if (totalDet) totalDet.textContent = json.stats.total_detections || 0;
      }

      // Load dataset count
      const dsRes = await fetch(`${this.apiBase}/dataset/stats`);
      const dsJson = await dsRes.json();
      if (dsJson.success && dsJson.stats) {
        const dsSamples = document.getElementById("dash-dataset-samples");
        if (dsSamples) dsSamples.textContent = dsJson.stats.total_images || 0;
      }

      // Load recent history table preview
      const histRes = await fetch(`${this.apiBase}/history?limit=5`);
      const histJson = await histRes.json();
      const tbody = document.getElementById("dash-recent-history-body");
      if (tbody && histJson.success) {
        if (!histJson.history || histJson.history.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No recognition events recorded yet.</td></tr>`;
        } else {
          tbody.innerHTML = histJson.history.map(row => `
            <tr>
              <td>${row.timestamp}</td>
              <td><span class="badge badge-${row.source}">${row.source.toUpperCase()}</span></td>
              <td style="font-weight: 700; color: var(--accent-cyan);">${row.sign_detected}</td>
              <td>${Math.round(row.confidence * 100)}%</td>
              <td style="font-weight: 600;">${row.translation || "—"}</td>
            </tr>
          `).join("");
        }
      }
    } catch (e) {
      console.warn("Could not refresh dashboard stats:", e);
    }
  }

  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }
}

// Instantiate global app controller
document.addEventListener("DOMContentLoaded", () => {
  window.app = new SignAIApp();
});
