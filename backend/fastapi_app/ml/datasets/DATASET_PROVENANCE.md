# CareerOS Domain Instruction Dataset: Provenance & Methodology

## 1. Dataset Overview
- **Name**: CareerOS Career-Domain Instruction Dataset
- **Target Model**: `Qwen/Qwen2.5-1.5B-Instruct`
- **Primary Objective**: Supervised Parameter-Efficient Fine-Tuning (PEFT LoRA / QLoRA) for career development tasks, including resume bullet rewriting, ATS keyword optimization, technical and behavioral interview preparation, and Responsible AI safety enforcement.
- **Format**: JSON Lines (`.jsonl`) with schema:
  - `id`: Unique string identifier
  - `category`: Domain category tag
  - `instruction`: Task prompt/directive
  - `input`: Specific candidate background, resume text, or context snippet
  - `output`: Gold-standard expert response
  - `messages`: ChatML conversational format compatible with Qwen chat templates

---

## 2. Domain Taxonomy & Coverage
The dataset spans 7 foundational CareerOS operational domains:

1. **Resume Bullet Optimization (`resume_bullet_optimization`)**:
   - Focus: Converting passive task descriptions ("was responsible for...") into structured, active STAR bullets with quantifiable performance impact, latency reductions, and business ROI.
2. **ATS Keyword Alignment (`ats_keyword_matching`)**:
   - Focus: Analyzing candidate resumes against specific job descriptions, isolating missing high-frequency tech keywords, and recommending contextual inclusion without spamming.
3. **Technical Interview Preparation (`technical_interview`)**:
   - Focus: Production-grade architectural discussions (FastAPI concurrency, N+1 query diagnostics, B-tree indexing trade-offs, high-concurrency race condition mitigation, hybrid RAG systems).
4. **Behavioral Interview Preparation (`behavioral_interview`)**:
   - Focus: Structured STAR-method answers addressing technical disagreements, high-severity outages, and professional job-transition narratives.
5. **Career Transition & Leveling (`career_transition_advice`)**:
   - Focus: Competency shift from Mid-level to Senior, Staff Engineer vs Engineering Manager decision matrix, and transition roadmaps to AI Engineering.
6. **Cover Letter & Elevator Pitch (`cover_letter_tailoring`)**:
   - Focus: High-density, role-tailored value propositions and 60-second interview pitches.
7. **Responsible AI & Safety Guardrails (`responsible_ai_safety`)**:
   - Focus: Refusing gender/demographic bias in hiring queries, resisting prompt injection overrides, and maintaining strict factual grounding against resume contexts.

---

## 3. Data Curation & Quality Assurance
- **Deduplication**: Strict hash-based deduplication on normalized `(instruction + input)` pairs using MD5 hashing.
- **Train / Validation / Test Splitting**:
  - Deterministic pseudo-random splitting using `seed=42`.
  - Partition ratio: ~80% Train, ~10% Validation, ~10% Test.
- **Leakage Prevention**:
  - Exact string match and normalized token overlap checks between the training split and the held-out evaluation datasets (`test_set` and `benchmark_dataset.jsonl`).
  - Automated CI assertion: Any cross-split overlap raises a build error.

---

## 4. Provenance & Licensing
- **Author**: CareerOS Engineering Team & Domain Expert Curators.
- **Data Generation Method**: Curated expert templates synthesized with verified software engineering case studies and validated against production career advisory scenarios.
- **License**: Apache 2.0 (Compatible with commercial and open-source fine-tuning).

---

## 5. Known Limitations
1. **Domain Breadth**: The current dataset specifically focuses on software engineering, data science, MLOps, and backend development. It has limited coverage of non-technical industries (e.g., healthcare, legal, finance accounting).
2. **Synthetic Specificity**: Quantitative metrics in examples are stylized for demonstration (e.g., "reduced latency from 420ms to 160ms"). Models trained on these must be instructed to rely on the user's actual resume data rather than hallucinatory metrics.
3. **Regional Compensation & Titles**: Does not contain regional salary benchmarks or geography-specific title equivalence matrices.
