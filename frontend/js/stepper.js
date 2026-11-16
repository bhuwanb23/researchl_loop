/* ==========================================================================
   stepper.js — the pipeline arc stepper (ResearchLoop's signature element).
   Five nodes joined by segments; the active node glows, finished nodes
   complete their segment with the accent gradient.
   ========================================================================== */

import { el } from "./ui.js";

export const PIPELINE = [
  { name: "Ask", icon: "💬", view: "view-ask" },
  { name: "Build", icon: "🧪", view: "view-build" },
  { name: "Audit", icon: "🔍", view: "view-audit" },
  { name: "Receipt", icon: "🧾", view: "view-receipt" },
  { name: "Export", icon: "📦", view: "view-export" },
];

export function initStepper() {
  const host = document.getElementById("pipeline");
  if (!host) return;

  let activeIndex = 0;
  let doneUpTo = -1; // highest completed index (for the segment glow)

  function render() {
    host.replaceChildren(
      ...PIPELINE.map((p, i) => {
        const state = i < activeIndex ? "done" : i === activeIndex ? "active" : "";
        const node = el(
          "button",
          { class: `pipe-node ${state}`, type: "button", "data-view": p.view },
          [el("span", { class: "dot" }, [p.icon]), el("span", { class: "label" }, [p.name])]
        );
        node.addEventListener("click", () => {
          activeIndex = i;
          render();
          window.__go?.(p.view);
        });
        return node;
      }).flatMap((node, i, arr) => [
        node,
        i < arr.length - 1 ? el("div", { class: `pipe-seg ${i < doneUpTo ? "done" : ""}` }) : null,
      ])
    );
  }

  // Expose state API used by views to mark progress.
  window.__pipeline = {
    to(index) {
      activeIndex = index;
      render();
    },
    done(index) {
      if (index > doneUpTo) doneUpTo = index;
      render();
    },
    current() {
      return { activeIndex, doneUpTo };
    },
  };

  render();
}
