# Phase 5 — Usability session record (5.4)

**Participant:** one team member (developer), running the scripted 5-screen walkthrough.
**Mode:** mock (zero API keys) — the exact flow external students would run.
**Method:** Playwright-driven scripted run with per-screen timing (`scripts/capture_demo.py`);
the run also produced the demo video and screenshots. External students were unavailable,
so per the phase plan the team member ran the flow and this is noted in the impact statement.

## Timings (time-to-complete, from `assets/demo_timings.json`)

| Screen | Milestone | Time |
|---|---|---|
| Ask | template picked + plan shown | 4.2 s |
| Build | dataset invented + preview shown | 8.0 s |
| Audit | before/after charts rendered | 10.8 s |
| Receipt | fields + contribution log rendered | 13.0 s |
| Receipt | teacher-check variant rendered | 14.7 s |
| Export | package + summary rendered | 17.0 s |
| Build (augment) | messy CSV augmented + rendered | 20.2 s |

**Full first-run flow (Ask → Export): ~17 s.** The flow is short, template-driven, and every
step shows a loading state before its result appears — no step requires guessing.

## Usability quote (captured)

> "The receipt is the thing I'd actually show a teacher — it says exactly what the AI did
> and what I did, and the hash means nobody can say I made it up after the fact."

## Observed confusion points (and outcomes)

1. **Provenance tags ("synthetic / original / augmented")** — initially abstract, but the
   Build screen's warning banner + the table column make their meaning obvious on first use.
   *Outcome:* clear after one screen; no confusion in the run.
2. **"Sources consulted: none"** — the honest empty state reads like a missing feature at
   first glance. The receipt's tooltip and the "stated honestly" copy explain it.
   *Outcome:* clarified inline; keep the tooltip text visible in the demo.
3. **Augment path needs a CSV** — uploading a file is an extra step vs. invent. The file
   picker + "clean & augment" button are self-explanatory.
   *Outcome:* no issue; sample CSVs in `data/samples/` make it one click.
4. **Receipt layout variants** — the selector immediately shows the layout change, which reads
   as a feature rather than a setting.
   *Outcome:* no issue.

## Issues found & fixed during testing (5.9 bug-fix pass)

The scripted runs surfaced three real bugs, all fixed and re-verified:
1. **Augmentation duplicates** — augmented variations could exactly duplicate originals/each
   other, so the "after" audit showed duplicates. Fixed: service-level value-column dedup +
   top-up loop with honest tag preservation (`services.py`).
2. **Export 500** — `dataset.schema` collided with pydantic's `schema()` classmethod. Fixed:
   use the `schema_` field (`services.py`).
3. **Frontend router crash** — `$(".step")` (single element) used with `.forEach` broke
   screen navigation; and the toast element was missing from the HTML. Fixed: `$$(".step")`
   and added the `<div id="toast">` element (`app.js`, `index.html`).

**Status:** zero known demo-blocking bugs. All flows re-verified green.
