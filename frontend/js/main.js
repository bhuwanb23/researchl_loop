/* ==========================================================================
   main.js — ResearchLoop SPA composition root: router + boot.
   Screens: Ask → Build → Audit → Receipt → Export.
   ========================================================================== */

import { apiGet, api } from "./api.js";
import { $, el } from "./ui.js";
import { initStepper } from "./stepper.js";
import { renderHome } from "./views/home.js";
import { renderBuild } from "./views/build.js";
import { renderAudit } from "./views/audit.js";
import { renderReceipt } from "./views/receipt.js";
import { renderExport } from "./views/export.js";

const VIEWS = {
  "view-ask": renderHome,
  "view-build": renderBuild,
  "view-audit": renderAudit,
  "view-receipt": renderReceipt,
  "view-export": renderExport,
};

let currentMode = "mock";

function route() {
  const name = (location.hash.replace("#", "") || "view-ask") in VIEWS ? location.hash.replace("#", "") : "view-ask";
  document.querySelectorAll(".screen").forEach((s) => s.remove());
  const host = $("main");
  (VIEWS[name] || renderHome)(host);
  window.scrollTo({ top: 0, behavior: "auto" });

  // reflect stepper position when navigating directly
  const idx = ["view-ask", "view-build", "view-audit", "view-receipt", "view-export"].indexOf(name);
  window.__pipeline?.to(Math.max(0, idx));
}

// shared navigation used by views
window.__go = (name) => {
  location.hash = name;
};

async function boot() {
  initStepper();

  // Mode chip (honesty gate) — never hide which mode the backend is running in.
  try {
    const health = await apiGet("/api/health");
    currentMode = health.llm_mode;
    localStorage.setItem("rl_llm_mode", currentMode);
  } catch {
    currentMode = "mock";
  }
  const chip = $("#mode-chip");
  if (chip) {
    chip.className = `badge mode ${currentMode === "live" ? "live" : "warn"}`;
    chip.textContent = currentMode === "live" ? "Live LLM" : "Mock mode";
    chip.title =
      currentMode === "mock"
        ? "The demo runs in labeled mock mode: deterministic offline generation, no external model called."
        : "Backend is using the live model and real Adaption service.";
  }

  window.addEventListener("hashchange", route);
  route();

  // health refresh every 30s (mode can switch after env changes)
  setInterval(async () => {
    try {
      const health = await apiGet("/api/health");
      if (health.llm_mode !== currentMode) {
        currentMode = health.llm_mode;
        location.reload();
      }
    } catch {
      /* server temporarily unavailable — keep current chip */
    }
  }, 30000);
}

// expose the live api for views that call it directly (home/build pass it in)
window.__api = api;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

// keep a stable session id for contribution/export accounting (F11)
(function ensureSession() {
  let sid = localStorage.getItem("rl_session");
  if (!sid) {
    sid = "sess-" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("rl_session", sid);
  }
})();

// log the student's first load in the session (F11)
(async function logStart() {
  try {
    const sid = localStorage.getItem("rl_session");
    await fetch(`/api/sessions/${sid}/contributions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "session_started", detail: "opened the research flow" }),
    });
  } catch {
    /* best-effort, never blocks the UI */
  }
})();
