/* ==========================================================================
   ui.js — small, composable DOM helpers + toasts + shared fragments.
   ========================================================================== */

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null) continue;
    if (k === "class") node.className = v;
    else if (k === "dataset") Object.assign(node.dataset, v);
    else if (k === "html") node.innerHTML = v;
    else node.setAttribute(k, v);
  }
  for (const child of [].concat(children)) {
    if (child === null || child === undefined) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

export function $(sel, root = document) {
  return root.querySelector(sel);
}

export function $$(sel, root = document) {
  return Array.from(root.querySelectorAll(sel));
}

/* ------------------------------------------------------------------ toasts */

function toastStack() {
  let stack = $("#toast-stack");
  if (!stack) {
    stack = el("div", { class: "toast-stack", id: "toast-stack" });
    document.body.append(stack);
  }
  return stack;
}

export function toast(msg, kind = "info", ms = 3600) {
  const t = el("div", { class: `toast ${kind}` }, [msg]);
  toastStack().append(t);
  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transition = "opacity 180ms";
    setTimeout(() => t.remove(), 200);
  }, ms);
}

/* ------------------------------------------------------------------ helpers */

export function fmtPct(x) {
  if (x === null || x === undefined) return "—";
  return `${Number(x).toFixed(1)}%`;
}

export function escapeHtml(s) {
  return String(s ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

/** UTF-8-safe base64 encode (the augment API expects base64 CSV). */
export function toBase64(text) {
  return btoa(unescape(encodeURIComponent(String(text))));
}

export function modeBadge(mode) {
  const label = mode === "live" ? "Live LLM" : "Mock mode";
  return el("span", { class: `badge mode ${mode === "live" ? "live" : "warn"}` }, [label]);
}

export function card(title, iconHtml, bodyEls, opts = {}) {
  const cardEl = el("div", { class: `card ${opts.tight ? "tight" : ""}` });
  if (title) {
    cardEl.append(
      el("div", { class: "card-title" }, [
        iconHtml ? el("span", { class: "card-icon", html: iconHtml }) : null,
        el("h3", {}, [title]),
        opts.right || null,
      ])
    );
  }
  for (const b of [].concat(bodyEls)) cardEl.append(b);
  return cardEl;
}

export function metric(label, value, delta = null, kind = "") {
  return el("div", { class: `metric ${kind}` }, [
    el("div", { class: "m-label" }, [label]),
    el("div", { class: "m-value" }, [String(value)]),
    delta ? el("div", { class: "m-delta" }, [delta]) : null,
  ]);
}

/* ------------------------------------------------------------------ chart: horizontal bars (before → after) */

export function hbarChart(rows) {
  // rows: [{ name, before, after }] — before/after as 0..100
  return el("div", { class: "bars" }, [
    ...rows.map((r) =>
      el("div", { class: `bar-row` }, [
        el("div", { class: "bar-name" }, [r.name]),
        el("div", { class: "bar-track" }, [
          el("div", { class: "bar-fill before", style: `width:${Math.max(r.before, 0)}%` }),
          el("div", { class: "bar-fill green", style: `width:${Math.max(r.after, 0)}%` }),
        ]),
        el("div", { class: "bar-val" }, [fmtPct(r.after)]),
      ])
    ),
  ]);
}

/* ------------------------------------------------------------------ chart: donut (SVG) */

const R = 74;
const CIRC = 2 * Math.PI * R;

export function donut(segs, centerValue, centerLabel) {
  // segs: [{ pct, color }]
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", "0 0 180 180");

  const track = document.createElementNS(svgNS, "circle");
  track.setAttribute("cx", "90");
  track.setAttribute("cy", "90");
  track.setAttribute("r", String(R));
  track.setAttribute("fill", "none");
  track.setAttribute("class", "donut-track");
  track.setAttribute("stroke-width", "20");
  svg.append(track);

  let offset = 0;
  for (const seg of segs) {
    const len = (seg.pct / 100) * CIRC;
    if (len <= 0) continue;
    const c = document.createElementNS(svgNS, "circle");
    c.setAttribute("cx", "90");
    c.setAttribute("cy", "90");
    c.setAttribute("r", String(R));
    c.setAttribute("fill", "none");
    c.setAttribute("stroke", seg.color);
    c.setAttribute("stroke-width", "20");
    c.setAttribute("stroke-linecap", "round");
    c.setAttribute("stroke-dasharray", `${len} ${CIRC - len}`);
    c.setAttribute("stroke-dashoffset", String(-offset));
    c.setAttribute("class", "donut-seg");
    svg.append(c);
    offset += len;
  }

  const wrap = el("div", { class: "donut" }, [svg]);
  wrap.append(
    el("div", { class: "donut-center" }, [
      el("div", { class: "d-value" }, [String(centerValue)]),
      el("div", { class: "d-label" }, [centerLabel]),
    ])
  );
  return wrap;
}

export function legend(items) {
  // items: [{ label, pct, color }]
  return el("div", { class: "legend" }, [
    ...items.map((it) =>
      el("div", { class: "legend-item" }, [
        el("span", { class: "legend-sw", style: `background:${it.color}` }),
        el("span", {}, [it.label]),
        el("span", { class: "lg-pct" }, [fmtPct(it.pct)]),
      ])
    ),
  ]);
}
