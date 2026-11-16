/* ==========================================================================
   views/audit.js — AUDIT: real quality metrics (completeness, duplicate
   rate, near-duplicates, diversity, label coverage) with before/after
   comparison against the stored baseline, plus a plain-language reading.
   ========================================================================== */

import { el, $, toast, card, metric, hbarChart, fmtPct } from "../ui.js";
import { api } from "../api.js";

const METRIC_DEFS = [
  { key: "completeness", label: "Completeness", lowerBetter: false },
  { key: "duplicate_rate", label: "Duplicate rate", lowerBetter: true },
  { key: "near_duplicate_rate", label: "Near-duplicates", lowerBetter: true },
  { key: "diversity", label: "Diversity", lowerBetter: false },
  { key: "label_coverage", label: "Label coverage", lowerBetter: false },
];

export function renderAudit(host) {
  host.replaceChildren();

  host.append(
    el("div", { class: "screen-head" }, [
      el("h2", {}, ["Audit the dataset quality"]),
      el(
        "p",
        { class: "muted" },
        [
          "Five real metrics computed from the data — no hardcoded numbers. “Before” is the messy baseline captured at build time; “after” is the delivered dataset.",
        ]
      ),
    ])
  );

  const loading = card("Quality audit", "", [el("div", { class: "loading-card" }, [el("span", { class: "spinner" }), "Computing metrics…"])]);
  host.append(loading);

  async function run() {
    const datasetId = localStorage.getItem("rl_dataset_id");
    if (!datasetId) {
      host.replaceChildren(
        el("div", { class: "screen-head" }, [
          el("h2", {}, ["Audit the dataset quality"]),
          el("p", { class: "muted" }, ["Build a dataset first (Ask → Build), then audit it here."]),
        ]),
        card("Nothing to audit yet", "", [el("p", { class: "muted" }, ["Use the Build step to invent or augment a dataset."])]),
      );
      window.__pipeline?.to(2);
      return;
    }
    try {
      const report = await api.audit(datasetId);
      loading.remove();
      host.append(renderReport(report));
      window.__pipeline?.done(2);
    } catch (e) {
      loading.replaceChildren(el("p", { class: "badge bad" }, ["Audit failed: " + e.message]));
      toast(e.message, "error");
    }
  }

  function renderReport(rep) {
    const m = rep.metrics || {};
    const wrap = el("div", { class: "screen" });

    // 1) headline metrics with before → after deltas
    const grid = el("div", { class: "metric-grid" });
    for (const def of METRIC_DEFS) {
      const entry = m[def.key] || {};
      const before = entry.before ?? null;
      const after = entry.after ?? null;
      const delta = before !== null && before !== undefined ? `${fmtPct((before ?? 0) * 100)} → ${fmtPct((after ?? 0) * 100)}` : null;
      grid.append(metric(def.label, fmtPct((after ?? 0) * 100), delta, ""));
    }

    // 2) before/after bar chart
    const chart = card(
      "Before vs after — the visible improvement",
      `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 14l4-4 4 4 5-7"/></svg>`,
      []
    );
    chart.append(
      hbarChart([
        { name: "Completeness", before: (m.completeness?.before ?? 0) * 100, after: (m.completeness?.after ?? 0) * 100 },
        { name: "Dedup (1−dupes)", before: 100 - (m.duplicate_rate?.before ?? 0) * 100, after: 100 - (m.duplicate_rate?.after ?? 0) * 100 },
        { name: "Uniqueness", before: 100 - (m.near_duplicate_rate?.before ?? 0) * 100, after: 100 - (m.near_duplicate_rate?.after ?? 0) * 100 },
        { name: "Diversity", before: (m.diversity?.before ?? 0) * 100, after: (m.diversity?.after ?? 0) * 100 },
      ])
    );
    chart.append(
      el("p", { class: "field-hint", style: "margin-top:10px" }, [
        "Gray = baseline before · green = delivered dataset. Percentages are real engine outputs.",
      ])
    );

    // 3) interpretation + sanity
    const reading = card(
      "Reading the numbers",
      `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>`,
      []
    );
    reading.append(
      el("div", { class: "screen" }, [
        ...(rep.interpretation || []).map((line) => el("p", { class: "small" }, [line])),
        el("div", { class: "row", style: "margin-top:12px" }, [
          el(
            "span",
            { class: `badge ${m.distribution_sanity ? "ok" : "warn"}` },
            [`distribution sanity: ${m.distribution_sanity ? "ok" : "check"}`]
          ),
        ]),
      ])
    );

    // 4) detail table
    const detailCard = card("Metric detail", `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>`, []);
    const tbl = el("table", { class: "data" }, [
      el("thead", {}, [el("tr", {}, [el("th", {}, ["Metric"]), el("th", {}, ["Before"]), el("th", {}, ["After"]), el("th", {}, ["Change"])])]),
    ]);
    const tb = el("tbody");
    for (const def of METRIC_DEFS) {
      const entry = m[def.key] || {};
      const before = entry.before ?? null;
      const after = entry.after ?? null;
      tb.append(
        el("tr", {}, [
          el("td", {}, [def.label]),
          el("td", {}, [before === null || before === undefined ? "—" : fmtPct((before ?? 0) * 100)]),
          el("td", {}, [fmtPct((after ?? 0) * 100)]),
          el("td", {}, [
            before === null || before === undefined
              ? "—"
              : `${(after - before) >= 0 ? "+" : ""}${fmtPct((after - before) * 100)} pts`,
          ]),
        ])
      );
    }
    tbl.append(tb);
    detailCard.append(el("div", { class: "table-wrap" }, [tbl]));

    wrap.append(grid, chart, el("div", { class: "grid-2" }, [reading, detailCard]));

    wrap.append(
      el("div", { class: "row", style: "margin-top:8px" }, [
        el("button", { class: "btn btn-primary", type: "button", id: "btn-receipt" }, ["Generate receipt →"]),
        el("button", { class: "btn btn-ghost", type: "button", id: "btn-back-build" }, ["Build another dataset"]),
      ])
    );
    wrap.querySelector("#btn-receipt").addEventListener("click", () => {
      window.__pipeline?.to(3);
      window.__go("view-receipt");
    });
    wrap.querySelector("#btn-back-build").addEventListener("click", () => {
      window.__pipeline?.to(1);
      window.__go("view-build");
    });

    return wrap;
  }

  run();
}
