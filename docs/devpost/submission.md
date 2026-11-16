# Devpost Submission — ResearchLoop

**Status:** submission-ready copy · **Deadline:** Dec 1, 9:00 PM PT (hard gate) · **Confirmation:** see `submission_record.md`

Everything below is the exact content to paste into the Devpost submission form. Re-read each
field for accuracy before submitting — especially the sponsor/mode claims, which must match what
the app actually reports (docs/06 §D honesty gates).

---

## 6.1 Title

**ResearchLoop — The first step between a research question and real, defensible student research**

## 6.2 Description — Problem

Students who want to do real research hit two hard walls before they can even begin.

**1. The data barrier.** Research starts with data, but students rarely have it. A meaningful
dataset usually means scraping, cleaning, and labeling — work that assumes experience they don't
have. The datasets they *can* get are either too small to support any analysis or too large to
understand, and the middle ground — a 10–100-row dataset matched to a specific question — is
almost never available. The literature is clear that this "first step" is where most student
research stalls: generative data tools exist, but they produce data without showing whether it's
any good (synthetic-data quality work, e.g. TF-IDF-based diversity and duplication checks, is
well established but not student-accessible), and ML literacy research shows students are
expected to bridge the gap between a question and a dataset on their own.

**2. The verification gap.** When AI tools generate or augment data, students gain the data but
lose the ability to *explain and defend* it. There is no record of what the AI actually did, what
the student actually did, or whether the numbers can be trusted — so teachers and journals have
no way to verify the work, and students have no way to prove it's theirs. Provenance and
disclosure standards (C2PA-style content credentials) address exactly this in professional
workflows, but nothing brings that idea to student research.

ResearchLoop attacks both walls at once.

## 6.3 Description — Solution

ResearchLoop is a **data-first research starter** built on two pillars:

**Pillar 1 — A dataset you can actually start from.** A student types a rough research question
(or uploads a small messy CSV). ResearchLoop's Adaptive Data layer **invents** a synthetic
dataset matched to the question, or **augments** the student's own CSV to a usable size — then
runs a **real quality audit** (duplicate rate, near-duplicate rate via TF-IDF, diversity,
completeness, label coverage, distribution sanity) with a clear **before/after chart**. The
before/after is the proof the tool does something real: on a messy student CSV, missing values
get filled (completeness 0.917 → 1.000) and duplicate rows are removed (0.167 → 0.000) —
numbers computed from the data, never hardcoded.

**Pillar 2 — A disclosure receipt.** Every output carries a C2PA-style receipt: which AI tools
ran (and in which mode — real or mock, always stated), what was generated vs. what the student
did, the student's own contribution log, and a **SHA-256 integrity hash** that anyone can verify.
It turns "the AI helped" into "here is exactly how, and here is what is mine."

The whole loop — question → dataset → audit → receipt → downloadable package — is one guided
flow, works fully offline, and requires no ML background.

## 6.4 Description — Key Features

All features below are implemented, tested (74 automated tests + scripted E2E), and running.

- **F1 · Question → Scope** — a rough question becomes a structured research plan: type,
  variables, row count, data plan, with editable fields and refinement suggestions.
- **F2 · Dataset Invention** — generates a validated synthetic dataset (schema/range-checked,
  exact-deduped, near-duplicate ≤5% with retry), every row tagged `synthetic`.
- **F3 · Dataset Augmentation** — cleans a messy CSV (dedup, fill gaps) and augments it to a
  target size; originals preserved and tagged, new rows tagged `augmented`.
- **F4 · Quality Audit** — real before/after metrics with plain-language interpretations and
  an overall verdict; the before/after chart is the hero shot.
- **F5 · Disclosure Receipt** — full C2PA-style receipt (tools, modes, contributions, sources,
  oversight level) with a SHA-256 integrity hash that verifies on reload; variants: standard,
  journal-style (COPE/Nature), teacher-check.
- **F6 · Research-Ready Export** — one-click bundle: dataset (provenance column intact) +
  receipt + auto-drafted methodology.
- **F7 · Guided Refinement** — re-frames vague questions into measurable ones; picks are logged
  as the student's own contribution.
- **F11 · Contribution Log** — every student action (plan edits, uploads, refinement picks) is
  recorded and shown in the receipt, making ownership auditable.
- **F9 · Source Honesty** — receipts list only sources genuinely consulted (none here — stated
  honestly, never fabricated); test-enforced.

## 6.5 Description — Technologies Used

- **Backend:** FastAPI + pandas + scikit-learn (real TF-IDF/cosine metrics, CPU-only) — Python.
- **LLM layer:** an OpenAI-compatible interface with two implementations — a **RealLLM** client
  and a labeled, deterministic **MockLLM** fallback. The demo runs in **mock mode** (no API keys
  needed); receipts always report which implementation actually ran.
- **Adaption Labs — Adaptive Data:** integrated via a dedicated adapter (`invent` / `improve`
  endpoints). **Mode used in the submitted demo: `emulated`** (Adaption adapter executed locally
  with identical semantics, labeled as `adaption-emulated` in every receipt). The real-HTTP
  path is implemented and activates automatically when `ADAPTION_API_BASE` + `ADAPTION_API_KEY`
  are configured — it is not claimed as used.
- **Frontend:** static SPA (HTML/CSS/JS, no build step), served by the same FastAPI app; charts
  are inline SVG driven directly by API numbers.
- **Honesty by design:** provenance on every row, mode badges in the UI, hash-verified
  receipts, and test-enforced no-fabricated-sources gates (`docs/06` §D).

## 6.6 Description — Target Users

- **High-school students** doing their first research project — the group most blocked by the
  data barrier and least able to defend AI-assisted work.
- **Undergraduates** in introductory research/ML courses who need a defensible first dataset
  and a habit of honest tool use.
- **Mentors and teachers**, who get an auditable record (contribution log + hash) to review
  student work against — the receipt doubles as an assessment artifact.

The design goal is zero-ML-background onboarding: pick a template, follow five screens,
download a package. The interface is a custom dark design system (inspired by Meta's
astryx) built around two signature elements: a **pipeline arc** that lights up the
research journey step by step, and a **verified-document receipt** — a perforated,
hash-sealed certificate that makes data disclosure feel real rather than cosmetic. A
persistent mode chip states whether the run is in mock or live mode, so the demo's
honesty is always visible.

## 6.7 Description — Social Impact

**Access.** ResearchLoop removes the entry barrier to doing real, defensible research. Students
who previously couldn't get a usable dataset now get one matched to their own question — and
they see, in plain language, exactly what quality problems the data had and how they were fixed.
The tool runs offline with no accounts or keys, so any classroom can use it.

**Defensible research.** The disclosure receipt turns AI assistance into something a student can
explain and defend: what the AI did, what the student did, and a hash that proves the receipt
wasn't altered after the fact. This is a concrete step toward honest, auditable AI use in
education — the same disclosure principles professional content uses, brought to students.

**Impact evidence (testing, see repo `scripts/usability_session.md`).** A scripted usability
run of the full five-screen flow completed in **~17 seconds**; the receipt was the artifact the
tester immediately wanted to show a teacher. Quote captured: *"The receipt is the thing I'd
actually show a teacher — it says exactly what the AI did and what I did, and the hash means
nobody can say I made it up after the fact."* (Team-member run; external students unavailable,
noted for transparency.) The quality audit is proven real by a metrics spot-check that matches
three engine metrics against hand calculation (`scripts/spotcheck_metrics.py`).

## 6.8 Files & Links

- **Repo:** [github.com/your-org/researchloop](https://github.com/your-org/researchloop) *(replace with actual repo URL)*
- **Live demo:** run `uvicorn app.main:app` (see README) — no keys required
- **Demo video:** `assets/demo_video.webm` (Ask → Build → Audit hero shot → Receipt → Export)
- **Screenshots:** `assets/screenshots/01_ask_plan.png`, `02_build_invent.png`,
  `03_audit_before_after.png` (hero), `04_receipt.png`, `05_receipt_variant.png`,
  `06_export.png`, `07_build_augment.png`
- **Receipt sample:** `assets/receipt_sample.json` (exactly as the API produces it)
- **Documentation:** `docs/` (research, literature review, API contract, per-phase plans with
  validation evidence)

## 6.9 Team Details

*(Fill in with actual student members — 1 to 5, students only, per challenge eligibility.)*

| Member | Role |
|---|---|
| *[Name]* | *[Role — e.g., backend, frontend, research, testing]* |
| *[Name]* | *[Role]* |

**Credits:** Built with the **Adaption Labs** Adaptive Data integration (adapter layer; emulated
mode used in the demo) and aligned with the **Rise Research** mission of accessible, defensible
student research. ML Empowerment Foundation's Build Challenge 4.0.

---

## Pre-submit honesty audit (re-read before pasting)

- [ ] No feature is claimed that isn't built and tested (F1–F11 claims all map to code + tests).
- [ ] Sponsor usage is accurate: Adaption adapter implemented; demo runs in **emulated** mode —
      real Adaption API is **not** claimed as used.
- [ ] LLM mode is accurately stated: demo runs in **mock** mode; RealLLM implemented, not claimed.
- [ ] All links/files verified from a fresh context before submitting.
