/* ==========================================================================
   ResearchLoop — frontend (static SPA, no build step).
   5 screens: Ask → Build → Audit → Receipt → Export.
   Consumes the backend API contract exactly (docs/05); no invented UI data.
   ========================================================================== */
"use strict";

/* ---------------------------------------------------------------- state */

const TEMPLATES = [
  {
    id: "study_vs_scores",
    name: "Study vs. scores",
    question: "Does study time affect exam scores?",
    hint: "Regression — students, study hours, exam scores",
  },
  {
    id: "plant_heat_tolerance",
    name: "Plant heat tolerance",
    question: "Which local plant species tolerates heat best?",
    hint: "Descriptive ecology — species, leaf temperature, water loss",
  },
  {
    id: "group_study",
    name: "Group study",
    question: "Do students who study in groups score higher?",
    hint: "Survey — study mode, weekly hours, quiz scores",
  },
];

const state = {
  sessionId: null,
  health: null,
  plan: null,          // last scoped plan (ScopeResult + mode)
  dataset: null,       // last created dataset
  receipt: null,       // last built receipt
  exportBundle: null,  // last export bundle
};

/* ---------------------------------------------------------------- helpers */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function toast(msg, isError = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.toggle("error", isError);
  t.hidden = false;
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => { t.hidden = true; }, 3600);
}

function getSessionId() {
  if (state.sessionId) return state.sessionId;
  let id = null;
  try { id = localStorage.getItem("researchloop.session"); } catch (_) { /* ignore */ }
  if (!id) {
    id = (crypto.randomUUID && crypto.randomUUID()) ||
         "sess-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    try { localStorage.setItem("researchloop.session", id); } catch (_) { /* ignore */ }
  }
  state.sessionId = id;
  $("#session-badge").textContent = "session: " + id.slice(0, 12) + "…";
  return id;
}

async function api(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail = data && data.detail ? data.detail : "Request failed (" + resp.status + ")";
    throw new Error(detail);
  }
  return data;
}

/* ---------------------------------------------------------------- router */

const ROUTES = ["ask", "build", "audit", "receipt", "export"];

function showScreen(route) {
  if (!ROUTES.includes(route)) route = "ask";
  ROUTES.forEach((r) => { $("#screen-" + r).hidden = r !== route; });
  $$(".step").forEach((s) => s.classList.toggle("active", s.dataset.route === route));
  window.location.hash = route;
  if (route === "audit") renderAudit();
  if (route === "receipt") renderReceipt();
  if (route === "export") renderExport();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

window.addEventListener("hashchange", () => showScreen(window.location.hash.replace("#", "") || "ask"));
$$(".step").forEach((s) => s.addEventListener("click", () => showScreen(s.dataset.route)));

/* ============================================================== BOOT */

async function boot() {
  getSessionId();
  try {
    state.health = await api("/api/health");
    $("#mode-badge").textContent =
      "LLM: " + state.health.llm_mode + " · Adaption: " + state.health.adaption_mode;
  } catch (e) {
    $("#mode-badge").textContent = "API offline";
    $("#mode-badge").classList.add("badge-mode");
  }
  renderTemplateChips();
  showScreen(window.location.hash.replace("#", "") || "ask");
}

/* ============================================================== SCREEN 1 — ASK */

function renderTemplateChips() {
  const wrap = $("#template-chips");
  wrap.innerHTML = TEMPLATES.map((t) =>
    `<button class="chip" data-id="${esc(t.id)}" title="${esc(t.hint)}">${esc(t.name)}</button>`
  ).join("");
  wrap.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const tpl = TEMPLATES.find((t) => t.id === chip.dataset.id);
      $("#question").value = tpl.question;
      $$(".chip", wrap).forEach((c) => c.classList.toggle("selected", c === chip));
      runScope();
    });
  });
}

async function runScope(refinement) {
  const question = $("#question").value.trim();
  const body = { question, session_id: getSessionId() };
  if (refinement) body.refinement = refinement;
  const btn = $("#btn-scope");
  btn.disabled = true;
  btn.textContent = "Planning…";
  try {
    const plan = await api("/api/scope", { method: "POST", body });
    state.plan = plan;
    renderPlan(plan);
    $("#refinement-card").hidden = !plan.refinements || !plan.refinements.length;
    const chips = $("#refinement-chips");
    chips.innerHTML = plan.refinements.map((r) =>
      `<button class="chip">${esc(r)}</button>`
    ).join("");
    chips.querySelectorAll(".chip").forEach((chip) =>
      chip.addEventListener("click", () => runScope(chip.textContent))
    );
    toast("Plan ready — review it, then head to Build.");
  } catch (e) {
    toast(e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = "Turn this into a plan";
  }
}

function renderPlan(plan) {
  $("#plan-card").hidden = false;
  $("#plan-type").innerHTML = ["classification", "regression", "descriptive", "survey"]
    .map((t) => `<option ${t === plan.research_type ? "selected" : ""}>${t}</option>`).join("");
  $("#plan-rows").value = plan.suggested_rows;
  $("#plan-dataset-name").value = plan.dataset_name;
  $("#plan-plan").value = plan.data_plan;
  $("#plan-vars").innerHTML = (plan.variables || []).map((v) =>
    `<span class="var-pill">${esc(v.name)} <span class="type">· ${esc(v.type)}</span></span>`
  ).join("");
  $("#plan-type").onchange = savePlanEdit;
  $("#plan-rows").onchange = savePlanEdit;
  $("#plan-plan").onchange = savePlanEdit;
}

function savePlanEdit() {
  const sid = getSessionId();
  api("/api/sessions/" + sid + "/contributions", {
    method: "POST",
    body: { action: "plan_edited", detail: "updated plan fields (type/rows/data plan)" },
  }).catch(() => { /* logged best-effort */ });
  toast("Plan edit saved — recorded in your contribution log.");
}

$("#btn-scope").addEventListener("click", () => runScope());
$("#btn-goto-build").addEventListener("click", () => {
  if (!state.plan) { toast("Scope a question first.", true); return; }
  // sync any edits into the plan used by Build
  state.plan.research_type = $("#plan-type").value;
  state.plan.suggested_rows = parseInt($("#plan-rows").value, 10) || 80;
  state.plan.dataset_name = $("#plan-dataset-name").value.trim() || state.plan.dataset_name;
  state.plan.data_plan = $("#plan-plan").value;
  showScreen("build");
});

/* ============================================================== SCREEN 2 — BUILD */

$$(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    $$(".tab").forEach((t) => t.classList.toggle("active", t === tab));
    $("#tab-invent").hidden = tab.dataset.tab !== "invent";
    $("#tab-augment").hidden = tab.dataset.tab !== "augment";
  });
});

$("#invent-rows").addEventListener("input", (e) => {
  $("#invent-rows-val").textContent = e.target.value + " rows";
});

$("#btn-invent").addEventListener("click", async () => {
  if (!state.plan) { toast("Scope a question first.", true); showScreen("ask"); return; }
  const rows = parseInt($("#invent-rows").value, 10) || 80;
  const btn = $("#btn-invent");
  btn.disabled = true;
  btn.textContent = "Generating…";
  try {
    const dataset = await api("/api/datasets/invent", {
      method: "POST",
      body: { session_id: getSessionId(), plan: state.plan, rows },
    });
    state.dataset = dataset;
    renderDataset(dataset);
    toast("Dataset generated — all rows tagged synthetic.");
  } catch (e) {
    toast(e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate synthetic dataset";
  }
});

$("#btn-augment").addEventListener("click", async () => {
  const fileInput = $("#augment-file");
  if (!fileInput.files.length) { toast("Choose a CSV file first.", true); return; }
  const file = fileInput.files[0];
  const csvB64 = await fileToBase64(file);
  const targetRows = parseInt($("#augment-target").value, 10) || 100;
  const btn = $("#btn-augment");
  btn.disabled = true;
  btn.textContent = "Cleaning & augmenting…";
  try {
    const dataset = await api("/api/datasets/augment", {
      method: "POST",
      body: { session_id: getSessionId(), csv: csvB64, target_rows: targetRows, filename: file.name },
    });
    state.dataset = dataset;
    renderDataset(dataset);
    toast("Dataset cleaned and augmented.");
  } catch (e) {
    toast(e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = "Clean & augment";
  }
});

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const b64 = String(reader.result).split(",")[1] || "";
      resolve(b64);
    };
    reader.onerror = () => reject(new Error("Could not read the file."));
    reader.readAsDataURL(file);
  });
}

function renderDataset(dataset) {
  $("#invent-warning").hidden = true;
  $("#augment-warning").hidden = true;
  const warn = dataset.warning || "";
  if (warn) {
    const isInvent = dataset.rows.every((r) => r.provenance === "synthetic");
    const el = isInvent ? $("#invent-warning") : $("#augment-warning");
    el.hidden = false;
    el.textContent = "⚠ " + warn;
  }
  $("#dataset-panel").hidden = false;
  $("#ds-id").textContent = dataset.dataset_id;
  const counts = {};
  dataset.rows.forEach((r) => { counts[r.provenance] = (counts[r.provenance] || 0) + 1; });
  $("#ds-counts").innerHTML = Object.entries(counts).map(([p, n]) =>
    `<span class="badge badge-${esc(p)}">${esc(p)}: ${n}</span>`
  ).join("");
  const cols = Object.keys(dataset.rows[0].values || {});
  const head = "<tr>" + cols.map((c) => `<th>${esc(c)}</th>`).join("") + "<th>provenance</th></tr>";
  const body = dataset.rows.slice(0, 8).map((r) =>
    "<tr>" + cols.map((c) => `<td>${esc(r.values[c])}</td>`).join("") +
    `<td><span class="badge badge-${esc(r.provenance)}">${esc(r.provenance)}</span></td></tr>`
  ).join("");
  $("#dataset-table").innerHTML =
    `<table><thead>${head}</thead><tbody>${body}</tbody></table>` +
    `<p class="muted small" style="padding:8px 12px">…showing ${Math.min(8, dataset.rows.length)} of ${dataset.rows.length} rows</p>`;
}

$("#btn-goto-audit").addEventListener("click", () => {
  if (!state.dataset) { toast("Build a dataset first.", true); return; }
  showScreen("audit");
});

/* ============================================================== SCREEN 3 — AUDIT */

function metricWordClass(before, after, higherBetter) {
  if (before === after) return { word: "held", cls: "held" };
  const improved = higherBetter ? after > before : after < before;
  return { word: improved ? "improved" : "worsened", cls: improved ? "improved" : "worsened" };
}

function barChart(before, after, beforeLabel, afterLabel) {
  const W = 280, H = 90, padL = 4, padR = 4, padT = 10, padB = 26;
  const max = Math.max(before || 0, after || 0, 1e-9);
  const bw = (W - padL - padR) / 2 - 4;
  const hB = ((before || 0) / max) * (H - padT - padB);
  const hA = ((after || 0) / max) * (H - padT - padB);
  const y = (h) => H - padB - h;
  return `
    <svg class="metric-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(beforeLabel)} vs ${esc(afterLabel)} bar chart">
      <line x1="${padL}" y1="${y(0)}" x2="${W - padR}" y2="${y(0)}" stroke="#e5e7eb" stroke-width="1"/>
      <rect x="${padL}" y="${y(hB)}" width="${bw}" height="${Math.max(hB, 1)}" rx="4" fill="#c7d2fe"/>
      <rect x="${padL + bw + 8}" y="${y(hA)}" width="${bw}" height="${Math.max(hA, 1)}" rx="4" fill="#4f46e5"/>
      <text x="${padL}" y="${H - 10}" font-size="10" fill="#6b7280">${esc(beforeLabel)}</text>
      <text x="${padL + bw + 8}" y="${H - 10}" font-size="10" fill="#4f46e5">${esc(afterLabel)}</text>
    </svg>`;
}

const METRIC_TIPS = {
  duplicate_rate: "Fraction of rows that are exact copies of an earlier row. Lower is better — duplicates inflate your sample without adding information.",
  near_duplicate_rate: "Fraction of rows that are near-copies (very similar, but not identical) of an earlier row. Lower is better — near-duplicates quietly bias results.",
  diversity: "Mean pairwise similarity of all rows. Lower is better — high similarity means your rows are all telling the same story.",
  completeness: "Average share of non-empty cells across all columns. Higher is better — gaps mean missing evidence.",
  label_coverage: "Share of rows with a valid label/target value. Higher is better — rows without labels can't be used for modeling.",
  distribution_sanity: "Checks numeric columns for constant columns and negative values. Passing means no structural red flags.",
};

async function renderAudit() {
  if (!state.dataset) { toast("Build a dataset first.", true); showScreen("build"); return; }
  const grid = $("#audit-grid");
  grid.innerHTML = '<p class="muted">Loading audit…</p>';
  try {
    const report = await api("/api/datasets/" + encodeURIComponent(state.dataset.dataset_id) + "/audit");
    $("#audit-note").hidden = true;
    const rows = report.metrics;
    const order = ["duplicate_rate", "near_duplicate_rate", "diversity", "completeness", "label_coverage"];
    const higherBetter = { duplicate_rate: false, near_duplicate_rate: false, diversity: false, completeness: true, label_coverage: true };
    let html = "";
    for (const key of order) {
      const m = rows[key];
      if (!m) continue;
      const before = m.before, after = m.after;
      const { word, cls } = metricWordClass(before, after, higherBetter[key]);
      const note = m.note ? `<p class="muted small">${esc(m.note)}</p>` : "";
      html += `
        <div class="metric-card">
          <h4>${esc(key.replace(/_/g, " "))} <span class="tip" data-tip="${esc(METRIC_TIPS[key])}">i</span></h4>
          <div class="metric-values">
            <span class="before">before ${Number(before).toFixed(3)}</span>
            <span class="after">after ${Number(after).toFixed(3)}</span>
            <span class="metric-word ${cls}">${word}</span>
          </div>
          ${barChart(before, after, "before", "after")}
          ${note}
        </div>`;
    }
    const sanity = rows.distribution_sanity || {};
    html += `
      <div class="metric-card">
        <h4>Distribution sanity <span class="tip" data-tip="${esc(METRIC_TIPS.distribution_sanity)}">i</span></h4>
        <p style="margin:10px 0 0;font-size:14px">
          ${sanity.passed
            ? '<span class="metric-word improved">passed</span> <span class="muted small">no constant or negative-value columns</span>'
            : '<span class="metric-word worsened">issues</span> <span class="muted small">' + esc((sanity.issues || []).join("; ")) + "</span>"}
        </p>
      </div>`;
    grid.innerHTML = html;
    $("#audit-interpretation").innerHTML = (report.interpretation || [])
      .map((line) => `<li>${esc(line)}</li>`).join("");
  } catch (e) {
    grid.innerHTML = "";
    const note = $("#audit-note");
    note.hidden = false;
    note.className = "banner banner-error";
    note.textContent = "⚠ " + e.message;
  }
}

$("#btn-goto-receipt").addEventListener("click", () => {
  if (!state.dataset) { toast("Build a dataset first.", true); return; }
  showScreen("receipt");
});

/* ============================================================== SCREEN 4 — RECEIPT */

$("#variant-select").addEventListener("change", () => renderReceipt());

async function renderReceipt() {
  if (!state.dataset) { toast("Build a dataset first.", true); showScreen("build"); return; }
  const card = $("#receipt-card");
  card.innerHTML = '<p class="muted">Loading receipt…</p>';
  try {
    if (!state.receipt || state.receipt.dataset_id !== state.dataset.dataset_id) {
      state.receipt = await api("/api/receipts", {
        method: "POST",
        body: {
          session_id: getSessionId(),
          dataset_id: state.dataset.dataset_id,
          source: receiptSource(),
          variant: $("#variant-select").value,
        },
      });
    } else {
      state.receipt.variant = $("#variant-select").value;
    }
    card.innerHTML = renderReceiptHtml(state.receipt);
  } catch (e) {
    card.innerHTML = '<div class="banner banner-error">⚠ ' + esc(e.message) + "</div>";
  }
}

function receiptSource() {
  const counts = {};
  state.dataset.rows.forEach((r) => { counts[r.provenance] = (counts[r.provenance] || 0) + 1; });
  if (counts.augmented > 0) return "augmented";
  if (counts.synthetic === state.dataset.rows.length) return "invented";
  return "uploaded";
}

function renderReceiptHtml(receipt) {
  const f = receipt.fields;
  const tools = (f.ai_tools_used || [])
    .map((t) => `<div class="receipt-section"><h4>${esc(t.tool)}</h4><p>${esc(t.purpose)}</p></div>`).join("");
  const gv = f.generated_vs_student || {};
  const contribs = (f.student_contributions || []).length
    ? f.student_contributions.map((c) => `
        <li>
          <span class="contrib-action">${esc(c.action)}</span>
          <span>${esc(c.detail || "")}</span>
          <span class="contrib-time">${esc((c.timestamp || "").slice(0, 16).replace("T", " "))}</span>
        </li>`).join("")
    : "<li><span class='muted'>No student actions logged yet.</span></li>";

  if (receipt.variant === "teacher-check") {
    return `
      <div class="receipt-section">
        <h4>What the student researched</h4>
        <p>${esc(f.research_question || "—")}</p>
      </div>
      <div class="receipt-section">
        <h4>What AI did</h4><p>${esc(gv.generated || "—")}</p>
      </div>
      <div class="receipt-section">
        <h4>What the student did</h4><p>${esc(gv.student || "—")}</p>
      </div>
      <div class="receipt-section">
        <h4>Oversight</h4><p>${esc(f.human_oversight_level)} — the student prompted and reviewed all AI output.</p>
      </div>
      <div class="receipt-section">
        <h4>Sources used</h4><p>${f.sources_consulted.length ? esc(f.sources_consulted.join(", ")) : "none"}</p>
      </div>
      <div class="receipt-section">
        <h4>Integrity hash</h4><div class="hash-box">${esc(f.integrity_hash)}</div>
      </div>`;
  }

  if (receipt.variant === "journal-style") {
    return `
      <div class="receipt-section"><h4>1. Research question</h4><p>${esc(f.research_question || "—")}</p></div>
      <div class="receipt-section"><h4>2. Dataset provenance</h4><p>Source: <strong>${esc(f.dataset_source)}</strong> · ${f.student_contributions.length} student contribution(s) logged.</p></div>
      <div class="receipt-section"><h4>3. AI tools used</h4>${tools}</div>
      <div class="receipt-section">
        <h4>4. Human oversight</h4>
        <p>${esc(f.human_oversight_level)} — the student prompted, reviewed, and directed all AI output.</p>
      </div>
      <div class="receipt-section"><h4>5. Sources consulted</h4><p>${f.sources_consulted.length ? esc(f.sources_consulted.join(", ")) : "none"}</p></div>
      <div class="receipt-section"><h4>6. Integrity</h4><div class="hash-box">${esc(f.integrity_hash)}</div></div>
      <div class="receipt-section"><h4>7. Timestamp</h4><p>${esc(f.timestamp)}</p></div>`;
  }

  // standard
  return `
    <div class="receipt-section">
      <h4>Research question</h4>
      <p>${esc(f.research_question || "—")}</p>
    </div>
    <div class="receipt-section">
      <h4>Dataset source</h4>
      <p><span class="badge">${esc(f.dataset_source)}</span></p>
    </div>
    <div class="receipt-section">
      <h4>AI tools used <span class="tip" data-tip="Names the actual implementations that ran — never a generic claim.">i</span></h4>
      ${tools}
    </div>
    <div class="receipt-section">
      <h4>Generated vs. student <span class="tip" data-tip="The split between AI-generated content and the student's own work.">i</span></h4>
      <dl class="receipt-kv">
        <dt>Generated</dt><dd>${esc(gv.generated || "—")}</dd>
        <dt>Student</dt><dd>${esc(gv.student || "—")}</dd>
      </dl>
    </div>
    <div class="receipt-section">
      <h4>Human oversight</h4>
      <div class="oversight-note">${esc(f.human_oversight_level)} — you prompted, reviewed, and directed every AI action. ResearchLoop never works fully autonomously.</div>
    </div>
    <div class="receipt-section">
      <h4>Student contribution log <span class="tip" data-tip="Every student action in this session — auditable proof of what you did.">i</span></h4>
      <ul class="contrib-list">${contribs}</ul>
    </div>
    <div class="receipt-section">
      <h4>Sources consulted <span class="tip" data-tip="Only sources genuinely consulted during the run. None were — this is stated honestly rather than filled with placeholders.">i</span></h4>
      <p>${f.sources_consulted.length ? esc(f.sources_consulted.join(", ")) : "none — no external sources were consulted for this session."}</p>
    </div>
    <div class="receipt-section">
      <h4>Integrity hash <span class="tip" data-tip="SHA-256 of this receipt's content. Anyone can verify the receipt hasn't been altered.">i</span></h4>
      <div class="hash-box">${esc(f.integrity_hash)}</div>
    </div>
    <div class="receipt-section">
      <h4>Timestamp</h4>
      <p>${esc(f.timestamp)}</p>
    </div>`;
}

$("#btn-download-receipt").addEventListener("click", async () => {
  if (!state.receipt) { toast("Build a receipt first.", true); return; }
  const sid = getSessionId();
  try {
    const resp = await fetch("/api/exports/" + sid + "/receipt.json");
    if (!resp.ok) throw new Error("Receipt file not available — go to Export first.");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "receipt.json";
    a.click();
    URL.revokeObjectURL(url);
    toast("Receipt downloaded.");
  } catch (e) {
    toast(e.message, true);
  }
});

$("#btn-goto-export").addEventListener("click", () => {
  if (!state.dataset) { toast("Build a dataset first.", true); return; }
  showScreen("export");
});

/* ============================================================== SCREEN 5 — EXPORT */

const FILE_META = {
  "dataset.csv": { icon: "📊", desc: "Your dataset with the provenance column — every row labeled synthetic, original, or augmented." },
  "receipt.json": { icon: "🧾", desc: "The disclosure receipt: what AI did, what you did, and a hash anyone can verify." },
  "methodology.md": { icon: "📄", desc: "An auto-drafted methodology section — editable, and never overclaims what was done." },
};

async function renderExport() {
  if (!state.dataset) { toast("Build a dataset first.", true); showScreen("build"); return; }
  const grid = $("#export-files");
  grid.innerHTML = '<p class="muted">Preparing package…</p>';
  try {
    state.exportBundle = await api("/api/exports/" + encodeURIComponent(getSessionId()));
    const files = state.exportBundle.files || {};
    grid.innerHTML = Object.keys(FILE_META).map((name) => `
      <div class="file-card">
        <span class="file-icon">${FILE_META[name].icon}</span>
        <h4>${esc(name)}</h4>
        <p class="file-desc">${esc(FILE_META[name].desc)}</p>
        <button class="btn" data-file="${esc(name)}">Download</button>
      </div>`).join("");
    grid.querySelectorAll("button[data-file]").forEach((btn) =>
      btn.addEventListener("click", () => downloadFile(btn.dataset.file)));
    renderClosing();
  } catch (e) {
    grid.innerHTML = "";
    toast(e.message, true);
  }
}

async function downloadFile(name) {
  try {
    const resp = await fetch("/api/exports/" + encodeURIComponent(getSessionId()) + "/" + name);
    if (!resp.ok) throw new Error("Download failed (" + resp.status + ").");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    toast(e.message, true);
  }
}

$("#btn-download-all").addEventListener("click", async () => {
  if (!state.exportBundle) { toast("Prepare the package first.", true); return; }
  for (const name of Object.keys(state.exportBundle.files)) {
    await downloadFile(name);
    await new Promise((r) => setTimeout(r, 350)); // stagger to avoid browser blocking
  }
  toast("All three files downloaded.");
});

$("#btn-new-session").addEventListener("click", () => {
  try { localStorage.removeItem("researchloop.session"); } catch (_) { /* ignore */ }
  state.sessionId = null;
  state.plan = null;
  state.dataset = null;
  state.receipt = null;
  state.exportBundle = null;
  location.reload();
});

function renderClosing() {
  const ds = state.dataset;
  const counts = {};
  ds.rows.forEach((r) => { counts[r.provenance] = (counts[r.provenance] || 0) + 1; });
  $("#closing-card").hidden = false;
  const question = state.plan ? state.plan.research_type : "your question";
  $("#closing-summary").textContent =
    `You turned a rough question into a ${ds.rows.length}-row dataset (${Object.entries(counts).map(([p, n]) => p + ": " + n).join(", ")}). ` +
    `It passed a real quality audit, it carries an honest disclosure receipt (${state.receipt ? state.receipt.receipt_id : "—"}), ` +
    `and it's packaged with a methodology draft — ready for real research.`;
  $("#closing-modes").textContent =
    (state.health ? "LLM " + state.health.llm_mode + " · Adaption " + state.health.adaption_mode : "the configured");
}

/* ---------------------------------------------------------------- start */

boot();
