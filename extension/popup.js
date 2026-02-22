const statusEl = document.getElementById("status");
const captureBtn = document.getElementById("capture-btn");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#a40000" : "#1b5e20";
}

function queryActiveTab() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      resolve(tabs[0]);
    });
  });
}

function extractFromTab(tabId) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, { type: "EXTRACT_JOB" }, (response) => {
      const runtimeError = chrome.runtime?.lastError;
      if (runtimeError?.message) {
        resolve({
          ok: false,
          error: `${runtimeError.message}. Refresh the LinkedIn tab and try again.`
        });
        return;
      }

      if (!response) {
        resolve({
          ok: false,
          error: "No response from page. Refresh the LinkedIn tab and try again."
        });
        return;
      }

      resolve(response);
    });
  });
}

async function captureCurrentJob() {
  captureBtn.disabled = true;
  setStatus("Capturing...");

  try {
    const tab = await queryActiveTab();
    if (!tab?.id || !tab.url?.startsWith("https://www.linkedin.com/jobs/")) {
      setStatus("Open a LinkedIn job page first.", true);
      return;
    }

    const extracted = await extractFromTab(tab.id);
    if (!extracted?.ok) {
      setStatus(extracted?.error || "Capture failed.", true);
      return;
    }

    const payload = {
      ...extracted.data,
      captured_at: new Date().toISOString()
    };

    const response = await fetch("http://localhost:8000/api/v1/jobs/capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      setStatus(result?.detail || `Capture failed (${response.status}).`, true);
      return;
    }

    setStatus(`Captured. App ${result.application_id.slice(0, 8)} created.`);
  } catch (_error) {
    setStatus("Could not reach backend at localhost:8000.", true);
  } finally {
    captureBtn.disabled = false;
  }
}

captureBtn.addEventListener("click", captureCurrentJob);
