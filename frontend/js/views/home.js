/* ==========================================================================
   views/home.js — ASK: capture a rough research question, refine it, then
   go to BUILD. Templates give a deterministic demo baseline.
   ========================================================================== */

import { getSession } from "../api.js";
import { el, $, $$, toast, card } from "../ui.js";
import { api } from "../api.js";

const TEMPLATES = [
  { id: "does_sleep_mediate", label: "Sleep → exam scores", hint: "classroom observation" },
  { id: "study_vs_scores", label: "Study time → scores", hint: "classroom observation" },
  { id: "plant_growth", label: "Sunlight → plant growth", hint: "home experiment" },
];

export function renderHome(host) {
  host.replaceChildren();

  const input = el("input", {
    class: "input",
    id: "question-input",
    placeholder: 'e.g. "Does sleeping more improve students exam scores?"',
    maxlength: 280,
  });

  const refineCard = card(
    "Smart refinement",
    `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M22 2 12 12"/><path d="M16 2h6v6"/></svg>`,
    []
  );

  async function refine(question) {
    refineCard.replaceChildren(el("div", { class: "loading-card" }, [el("span", { class: "spinner" }), "Refining…"]));
    try {
      const data = await api.scope(question, getSession(), null);
      const opts = TEMPLATES.map((t) =>
        el(
          "button",
          {
            class: "badge info",
            type: "button",
            "data-refinement": t.id,
            style: "cursor:pointer;padding:5px 12px;font-size:13px",
          },
          [`${t.label} — ${data.refinement_hint || ""}`]
        )
      );
      refineCard.replaceChildren(
        el("p", { class: "small muted" }, [
          "The plan matched to your question. Pick a direction to sharpen it:",
        ]),
        el("div", { class: "row", style: "margin:10px 0 0" }, opts),
        el("p", { class: "field-hint" }, [
          data.mode === "mock"
            ? "Refinement runs in labeled mock mode — a deterministic plan generator for offline demos."
            : "Refinement runs with the live model.",
        ])
      );
      opts.forEach((b, i) => b.addEventListener("click", () => onConfirm(question, TEMPLATES[i].id)));
    } catch (e) {
      refineCard.replaceChildren(el("p", { class: "badge bad" }, ["Refinement unavailable: " + e.message]));
    }
  }

  async function onConfirm(question, templateId) {
    try {
      localStorage.setItem("rl_last_question", question);
      await api.scope(question, getSession(), templateId);
      toast("Question captured — ready to build the dataset.", "success");
      window.__pipeline?.to(1);
      window.__go("view-build");
    } catch (e) {
      toast(e.message, "error");
    }
  }

  host.append(
    el("div", { class: "screen-head" }, [
      el("h2", {}, ["Start with a rough question"]),
      el(
        "p",
        { class: "muted" },
        [
          "ResearchLoop turns an unshaped question into a small, research-ready dataset with a full audit and a disclosure receipt. Anything you type is refined into an explicit data plan before a single data point is created.",
        ]
      ),
    ]),
    card(
      "Your research question",
      `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9 9h.01M15 9h.01M9 15c1 1 2 1.5 3 1.5s2-.5 3-1.5"/></svg>`,
      [
        el("div", { class: "field" }, [
          el("label", { for: "question-input" }, ["What do you want to investigate?"]),
          input,
          el("div", { class: "datalist-hint" }, [
            "Tip: try a sample to see the full flow in one click — the demo is deterministic in mock mode.",
          ]),
        ]),
        el(
          "div",
          { class: "row" },
          [
            el("button", { class: "btn btn-primary", type: "button", id: "btn-scope" }, [
              "Analyze question",
            ]),
            el("div", { class: "badge", style: "border-style:dashed" }, [
              el("span", {}, ["Templates:"]),
            ...TEMPLATES.map((t) =>
              el(
                "button",
                {
                  class: "badge info",
                  type: "button",
                  dataset: { template: t.id },
                  style: "cursor:pointer;padding:3px 10px",
                },
                [t.label]
              )
            ),
            ]),
          ]
        ),
        refineCard,
      ]
    )
  );

  $("#btn-scope").addEventListener("click", () => {
    const q = input.value.trim();
    if (!q) {
      toast("Type your research question first.", "error");
      input.focus();
      return;
    }
    refine(q);
  });
  // Wire template chips — fill the input with a sample question, then refine
  $$("[data-template]", host).forEach((chip) => {
    chip.addEventListener("click", () => {
      const idx = $$("[data-template]", host).indexOf(chip);
      const parts = TEMPLATES[idx].label.split(" → ");
      input.value = `Does ${parts[0]} affect ${parts[1]}?`;
      refine(input.value);
    });
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") $("#btn-scope").click();
  });
}
