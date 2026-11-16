# ResearchLoop — Mock-mode demo script (4.9)

**Purpose:** The recorded demo walkthrough. Uses **templates only, zero API keys** —
every screen is deterministic, so the video never breaks. Total runtime target: ~90–120 s.

**Setup:** start the backend (`cd backend && .venv/bin/uvicorn app.main:app`), open the
app, confirm the mode badge reads `LLM: mock · Adaption: emulated`.

---

## 0. Open (5 s)
- Show the top bar: **ResearchLoop** brand, `session: …` badge, mode badge (mock).
- Point out: "It runs fully offline — no API keys, and it tells you exactly which modes ran."

## 1. Ask (20 s)
- Click template chip **"Study vs. scores"** → question pre-fills, plan appears automatically.
- Point out the **plan card**: research type (regression), variables, suggested rows, data plan.
- **Edit the data plan** (add one sentence) → toast: "Plan edit saved — recorded in your contribution log."
- Point out the **refinement chips** (F7): "Too broad? Pick a re-framing — it's logged as your work."
- (Optional quick pick: click a refinement to show re-scoping works.)

## 2. Build (25 s)
- Click **Use this plan → Build**.
- On Build: keep the default **80 rows**, click **Generate synthetic dataset**.
- Show the **synthetic warning banner** and the preview table with the `synthetic` provenance column.
- (Second pass for the other path:) switch to **Augment a CSV**, upload a small messy CSV
  (`data/samples/` — e.g. a 4-row survey with a missing value), target 12 rows, click **Clean & augment**.
- Show that originals stay tagged `original`, new rows are `augmented`.

## 3. Audit (20 s)
- Click **Audit this dataset →**.
- The before/after dashboard renders **real numbers** from the API (bar chart per metric).
- For the augment path: completeness improves (missing value filled) — point at the **improved** badge.
- Hover a metric's **ⓘ** tooltip: "why this matters" (F12 explainers).
- Read the **interpretation list** + overall verdict.

## 4. Receipt (15 s)
- Click **See the disclosure receipt →**.
- Show the **mode badge** (LLM mock · Adaption emulated) — "the UI never hides what ran."
- Show the **student contribution log** (question submitted, plan edited, plan submitted…).
- Show the **integrity hash** and the honesty note: "no external sources were consulted."
- Switch the **layout selector** to **Teacher-check** → one-page re-render (F8 variants).

## 5. Export (10 s)
- Click **Get the research-ready package →**.
- **Download all three**: dataset.csv, receipt.json, methodology.md.
- Show the closing summary card: "You turned a rough question into an N-row dataset…"

## 6. Close (5 s)
- Final line: "A defensible first step — real numbers, honest labels, and a receipt that proves what's yours."

---

## Capture notes
- Record at 1280×720; the UI is responsive down to mobile width.
- If anything fails mid-recording: the flow is template-driven, so a refresh + re-click on the
  same template reproduces the same state (deterministic mock mode).
- No free-text questions in the recording — templates keep it deterministic (demo-safety rule).
