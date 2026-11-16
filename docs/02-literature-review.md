# ResearchLoop — Literature Review: Primary & Secondary Sources

**Purpose:** Establish uniqueness/novelty for the scoped Direction A' (ResearchLoop: AI research helper that (1) invents/augments a student's dataset via Adaption Adaptive Data, (2) attaches a disclosure receipt). This document is the evidence base for the Define stage.

**Sweep structure:** Primary = peer-reviewed papers, technical reports, standards specifications, benchmark systems. Secondary = surveys, industry reports, tool comparisons, policy analyses. All sources checked live on 16–17 Nov 2026.

---

## Part 1 — Primary Literature

### A. Synthetic / Adaptive Data Generation (the "invent or augment a dataset" pillar)

| Source | What it establishes | Relevance to ResearchLoop |
|---|---|---|
| **Self-Instruct** (Wang et al., ACL 2023) — arxiv.org/abs/2212.10560 | Bootstraps instruction datasets from a tiny seed set via the model's own generations, with light heuristic filtering (~30–40% removed); near-annotation-free; ~33% gain on Super-NaturalInstructions | The canonical method for "generate data where none exists" — exactly what ResearchLoop's dataset-invention step implements at student scale |
| **Evol-Instruct / WizardLM** (Xu et al.) — arxiv.org/abs/2304.12244 | Iteratively rewrites instructions into harder/more diverse ones (depth + breadth); evolved instructions beat human-written ones | Powers difficulty/diversity control in the augmentation step — lets ResearchLoop evolve a student's tiny dataset rather than just copying it |
| **Magpie** (arxiv.org/abs/2406.08464) | Generates alignment data "from nothing" by feeding a model only the chat-template prefix; 4M pairs curating to 300K matched Llama-3-Instruct | Proof that useful datasets can be synthesized with **no seed data at all** — supports ResearchLoop's "no data, no problem" onboarding path |
| **A Survey on Data Synthesis and Augmentation for LLMs** — arxiv.org/html/2410.12896v1 | Taxonomy: distillation, self-improvement, augmentation; lifecycle view (pretraining → fine-tuning → instruction tuning) | Frames where ResearchLoop sits: student-facing *data preparation* for small research tasks |
| **Synthetic Data Generation Using LLMs: Advances in Text and Code** — arxiv.org/html/2503.14023v1 | Survey of prompt-based generation, iterative refinement (Self-Instruct variants), filtering | Reference for the generation pipeline design (seed → generate → filter → evaluate) |
| **Beyond Model Collapse: Scaling up with Synthesized Data Requires Verification** — arxiv.org/pdf/2406.07515 | Model collapse occurs with unverified synthetic data; **verification/selection is what prevents collapse**; "accuracy of the best synthesized solution is 3× higher than the model's own perplexity-based pick" | Key theoretical justification: ResearchLoop must pair *generation* with a *verifier* — the disclosure receipt's quality-check component |
| **Collapse or Creativity — Hallucinations in Recursive Synthetic Data Generation** (Research Square, 2026) | Recursive synthetic generation fails within ~5 generations; loss of diversity/fidelity (mean collapse, mode invention); "clear provenance with quality evaluation metadata is needed" | Direct support for ResearchLoop's **quality-audit + provenance** requirement; warns against unchecked recursive generation |
| **A Survey on Evaluating Quality and Trustworthiness in LLM-Generated Data (LLM Data Auditor)** — arxiv.org/html/2601.17717v3 | Intrinsic quality/trustworthiness metrics (faithfulness, diversity, fairness) across modalities; "faithfulness is central to controlling hallucination" | Provides the metric menu for ResearchLoop's before/after quality dashboard |
| **Synthetic Data: Generation, Quality, Diversity, Distillation** (mbrenndoerfer.com) | Practical synthesis: backtranslation, rejection sampling, diversity thresholds (ROUGE-L dedup), temperature/diversity knobs | Concrete implementation levers for the augmentation module |

**Takeaway:** Synthetic data generation is mature but its *verification, quality-audit, and provenance* layer is the recognized weak point. ResearchLoop's "invent/augment + quality-check + disclose" is precisely the frontier that primary literature flags as the open problem — not a solved, crowded space.

### B. AI Research Assistants & Automated Research Agents (the "help students do research" pillar)

| Source | What it establishes | Relevance |
|---|---|---|
| **Redefining Literature Reviews: A Scoping Review of AI-Powered Research Assistants** (AWEJ, 2026) | Analyzes Google Scholar Labs, Scopus AI, NotebookLM, Elicit, ResearchRabbit, Connected Papers, LeapSpace | The landscape ResearchLoop sits *adjacent to* — but these are discovery/synthesis tools for experts, not student dataset-building tools |
| **AI Powered Research Assistant: Real Citations vs Hype** (Botonomy) | 67% of STEM researchers use AI in ≥1 lit-review stage (2026); **hallucination 6–12% even with RAG**; agentic multi-step workflows emerging | Confirms the problem ResearchLoop's receipt/verification addresses: AI research help without verification produces noise |
| **The Hitchhiker's Guide to Autonomous Research: A Survey of Scientific Agents** (2026, IEEE) | Maps scientific agents across the research lifecycle | Frames the automated-research field; ResearchLoop is a *human-in-the-loop, beginner* variant |
| **Hidden Pitfalls of AI Scientist Systems** — arxiv.org/pdf/2509.08713 | Audits Agent Laboratory & AI Scientist v2; recommends journals mandate **submission of trace logs/code** alongside papers for transparency & reproducibility | Strong external validation: the field is converging on "traceability artifacts must ship with research" — ResearchLoop's disclosure receipt is the student-scale version of this |
| **MLReplicate: Benchmarking Autonomous Research Systems** — arxiv.org/html/2605.16616 | 6 systems, 45 manuscripts; **fabricated/unsupported claims in 59% of accepted outputs**; no system reliably publication-ready | Evidence that AI research output is untrustworthy without verification — the core justification for a disclosure + verification layer |
| **The Agentic Scientist** — arxiv.org/html/2610.18933v1 | Human-steerable scaffold; explicitly requires "provenance for generated code and text, disclosure of agent contributions, watermarking, human accountability" | Mirrors ResearchLoop's design principles at research-grade scale |
| **From AI for Science to Agentic Science: A Survey** — arxiv.org/html/2508.14111v1 | "Human-in-the-loop" as the key paradigm; reproducibility and provenance are "non-negotiable" | Supports ResearchLoop's human-in-the-loop, receipt-based design |
| **Agentic Laboratories of the Future** (Preprints, 2026) | Agentic labs must "preserve provenance, uncertainty, decision histories"; publishing may evolve "toward process-level disclosure" | Vision statement: process-level disclosure is the future — ResearchLoop builds the student-facing version now |

**Takeaway:** The automated-research field has *proven* the verification/disclosure gap is real (59% fabrication rate in MLReplicate; hallucination in every assistant). But every system targets **PhD-level, compute-heavy** research. **No system targets high-school/beginner students with a small-dataset, low-compute workflow** — that is ResearchLoop's white space.

### C. Provenance, Disclosure & Academic Integrity (the "disclosure receipt" pillar)

| Source | What it establishes | Relevance |
|---|---|---|
| **C2PA Technical Specification (v2.4)** — spec.c2pa.org | Open standard for cryptographically signed provenance; `ai-model-disclosure` assertion with model provenance + **human oversight level** (fully_autonomous / prompt_guided / human_validated) | The receipt's design language: model used + human oversight level — directly adoptable as a simple, principled schema |
| **IPTC 2025.1 & C2PA** — numonic.ai | Four new XMP fields (AISystemUsed, AISystemVersionUsed, AIPromptInformation, AIPromptWriterName); satisfies EU AI Act Art. 50 + California SB 942 | Confirms the regulatory direction of travel: machine-readable AI-use disclosure is becoming mandatory |
| **COPE AI authorship guidelines** (2023, updated 2025) | AI cannot be an author; AI use must be disclosed; three-category framework (assistive / generative-disclosed / prohibited) | The exact disclosure standard Rise Research teaches — ResearchLoop automates it for students |
| **Nature / Elsevier / IEEE AI policies (2026)** | Generative AI use declared in Methods/Acknowledgments; name tool+version; copy-editing exempt; verify every AI-generated reference | The receipt should encode "what tool, for what purpose, how much" — aligned with publisher requirements |
| **AI Content Provenance and Watermarking: The New Era of Academic Integrity (2026)** | Universities shifting from AI *detection* (43–83% false positives) to cryptographic proof; version history as evidence | Receipts are the defensible alternative to detection — strong judging narrative |
| **Digital Provenance in AI** (Trantor) | C2PA coalition (Adobe, Microsoft, Google, Meta, OpenAI…); EU/NY/California mandates | Shows the receipt concept is not speculative — it's standards-backed infrastructure |

**Takeaway:** Disclosure/provenance is a *standards-backed, policy-mandated* direction — but existing tooling is built for **publishers, platforms, and journals**, not for **students**. ResearchLoop's innovation is *translating institutional disclosure standards into a student-facing, per-artifact receipt*.

### D. Dataset Documentation & Auditing (the "quality before/after" pillar)

| Source | What it establishes | Relevance |
|---|---|---|
| **Datasheets for Datasets** (Gebru et al., 2021) | The canonical dataset documentation standard | The receipt's data section is a mini-datasheet; students learn documentation discipline |
| **Data Cards** (Pushkarna et al., 2022); **Dataset Nutrition Label** (Chmielinski et al.) | Structured dataset documentation artifacts | Sources for the receipt's structured fields |
| **Too Big to Inspect? Ethically Auditing Large Datasets Through Small Samples** — arxiv.org/html/2611.10399v1 | **Small random samples can reveal structural bias and quality flaws** — no need to inspect everything | Validates ResearchLoop's approach: a student's 50-row dataset can be meaningfully audited, not dismissed as "too small" |
| **AI Transparency: Model Cards & Datasheets** (2026 study notes) | Lifecycle of documentation: datasheet → training → model card → monitoring | The full transparency pipeline ResearchLoop simplifies for beginners |
| **Dataset cards (theneuralbase)** | Dataset cards as "Carfax for data" — motivation, composition, known limitations | The receipt can be framed as a student's first dataset card — a real research skill |

**Takeaway:** The literature explicitly validates **small-sample, lightweight auditing** — a student-scale dataset is not a barrier; it's an opportunity. ResearchLoop turns datasheet/nutrition-label practice into an automatic, per-run artifact.

### E. Low-Resource Languages & Data Scarcity (optional accent)

| Source | What it establishes | Relevance |
|---|---|---|
| **NLP applications for low-resource languages** (Cambridge, 2025) | Data scarcity is the central barrier; community engagement + transfer learning are key strategies | If ResearchLoop adds a multilingual mode, this is the justification |
| **NLP for Personalized Education in Low-Resource Environments** (2025) | Adaptive learning + data augmentation + community-sourced datasets for underserved regions | Maps directly to the user story: students where data doesn't exist |
| **NLP Benchmarks in an Extremely Low-Resource Setting** — arxiv.org/pdf/2509.03962 | Synthetic augmentation from monolingual resources created a first benchmark for an endangered language | Proof that synthetic data invention can *create* research resources for a community — a powerful impact narrative |

**Takeaway:** Optional, not core. A multilingual data-invention accent makes the impact story global ("students in any language can invent their own dataset") but adds scope — keep as a stretch feature.

### F. Student Research Access & Mentorship (the "why this matters" pillar)

| Source | What it establishes | Relevance |
|---|---|---|
| **Democratization of Undergraduate Research** (CUR, Summer 2017) | UR is a high-impact practice; mentors want broader access; **communication technologies can widen access across geography**; the bottleneck is mentor time | The core problem ResearchLoop attacks: demand for mentored research outstrips mentor supply |
| **Research Barriers and Mentorship Quality** (Kennesaw, 2026) | Top barriers: external commitments, lack of time, **lack of awareness of opportunities** | Confirms the "how do I even start" pain point for students |
| **Mentoring for Inclusion** (2016); **National Academies: Role and Impact of Mentoring** | Mentored research raises GPA, retention, science identity; mentor training matters | The impact narrative: ResearchLoop is a force-multiplier for scarce human mentors |
| **Polygence** (program site) | Commercial precedent for 1-on-1 PhD-mentored student research; outcomes = papers, prototypes, apps | Shows the market/need exists; ResearchLoop is the AI-assisted, accessible analog (and a sponsor-aligned differentiator vs. Rise/Polygence: it's a *tool*, not a paid program) |

**Takeaway:** The access gap is documented, quantified, and persistent. ResearchLoop is a *scalable, free* response to a documented, high-impact educational need — this is the Real-World Impact (20%) backbone.

### G. AI Literacy & Project-Based Learning (the "ML Empowerment fit" pillar)

| Source | What it establishes | Relevance |
|---|---|---|
| **AI Literacy Framework: PBL course for senior secondary students** (ScienceDirect, 2024) | 14-hour PBL course improved students' AI problem-solving ability, metacognition, and **ethical understanding** | Direct evidence that project-based AI building is the effective pedagogy — exactly ML Empowerment's model |
| **Using AI Tools to Support PBL** (Edutopia, 2025) | Digital Promise AI Literacy Framework: **Understand / Evaluate / Use**; students should fact-check AI output against sources | The receipt's design maps to the "Evaluate" dimension — turning an abstract skill into a concrete workflow |
| **The Future of AI Literacy Education (OECD Education 2030)** — edtecharchives.org | AI literacy = knowledge + skills + attitudes/values; **ELSI-integrated PBL** (ethical, legal, social issues in problem-solving) is recommended | ResearchLoop = ELSI-integrated PBL in tool form: students build, and the tool forces the ethics/quality step |

**Takeaway:** The education literature validates ResearchLoop as *pedagogy-aligned*, not just tech-aligned. It operationalizes the "Evaluate" and "ethics" dimensions of AI literacy — a strong differentiator from generic chatbots.

### H. Crowdsourced / Non-Expert Annotation (the "students can produce real data" pillar)

| Source | What it establishes | Relevance |
|---|---|---|
| **Crowd-powered research (RFI, Franklin/Zooniverse)** | 18,000+ volunteers produced 3.49M classifications; **non-expert annotations, aggregated, can match expert quality** | Supports the flipped workflow: students as data creators, not just AI consumers |
| **Building a Bird Recognition App & Large Scale Dataset (CVPR 2015)** | **Citizen scientists have 2–4× lower error rates than paid crowdworkers**; one expert-label = 10 MTurk labels | Quality argument: engaged, domain-interested students annotate well — the target users are ideal annotators |
| **CrowdAnno** (arxiv.org/html/1508.06044) | Simplified visual operators let non-experts produce high-quality NLP annotations | Design principle for the UI: low barrier to contribute labels |
| **FloodTrace** (arxiv.org/html/2408.05350v1) | Elevation-guided tools + uncertainty visualization; **untrained students' aggregated annotations matched expert-labeled training data** | Validates the "guide the student, aggregate, verify" pipeline ResearchLoop uses |

**Takeaway:** ResearchLoop's "student supplies the question, tool supplies the data, student verifies" loop is consistent with crowdsourcing literature that says **guided non-experts + aggregation + verification = expert-grade data**. This is a defensible, novel framing: the student is the domain expert, the AI is the data engineer.

---

## Part 2 — Secondary Literature (surveys, industry, tools, policy)

| Source | Type | Key contribution |
|---|---|---|
| **Adaption Labs** (adaptionlabs.ai; ai-market-watch; Crunchbase; explainx.ai AutoScientist review) | Industry/primary-vendor | Adaption's three pillars: Adaptive Data (242 languages, "invent a dataset"), Adaptive Intelligence (AutoScientist, continuous learning), Adaptive Interfaces. Sponsor context for ResearchLoop |
| **Rise Research** (riseglobaleducation.com; Data Labs page; AI-research blog) | Industry | 1-on-1 PhD mentorship → peer-reviewed publication; 90% publication rate; **AI-as-assistant-with-disclosure** ethos; expert data labs. Sponsor context |
| **Best AI Research Assistants in 2026** (insideaimedia) | Tool comparison | Elicit, Consensus, Scite, SciSpace, ResearchRabbit — all expert-facing discovery tools; none do student dataset-building |
| **Best AI for Deep Research 2026** (aiagentchooser) | Tool comparison | Stage-dependent tool choice; citation verification workflows |
| **Best AI for Literature Review 2026** (botonomy) | Industry analysis | Hallucination rates, RAG limits, agentic workflows |
| **ML Empowerment Foundation** (mlempowermentfoundation.org; Udemy curriculum; LinkedIn) | Organizer | Mission, reach (72K+ students), curriculum structure, sponsor network |
| **Synthetic data quality evaluation guides** (theneuralbase, apxml, ai-infrastructure.net) | Engineering practice | Implementation-level guidance for the quality dashboard (dedup, semantic similarity, distribution matching) |
| **Synthetic Data Poisoning / Model Collapse** (dev.to, enterprise) | Industry | Recursive-generation degradation table; provenance-gate pipelines |
| **EU AI Act Art. 50 / California SB 942 / NY Stop Deepfakes** | Policy | Regulatory direction toward mandatory AI disclosure — receipt concept is future-proof |

---

## Part 3 — Gap Analysis & Novelty Statement

### What exists (and is crowded)
1. **Synthetic data generation** for model training — mature, heavily commercialized (Self-Instruct lineage, Magpie, vendor platforms).
2. **AI research assistants / deep research** — crowded (Elicit, Consensus, Perplexity, NotebookLM…), expert-facing, high compute.
3. **Automated research agents** — active research frontier (AI Scientist, Agent Laboratory), PhD-scale, and *failing* on verification.
4. **Provenance/disclosure standards** — C2PA/IPTC/COPE exist but target publishers/platforms, not learners.
5. **Dataset documentation** — datasheets/data cards are standards, but authoring is manual and expert-oriented.
6. **Student research mentorship** — exists as *paid human services* (Polygence, Rise), not as *AI tooling*.

### What does NOT exist (the white space — ResearchLoop's novelty)
1. **No tool combines student-scale dataset invention/augmentation with automatic quality auditing** — generation tooling targets enterprises/models; auditing targets big datasets; the *small, student-owned dataset* is unclaimed.
2. **No tool makes "AI-use disclosure" a per-artifact, automated, student-facing receipt** — the standards exist at institutional scale; nobody has translated them into a beginner workflow. The 59% fabrication rate in AI research output makes this the *timely* gap.
3. **No tool positions the student as the domain expert + AI as data engineer** — crowdsourcing literature proves non-experts can produce quality data when guided; ResearchLoop applies this to student research, inverting the usual "AI answers, student consumes" pattern.
4. **No AI-mentorship tool at the beginner/high-school level that is free and tool-based** — mentorship is a human-service market; ResearchLoop is the scalable, free, sponsor-aligned complement.

### Novelty statement (draft, for the Devpost description)
> ResearchLoop is not another research-summary chatbot. It is a **data-first research starter**: a student types a rough question (or pastes a tiny messy dataset), and ResearchLoop **invents or augments a usable dataset for that topic** — then attaches a **disclosure receipt** that records exactly what the AI generated, what sources/data were used, and what remains the student's own work. Built on Adaption's Adaptive Data capability and aligned with Rise Research's disclosure ethos, it addresses the documented gap between *AI research assistance* and *verifiable, defensible student research* — the same verification gap that recent benchmarks show causes majority of AI-generated research to contain unsupported claims.

### Differentiation matrix (vs. closest neighbors)

| Capability | ResearchLoop | Elicit/Consensus | AI Scientist/Agent Laboratory | C2PA/COPE tooling | Polygence/Rise |
|---|---|---|---|---|---|
| Student-scale, free | ✅ | ❌ | ❌ | ❌ | ❌ (paid) |
| Invents/augments datasets | ✅ | ❌ | ⚠️ (model-scale) | ❌ | ❌ |
| Automatic quality audit (before/after) | ✅ | ❌ | ⚠️ | ❌ | ❌ |
| Per-artifact disclosure receipt | ✅ | ❌ | ⚠️ (paper-level) | ✅ (institutional) | ⚠️ (policy) |
| Beginner/high-school UX | ✅ | ❌ | ❌ | ❌ | ✅ |
| Mentorship/ethos alignment | ✅ | ❌ | ❌ | ✅ | ✅ |

---

## Part 4 — Define Stage Blueprint (ready for iteration)

*Built on the literature above; to be refined with your input.*

### 4.1 Problem Statement
Students who want to do real research face three documented barriers: **(1) no data** — research starts with data they can't collect or don't have access to; **(2) no verification** — AI research help produces plausible-but-untrustworthy output (6–12% hallucination even with RAG; 59% of AI-generated research claims unsupported in benchmarks); **(3) no way to prove their own contribution** — journals and universities now require AI-use disclosure, but students have no tool to produce it. Human mentorship (the current solution) is scarce, slow, and expensive.

### 4.2 Target Users
- **Primary:** high-school students (grades 9–12) doing original research projects (science fairs, school journals, Rise-style mentorship, ML Empowerment learners).
- **Secondary:** undergraduates doing first research projects; teachers/mentors who want a free, verifiable tool to supervise students.

### 4.3 Core Value Proposition
One vertical slice, two outputs:
1. **A usable dataset** — invented or augmented for the student's question, with a visible before/after quality score.
2. **A disclosure receipt** — what the AI did, what sources/data were used, what the student authored — automatically generated and exportable.

### 4.4 Feature Scope (Defined — locked to the 16-day build)
- **F1 — Question → Dataset (Invent):** Student enters a research question; ResearchLoop generates a seed dataset (rows, labels, metadata) for the topic. (Adaption Adaptive Data "Invent")
- **F2 — Tiny dataset → Augmented (Augment):** Student uploads a small messy CSV; ResearchLoop augments/cleans it and shows quality before/after. (Adaption Adaptive Data "Improve")
- **F3 — Quality dashboard:** Dedup rate, diversity/similarity score, label coverage, distribution check — presented as a simple before/after chart. (Datasheets/Nutrition-Label lite + verification literature)
- **F4 — Disclosure receipt:** Auto-generated per run: model/tool used, purpose, oversight level, student's own edits, sources — exportable as a file for journals/mentors. (C2PA/COPE/Nature policy)
- **F5 — Research-readiness export:** Download dataset + receipt + a short methodology summary — the student's submission package.

**Explicitly out of scope (defended by literature review):** full research-cycle automation, continuous learning/retraining, multilingual data invention (stretch), chatbot-style answer generation.

### 4.5 Success Criteria (mapped to judging rubric)
| Criterion | How ResearchLoop scores it |
|---|---|
| **Technical Implementation (30%)** | Real generation + augmentation pipeline, real quality metrics, working receipt system — not a mock |
| **Creativity & Innovation (20%)** | The *combination* (student dataset invention + auto-audit + disclosure receipt) is unclaimed in the gallery and literature |
| **Real-World Impact (20%)** | Documented access gap; free, scalable mentorship substitute; defensible student research |
| **Design & UX (15%)** | One clean flow: question → dataset → receipt; beginner-first, no jargon |
| **Presentation & Documentation (15%)** | Description written to the rubric; before/after demo; receipts showcased; social-impact statement |

### 4.6 Risks & Defensibility (from literature)
- **"Synthetic data is risky"** → counter with the verification literature: generation *with* audit + receipt is exactly the recommended practice.
- **"AI research tools are saturated"** → counter with the differentiation matrix: no student-scale, data-first, receipt-generating tool exists.
- **"Disclosure receipts feel gimmicky"** → counter with policy: COPE/Nature/Elsevier/IEEE already require exactly this; C2PA is the industry standard.

### 4.7 Define-stage open questions (to decide with you)
1. **Demo topic:** which sample research question should the demo use? (e.g., "Does study time affect exam scores?" / "Which local tree species tolerates heat best?" — something where a 60-row dataset is meaningful)
2. **Receipt depth:** full C2PA-style manifest (complex) vs. a clear human-readable receipt with structured fields (buildable, still credible) — recommend the latter for v1.
3. **Adaption integration level:** actual API use of Adaption credits vs. a faithful simulation of the Adaptive Data workflow if API access is constrained — we must be honest about this in the submission.
4. **Impact evidence:** do we have 1–2 real students to test with, to capture before/after + usability (strengthens Impact + Presentation)?

## Source List (all live-checked 16–17 Nov 2026)
arxiv.org/abs/2212.10560 · arxiv.org/abs/2304.12244 · arxiv.org/abs/2406.08464 · arxiv.org/html/2410.12896v1 · arxiv.org/html/2503.14023v1 · arxiv.org/pdf/2406.07515 · researchsquare.com/article/rs-10883391 · arxiv.org/html/2601.17717v3 · awej.org (scoping review) · arxiv.org/pdf/2509.08713 · arxiv.org/html/2605.16616 · arxiv.org/html/2610.18933v1 · arxiv.org/html/2508.14111v1 · preprints.org/manuscript/202608.0213 · spec.c2pa.org (C2PA 2.4) · numonic.ai (IPTC 2025.1) · academicjobs.com (provenance) · paper-checker.com (academic integrity 2026) · trantorinc.com (digital provenance) · arxiv.org/html/2611.10399v1 · theneuralbase.com (dataset cards, synthetic quality) · sciencedirect.com (AI literacy PBL) · educative/edutopia (PBL) · edtecharchives.org (OECD AI literacy) · rfi.ac.uk (crowd-powered research) · openaccess.thecvf.com (bird dataset CVPR 2015) · arxiv.org/html/1508.06044 (CrowdAnno) · arxiv.org/html/2408.05350v1 (FloodTrace) · adaptionlabs.ai · riseglobaleducation.com · mlempowermentfoundation.org
