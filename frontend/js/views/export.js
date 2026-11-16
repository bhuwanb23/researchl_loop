/* ==========================================================================
   views/export.js — EXPORT: download the research-ready package
   (dataset.csv + receipt.json + methodology.md).
   ========================================================================== */

import { getSession } from "../api.js";
import { el, $, toast, card, modeBadge } from "../ui.js";
import { api } from "../api.js";

export function renderExport(host) {
  host.replaceChildren();

  host.append(
    el("div", { class: "screen-head" }, [
      el("h2", {}, ["Export the research-ready package"]),
      el(
        "p",
        { class: "muted" },
        [
          "Everything your research needs in one bundle: the clean dataset with provenance tags, the signed disclosure receipt, and a methodology draft explaining the data plan and every metric.",
        ]
      ),
    ])
  );

  const sessionId = getSession();
  const loading = card("Package", "", [el("div", { class: "loading-card" }, [el("span", { class: "spinner" }), "Assembling export…"])]);
  host.append(loading);

  async function run() {
    try {
      const bundle = await api.export(sessionId);
      loading.remove();

      // bundle.files = { "dataset.csv": "/api/exports/{sid}/dataset.csv", ... }
      const files = Object.entries(bundle.files || {}).map(([name, url]) => ({
        name,
        url,
        desc: {
          "dataset.csv": "Clean, provenance-tagged dataset.",
          "receipt.json": "Signed disclosure receipt.",
          "methodology.md": "Methodology draft (F7).",
        }[name] || "Export file.",
      }));

      // mode chip from live health (the export response carries no mode)
      const health = await api.health().catch(() => ({ llm_mode: "mock" }));

      const list = el("div", { class: "screen" }, [
        el("div", { class: "row" }, [
          el("button", { class: "btn btn-primary", type: "button", id: "btn-all" }, ["Download all"]),
          modeBadge(health.llm_mode),
        ]),
        ...files.map((f) =>
          card(
            f.name,
            `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
            [
              el("p", { class: "small muted", style: "margin-bottom:12px" }, [f.desc]),
              el("div", { class: "row", style: "margin:0" }, [
                el("span", { class: "badge mono" }, [f.name]),
                el("button", { class: "btn btn-ghost btn-sm", type: "button", dataset: { file: f.name, url: f.url } }, ["Download"]),
              ]),
            ]
          )
        ),
        el("p", { class: "field-hint" }, [
          health.llm_mode === "mock"
            ? "Exported in labeled mock mode — the receipt states the AI ran in mock/emulated mode, so the package stays honest."
            : "Exported in live mode with the real model.",
        ]),
      ]);

      // per-file download
      list.querySelectorAll("[data-file]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const name = btn.dataset.file;
          try {
            const res = await fetch(btn.dataset.url);
            if (!res.ok) throw new Error(`download failed (${res.status})`);
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = el("a", { href: url, download: name });
            document.body.append(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            toast(`${name} downloaded.`, "success");
          } catch (e) {
            toast(e.message, "error");
          }
        });
      });

      // download-all: fetch the three files and trigger them sequentially
      $("#btn-all", list).addEventListener("click", async () => {
        try {
          toast("Downloading package files…", "info");
          for (const f of files) {
            const res = await fetch(f.url);
            if (!res.ok) throw new Error(`${f.name} failed (${res.status})`);
            const url = URL.createObjectURL(await res.blob());
            const a = el("a", { href: url, download: f.name });
            document.body.append(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            await new Promise((r) => setTimeout(r, 350)); // avoid browser blocking bursts
          }
          toast("Package downloaded (3 files).", "success");
        } catch (e) {
          toast(e.message, "error");
        }
      });

      host.append(list);
      window.__pipeline?.done(4);
    } catch (e) {
      loading.replaceChildren(el("p", { class: "badge bad" }, ["Export failed: " + e.message]));
      toast(e.message, "error");
    }
  }

  run();
}
