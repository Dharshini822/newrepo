/**
 * SignAI — Translation & Text-to-Speech Controller
 * English ↔ Tamil Translation, Browser Web Speech API, ISL Glossary Table
 */

class TranslationModule {
  constructor() {
    this.glossary = [];
    this.speechSynth = window.speechSynthesis || null;
    this.init();
  }

  init() {
    const runBtn = document.getElementById("run-trans-btn");
    const speakBtn = document.getElementById("trans-speak-btn");
    const stopBtn = document.getElementById("trans-stop-btn");
    const searchInput = document.getElementById("glossary-search");
    const testTtsBtn = document.getElementById("test-tts-btn");

    if (runBtn) {
      runBtn.addEventListener("click", () => this.runManualTranslation());
    }

    if (speakBtn) {
      speakBtn.addEventListener("click", () => {
        const text = document.getElementById("trans-output-text")?.textContent;
        const lang = document.getElementById("trans-target-lang")?.value || "ta";
        if (text && text !== "—") this.speakText(text, lang);
      });
    }

    if (stopBtn) {
      stopBtn.addEventListener("click", () => this.stopSpeech());
    }

    if (testTtsBtn) {
      testTtsBtn.addEventListener("click", () => {
        const lang = window.app ? window.app.targetLanguage : "ta";
        const sampleText = lang === "ta" ? "வணக்கம். சைகை மொழி அமைப்புக்கு நல்வரவு." : "Hello. Welcome to the Sign Language Communication System.";
        this.speakText(sampleText, lang);
      });
    }

    if (searchInput) {
      searchInput.addEventListener("input", (e) => this.filterGlossary(e.target.value));
    }

    this.loadGlossary();
  }

  async runManualTranslation() {
    const inputEl = document.getElementById("trans-input-text");
    const targetLangEl = document.getElementById("trans-target-lang");
    const outEl = document.getElementById("trans-output-text");
    const pronounceEl = document.getElementById("trans-pronunciation-text");
    const speakBtn = document.getElementById("trans-speak-btn");
    const stopBtn = document.getElementById("trans-stop-btn");

    const text = inputEl?.value.trim();
    if (!text) {
      window.app.showToast("Please enter text or a sign gloss to translate.", "warning");
      return;
    }

    const targetLang = targetLangEl?.value || "ta";

    try {
      const res = await fetch("/api/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, target_lang: targetLang })
      });

      const data = await res.json();
      if (!data.success) {
        window.app.showToast(data.error || "Translation failed.", "error");
        return;
      }

      const result = data.result;
      if (outEl) outEl.textContent = result.translated || text;
      if (pronounceEl) pronounceEl.textContent = result.pronunciation ? `Pronunciation: ${result.pronunciation}` : "";

      if (speakBtn) speakBtn.disabled = false;
      if (stopBtn) stopBtn.disabled = false;

    } catch (err) {
      window.app.showToast("Translation service error.", "error");
    }
  }

  speakText(text, language = "ta") {
    if (!this.speechSynth) {
      window.app.showToast("Speech synthesis is not supported on this browser.", "warning");
      return;
    }

    if (!text || text === "—") return;

    // Cancel any ongoing speech
    this.speechSynth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const speechRate = parseFloat(document.getElementById("settings-speech-rate")?.value || "1.0");
    utterance.rate = isNaN(speechRate) ? 1.0 : speechRate;

    const voices = this.speechSynth.getVoices();
    let selectedVoice = null;

    if (language === "ta") {
      utterance.lang = "ta-IN";
      selectedVoice = voices.find(v => v.lang.startsWith("ta") || v.name.toLowerCase().includes("tamil"));
    } else {
      utterance.lang = "en-US";
      selectedVoice = voices.find(v => v.lang.startsWith("en"));
    }

    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    utterance.onerror = (e) => {
      console.warn("Speech synthesis error:", e);
    };

    this.speechSynth.speak(utterance);
  }

  stopSpeech() {
    if (this.speechSynth) {
      this.speechSynth.cancel();
      window.app.showToast("Audio stopped.", "info");
    }
  }

  async loadGlossary() {
    try {
      const res = await fetch("/api/translate/glossary");
      const data = await res.json();
      if (data.success && data.glossary) {
        this.glossary = data.glossary;
        this.renderGlossary(this.glossary);
      }
    } catch (err) {
      console.warn("Could not load glossary:", err);
    }
  }

  renderGlossary(items) {
    const tbody = document.getElementById("glossary-table-body");
    if (!tbody) return;

    if (!items || items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No matching signs found.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(item => `
      <tr>
        <td style="font-weight: 700; color: var(--accent-cyan);">${item.sign}</td>
        <td>${item.english}</td>
        <td style="font-weight: 600;">${item.tamil}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="window.translationModule.speakText('${item.tamil}', 'ta')" title="Pronounce in Tamil">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
            <span>Play</span>
          </button>
        </td>
      </tr>
    `).join("");
  }

  filterGlossary(query) {
    const q = (query || "").toLowerCase().trim();
    if (!q) {
      this.renderGlossary(this.glossary);
      return;
    }
    const filtered = this.glossary.filter(item => 
      item.sign.toLowerCase().includes(q) ||
      item.english.toLowerCase().includes(q) ||
      item.tamil.toLowerCase().includes(q)
    );
    this.renderGlossary(filtered);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.translationModule = new TranslationModule();
});
