# PROJECT_BRIEF — CodeReviewer.NLP
## Semantic Commit / PR Consistency Auditor

> **Status:** Approved · **Version:** 0.5 (Compressed 4-Milestone Scope) · **Target Environment:** Python 3.13 (>=3.11) · **Author:** Solo University NLP Mini-Project

---

## 1. Problem Statement

Developers write commit messages inconsistently: vague, in the wrong mood, or failing to mention which files or functions were changed. Existing lightweight tools are either **format-only** (commitlint validates prefix and length but ignores content) or **surface-level heuristics** (diffmatch compares text n-gram overlap without any linguistic structure). Neither provides an **explainable, linguistically grounded score** of how well a commit message reflects the actual code change.

**CodeReviewer.NLP** fills this gap by combining classical NLP — POS tagging, TF-IDF classification, n-gram language models, GloVe embeddings — with diff-level static analysis to produce a structured, evidence-backed audit report per commit. Every score exposes the raw tokens and rules that produced it.

---

## 2. Course Outcome Mapping

| CO | Requirement | Implementation in this project |
|----|-------------|-------------------------------|
| CO1 | Text pre-processing | `preprocessor` module: Unicode normalization, camelCase/snake_case splitting, NLTK tokenizer, stop-word removal, Porter stemmer vs WordNet lemmatizer comparison, verb inflection analysis |
| CO2 | Custom POS tagger | `tagger` module: NLTK backoff chain (regex suffix rules → commit-verb lexicon → unigram tagger trained on NLTK treebank + lexicon → default tag); used for imperative-mood check; evaluated on ≥200 annotated commit titles sampled from the held-out test split (disjoint from lexicon); headline metric = first-token accuracy |
| CO3 | Text classification | `classifier` module: commit-type classifier (feat/fix/docs/refactor/test/chore) on TF-IDF vs BoW; compare MultinomialNB, Logistic Regression, LinearSVC; report macro-F1 + confusion matrix; all languages, **type prefix STRIPPED** before training |
| CO4 | Full pipeline | `api` module (FastAPI) + `frontend` (React + Tailwind v4 + Recharts RadarChart + custom DiffViewer); end-to-end from raw diff + message → scored JSON → visual dashboard |

---

## 3. System Inputs & Outputs

### Input — Paste Mode (primary graded mode)
| Field | Description |
|-------|-------------|
| `diff` | Raw unified diff text (copy-pasted) |
| `commit_message` | Commit message string |

> **Stretch goals** (after Phase 8, not required for grading): `github_client.py` (GitHub API content fetcher) and `ast_extractor.py` (tree-sitter Python AST for repo+SHA mode).

### Output — Audit Report (JSON + UI)
```json
{
  "commit_type": "feat",
  "diff_inferred_type": "feat",
  "scores": {
    "imperative_mood":   { "score": 1.0, "evidence": "First verb 'Add' is imperative" },
    "coverage":          { "score": 0.6, "evidence": "3/5 changed symbols soft-matched" },
    "risk_flags":        { "score": 0.0, "flags": ["auth/ touched, not mentioned in message"] },
    "fluency":           { "score": 0.82, "perplexity": 34.2 },
    "alignment":         { "score": 0.71, "cosine": 0.71 },
    "type_consistency":  { "score": 1.0, "predicted": "feat", "inferred": "feat" },
    "overall":           { "score": 0.79, "weights": { } }
  }
}
```

All sub-scores are in **[0, 1] where 1 = good**.

---

## 4. Key Components

| Component | Role |
|-----------|------|
| `diff_parser` | Parse unified diff; extract changed file names; extract function/class symbols via `section_header` parsing + regex on `def`/`class` lines in +/- hunks |
| `diff_type_inference` | Infer commit type from diff content: tests-only → `test`, docs-only → `docs`, config/CI-only → `chore`, else → `ambiguous` |
| `risk_scorer` | Rule-based tagger matching **whole path components** against `config/risk_rules.yaml`; includes message-side synonyms per layer; flags sensitive layer touched but not mentioned |
| `coverage_scorer` | **Soft matching**: split identifiers + lemmatize; overlap OR embedding cosine similarity above a validation-tuned threshold; no bonus points |
| `preprocessor` | Full CO1 pipeline (normalize → split identifiers → tokenize → remove stop words → stem/lemmatize) |
| `tagger` | CO2 backoff POS tagger; imperative-mood check |
| `classifier` | CO3 commit-type classifier (TF-IDF/BoW × 3 models); trained on prefix-stripped messages |
| `lm_scorer` | Kneser-Ney trigram LM with bigram backoff (nltk.lm); UNK cutoff; corpus capped at ~150k messages; perplexity → fluency score |
| `embedding_aligner` | GloVe-100 via gensim.downloader; cosine similarity between diff tokens and message tokens |
| `aggregator` | Weighted combination of all sub-scores → overall score; weights from `config/weights.yaml` |
| `api` | FastAPI backend exposing `POST /audit` |
| `frontend` | React + Tailwind v4; Recharts RadarChart for scores; custom DiffViewer component |
| `github_client` *(stretch)* | GitHub API content fetcher (repo+SHA mode) |
| `ast_extractor` *(stretch)* | tree-sitter Python AST (repo+SHA mode) |

---

## 5. Constraints & Decisions

- **Python ≥ 3.11** — project targets 3.11+; active interpreter is 3.13.7
- **No LLMs / external AI APIs** anywhere in the scoring pipeline
- Every score returns `evidence` (the raw tokens / rule that produced it)
- All dependency versions pinned in `requirements.txt` (verified to install on Python 3.13)
- Modules are small (< 200 lines each); each has a corresponding `tests/test_<module>.py`
- `data/` and `models/` are git-ignored; raw CommitBench parquet/CSV stored locally
- `github_client` and `ast_extractor` are stretch goals, not part of core grading
- Every experiment script writes to `results/*.json`; reports use only those files — no invented numbers
- All sub-scores are **[0, 1] where 1 = good** (risk_flags: 1 = no risky omissions)

---

## 6. Dataset

| Dataset | Source | Notes |
|---------|--------|-------|
| CommitBench | `Maxscha/commitbench` on Hugging Face | Large CSV; **no language column**; stream/sample; infer Python from `.py` file extensions in diff |
| Python-inferred subset | Filtered from CommitBench | Primary focus for CO2 evaluation |
| All-language subset | Full CommitBench (prefix-stripped) | CO3 classifier training; LM training (separate split) |
| Gold 200 titles | Sampled from held-out test split | Manually annotated POS labels; disjoint from lexicon source |

---

## 7. Risks & Assumptions (Flagged)

| # | Risk / Assumption | Confidence | Mitigation |
|---|-------------------|------------|------------|
| R1 | CommitBench has **no language column** — must infer Python from diff file extensions | Confirmed | Filter rows where diff contains `.py` files |
| R2 | CommitBench is large; full load may OOM | High | Stream with `datasets` iterable mode; sample ≤150k for LM |
| R3 | Class label counts may be thin after filtering | Medium | **Phase 1 gate**: if any class <200, STOP and report options before proceeding |
| R4 | GloVe-100 download: ~66 MB (word vectors only, not full 822 MB) | Confirmed (gensim docs) | Cache in `models/`; document in README |
| R5 | nltk 3.8.2 does not exist on PyPI — latest is 3.10.x | Confirmed | Pin `nltk==3.10.1` |
| R6 | tree-sitter 0.21.3 API is deprecated; current is 0.26.0 with a breaking API | Confirmed | Move to stretch goal; pin 0.26.0 if used |
| R7 | Active Python is 3.13.7, not 3.11 | Confirmed | All pins verified against 3.13; project runs on ≥3.11 |
| R8 | Kneser-Ney sparse-data with short corpus | Medium | Bigram backoff instead of add-one; UNK cutoff min_count=2 |
| R9 | Imperative mood detection may miss gerunds | Medium | Regex pre-check before POS; document false positives |
| R10 | 200-sample POS annotation is manual effort | High | Provide `scripts/annotate_pos.py` helper; budget ~3 hrs |

---

---

## 8. Known Limitations (M1 Scope)

1. **Hunk-Header Symbol Extraction**:
   - Git hunk headers (`@@ ... @@ def func():`) display the nearest preceding function/class definition found by Git's diff heuristic, which may not always be the exact block modified (e.g., if modifications occur in module-level code or comments immediately after a function). Full AST verification with tree-sitter is slated for future scope.
2. **Inflection-Based Imperative Checker**:
   - The M1 imperative checker relies on first-word morphological inflection analysis. It correctly evaluates standard imperative verbs (`add`, `fix`, `update`) and flags past/gerund forms (`fixed`, `adding`), but will miss inverted nominal phrases and non-verb openers (e.g., `"login issue fix"`, `"bug in auth"`). Robust resolution of complex phrase structures requires the full statistical backoff POS tagger introduced in Milestone 2 (M2).

---

## 9. Compressed 4-Milestone Scope & Roadmap (v0.5)

| Milestone | Focus | Core Outputs |
|:---|:---|:---|
| **M1: Demo Slice** | End-to-end working pipeline (no trained models) | `diff_parser`, `risk_rules`, `coverage_scorer`, `diff_type_inference`, imperative check with correction, weighted `aggregator`, FastAPI (`/audit`, `/health`), CLI demo, React + Tailwind dashboard |
| **M2: Classical NLP Core** | Supervised components & evaluations | CO2 Backoff POS Tagger (200 test annotations, GroupKFold on train+val), CO3 Commit-Type Classifier (TF-IDF vs BoW, MultinomialNB, LogReg, LinearSVC, prefix-stripped) |
| **M3: Semantic & Language Models** | Probabilistic & distributed representations | N-gram Language Model & perplexity fluency scorer (Kneser-Ney), GloVe-100 semantic alignment scorer |
| **M4: Evaluation & Packaging** | System-level evaluation & reporting | Synthetic inconsistent commit detection (AUROC), documentation, final evaluation report, package distribution |

---

## 10. Future Scope (Post-Project)

The following components are formally designated as future extensions and not required for core grading:
1. **AST-Level Diff Parsing via Tree-Sitter**: Full structural Python AST comparison for repo+SHA mode.
2. **GitHub API Client (`github_client.py`)**: Remote repo+SHA cloning and direct PR fetching via GitHub REST API.
3. **Custom Domain Embeddings & Topics**: Training custom Word2Vec / FastText on Git commits and LDA topic modeling.
4. **HMM POS Tagger**: Training Hidden Markov Model with Viterbi decoding as an additional tagger comparison.
5. **Learned Aggregator Weights**: Replacing fixed rule weights with logistic regression or learning-to-rank on human consistency annotations.
6. **Multi-Language Support**: AST and symbol extractors for JavaScript/TypeScript, Go, Rust, Java.
7. **Automated CI/CD Pipeline**: GitHub Actions for automated linting, test suites, and Docker container deployment.

---

## 10. Deliverables Checklist

- [x] `docs/PROJECT_BRIEF.md` (v0.5)
- [x] `docs/IMPLEMENTATION_PLAN.md` (v0.5)
- [x] Data audit & splits (`results/phase1_data_audit.json`, `lm_train.csv`, `lm_heldout.csv`, project-grouped splits)
- [x] CO1 text pre-processing (`src/code_reviewer/preprocessor.py`, 23 tests, `02_co1_preprocessing.ipynb`)
- [ ] M1 Demo Slice (FastAPI, React dashboard, CLI demo, diff parser, heuristics)
- [ ] M2 Custom POS Tagger & Classifier
- [ ] M3 LM Fluency & GloVe Semantic Alignment
- [ ] M4 System-Level Evaluation & Report

