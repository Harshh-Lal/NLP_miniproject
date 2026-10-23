# IMPLEMENTATION PLAN — CodeReviewer.NLP
## Semantic Commit / PR Consistency Auditor

> **Version:** 0.5 — Compressed 4-Milestone Scope. Python 3.13 active. M1 Demo Slice in progress.
> **Active interpreter:** Python 3.13.7 (targets >=3.11).
> **Current status:** Phase 1 & 2 Complete. Executing Milestone 1 (M1 Demo Slice). Future scope explicitly segregated.

---

## 1. Folder Structure

```
NLP-miniproject/
│
├── config/
│   ├── risk_rules.yaml        # Sensitive-layer keyword rules (whole path components + synonyms)
│   └── weights.yaml           # Sub-score weights for aggregator
│
├── data/                      # Git-ignored
│   ├── raw/
│   │   └── commitbench_sample.csv   # Streamed/sampled from HuggingFace (200k rows, 166 MB)
│   ├── processed/
│   │   ├── train_classifier.csv     # For CO3 (project-grouped, prefix stripped; 5,912 rows)
│   │   ├── val_classifier.csv       # (1,399 rows, zero project overlap)
│   │   ├── test_classifier.csv      # (1,457 rows, zero project overlap)
│   │   ├── lm_train.csv             # Rebuilt LM train corpus (128,626 rows)
│   │   ├── lm_heldout.csv           # Held-out LM evaluation corpus (5,000 rows)
│   │   └── python_inferred.csv      # Rows with .py file extensions in diff
│   └── annotations/
│       └── pos_gold_200.json        # Hand-annotated; sampled from test split
│
├── models/                    # Git-ignored
│   ├── unigram_tagger.pkl
│   ├── classifier_tfidf_lsvc.pkl
│   ├── tfidf_vectorizer.pkl
│   ├── bow_vectorizer.pkl
│   └── glove-wiki-gigaword-100.kv   # Cached gensim KeyedVectors
│
├── results/                   # All experiment outputs (JSON); used by reports
│   ├── phase1_data_audit.json
│   ├── phase3_tagger_eval.json
│   ├── phase4_classifier_eval.json
│   ├── phase6_lm_calibration.json
│   ├── phase6_alignment_auroc.json
│   ├── phase6_coverage_auroc.json
│   └── phase6_e2e_sample.json
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_co1_preprocessing.ipynb
│   ├── 03_co2_tagger_eval.ipynb
│   ├── 04_co3_classifier_eval.ipynb
│   └── 05_end_to_end_demo.ipynb
│
├── src/
│   └── code_reviewer/
│       ├── __init__.py
│       ├── preprocessor.py          # CO1
│       ├── tagger.py                # CO2
│       ├── classifier.py            # CO3
│       ├── diff_parser.py           # Diff-level extractor + symbol extraction
│       ├── diff_type_inference.py   # Infer commit type from diff content
│       ├── risk_scorer.py           # Rule-based risk flags
│       ├── coverage_scorer.py       # Soft-match coverage / omission
│       ├── lm_scorer.py             # Kneser-Ney LM + perplexity
│       ├── embedding_aligner.py     # GloVe cosine alignment
│       └── aggregator.py            # Weighted score combiner
│       # github_client.py  ← STRETCH GOAL (after Phase 8)
│       # ast_extractor.py  ← STRETCH GOAL (after Phase 8)
│
├── scripts/
│   ├── download_data.py         # Stream/sample CommitBench; save raw CSV
│   ├── prepare_dataset.py       # Label, filter, split; write phase1_data_audit.json
│   ├── train_tagger.py          # Train & save unigram tagger
│   ├── train_classifier.py      # Train all CO3 models; write phase4_classifier_eval.json
│   ├── train_lm.py              # Train & serialize Kneser-Ney LM
│   ├── download_glove.py        # gensim.downloader cache
│   └── annotate_pos.py          # Helper for manual POS annotation
│
├── tests/
│   ├── conftest.py
│   ├── test_preprocessor.py
│   ├── test_tagger.py
│   ├── test_classifier.py
│   ├── test_diff_parser.py
│   ├── test_diff_type_inference.py
│   ├── test_risk_scorer.py
│   ├── test_coverage_scorer.py
│   ├── test_lm_scorer.py
│   ├── test_embedding_aligner.py
│   ├── test_aggregator.py
│   └── test_api.py
│
├── api/
│   ├── main.py
│   ├── schemas.py
│   └── routers/
│       └── audit.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css              # @import "tailwindcss"
│       └── components/
│           ├── ScoreCard.tsx
│           ├── RadarScoreChart.tsx  # Recharts RadarChart
│           ├── ScoreBar.tsx
│           ├── EvidencePanel.tsx
│           ├── DiffViewer.tsx       # Custom syntax-highlighted diff viewer
│           ├── DiffInput.tsx
│           └── RiskBadge.tsx
│
├── docs/
│   ├── PROJECT_BRIEF.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── EVALUATION_REPORT.md     # Written in Phase 8
│
├── .gitignore
├── pyproject.toml
├── requirements.txt             # Pinned, verified on Python 3.13
├── requirements-dev.txt
└── README.md
```

---

## 2. Dependency List — Verified Pins (Python 3.13 / ≥3.11)

> All versions confirmed to exist on PyPI as of 2026-10-20.
> Corrections from v0.1 are marked ⚠️.

### Core (requirements.txt)
```
# NLP
nltk==3.10.1            # ⚠️ 3.8.2 does not exist; latest stable is 3.10.x
gensim==4.3.3           # 4.4.0 exists but 4.3.3 is pinned for stability
scikit-learn==1.5.2
numpy==1.26.4
scipy==1.13.1

# Diff parsing  (tree-sitter moved to stretch goal)
unidiff==0.7.5

# Data
datasets==2.20.0        # Iterable (streaming) mode used
pandas==2.2.2
pyarrow==16.1.0

# API
fastapi==0.111.1
uvicorn[standard]==0.30.3
pydantic==2.8.2
httpx==0.27.0

# Utilities
pyyaml==6.0.2
python-dotenv==1.0.1
joblib==1.4.2
```

### Dev (requirements-dev.txt)
```
pytest==8.2.2
pytest-cov==5.0.0
httpx==0.27.0
black==24.4.2
ruff==0.5.0
mypy==1.10.1
respx==0.21.1           # HTTP mock for github_client tests
```

### Stretch / Optional
```
# Only needed if stretch goals (github_client, ast_extractor) are implemented
tree-sitter==0.26.0         # ⚠️ 0.21.x API is deprecated; 0.26.0 has breaking changes
tree-sitter-python==0.23.4  # ⚠️ must match grammar API version
```

> **GloVe note:** `glove-wiki-gigaword-100` downloaded via `gensim.downloader` is ~66 MB (word vectors only). The 822 MB figure referred to the full GloVe release archive. Cached to `models/glove-wiki-gigaword-100.kv`.

---

## 3. Module-by-Module Responsibilities

### 3.1 `preprocessor.py` (CO1)

| Function | Responsibility |
|----------|----------------|
| `normalize(text)` | Unicode NFC, lowercase, strip control chars |
| `split_identifiers(token)` | camelCase → `["camel","Case"]`; snake_case → `["snake","case"]` via regex |
| `tokenize(text)` | `nltk.word_tokenize` after normalize + identifier splitting |
| `remove_stopwords(tokens)` | `nltk.corpus.stopwords` English set removal |
| `stem(tokens)` | `nltk.stem.PorterStemmer` |
| `lemmatize(tokens)` | `nltk.stem.WordNetLemmatizer` with POS hint |
| `compare_stem_lemma(tokens)` | Returns `{token: {stem, lemma}}` for notebook comparison |
| `analyze_verb_inflection(tokens)` | Regex patterns detecting -ing/-ed/-s suffixes; returns inflection type |
| `preprocess_pipeline(text, mode)` | Orchestrates all steps; `mode` selects `"stem"` or `"lemma"` |

**Evidence contract:** every public function returns `(result, evidence: dict)`.

---

### 3.2 `tagger.py` (CO2)

| Function | Responsibility |
|----------|----------------|
| `build_regex_tagger()` | Suffix rules: `-ing→VBG`, `-ed→VBD`, `-tion→NN`, `-ly→RB`, `-er→NN`, `-ness→NN`, `-able→JJ`, `-ment→NN` (≥8 rules) |
| `load_commit_verb_lexicon()` | Hardcoded dict of ≥50 imperative verbs from CommitBench most-frequent first words → `VB` |
| `train_unigram_tagger(tagged_sents)` | Fits `nltk.UnigramTagger` on **NLTK Penn Treebank** gold data + lexicon; NOT on silver CommitBench |
| `build_backoff_tagger(unigram)` | Chain: RegexTagger → LexiconTagger → UnigramTagger(treebank) → DefaultTagger(`NN`) |
| `tag(tokens)` | Applies backoff chain; returns `[(token, tag)]` |
| `check_imperative_mood(commit_title)` | Tokenizes, POS-tags; checks first non-punctuation token is `VB`; returns `(bool, evidence)` |
| `evaluate_tagger(gold_data)` | Computes accuracy, per-tag precision/recall vs gold_200; writes `results/phase3_tagger_eval.json` |

**Key CO2 distinction:** Unigram tagger is trained on **NLTK treebank (gold)** not silver-labelled CommitBench data. The lexicon and regex layers provide commit-domain specialisation on top.

**Headline metric:** first-token accuracy on gold_200 (i.e., did we correctly tag the first word of each commit title?).

---

### 3.3 `classifier.py` (CO3)

| Function | Responsibility |
|----------|----------------|
| `strip_type_prefix(message)` | Removes `feat:`, `fix(scope):`, etc. before featurisation |
| `build_tfidf_vectorizer(corpus)` | `TfidfVectorizer(ngram_range=(1,2), max_features=15000, sublinear_tf=True)` |
| `build_bow_vectorizer(corpus)` | `CountVectorizer(ngram_range=(1,2), max_features=15000)` |
| `train_models(X_train, y_train)` | Trains MultinomialNB, LogisticRegression, LinearSVC × 2 feature sets = 6 models |
| `evaluate_models(...)` | Macro-F1 + confusion matrix; writes `results/phase4_classifier_eval.json` |
| `select_best_model(results)` | Picks highest macro-F1 |
| `predict_commit_type(message)` | Returns `(label, confidence, evidence_tokens)` |
| `save_model / load_model` | joblib serialization |

> **Training data:** all-language CommitBench, type prefix stripped. Labels extracted from conventional commit prefixes (`feat:`, `fix:`, etc.) via regex; rows without a recognized prefix are discarded.

---

### 3.4 `diff_parser.py`

| Function | Responsibility |
|----------|----------------|
| `parse_diff(raw_diff: str)` | `unidiff.PatchSet` → list of `DiffFile` dataclasses |
| `extract_changed_files(diff)` | Returns `[filename]` list |
| `extract_symbols_from_hunk(hunk)` | (1) Parse `section_header` for function context; (2) regex `^[+-]\s*(def|class)\s+(\w+)` on added/removed lines |
| `extract_added_lines(diff)` | All added line tokens |
| `diff_summary(diff)` | `{files_changed, lines_added, lines_removed, changed_tokens, symbols}` |

**`DiffFile` dataclass:**
```python
@dataclass
class DiffFile:
    path: str
    added_lines: list[str]
    removed_lines: list[str]
    symbols: list[str]   # function/class names found
    hunks: list
```

> **Paste mode coverage note:** In paste mode, `symbols` includes names from (a) `section_header` context like `@@ ... @@ def foo():` and (b) `def`/`class` lines in +/- hunks. This covers the vast majority of real diffs without tree-sitter.

---

### 3.5 `diff_type_inference.py`

| Function | Responsibility |
|----------|----------------|
| `infer_type(diff_files: list[DiffFile])` | Classify the diff into a commit type by file extension and path heuristics |
| Evidence rules | tests-only (all files match `test_*.py`, `*_test.py`, `tests/`) → `"test"`; docs-only (all files `.md`/`.rst`/`.txt`/`docs/`) → `"docs"`; config/CI-only (all files `.yml`/`.yaml`/`.cfg`/`.ini`/`.toml`/`.github/`) → `"chore"`; else → `"ambiguous"` |

**type_consistency score:**
```
type_consistency = 1.0  if classifier_prediction == inferred_type
                   0.5  if inferred_type == "ambiguous"
                   0.0  if classifier_prediction != inferred_type (both unambiguous)
```
This replaces the v0.1 approach of comparing against a stated prefix in the message.

---

### 3.6 `risk_scorer.py`

| Function | Responsibility |
|----------|----------------|
| `load_rules(yaml_path)` | Loads rules: `{layer, path_patterns[], message_synonyms[], severity}` |
| `match_path(file_path, path_patterns)` | Matches **whole path components** (split on `/`): `auth` matches `src/auth/login.py` but not `unauthorized.py` |
| `match_message(message_tokens, synonyms)` | Any synonym present → layer mentioned |
| `score_risk(diff_files, message_tokens)` | For each layer with matching files, check if any synonym in message; flag if not |
| `risk_report()` | `{score: float, flags: [RiskFlag], evidence}` where `score = 1.0 - (critical_flags / max_critical)` |

**`config/risk_rules.yaml` schema (v2):**
```yaml
rules:
  - layer: "authentication"
    path_patterns: ["auth", "login", "logout", "session", "oauth"]
    message_synonyms: ["auth", "login", "logout", "session", "oauth", "token", "credential"]
    severity: "high"
  - layer: "cryptography"
    path_patterns: ["crypt", "cipher", "hash", "encrypt", "decrypt"]
    message_synonyms: ["crypt", "encrypt", "decrypt", "hash", "cipher", "sign", "verify"]
    severity: "critical"
  - layer: "database"
    path_patterns: ["db", "database", "migration", "schema", "models", "repository"]
    message_synonyms: ["db", "database", "migration", "schema", "model", "query", "sql"]
    severity: "high"
  - layer: "secrets"
    path_patterns: ["secrets", "credentials", "env", "keys", "vault"]
    message_synonyms: ["secret", "credential", "key", "password", "env", "vault", "token"]
    severity: "critical"
  - layer: "network"
    path_patterns: ["api", "client", "request", "socket", "http"]
    message_synonyms: ["api", "endpoint", "request", "network", "socket", "http", "client"]
    severity: "medium"
  - layer: "filesystem"
    path_patterns: ["fs", "file", "path", "io", "storage"]
    message_synonyms: ["file", "path", "storage", "io", "filesystem", "directory"]
    severity: "medium"
```

---

### 3.7 `coverage_scorer.py`

| Function | Responsibility |
|----------|----------------|
| `soft_match(symbol, message_tokens, embedder, threshold)` | Split + lemmatize both sides; return True if token overlap OR max cosine similarity ≥ `threshold` |
| `tune_threshold(val_pairs)` | Grid search threshold on validation (real vs shuffled pairs); writes to `results/phase6_coverage_auroc.json` |
| `compute_coverage(symbols, message_tokens)` | Fraction of symbols that soft-match |
| `omission_list(symbols, message_tokens)` | Unmatched symbols |
| `coverage_report()` | `{score, mentioned, omitted, evidence, threshold_used}` |

**Scoring:**
```
coverage_score = |soft_matched_symbols| / max(|symbols|, 1)
```
No bonus. Threshold validated on held-out data and stored in `results/`.

---

### 3.8 `lm_scorer.py`

| Function | Responsibility |
|----------|----------------|
| `train_lm(corpus_sentences, max_messages=150_000)` | Caps corpus; applies UNK cutoff (min_count=2); trains `nltk.lm.KneserNeyInterpolated(order=3)` with bigram backoff via `nltk.lm.Laplace(order=2)` |
| `save_lm / load_lm` | pickle serialization |
| `compute_perplexity(lm, tokens)` | Raw perplexity float |
| `perplexity_to_score(perplexity, p_max)` | `score = 1 / (1 + log(1 + perplexity) / log(1 + p_max))` where `p_max` = 95th-percentile perplexity on validation set (calibrated; written to `results/phase6_lm_calibration.json`) |
| `fluency_report(tokens)` | `{score, perplexity, evidence}` |

**LM training data:** all-language CommitBench, prefix stripped; **separate split** from classifier (no data leak between CO3 training set and LM training set).

---

### 3.9 `embedding_aligner.py`

| Function | Responsibility |
|----------|----------------|
| `load_glove()` | `gensim.downloader.load("glove-wiki-gigaword-100")` (~66 MB); cached to `models/` |
| `embed_tokens(tokens, model)` | Mean-pooled vector; OOV tokens skipped |
| `cosine_similarity(vec_a, vec_b)` | `1 - scipy.spatial.distance.cosine(a, b)` |
| `align(diff_tokens, message_tokens)` | Embeds both; returns cosine similarity |
| `alignment_report()` | `{score, cosine, evidence, oov_rate}` |

**OOV:** If >50% tokens OOV, flag `low_confidence: true` in evidence. Score still returned.

---

### 3.10 `aggregator.py`

| Function | Responsibility |
|----------|----------------|
| `load_weights(yaml_path)` | Loads `config/weights.yaml` |
| `aggregate(scores: dict)` | Validates weights sum to 1.0; computes weighted sum |
| `build_report(sub_reports)` | Merges all sub-reports into final audit JSON |

**Default weights (config/weights.yaml):**
```yaml
weights:
  imperative_mood:  0.15
  coverage:         0.25
  risk_flags:       0.20
  fluency:          0.10
  alignment:        0.15
  type_consistency: 0.15
```

---

## 4. Test Strategy

### Philosophy
- Every public function: ≥1 happy-path + ≥1 edge-case test
- No network calls in tests (GitHub client mocked; GloVe model mocked with tiny KeyedVectors fixture)
- Target: **≥80% line coverage** (`pytest-cov`)

### Test Matrix

| File | Key Scenarios |
|------|---------------|
| `test_preprocessor.py` | camelCase, snake_case, unicode, empty string, stem≠lemma cases |
| `test_tagger.py` | Imperative (Add/Fix/Remove), non-imperative (Adding/Added), unknown word → default tag |
| `test_classifier.py` | Correct label, OOV message, empty string, prefix-stripping applied |
| `test_diff_parser.py` | Multi-file, binary file, empty diff, rename, section_header symbol extraction, def/class regex |
| `test_diff_type_inference.py` | test-only diff, docs-only, config-only, mixed → ambiguous |
| `test_risk_scorer.py` | Whole-component match (not substring), synonym in message → no flag, missing → flag |
| `test_coverage_scorer.py` | Perfect soft match → 1.0, zero match → 0.0, partial, embedding fallback |
| `test_lm_scorer.py` | Trained LM finite perplexity, score in [0,1], UNK handling |
| `test_embedding_aligner.py` | Identical tokens → high score, orthogonal → low, all OOV → low_confidence |
| `test_aggregator.py` | Weight sum invariant, missing sub-score graceful, output JSON schema |
| `test_api.py` | POST /audit → 200 with all fields; 422 on bad input |

---

## 5. Experiment Output Convention

> **Rule:** every script that trains a model or runs an evaluation writes its results to `results/<phase>_<name>.json`. Reports and notebooks consume only those files. No numbers are invented or hard-coded in prose.

Mandatory `results/*.json` files:

| File | Written by | Contents |
|------|-----------|----------|
| `phase1_data_audit.json` | `scripts/prepare_dataset.py` | Row counts, label distribution, Python-inferred count, gate decision |
| `phase3_tagger_eval.json` | `scripts/train_tagger.py` | Accuracy, first-token accuracy, per-tag P/R |
| `phase4_classifier_eval.json` | `scripts/train_classifier.py` | Macro-F1 for all 6 models, confusion matrices |
| `phase6_lm_calibration.json` | `scripts/train_lm.py` | p_max, val perplexity stats |
| `phase6_alignment_auroc.json` | Phase 6d eval script | AUROC on real-vs-shuffled diff/message pairs |
| `phase6_coverage_auroc.json` | Phase 6d eval script | AUROC on real-vs-shuffled pairs; tuned threshold |
| `phase6_e2e_sample.json` | Phase 6d eval script | Full audit output for 100 held-out samples |

---

## 6. Eight Development Phases

---

### Phase 1 — Data Audit ← **COMPLETE & AMENDED (GATE PASSED)**
**Goal:** Understand CommitBench; produce processed splits; apply gate.

**Tasks:**
1. [x] `scripts/download_data.py` — streamed 200k rows from `Maxscha/commitbench` to `data/raw/commitbench_sample.csv` (166 MB)
2. [x] Audit schema: confirmed columns `['hash', 'diff', 'message', 'project', 'split', 'diff_languages']`
3. [x] Distinct projects analyzed: 35,884 distinct projects; top-10 projects account for 4.93% of stream; stream ordering verified as interleaved/random.
4. [x] Rebuilt LM corpus: 128,626 train messages (`data/processed/lm_train.csv`) and 5,000 held-out messages (`data/processed/lm_heldout.csv`), excluding python rows and classifier evaluation sets.
   - **`python_inferred.csv` Clarification:**
     - **1,272 rows:** Python commits filtered from the **8,768 labeled conventional-commit subset** (commits touching `.py` files).
     - **56,778 rows:** Python commits identified across the **full 200,000 raw CommitBench stream** (used solely to exclude Python commits from the unlabeled LM corpus so that the LM corpus does not leak into the Python evaluation splits).
   - **Classifier Evaluation Population:** The classifier evaluation strictly uses the full multi-language conventional-commit population (all 6 classes: `fix`, `feat`, `chore`, `test`, `refactor`, `docs`), with conventional-commit type prefixes stripped before vectorization, partitioned by project (`train_classifier.csv`: 5,912 rows; `val_classifier.csv`: 1,399 rows; `test_classifier.csv`: 1,457 rows across 8,768 total labeled rows).
5. [x] Project-grouped classifier split: 0 project overlap between splits.
   - `train_classifier.csv`: 5,912 rows (2,816 projects)
   - `val_classifier.csv`: 1,399 rows (28 projects)
   - `test_classifier.csv`: 1,457 rows (54 projects)
6. [x] Evaluated Gate and wrote `results/phase1_data_audit.json`:
   - `fix`: 3,402 train rows
   - `chore`: 610 train rows
   - `feat`: 625 train rows
   - `test`: 567 train rows
   - `refactor`: 469 train rows
   - `docs`: 239 train rows (smallest class, exceeds >=200 threshold)
   - Gate check: **PASSED** (0 thin classes).

**Gate condition (HARD STOP):** PASSED. All 6 classes have >=200 training examples in project-grouped split.

**Outputs:** `data/raw/commitbench_sample.csv`, `data/processed/*.csv`, `results/phase1_data_audit.json`

**Done when:** splits exist, `phase1_data_audit.json` written with real counts, gate condition evaluated -> **DONE**

---

### Phase 2 — CO1: Text Pre-processing ← **COMPLETE (GATE PASSED)**
**Goal:** Build and verify the full preprocessing pipeline.

**Tasks:**
1. [x] Implement `src/code_reviewer/preprocessor.py` adhering to `(result, evidence: dict)` contract.
2. [x] Write `tests/test_preprocessor.py` (23 unit tests covering normalization, identifier splitting, stop-word verb preservation, stemming, verb-first lemmatization, verb inflection analysis, and pipeline modes).
3. [x] Create `notebooks/02_co1_preprocessing.ipynb`:
   - Normalization with URL, trailer, issue ref stripping, whitespace collapse
   - Identifier splitting (camelCase, PascalCase, snake_case, kebab-case, digits, acronyms)
   - Stop-word removal with action verb preservation (9.96 -> 6.88 tokens/msg, -30.94% reduction)
   - Side-by-side stem vs lemma comparison (31 examples)
   - Conflation metrics over full 7,114 vocab (3,171 differing, 5,283 stems vs 5,745 lemmas, 1.35 vs 1.24 avg surface forms, 15 verified semantic false-merges)
   - Verb inflection analysis on all 5,912 training commit messages (86.74% imperative adherence, 11.43% violations, 89 ambiguous homographs)
   - Explainability evidence contract inspection
4. [x] Export metrics to `results/phase2_preprocessing.json`.
5. [x] Expose `mode` flag (`lemma` vs `stem`) for Phase 4 classifier comparison.

**Done when:** all tests pass (23/23 passing), notebook shows >=4 distinct CO1 outputs with commentary, numbers written to `results/phase2_preprocessing.json` -> **DONE**

**Gate condition:** All preprocessor tests pass. Mode flag exposed. -> **PASSED**

---

### Phase 3 — CO2: Custom POS Tagger
**Goal:** Build, train, evaluate, deploy backoff tagger.

**Tasks:**
1. Curate commit verb lexicon (≥50 imperative verbs from CommitBench most-frequent first words)
2. Define ≥8 regex suffix rules
3. Train unigram tagger on **NLTK Penn Treebank** (gold); chain with lexicon and regex
4. `scripts/train_tagger.py` → save `models/unigram_tagger.pkl`
5. Sample 200 commit titles from **held-out test split** (disjoint from lexicon source); **MUST include non-verb-opener cases** (e.g. `"login issue fix"`, `"bug in auth"`) to evaluate nominal-phrase and inversion handling.
6. `scripts/annotate_pos.py` → helper for manual POS annotation → `data/annotations/pos_gold_200.json`
7. Evaluate; write `results/phase3_tagger_eval.json` (headline: **first-token accuracy** and full-sentence accuracy)
8. Implement `check_imperative_mood()`
9. `notebooks/03_co2_tagger_eval.ipynb`: confusion matrix, error analysis

**Done when:** first-token accuracy reported in `results/`, imperative check working, notebook complete

---

### Phase 4 — CO3: Commit-Type Classifier
**Goal:** Train 6 models, compare, pick best, integrate `predict_commit_type`.

**Tasks:**
1. Preprocess prefix-stripped messages with CO1 pipeline (stem mode)
2. Build TF-IDF and BoW vectorizers; save both
3. Train 6 model/feature combinations (MultinomialNB, Logistic Regression, LinearSVC × TF-IDF, BoW)
4. **M2 Evaluation Requirements:**
   - **Metrics:** Report **macro-F1** and per-class precision / recall / F1, not just accuracy (due to class imbalance: `fix` accounts for ~51% of val and test splits).
   - **Cross-Validation:** Conduct `GroupKFold` (5 folds) on `train + val` grouped by `project`; report mean and standard deviation across folds for each model.
   - Evaluate best model on held-out `test_classifier.csv`.
5. Write all evaluation numbers to `results/phase4_classifier_eval.json`
6. Select best model; save via joblib
7. `notebooks/04_co3_classifier_eval.ipynb`: comparison table, confusion matrix heatmap, top-10 TF-IDF features per class
8. Implement `predict_commit_type()` with evidence (top contributing tokens)

**Done when:** `phase4_classifier_eval.json` has real macro-F1 and per-class metrics for all 6 models; GroupKFold mean±std reported; best model saved

---

### Phase 5 — Diff Parsing + diff_type_inference + Risk + Coverage
**Goal:** Extract all diff-level signals; compute risk and coverage scores.

**Tasks:**
1. Implement `diff_parser.py` with symbol extraction (section_header + def/class regex); unit-test on synthetic diffs
2. Implement `diff_type_inference.py`; unit-test all four cases
3. Author `config/risk_rules.yaml` (≥6 layers, whole path components, message synonyms)
4. Implement `risk_scorer.py`; test: path-component matching (not substring), synonym matching
5. Implement `coverage_scorer.py` with soft matching; tune threshold on val pairs
6. End-to-end paste-mode test: diff → symbols → coverage + risk scores with evidence

**Done when:** all tests pass, all scores return `evidence`, whole-component matching verified

---

### Phase 6 — LM + Embeddings + Alignment + Aggregation + Evaluation
**Goal:** Complete all remaining scoring components; wire aggregator; run E2E evaluation.

#### 6a — LM Scorer
1. `scripts/train_lm.py`: pad messages, apply UNK cutoff (min_count=2), cap at 150k, train Kneser-Ney trigram with bigram backoff
2. Calibrate `p_max` on val set; write `results/phase6_lm_calibration.json`
3. Verify score range [0,1]; test fluent vs gibberish

#### 6b — Embedding Aligner
1. `scripts/download_glove.py`: cache `glove-wiki-gigaword-100` (~66 MB)
2. Implement `embedding_aligner.py`

#### 6c — Aggregator
1. Implement `aggregator.py` with weight loading
2. Validate weight-sum invariant; test missing sub-score handling

#### 6d — End-to-End Evaluation
1. Run full pipeline on 100 held-out CommitBench samples; write `results/phase6_e2e_sample.json`
2. **Alignment AUROC:** real (diff, message) pairs vs shuffled (diff, random message) pairs; write `results/phase6_alignment_auroc.json`
3. **Coverage AUROC:** same real-vs-shuffled setup; write `results/phase6_coverage_auroc.json`; use this to select/confirm coverage threshold
4. Human spot-check 20 outputs; note errors

**Done when:** all `results/phase6_*.json` written with real numbers; AUROC reported

---

### Phase 7 — API + Frontend (CO4)
**Goal:** Expose pipeline via FastAPI; build React dashboard.

#### 7a — FastAPI Backend
- `POST /audit` — full pipeline; Pydantic request/response
- `GET /health` — liveness check
- Models loaded once at startup via FastAPI `lifespan`
- `tests/test_api.py` — TestClient coverage

**Request schema:**
```json
{ "mode": "paste", "diff": "...", "commit_message": "..." }
```

#### 7b — React Frontend
- Vite + React 18 + TypeScript + Tailwind v4 (`@tailwindcss/vite`)
- **`DiffViewer.tsx`**: custom line-by-line diff renderer (green `+`, red `-`, gray context lines)
- **`RadarScoreChart.tsx`**: Recharts `RadarChart` with one axis per sub-score
- **`EvidencePanel.tsx`**: expandable per-score evidence drawer
- **`RiskBadge.tsx`**: severity-coloured badge per flag
- Dark mode; no device frame

**Done when:** `npm run dev` renders working UI; paste-mode audit returns and renders all 6 sub-scores + radar chart + diff viewer

---

### Phase 8 — Documentation & Final Evaluation Report
**Goal:** Produce all required documentation; finalize.

**Tasks:**
1. `docs/EVALUATION_REPORT.md` — pulls numbers from `results/*.json`:
   - CO1: stem/lemma table, verb inflection chart
   - CO2: first-token accuracy, confusion matrix
   - CO3: model comparison table, confusion matrix heatmap, top features per class
   - Alignment AUROC + Coverage AUROC charts
   - 5 worked examples (good commit, bad commit, risky commit, unrelated message, gerund edge case)
2. `README.md`: setup, env vars, run commands, Mermaid architecture diagram
3. Final `pytest --cov` run; fix gaps
4. `pip freeze > requirements.txt`
5. *If time permits:* implement `github_client.py` + `ast_extractor.py` (stretch)

**Done when:** all docs written, ≥80% coverage, project runs from fresh clone

---

## 7. Timeline Estimate (Solo)

| Phase | Estimated Hours |
|-------|----------------|
| 1 — Data Audit | 3h |
| 2 — CO1 Preprocessing | 4h |
| 3 — CO2 Tagger | 5h |
| 4 — CO3 Classifier | 4h |
| 5 — Diff + Risk + Coverage | 5h |
| 6 — LM + Embeddings + Aggregation | 6h |
| 7 — API + Frontend | 7h |
| 8 — Docs + Final Report | 3h |
| **Total** | **~37h** |

---

## 8. Open Questions (Resolved)

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Does CommitBench have explicit type labels? | No — extract from `feat:`/`fix:` prefix with regex; discard unlabelled |
| Q2 | Is tree-sitter required for grading? | No — stretch goal after Phase 8; paste mode is primary |
| Q3 | Fully manual POS annotation? | Yes — 200 titles from held-out test split, disjoint from lexicon |
| Q4 | Weight config adjustable via UI? | Not in v1 UI; `config/weights.yaml` only |
| Q5 | CI pipeline expected? | Not required; README documents local test command |
| Q6 | Dependency pins verified? | Yes — all corrected to verified PyPI versions (2026-10-20) |

---

> **Phase 1 complete. Gate PASSED. Ready to begin Phase 2 (CO1: Text Pre-processing) upon user instruction.**
