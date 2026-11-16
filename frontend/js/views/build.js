/* ==========================================================================
   views/build.js — BUILD: two ways to get a dataset.
   1) Invent: schema from the scoped plan (deterministic in mock mode).
   2) Augment: upload a messy CSV (or pick a sample) and grow it to N rows.
   Both store to the backend and jump to AUDIT.
   ========================================================================== */

import { getSession } from "../api.js";
import { el, $, $$, toast, card, metric, toBase64 } from "../ui.js";
import { api } from "../api.js";

export function renderBuild(host) {
  const SESSION = getSession(); // resolved at render time (session id exists by then)
  host.replaceChildren();

  host.append(
    el("div", { class: "screen-head" }, [
      el("h2", {}, ["Build a research-ready dataset"]),
      el(
        "p",
        { class: "muted" },
        [
          "Either invent a small dataset from the plan on the previous step, or upload a tiny messy spreadsheet and watch it grow. Every row carries provenance — nothing is invented silently.",
        ]
      ),
    ])
  );

  // ------------------------------------------------------------- 1) Invent

  const inventCard = card(
    "Option A — Invent a dataset from your plan",
    `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/></svg>`,
    []
  );

  const rowsSelect = el("select", { class: "select", id: "invent-rows" }, [
    el("option", { value: "12" }, ["12 rows — quick demo"]),
    el("option", { value: "20", selected: "" }, ["20 rows — default"]),
    el("option", { value: "30" }, ["30 rows — fuller dataset"]),
  ]);

  const inventPreview = el("div", { class: "empty" }, ["No dataset yet. Press “Invent dataset” to generate one."]);

  inventCard.append(
    el("div", { class: "grid-2" }, [
      el("div", { class: "field" }, [
        el("label", { for: "invent-rows" }, ["Target size"]),
        rowsSelect,
        el("div", { class: "field-hint" }, [
          "In mock mode rows are generated deterministically from the plan, so the demo never breaks.",
        ]),
      ]),
      el("div", { class: "align-end" }, [
        el("button", { class: "btn btn-primary", type: "button", id: "btn-invent" }, [
          "Invent dataset",
        ]),
      ]),
    ]),
    inventPreview,
  );

  async function doInvent() {
    inventPreview.replaceChildren(el("div", { class: "loading-card" }, [el("span", { class: "spinner" }), "Building dataset…"]));
    try {
      // The last scoped question/template from the ask step, else a sensible default.
      const question = localStorage.getItem("rl_last_question") || "Does sleep improve exam scores?";
      const scope = await api.scope(question, SESSION, null);
      const ds = await api.invent(SESSION, scope, Number(rowsSelect.value));
      localStorage.setItem("rl_dataset_id", ds.dataset_id);
      localStorage.setItem("rl_dataset_name", ds.name);
      localStorage.setItem("rl_dataset_source", "invented");
      renderDatasetPreview(inventPreview, ds);
      window.__pipeline?.done(1);
      toast(`Dataset “${ds.name}” ready — ${ds.rows.length} rows.`, "success");
    } catch (e) {
      inventPreview.replaceChildren(el("p", { class: "badge bad" }, ["Failed: " + e.message]));
      toast(e.message, "error");
    }
  }

  function renderDatasetPreview(hostEl, ds) {
    const columns = ds.schema?.columns || [];
    const counts = {};
    for (const r of ds.rows) counts[r.provenance] = (counts[r.provenance] || 0) + 1;

    const table = el("table", { class: "data" }, [
      el("thead", {}, [
        el("tr", {}, [el("th", {}, ["#"]), ...columns.map((c) => el("th", {}, [c])), el("th", {}, ["provenance"])]),
      ]),
    ]);
    const body = el("tbody");
    ds.rows.slice(0, 8).forEach((row, i) => {
      const cells = columns.map((c) => el("td", {}, [String(row.values[c] ?? "")]));
      body.append(
        el("tr", {}, [
          el("td", { class: "row-i" }, [String(i + 1)]),
          ...cells,
          el("td", {}, [el("span", { class: `prov-tag ${row.provenance}` }, [row.provenance])]),
        ])
      );
    });
    table.append(body);
    hostEl.replaceChildren(
      el("div", { class: "metric-grid", style: "margin-bottom:14px" }, [
        metric("Dataset", ds.name),
        metric("Rows", String(ds.rows.length)),
        metric("Columns", String(columns.length)),
        metric("Provenance", Object.entries(counts).map(([k, v]) => `${v} ${k}`).join(" · ")),
      ]),
      el("div", { class: "table-wrap" }, [table]),
      el("p", { class: "field-hint", style: "margin-top:10px" }, [
        `${ds.rows.length > 8 ? "Showing first 8 rows" : "All rows shown"} · provenance recorded per row.`,
      ]),
      el("button", { class: "btn btn-primary", type: "button", id: "btn-to-audit" }, ["Audit this dataset →"]),
    );
    hostEl.querySelector("#btn-to-audit").addEventListener("click", goAudit);
  }

  // ------------------------------------------------------------- 2) Augment

  const fileInput = el("input", { type: "file", id: "csv-file", accept: ".csv,text/csv", style: "display:none" });
  const csvName = el("span", { class: "muted mono small" }, ["No file selected"]);
  const csvPreview = el("div", { class: "empty" }, ["Pick a messy CSV (or use the sample) to see the before/after."])

  const augmentCard = card(
    "Option B — Augment a messy spreadsheet",
    `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
    [
      el("div", { class: "row", style: "margin:0" }, [
        el("button", { class: "btn btn-ghost", type: "button", id: "btn-pick" }, ["Choose CSV…"]),
        fileInput,
        csvName,
        el("button", { class: "btn btn-primary btn-sm", type: "button", id: "btn-augment" }, ["Augment"]),
      ]),
      el("div", { class: "field" }, [
        el("label", { for: "augment-rows" }, ["Target rows"]),
        el("select", { class: "select", id: "augment-rows" }, [
          el("option", { value: "16" }, ["16 rows"]),
          el("option", { value: "24", selected: "" }, ["24 rows"]),
          el("option", { value: "32" }, ["32 rows"]),
        ]),
      ]),
      csvPreview,
    ]
  );

  function renderCsvPreview(hostEl, lines) {
    const wrap = el("div", { class: "table-wrap csv-preview" });
    lines.slice(0, 8).forEach((line, i) => {
      wrap.append(el("div", { class: `cell ${i === 0 ? "new" : ""}` }, [line]));
    });
    hostEl.replaceChildren(
      el("p", { class: "small muted", style: "margin-bottom:8px" }, [`Preview (${lines.length} rows shown):`]),
      wrap,
    );
  }

  // Shared augment flow: POST → store → preview → audit button
  async function augmentAndRender(csv, filename) {
    csvPreview.replaceChildren(el("div", { class: "loading-card" }, [el("span", { class: "spinner" }), `Augmenting ${filename}…`]));
    try {
      // the augment API expects base64 CSV
      const ds = await api.augment(SESSION, toBase64(csv), Number($("#augment-rows").value), filename);
      localStorage.setItem("rl_dataset_id", ds.dataset_id);
      localStorage.setItem("rl_dataset_name", ds.name);
      localStorage.setItem("rl_dataset_source", "augmented");
      renderCsvPreview(csvPreview, ds.rows.slice(0, 12).map((r) => Object.values(r.values).join(" | ")));
      csvPreview.append(
        el("div", { class: "metric-grid", style: "margin-top:14px" }, [
          metric("Dataset", ds.name),
          metric("Rows", String(ds.rows.length)),
          metric("Synthetic", String(ds.rows.filter((r) => r.provenance === "synthetic").length)),
          metric("Augmented", String(ds.rows.filter((r) => r.provenance === "augmented").length)),
        ]),
        el("button", { class: "btn btn-primary", type: "button", id: "btn-to-audit-b" }, ["Audit this dataset →"]),
      );
      csvPreview.querySelector("#btn-to-audit-b").addEventListener("click", goAudit);
      window.__pipeline?.done(1);
      toast(`“${ds.name}” grown to ${ds.rows.length} rows.`, "success");
    } catch (e) {
      csvPreview.replaceChildren(el("p", { class: "badge bad" }, ["Failed: " + e.message]));
      toast(e.message, "error");
    }
  }

  function goAudit() {
    window.__pipeline?.to(2);
    window.__go("view-audit");
  }

  // Sample chips for quick demo (fetch sample CSVs served from data/samples)
  const SAMPLES = [
    { name: "messy_study_survey.csv", label: "Sleep study" },
    { name: "messy_plant_survey.csv", label: "Plant growth" },
  ];
  augmentCard.append(
    el("div", { class: "row", style: "margin-top:14px" }, [
      el("span", { class: "small muted" }, ["Try a sample:"]),
      ...SAMPLES.map((s) =>
        el(
          "button",
          {
            class: "badge info",
            type: "button",
            style: "cursor:pointer;padding:5px 12px",
            dataset: { sample: s.name },
          },
          [s.label]
        )
      ),
    ]),
  );
  $$("[data-sample]", augmentCard).forEach((chip) => {
    chip.addEventListener("click", async () => {
      const sampleName = chip.dataset.sample;
      try {
        const res = await fetch(`/api/samples/${sampleName}`);
        if (!res.ok) throw new Error(`sample fetch failed (${res.status})`);
        csvName.textContent = sampleName;
        augmentAndRender(await res.text(), sampleName);
      } catch (e) {
        toast(e.message, "error");
        csvPreview.replaceChildren(el("p", { class: "badge bad" }, ["Failed: " + e.message]));
      }
    });
  });

  $("#btn-pick", augmentCard).addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) {
      csvName.textContent = fileInput.files[0].name;
      csvPreview.replaceChildren(el("p", { class: "small muted" }, ["Press “Augment” below to process the file…"]));
    }
  });
  $("#btn-invent", inventCard).addEventListener("click", doInvent);
  $("#btn-augment", augmentCard).addEventListener("click", () => {
    const file = fileInput.files[0];
    if (!file) {
      toast("Choose a CSV file first (or use a sample).", "error");
      return;
    }
    file.text().then((csv) => augmentAndRender(csv, file.name));
  });

  host.append(inventCard, augmentCard);
}
