/* ==========================================================================
   views/receipt.js — RECEIPT: the verified-document panel.
   A disclosure receipt recording what the AI did, which sources were used,
   and the student's own contribution — integrity hash + variant selector.
   ========================================================================== */

import { getSession } from "../api.js";
import { el, $, toast, card } from "../ui.js";
import { api } from "../api.js";

const VARIANTS = [
  { id: "standard", label: "Standard", desc: "Full disclosure receipt." },
  { id: "journal-style", label: "Journal-style", desc: "Structured for methods sections." },
  { id: "teacher-check", label: "Teacher-check", desc: "With oversight checklist." },
];

export function renderReceipt(host) {
  host.replaceChildren();

  host.append(
    el("div", { class: "screen-head" }, [
      el("h2", {}, ["Disclosure receipt"]),
      el(
        "p",
        { class: "muted" },
        [
          "Every dataset ships with a receipt that states exactly what the AI created, which tools ran, and what you contributed. Receipts are signed with an integrity hash — and the source is derived from row provenance, never assumed.",
        ]
      ),
    ])
  );

  const loading = card("Receipt", "", [el("div", { class: "loading-card" }, [el("span", { class: "spinner" }), "Signing receipt…"])]);
  host.append(loading);

  async function run() {
    const datasetId = localStorage.getItem("rl_dataset_id");
    const sessionId = getSession();
    if (!datasetId) {
      host.replaceChildren(
        el("div", { class: "screen-head" }, [
          el("h2", {}, ["Disclosure receipt"]),
          el("p", { class: "muted" }, ["Build a dataset first — the receipt is generated from the dataset + session."]),
        ]),
        card("Nothing to sign yet", "", [el("p", { class: "muted" }, ["Run Ask → Build → Audit first."])]),
      );
      window.__pipeline?.to(3);
      return;
    }
    try {
      const receipt = await fetchReceipt(sessionId, datasetId, "standard");
      loading.remove();
      const screen = renderReceiptDoc(receipt, sessionId, datasetId);
      host.append(screen);
      window.__pipeline?.done(3);
    } catch (e) {
      loading.replaceChildren(el("p", { class: "badge bad" }, ["Receipt failed: " + e.message]));
      toast(e.message, "error");
    }
  }

  async function fetchReceipt(sessionId, datasetId, variant) {
    const source = localStorage.getItem("rl_dataset_source") || "invented";
    return api.receipt(sessionId, datasetId, source, variant);
  }

  function row(k, v) {
    return el("div", { class: "receipt-item" }, [el("div", { class: "k" }, [k]), el("div", { class: "v" }, [v])]);
  }

  function renderReceiptDoc(r, sessionId, datasetId) {
    const f = r.fields;
    const doc = el("div", { class: "receipt-doc" }, [
      el("div", { class: "receipt-title" }, [
        el("div", {}, [
          el("div", { class: "receipt-seal" }, ["✓ VERIFIED RECEIPT"]),
          el("h2", {}, ["Disclosure receipt"]),
          el("p", { class: "muted small" }, [`${r.dataset_id} · session ${r.session_id}`]),
        ]),
        el("div", { style: "text-align:right" }, [
          el("span", { class: `badge ${r.variant === "standard" ? "info" : "ok"}` }, [`variant: ${r.variant}`]),
          el("div", { class: "field-hint" }, [`generated ${f.timestamp.slice(0, 16).replace("T", " ")}`]),
        ]),
      ]),
      el("div", { class: "receipt-perf" }),
      el("div", { class: "receipt-grid" }, [
        row("Research question", f.research_question || "—"),
        row("Dataset source", `${f.dataset_source} (derived from row provenance)`),
        row("Oversight level", f.human_oversight_level === "prompt_guided" ? "Prompt-guided" : f.human_oversight_level),
        row("Mode", `llm=${localStorage.getItem("rl_llm_mode") || "mock"} · runs offline in demo mode`),
      ]),
      el("div", { class: "receipt-perf" }),
      // AI tools
      el("div", {}, [
        el("div", { class: "k", style: "font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--text-3);margin-bottom:6px" }, ["AI tools used"]),
        el("div", { class: "source-list" }, [
          ...(f.ai_tools_used || []).map((t) =>
            el("div", { class: "source-row" }, [
              el("span", { class: "src-icon" }, ["🤖"]),
              el("span", {}, [`${t.tool} — ${t.purpose}`]),
            ])
          ),
        ]),
      ]),
      el("div", { style: "height:12px" }),
      row("What was generated", f.generated_vs_student?.generated || "—"),
      row("Student's contribution", f.generated_vs_student?.student || "—"),
      el("div", { style: "height:12px" }),
      row("Sources consulted", (f.sources_consulted || []).length ? f.sources_consulted.join(", ") : "None — this pipeline runs offline; no external sources were consulted."),
      row("Student actions logged", String((f.student_contributions || []).length)),
      el("div", { style: "height:8px" }),
      row("Integrity hash", f.integrity_hash),
    ]);

    const variantSelect = el("select", { class: "select", id: "variant-select", style: "max-width:280px" }, [
      ...VARIANTS.map((v) =>
        el("option", { value: v.id, selected: r.variant === v.id ? "" : undefined }, [v.label])
      ),
    ]);
    variantSelect.addEventListener("change", async () => {
      try {
        const updated = await fetchReceipt(sessionId, datasetId, variantSelect.value);
        const screen = renderReceiptDoc(updated, sessionId, datasetId);
        host.replaceChildren(screen);
        toast(`Receipt re-signed as “${updated.variant}”.`, "success");
      } catch (e) {
        toast(e.message, "error");
      }
    });

    const actions = el("div", { class: "row" }, [
      variantSelect,
      el("button", { class: "btn btn-primary", type: "button", id: "btn-export" }, ["Continue to export →"]),
      el("button", { class: "btn btn-ghost", type: "button", id: "btn-copy-hash" }, ["Copy hash"]),
    ]);

    // contributions log (F11 evidence)
    const contribCard = card(
      "Student action log (what you did)",
      `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
      [
        el("div", { class: "contrib-list" }, [
          ...(f.student_contributions || []).map((c) =>
            el("div", { class: "contrib-row" }, [
              el("span", { class: "c-dot" }),
              el("span", {}, [`${c.action}${c.detail ? ` — ${c.detail}` : ""}`]),
              el("span", { class: "field-hint", style: "margin-left:auto" }, [c.timestamp ? c.timestamp.slice(11, 19) : ""]),
            ])
          ),
        ]),
      ]
    );

    const wrap = el("div", { class: "screen" }, [doc, actions, contribCard]);
    wrap.querySelector("#btn-export").addEventListener("click", () => {
      window.__pipeline?.to(4);
      window.__go("view-export");
    });
    wrap.querySelector("#btn-copy-hash").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(f.integrity_hash);
        toast("Hash copied to clipboard.", "success");
      } catch {
        toast("Clipboard unavailable — hash is displayed above.", "info");
      }
    });
    return wrap;
  }

  run();
}
