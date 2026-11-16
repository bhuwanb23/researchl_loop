/* ==========================================================================
   api.js — thin fetch wrapper for the ResearchLoop /api contract.
   Every response carries a top-level `mode` field (mock | live); the UI
   surfaces it via the mode chip (honesty gate, never hidden).
   ========================================================================== */

const API_BASE = ""; // same origin — FastAPI serves both /api and the SPA

/** The stable session id for this browser tab (F11 contribution log + exports). */
export function getSession() {
  return localStorage.getItem("rl_session") || "adhoc";
}

export async function apiFetch(path, options = {}) {
  const opts = { headers: {}, ...options };
  if (opts.body !== undefined && !opts.headers["Content-Type"]) {
    opts.headers["Content-Type"] = "application/json";
  }
  const res = await fetch(API_BASE + path, opts);
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) {
    const detail = (data && (data.detail || data.error)) || `HTTP ${res.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export function apiGet(path) {
  return apiFetch(path);
}

export function apiPost(path, body) {
  return apiFetch(path, { method: "POST", body: JSON.stringify(body ?? {}) });
}

export const api = {
  health: () => apiGet("/api/health"),
  scope: (question, sessionId, refinement = null) =>
    apiPost("/api/scope", { question, session_id: sessionId, refinement }),
  invent: (sessionId, plan, rows) =>
    apiPost("/api/datasets/invent", { session_id: sessionId, plan, rows }),
  augment: (sessionId, csv, targetRows, filename) =>
    apiPost("/api/datasets/augment", { session_id: sessionId, csv, target_rows: targetRows, filename }),
  audit: (datasetId) => apiGet(`/api/datasets/${encodeURIComponent(datasetId)}/audit`),
  receipt: (sessionId, datasetId, source, variant = "standard") =>
    apiPost("/api/receipts", { session_id: sessionId, dataset_id: datasetId, source, variant }),
  export: (sessionId) => apiGet(`/api/exports/${encodeURIComponent(sessionId)}`),
};
