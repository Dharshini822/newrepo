/**
 * SignAI — Recognition History Controller
 * SQLite Backed Recognition Logs, Source Filtering, Row Deletion & History Purge
 */

class HistoryModule {
  constructor() {
    this.init();
  }

  init() {
    const filterSelect = document.getElementById("history-source-filter");
    const clearBtn = document.getElementById("clear-history-btn");

    if (filterSelect) {
      filterSelect.addEventListener("change", () => this.loadHistory());
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => this.clearAllHistory());
    }

    this.loadHistory();
  }

  async loadHistory() {
    const tbody = document.getElementById("history-table-body");
    const sourceFilter = document.getElementById("history-source-filter")?.value || "";
    if (!tbody) return;

    try {
      const url = sourceFilter ? `/api/history?source=${encodeURIComponent(sourceFilter)}&limit=100` : `/api/history?limit=100`;
      const res = await fetch(url);
      const data = await res.json();

      if (!data.success || !data.history || data.history.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" class="empty-state">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <h4>No Recognition Events</h4>
              <p>Real detections from the live camera or image uploads will appear here.</p>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = data.history.map(item => `
        <tr id="hist-row-${item.id}">
          <td>#${item.id}</td>
          <td style="color: var(--text-muted); font-size: 0.8rem;">${item.timestamp}</td>
          <td><span class="badge badge-${item.source}">${item.source.toUpperCase()}</span></td>
          <td style="font-weight: 700; color: var(--accent-cyan); font-size: 1rem;">${item.sign_detected}</td>
          <td>${Math.round(item.confidence * 100)}%</td>
          <td>${item.target_lang.toUpperCase()}</td>
          <td style="font-weight: 600;">${item.translation}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="window.historyModule.deleteEntry(${item.id})" title="Delete entry" style="padding: 4px 8px;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
            </button>
          </td>
        </tr>
      `).join("");

    } catch (err) {
      console.warn("Could not load history:", err);
      tbody.innerHTML = `<tr><td colspan="8" class="empty-state">Failed to load recognition history.</td></tr>`;
    }
  }

  async deleteEntry(id) {
    try {
      const res = await fetch(`/api/history/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (data.success) {
        const row = document.getElementById(`hist-row-${id}`);
        if (row) row.remove();
        window.app.showToast(`Deleted history record #${id}`, "info");
        window.app.loadDashboardStats();
      }
    } catch (err) {
      window.app.showToast("Error deleting history record.", "error");
    }
  }

  async clearAllHistory() {
    if (!confirm("Are you sure you want to permanently clear all recognition history?")) {
      return;
    }

    try {
      const res = await fetch("/api/history/clear", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        window.app.showToast("Recognition history cleared.", "success");
        this.loadHistory();
        window.app.loadDashboardStats();
      }
    } catch (err) {
      window.app.showToast("Failed to clear history.", "error");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.historyModule = new HistoryModule();
});
