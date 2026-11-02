/**
 * SignAI — Dataset Manager Controller
 * ZIP & Image Uploads, Distribution Analytics, Sample Gallery & Manifest Export
 */

class DatasetModule {
  constructor() {
    this.classes = [];
    this.init();
  }

  init() {
    this.bindZipUpload();
    this.bindSingleUpload();
    this.bindGalleryControls();
    this.bindManifestExport();
    this.loadStats();
    this.loadSamples();
  }

  bindZipUpload() {
    const dropzone = document.getElementById("zip-dropzone");
    const fileInput = document.getElementById("zip-file-input");
    const statusEl = document.getElementById("zip-upload-status");

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
          this.uploadZipFile(e.dataTransfer.files[0]);
        }
      });

      fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
          this.uploadZipFile(e.target.files[0]);
        }
      });
    }
  }

  async uploadZipFile(file) {
    if (!file.name.toLowerCase().endsWith(".zip")) {
      window.app.showToast("Only .zip archives are supported.", "error");
      return;
    }

    const statusEl = document.getElementById("zip-upload-status");
    if (statusEl) {
      statusEl.innerHTML = `<span style="color: var(--accent-cyan);">Uploading and safely extracting archive...</span>`;
    }

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("default_split", "train");

      const res = await fetch("/api/dataset/upload-zip", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      if (!data.success) {
        if (statusEl) statusEl.innerHTML = `<span style="color: var(--accent-rose);">${data.error}</span>`;
        window.app.showToast(data.error || "ZIP upload failed.", "error");
        return;
      }

      const resInfo = data.result;
      const msg = `Successfully imported ${resInfo.organized_count} images across classes: ${resInfo.classes_detected.join(", ")}`;
      if (statusEl) statusEl.innerHTML = `<span style="color: var(--accent-emerald);">${msg}</span>`;
      window.app.showToast("Dataset ZIP extracted and organized safely!", "success");

      this.loadStats();
      this.loadSamples();
      window.app.loadDashboardStats();

    } catch (err) {
      console.error("ZIP upload error:", err);
      if (statusEl) statusEl.innerHTML = `<span style="color: var(--accent-rose);">Upload failed.</span>`;
      window.app.showToast("Failed to upload dataset ZIP.", "error");
    }
  }

  bindSingleUpload() {
    const form = document.getElementById("single-sample-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const classInput = document.getElementById("sample-class-name");
      const splitSelect = document.getElementById("sample-split");
      const fileInput = document.getElementById("sample-file-input");
      const submitBtn = document.getElementById("save-sample-btn");

      if (!fileInput.files || !fileInput.files[0]) {
        window.app.showToast("Please choose an image file.", "warning");
        return;
      }

      try {
        if (submitBtn) submitBtn.disabled = true;

        const formData = new FormData();
        formData.append("class_name", classInput.value.trim());
        formData.append("split", splitSelect.value);
        formData.append("file", fileInput.files[0]);

        const res = await fetch("/api/dataset/upload-image", {
          method: "POST",
          body: formData
        });

        const data = await res.json();
        if (submitBtn) submitBtn.disabled = false;

        if (!data.success) {
          window.app.showToast(data.error || "Failed to save sample.", "error");
          return;
        }

        window.app.showToast(`Saved sample to class '${data.sample.class_name}'!`, "success");
        fileInput.value = "";
        
        this.loadStats();
        this.loadSamples();
        window.app.loadDashboardStats();

      } catch (err) {
        if (submitBtn) submitBtn.disabled = false;
        window.app.showToast("Error uploading sample.", "error");
      }
    });
  }

  async loadStats() {
    try {
      const res = await fetch("/api/dataset/stats");
      const data = await res.json();
      if (!data.success) return;

      const stats = data.stats;
      this.classes = stats.classes || [];

      // Update stat cards
      const totEl = document.getElementById("ds-total-images");
      const clsEl = document.getElementById("ds-total-classes");
      const trnEl = document.getElementById("ds-train-images");
      const valEl = document.getElementById("ds-val-images");

      if (totEl) totEl.textContent = stats.total_images;
      if (clsEl) clsEl.textContent = stats.num_classes;
      if (trnEl) trnEl.textContent = stats.train_images;
      if (valEl) valEl.textContent = stats.val_images;

      // Update class distribution chips
      const chipsContainer = document.getElementById("dataset-classes-chips");
      if (chipsContainer) {
        if (!stats.distribution || stats.distribution.length === 0) {
          chipsContainer.innerHTML = `<span style="color: var(--text-dim); font-size: 0.82rem;">No classes found in dataset. Upload samples above.</span>`;
        } else {
          chipsContainer.innerHTML = stats.distribution.map(item => `
            <div class="class-chip">
              <span>${item.class_name}</span>
              <span class="chip-count">${item.total_count} (T:${item.train_count} V:${item.val_count})</span>
            </div>
          `).join("");
        }
      }

      // Update gallery class filter dropdown
      const filterSelect = document.getElementById("gallery-class-filter");
      if (filterSelect) {
        const currentVal = filterSelect.value;
        filterSelect.innerHTML = `<option value="">All Classes (${stats.total_images})</option>` +
          this.classes.map(c => `<option value="${c}" ${c === currentVal ? 'selected' : ''}>${c}</option>`).join("");
      }

    } catch (err) {
      console.warn("Could not load dataset stats:", err);
    }
  }

  bindGalleryControls() {
    const filterSelect = document.getElementById("gallery-class-filter");
    const refreshBtn = document.getElementById("refresh-gallery-btn");

    if (filterSelect) {
      filterSelect.addEventListener("change", () => this.loadSamples());
    }

    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        this.loadStats();
        this.loadSamples();
      });
    }
  }

  async loadSamples() {
    const gallery = document.getElementById("dataset-sample-gallery");
    if (!gallery) return;

    const classFilter = document.getElementById("gallery-class-filter")?.value || "";
    const url = classFilter ? `/api/dataset/samples?class_name=${encodeURIComponent(classFilter)}&limit=60` : `/api/dataset/samples?limit=60`;

    try {
      const res = await fetch(url);
      const json = await res.json();

      if (!json.success || !json.data.samples || json.data.samples.length === 0) {
        gallery.innerHTML = `
          <div class="empty-state" style="grid-column: 1 / -1;">
            <p>No sample images stored yet in this partition.</p>
          </div>
        `;
        return;
      }

      gallery.innerHTML = json.data.samples.map(sample => `
        <div class="sample-card" id="sample-${sample.filename.replace(/[^a-zA-Z0-9]/g, '_')}">
          <img class="sample-thumb" src="/api/dataset/sample-image/${encodeURIComponent(sample.relative_path)}" alt="${sample.class_name}" loading="lazy">
          <div class="sample-meta">
            <div>
              <div class="sample-label">${sample.class_name}</div>
              <div style="font-size: 0.68rem; color: var(--text-dim); text-transform: uppercase;">${sample.split}</div>
            </div>
            <button class="sample-delete-btn" onclick="window.datasetModule.deleteSample('${sample.relative_path}')" title="Delete sample">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
            </button>
          </div>
        </div>
      `).join("");

    } catch (err) {
      console.warn("Could not load samples:", err);
    }
  }

  async deleteSample(relativePath) {
    if (!confirm(`Are you sure you want to remove sample: ${relativePath}?`)) {
      return;
    }

    try {
      const res = await fetch("/api/dataset/delete-sample", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ relative_path: relativePath })
      });

      const data = await res.json();
      if (data.success) {
        window.app.showToast("Sample removed.", "info");
        this.loadStats();
        this.loadSamples();
        window.app.loadDashboardStats();
      } else {
        window.app.showToast(data.error || "Could not delete sample.", "error");
      }
    } catch (err) {
      window.app.showToast("Error deleting sample.", "error");
    }
  }

  bindManifestExport() {
    const btn = document.getElementById("export-manifest-btn");
    if (!btn) return;

    btn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/dataset/manifest");
        const manifest = await res.json();

        const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "signai_dataset_manifest.json";
        a.click();
        URL.revokeObjectURL(url);

        window.app.showToast("Dataset manifest downloaded.", "success");
      } catch (err) {
        window.app.showToast("Failed to export manifest.", "error");
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.datasetModule = new DatasetModule();
});
