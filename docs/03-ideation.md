# ResearchLoop — Ideation Stage: Concept, Features & Specification

**Status:** Ideation (post literature review) · **Build window:** ~16 days · **Sponsors:** Adaption Labs, Rise Research · **Organizer:** ML Empowerment Foundation

---

## 1. Precise Idea Statement

> **ResearchLoop** is a **data-first research starter for students**. A student enters a rough research question (or pastes a small, messy dataset), and ResearchLoop does exactly two things, end to end:
>
> 1. **Invents or augments a usable dataset for that question** — generating a seed dataset where none exists, or improving a tiny uploaded one, with a visible before/after quality score.
> 2. **Attaches a disclosure receipt to every output** — a tamper-evident record stating what the AI generated, what sources/data were used, what was verified, and what remains the student's own contribution.
>
> The output is a **research-ready package**: dataset + receipt + methodology summary, ready for a mentor, teacher, or journal. It is **not** a chatbot, **not** a full research-automation agent, and **not** a mentorship substitute — it is the *first, verifiable 5%* of a research project, the part every student gets stuck on.

**One-line positioning:** *The missing first step between a research question and real, defensible student research.*

---

## 2. Name & Branding (decision point — recommended option marked)

| Candidate | Why it fits |
|---|---|
| **ResearchLoop** *(recommended)* | Describes the loop: question → data → audit → receipt → package. Loops imply iteration (improve, re-audit). Easy to say, easy to demo. |
| **DataSeed** | Evoke the core act: plant a seed of data for your research. Short, memorable. |
| **Receipted** | Puns on the receipt; emphasizes the disclosure novelty. Less descriptive of the data side. |

**Recommendation:** keep **ResearchLoop** — it covers both pillars (research + the loop of verify), and the receipt is a feature of the loop, not the whole product.

---

## 3. The Core Loop (the entire product, at a glance)

```
STUDENT INPUT                RESEARCHLOOP                         OUTPUT
─────────────────────────────────────────────────────────────────────────────
Rough research question ──► ① SCOPE    ──► Research brief + data plan
(or messy small CSV)         (question → task type → variables)
                              │
                              ▼
                          ② BUILD      ──► Invented or augmented dataset
                               (Adaption Adaptive Data)   (rows, labels, metadata)
                              │
                              ▼
                          ③ AUDIT      ──► Quality report: before/after scores
                               (dedup, diversity, coverage, distribution)
                              │
                              ▼
                          ④ RECEIVE    ──► Disclosure receipt (AI use, sources,
                               (receipt + export)        student's own work)
                              │
                              ▼
                     research-ready package (dataset + receipt + methodology)
```

Every stage is a screen. The whole flow is the demo.

---

## 4. Feature Taxonomy

### 4.1 CORE — Must-have (the MVP; without these the idea is not ResearchLoop)

| # | Feature | Spec | Why it's core | Build risk |
|---|---|---|---|---|
| **F1** | **Question → Scope** | Student types a rough question. ResearchLoop parses it into: research type (classification / regression / survey-style / descriptive), candidate variables, and a suggested data plan (what data would answer this, roughly how many rows). Student can edit the plan. | Turns a vague question into a buildable task — the first thing stuck students need. Shows real NLP/understanding skill (Technical 30%). | Low — LLM parsing + template output. |
| **F2** | **Dataset Invention** | Given the scoped plan, generate a seed dataset for the topic: rows of plausible, context-correct data + labels + a schema (columns, units, notes). E.g., "study time vs exam score" → 60–100 synthesized student records. Mark every row as *synthetic*. | The literal demo of Adaption's flagship "Invent a dataset" capability. The single most novel, sponsor-aligned feature. | Medium — prompt design + structured generation; must look credible, not random. |
| **F3** | **Dataset Augmentation** | Student uploads a small messy CSV (5–200 rows). ResearchLoop cleans it (duplicates, missing values, formatting), augments it to a usable size, and preserves the original as a baseline. | Covers the "student already has tiny data" case — half the real scenario. Direct Adaption "Improve" use. | Medium — real data cleaning logic + LLM augmentation; must handle messy real files. |
| **F4** | **Quality Audit & Before/After Dashboard** | For any dataset (invented or uploaded): computes quality scores — duplicate rate, diversity (embedding similarity), label coverage/completeness, distribution sanity — and shows a **before → after** comparison chart. | The "proof it works" artifact. Validates against the verification literature (LLM Data Auditor, model-collapse work). The single best screenshot for the submission. | Medium — metrics must be real (not faked), but each is simple to compute. |
| **F5** | **Disclosure Receipt** | Auto-generated, per run: (a) AI tools used + purpose; (b) what was generated vs. what was student-supplied; (c) human oversight level; (d) sources/references consulted; (e) a signature/hash + timestamp. Exportable as a file (PDF/JSON). | The Rise-aligned integrity pillar; the differentiator vs. every chatbot. Policy-backed (COPE/C2PA/Nature). | Low–medium — template + structured data; no crypto needed for v1 (see open questions). |
| **F6** | **Research-Ready Export** | One-click package: dataset (CSV) + receipt + one-paragraph methodology summary written in the student's voice (auto-draft, student-editable), downloadable together. | The finish line — makes the tool's output *submittable*, not just a demo artifact. Strong Impact + Presentation story. | Low — file bundling. |

### 4.2 IMPORTANT — Should-have (strongly strengthen the submission; include if time allows, after core is solid)

| # | Feature | Spec | Value | Priority |
|---|---|---|---|---|
| **F7** | **Guided Question Refinement** | If the question is too vague ("help me with climate"), ResearchLoop offers 2–3 concrete, researchable re-framings the student can pick. | Teaches research framing (ML Empowerment pedagogy); prevents dead-end demos. | High (cheap, high polish value) |
| **F8** | **Receipt Variants** | Receipt modes: *standard* (default) / *journal-style* (fields matching COPE/Nature requirements) / *teacher-check* (one-page summary for mentors). | Shows depth; directly maps to sponsor ethos and real policies. | Medium |
| **F9** | **Source Grounding** | For invention tasks that reference real concepts, the receipt lists the references/data sources consulted (with links) — only where genuinely consulted, never fabricated. | Combats the citation-hallucination problem head-on; defensible honesty. | Medium |
| **F10** | **Scenario Templates** | 5–8 pre-built research scenarios ("Does sleep affect focus?", "Which local plant is most heat-tolerant?", "Do students who study in groups score higher?") — one click to demo. | Guarantees a flawless demo even under time pressure; great for the video. | High (demo insurance) |
| **F11** | **Student Contribution Log** | Lightweight journal: every student edit/correction is logged and shown on the receipt ("Student edited 12 rows, corrected 3 labels"). | Makes "student owns the thinking" visible and auditable — core to Rise ethos. | High (cheap) |
| **F12** | **Plain-language Explainers** | Each quality score and receipt field has a one-line "why this matters" tooltip. | Beginner-friendly (Beginner Friendly theme); UX score. | Medium |

### 4.3 EXISTING / LEVERAGED — capabilities we build *on*, not build *from scratch*

These are existing capabilities we integrate or emulate; listing them is honest and shows technical competence:

| Capability | Source | How ResearchLoop uses it |
|---|---|---|
| **Adaptive Data — Invent** | Adaption Labs platform | F2 dataset invention (sponsor's flagship feature; the project must state real usage of Adaption credits) |
| **Adaptive Data — Improve** | Adaption Labs platform | F3 augmentation/cleaning pipeline (82% quality-lift claim context) |
| **Data connectors** (HuggingFace, Kaggle, upload) | Adaption platform | Real student datasets can be sourced via Adaption connectors; upload fallback in the UI |
| **LLM generation + structured output** | Open LLM APIs | F1 scope parsing, F2 invention, F3 augmentation, F6 methodology draft |
| **Embedding models** (e.g., sentence-transformers) | Open models | F4 diversity/duplicate metrics |
| **C2PA / Content Credentials** | Industry standard | F5 receipt design language (adopt the human-oversight-level schema; v1 may be simplified — see open questions) |
| **COPE / Nature disclosure fields** | Publisher policies | F5 receipt fields and F8 journal-style mode |
| **Datasheets / Data Nutrition Label** | Documentation standards | F4 audit dimensions + F6 methodology summary structure |

### 4.4 NICE-TO-HAVE — could-have (stretch; only if core + important are done and demo is safe)

| # | Feature | Note |
|---|---|---|
| **N1** | **Multilingual mode** | Invent/augment + receipt in the student's language (Adaption's 242-language claim). Powerful impact story, but adds real scope — keep as stretch. |
| **N2** | **Mentor review mode** | A teacher/mentor dashboard to review a student's receipt and dataset. Strong impact story, needs a second user role — likely too much for 16 days. |
| **N3** | **Reproducibility re-runs** | "Re-run and compare" — shows generation stability across runs. Nice technical depth; only if the pipeline is robust. |
| **N4** | **Dataset gallery / share** | Students publish (anonymized) their invented datasets to a community gallery. Great impact, but adds moderation/privacy concerns — post-hackathon. |

### 4.5 EXPLICITLY EXCLUDED — will-not-have (defend in the submission)

| Excluded | Why excluded |
|---|---|
| **Full research-cycle automation** (lit review → analysis → paper) | Crowded (Elicit/Consensus/AI Scientist); high stub risk; dilutes the 30% Technical score |
| **Chatbot / answer-generation** | Saturated; off-brand ("data-first, not answer-first") |
| **Continuous learning / model retraining** | The dropped AutoScientist layer — highest stub risk; not needed for the two-pillar value |
| **Training/serving a custom model** | Out of scope; the deliverable is a dataset + receipt, not a model |
| **Fake "AI-detection"** | Literature is clear: detection has 43–83% false positives and is being abandoned — our receipt is the honest alternative |
| **Multilingual invention** | Stretch (N1) — only after core is solid |
| **Mentor matching / matching engine** | Too heavy; mentorship is Rise's domain, we complement it |

---

## 5. Detailed Feature Specs (core features)

### F1 — Question → Scope
- **Input:** free-text question; optional target sample size.
- **Process:** LLM extraction → structured JSON: `{research_type, variables: [{name, type, unit}], suggested_rows, data_plan, suggested_dataset_name}` → render as editable plan card.
- **Output:** editable research plan card.
- **Rubric:** Technical (NLP understanding) · UX (clean step 1) · Beginner-friendly.

### F2 — Dataset Invention
- **Input:** the scoped plan (variables, rows, topic).
- **Process:** LLM generates rows in a strict schema (JSON), validated for type/range; a diversity prompt keeps records varied; every row tagged `synthetic: true`; duplicates filtered.
- **Output:** dataset table (preview) + schema + row-level provenance tag.
- **Rubric:** Technical (real generation pipeline) · Creativity (the core novel act) · Adaption alignment.
- **Key honesty rule:** the UI must label invented data as synthetic everywhere — never present synthetic data as real measurements.

### F3 — Dataset Augmentation
- **Input:** uploaded CSV (5–200 rows) + a target size.
- **Process:** parse → validate → clean (dedup, missing-value handling, type normalization) → augment via LLM (paraphrase/replicate with variation, respecting distribution) → keep the original as baseline for before/after.
- **Output:** cleaned + augmented dataset, original preserved.
- **Rubric:** Technical (real data engineering) · Impact (real student use case).
- **Key honesty rule:** augmented rows are tagged `augmented`; original rows stay `original` — provenance preserved per row.

### F4 — Quality Audit & Before/After Dashboard
- **Metrics (all real, computed in-app):**
  - *Duplicate rate* (exact + near-duplicate via embedding cosine similarity)
  - *Diversity score* (mean pairwise embedding similarity — lower is more diverse)
  - *Completeness* (missing-value % per column)
  - *Label coverage* (% rows with valid labels, for classification tasks)
  - *Distribution sanity* (range checks on numeric columns)
- **UI:** before/after bar or radar chart per metric; one-line interpretation per metric ("diversity improved: mean similarity 0.71 → 0.42").
- **Rubric:** Technical (metrics are real) · Presentation (best screenshot in the submission) · literature-backed (verification gap).

### F5 — Disclosure Receipt
- **Fields:** research question · dataset source (invented / uploaded / augmented) · AI tools used + purpose · what was generated vs. student-supplied · human oversight level (fully_autonomous / prompt_guided / human_validated) · student contribution log (edits, corrections) · sources consulted · timestamp + integrity hash.
- **Format:** human-readable one-page view + downloadable JSON (and PDF if time).
- **Rubric:** Creativity (novel differentiator) · Impact (integrity) · Rise alignment.
- **Design note:** adopt the C2PA `humanOversightLevel` vocabulary so the receipt speaks the industry's language.

### F6 — Research-Ready Export
- **Package:** dataset CSV + receipt + methodology summary (auto-drafted, student-editable) + plan card.
- **One-click download** as a folder/zip or individual files.
- **Rubric:** Presentation (submission completeness) · Impact (output is submittable).

---

## 6. User Flow (the demo script — 5 screens)

1. **Ask screen:** "What question do you want to research?" (+ template picker) → ResearchLoop returns the **scoped plan card** (F1/F7).
2. **Build screen:** "We'll invent 80 records for your question." → generates, shows the **dataset preview** (F2) — or, alternate path, "Upload your own small dataset" (F3).
3. **Audit screen:** **before/after quality dashboard** (F4) with plain-language interpretations (F12).
4. **Receipt screen:** the **disclosure receipt** (F5) with the student's contribution log (F11).
5. **Export screen:** **research-ready package** download (F6) → closing line: *"Your dataset, your receipt, your methodology — ready to submit."*

The demo video is exactly this flow, 90–120 seconds, one question.

---

## 7. System Architecture (buildable in 16 days)

```
┌─────────────────────────┐     ┌───────────────────────────────┐
│  Web UI (React/Next.js) │────►│  Backend API (Python/FastAPI) │
│  5 screens, dashboard,  │     │  - scope parsing               │
│  receipt render, charts │     │  - generation orchestration   │
└─────────────────────────┘     │  - audit engine               │
                                 │  - receipt builder            │
                                 └───────┬───────────────┬───────┘
                                 │               │
                     ┌───────────▼──────┐   ┌────▼────────────────┐
                     │ LLM Layer        │   │ Quality Engine       │
                     │ (scope, invent,  │   │ (dedup, diversity,  │
                     │  augment, draft)│   │  completeness, hash)│
                     └──────────────────┘   └──────────────────────┘
                                 │
                     ┌───────────▼──────────────────────────┐
                     │ Adaption Integration Layer           │
                     │ (Adaptive Data via Adaption credits  │
                     │  or faithful emulation — TBD)        │
                     └──────────────────────────────────────┘
```

- **Data:** in-memory / local SQLite per session; datasets as CSV artifacts.
- **No heavy infra:** no GPU, no model training — all LLM calls are API-based; metrics run on CPU with a small embedding model.
- **Honesty:** every LLM-generated artifact is tagged; the receipt reflects actual tool usage.

---

## 8. Sponsor & Organizer Alignment Matrix

| Feature | Adaption Labs | Rise Research | ML Empowerment Foundation |
|---|---|---|---|
| F2 Invention | ✅ **flagship "Invent a dataset"** — real use of credits | ✅ data for student research | ✅ learns "data is the foundation" |
| F3 Augmentation | ✅ **"Improve" / 82% quality lift** | ✅ turning messy student data into research data | ✅ practical data skills |
| F4 Audit | ✅ Adaptive Data quality focus | ✅ verification ethos | ✅ "evaluate AI outputs" (curriculum) |
| F5 Receipt | ⚠️ thematic | ✅ **core ethos (disclose AI use)** | ✅ AI ethics lesson |
| F6 Export | ✅ ownership story | ✅ submission-ready work | ✅ "ship a real project" |
| F7/F11 Refinement + contribution log | ✅ human-in-the-loop | ✅ **student owns the thinking** | ✅ problem-framing skills |

**Sponsor support statement for the submission:** ResearchLoop directly exercises Adaption's Adaptive Data capabilities (invent/improve) and operationalizes Rise Research's AI-disclosure ethos as an automatic, student-facing artifact.

---

## 9. Rubric Coverage Map

| Judging criterion (weight) | Features serving it |
|---|---|
| **Technical Implementation (30%)** | F1 (NLP parsing), F2/F3 (real generation + cleaning pipelines), F4 (real metrics), F5 (structured receipt), F6 (export) |
| **Creativity & Innovation (20%)** | The *combination* — data-first student research starter + auto disclosure receipt; no gallery/literature equivalent |
| **Real-World Impact (20%)** | F2/F3 (democratized data access), F4 (verifiable quality), F5/F6 (defensible, submittable student work); documented access-gap backing |
| **Project Design & UX (15%)** | F7, F10, F12 — guided flow, templates, plain-language explainers, 5-screen loop |
| **Presentation & Documentation (15%)** | F4 before/after chart (hero screenshot), F5 receipt (novel artifact), F6 package, rubric-aligned description, social-impact statement |

---

## 10. Feature → 16-Day Build Mapping

| Days | Focus | Features |
|---|---|---|
| 1–2 | Setup, repo, Adaption credits, decision locks | — |
| 3–5 | Core flow: scope + invention + augmentation | F1, F2, F3 (+ F7 quick win) |
| 6–7 | Quality engine + dashboard | F4, F12 |
| 8–9 | Receipt + export | F5, F6, F11 |
| 10–12 | Templates, testing with real students, fixes | F10, polish, impact evidence |
| 13–14 | Devpost description to rubric | — |
| 15 | Demo video + screenshots | — |
| 16 | **Submit** | — |

**Demo-safety rule:** F10 (templates) is built on day 10–12 *only* as insurance — if any custom question fails in testing, the demo falls back to a template.

---

## 11. Risk Register (per feature)

| Feature | Risk | Mitigation |
|---|---|---|
| F2 Invention | Output looks fake/random → judges discount it | Strict schema + range validation + diversity prompts + always label as synthetic; test with template questions first |
| F3 Augmentation | Messy real CSVs break parsing | Constrain input format (guided CSV template), robust parsing, fallback error UX |
| F4 Audit | Metrics perceived as fake | Compute them for real, show the formula in a tooltip; a real before/after is the hero evidence |
| F5 Receipt | Feels gimmicky | Ground in C2PA/COPE fields; show it next to real journal requirements |
| F1 Scope parsing | Vague inputs derail | F7 refinement step + templates (F10) as guardrails |
| Overall | Over-scoping creeps back in | Hard rule: core F1–F6 only; important features only if core is solid and demo-safe |

---

## 12. Open Decisions (from Define stage — confirm to lock the build)

1. **Demo topic / template set** — recommended: 3 templates spanning task types: *"Does study time affect exam scores?"* (classification/regression), *"Which local plant species tolerates heat best?"* (descriptive/ecology), *"Do students who study in groups score higher?"* (survey-style). Rationale: covers different research types, all dataset-meaningful at 60–100 rows.
2. **Receipt depth** — recommended: **structured human-readable receipt + downloadable JSON** (C2PA-style fields, no cryptography). Honest, credible, buildable; the submission states the design follows C2PA's disclosure schema.
3. **Adaption integration level** — recommended: **use Adaption credits for the real Adaptive Data workflow where feasible** (invent/improve on a small dataset); if the API/UI proves constrained in the sandbox, implement a *faithful emulation* and state exactly that in the submission ("demo uses Adaption's Adaptive Data workflow; full credit-based run documented in repo"). Honesty is non-negotiable.
4. **Impact testing** — recommended: test with **1–2 real students** (even team members' siblings/classmates), capture before/after quality + receipt usability; quote one line in the impact statement.

**Next action after your confirmation:** lock decisions → scaffold the repo (web app + backend) → build F1–F4 first (the demo spine).
