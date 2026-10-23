"""Phase 1 – Data Audit for CodeReviewer.NLP
Streams CommitBench, labels rows by conventional-commit prefix,
NOTE: CommitBench actual columns: hash, diff, message, project, split, diff_languages
infers Python rows from diff extensions, produces train/val/test splits,
writes results/phase1_data_audit.json.

Gate: if any class has <200 training samples, script prints options and exits 1.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

for d in (DATA_RAW, DATA_PROC, RESULTS):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MAX_ROWS = 200_000          # Stream cap
SEED = 42
SPLIT_RATIOS = (0.70, 0.15, 0.15)   # train / val / test
MIN_TRAIN_PER_CLASS = 200            # Gate threshold

LABEL_PATTERN = re.compile(
    r"^(feat|fix|docs|refactor|test|chore)(?:\([^)]*\))?[!]?\s*:",
    re.IGNORECASE,
)
PY_EXTENSION = re.compile(r"\.py\b")

VALID_LABELS = {"feat", "fix", "docs", "refactor", "test", "chore"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def extract_label(message: str) -> str | None:
    """Return normalized label from conventional-commit prefix, or None."""
    m = LABEL_PATTERN.match(message.strip())
    if m:
        return m.group(1).lower()
    return None


def strip_prefix(message: str) -> str:
    """Remove the conventional-commit prefix and return body only."""
    return LABEL_PATTERN.sub("", message).strip()


def is_python_row(diff_text: str, diff_languages: str = "") -> bool:
    """True if row is Python: check diff_languages column first, then .py in diff."""
    if diff_languages:
        langs = [l.strip().lower() for l in str(diff_languages).split(",")]
        if "python" in langs:
            return True
    return bool(PY_EXTENSION.search(diff_text or ""))


def stream_commitbench(max_rows: int) -> Iterator[dict]:
    """Stream CommitBench from HuggingFace datasets in iterable mode."""
    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit("ERROR: 'datasets' package not installed. Run: pip install datasets==2.20.0")

    print("Streaming CommitBench (this may take a few minutes)...")
    ds = load_dataset(
        "Maxscha/commitbench",
        split="train",
        streaming=True,
        trust_remote_code=False,
    )
    for i, row in enumerate(ds):
        if i >= max_rows:
            break
        if i == 0:
            print(f"  [CommitBench schema] columns: {list(row.keys())}")
        yield row


def stratified_split(rows: list[dict], ratios: tuple[float, float, float], seed: int):
    """Stratified split by label. Returns (train, val, test) lists."""
    import random
    rng = random.Random(seed)

    by_label: dict[str, list[dict]] = {}
    for r in rows:
        by_label.setdefault(r["label"], []).append(r)

    train, val, test = [], [], []
    for label, items in by_label.items():
        rng.shuffle(items)
        n = len(items)
        n_train = int(n * ratios[0])
        n_val = int(n * ratios[1])
        train.extend(items[:n_train])
        val.extend(items[n_train: n_train + n_val])
        test.extend(items[n_train + n_val:])

    return train, val, test


def write_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows -> {path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # ------------------------------------------------------------------
    # 1. Stream and sample
    # ------------------------------------------------------------------
    raw_rows: list[dict] = []
    column_sample: dict = {}

    for i, row in enumerate(stream_commitbench(MAX_ROWS)):
        if i == 0:
            column_sample = {k: type(v).__name__ for k, v in row.items()}
            print(f"\nCommitBench columns: {list(column_sample.keys())}")

        message = row.get("message") or ""
        diff = row.get("diff") or ""
        diff_languages = row.get("diff_languages") or ""
        raw_rows.append({"message": message, "diff": diff, "diff_languages": diff_languages})

        if (i + 1) % 20_000 == 0:
            print(f"  ...streamed {i + 1:,} rows")

    total_streamed = len(raw_rows)
    print(f"\nTotal streamed: {total_streamed:,}")

    # Write raw sample (message + diff only) as CSV
    raw_path = DATA_RAW / "commitbench_sample.csv"
    write_csv(raw_rows, raw_path, ["message", "diff"])

    # ------------------------------------------------------------------
    # 2. Label and filter
    # ------------------------------------------------------------------
    labeled_rows: list[dict] = []
    python_count = 0
    unlabeled_count = 0

    for row in raw_rows:
        label = extract_label(row["message"])
        if label is None or label not in VALID_LABELS:
            unlabeled_count += 1
            continue
        stripped = strip_prefix(row["message"])
        is_py = is_python_row(row["diff"], row.get("diff_languages", ""))
        if is_py:
            python_count += 1
        labeled_rows.append({
            "label": label,
            "message_stripped": stripped,
            "diff": row["diff"],
            "is_python": is_py,
        })

    print(f"\nLabeled rows: {len(labeled_rows):,}  "
          f"| Unlabeled/discarded: {unlabeled_count:,}  "
          f"| Python rows (diff_languages+regex): {python_count:,}")

    label_counts_total = Counter(r["label"] for r in labeled_rows)
    print("\nLabel distribution (all labeled):")
    for lbl, cnt in sorted(label_counts_total.items()):
        print(f"  {lbl:12s}: {cnt:,}")

    # ------------------------------------------------------------------
    # 3. Split: classifier set (70/15/15)
    # ------------------------------------------------------------------
    train, val, test = stratified_split(labeled_rows, SPLIT_RATIOS, SEED)
    label_counts_train = Counter(r["label"] for r in train)

    # ------------------------------------------------------------------
    # 4. LM set: separate sample (no overlap with classifier splits)
    # Use val+test rows only to guarantee disjointness
    # ------------------------------------------------------------------
    lm_rows = val + test   # non-training rows used for LM
    # In practice LM wants more data -- we note this in the report

    # Write CSVs
    fields_clf = ["label", "message_stripped", "is_python"]
    fields_full = ["label", "message_stripped", "diff", "is_python"]
    for rows, fname, fields in [
        (train, "train_classifier.csv", fields_clf),
        (val,   "val_classifier.csv",   fields_clf),
        (test,  "test_classifier.csv",  fields_clf),
        (lm_rows, "train_lm.csv",       ["label", "message_stripped"]),
        ([r for r in labeled_rows if r["is_python"]], "python_inferred.csv", fields_full),
    ]:
        write_csv(rows, DATA_PROC / fname, fields)
        print(f"  Wrote {len(rows):,} rows -> data/processed/{fname}")

    # ------------------------------------------------------------------
    # 5. Gate check
    # ------------------------------------------------------------------
    thin_classes = {lbl: label_counts_train.get(lbl, 0) for lbl in sorted(VALID_LABELS) if label_counts_train.get(lbl, 0) < MIN_TRAIN_PER_CLASS}
    gate_passed = len(thin_classes) == 0

    # ------------------------------------------------------------------
    # 6. Write results JSON
    # ------------------------------------------------------------------
    audit = {
        "total_streamed": total_streamed,
        "unlabeled_discarded": unlabeled_count,
        "total_labeled": len(labeled_rows),
        "python_inferred": python_count,
        "label_distribution_total": dict(sorted(label_counts_total.items())),
        "label_distribution_train": dict(sorted(label_counts_train.items())),
        "split_sizes": {
            "train": len(train),
            "val": len(val),
            "test": len(test),
            "lm_set": len(lm_rows),
        },
        "gate": {
            "passed": gate_passed,
            "threshold": MIN_TRAIN_PER_CLASS,
            "thin_classes": thin_classes,
        },
        "column_schema": column_sample,
    }

    results_path = RESULTS / "phase1_data_audit.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    print(f"\nResults written -> {results_path.relative_to(ROOT)}")

    # ------------------------------------------------------------------
    # 7. Gate report
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    if gate_passed:
        print("[PASSED] GATE PASSED -- all classes have >=200 training samples.")
        print("         Proceed to Phase 2 (CO1 Preprocessing).")
    else:
        print("[FAILED] GATE FAILED -- thin classes detected:")
        for lbl, cnt in thin_classes.items():
            print(f"    {lbl}: {cnt} training samples (need >={MIN_TRAIN_PER_CLASS})")
        print("""
Options before proceeding:
  A) Scrape additional conventional-commit repos via GitHub API
     (~1-3 days; produces clean labels; no LLM involved)
  B) Keyword-label unlabeled rows
     (fast; labels flagged as WEAK; may degrade CO3 macro-F1)
  C) Merge thin classes (e.g., refactor + chore -> "other")
     (reduces classifier targets; simpler but less academically rich)

Report options to supervisor and WAIT for approval before Phase 2.
""")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
