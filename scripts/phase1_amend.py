"""Phase 1 Amendment: Project analysis, Project-grouped split, and LM rebuild.
"""
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

LABEL_PATTERN = re.compile(
    r"^(feat|fix|docs|refactor|test|chore)(?:\([^)]*\))?[!]?\s*:",
    re.IGNORECASE,
)
VALID_LABELS = {"feat", "fix", "docs", "refactor", "test", "chore"}
PY_EXTENSION = re.compile(r"\.py\b")
SEED = 42

def extract_label(message: str) -> str | None:
    m = LABEL_PATTERN.match(message.strip())
    if m:
        return m.group(1).lower()
    return None

def strip_prefix(message: str) -> str:
    return LABEL_PATTERN.sub("", message).strip()

def is_python_diff(diff_text: str, diff_languages: str = "") -> bool:
    if diff_languages:
        langs = [l.strip().lower() for l in str(diff_languages).split(",")]
        if "python" in langs:
            return True
    return bool(PY_EXTENSION.search(diff_text or ""))

def write_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows -> {path.relative_to(ROOT)}")

def main():
    print("=" * 60)
    print("Starting Phase 1 Amendment...")
    print("=" * 60)

    # 1. Read raw sample from disk (fast)
    print("Reading data/raw/commitbench_sample.csv...")
    raw_path = DATA_RAW / "commitbench_sample.csv"
    with open(raw_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)
    total_raw = len(raw_rows)
    print(f"Loaded {total_raw:,} rows from raw CSV.")

    # 2. Stream project and hash from CommitBench (200k rows)
    from datasets import load_dataset
    print("Streaming 'project' and 'hash' from Maxscha/commitbench (select_columns)...")
    ds = load_dataset("Maxscha/commitbench", split="train", streaming=True).select_columns(["project", "hash"])

    projects = []
    hashes = []
    for i, r in enumerate(ds):
        if i >= total_raw:
            break
        projects.append(r.get("project") or "unknown")
        hashes.append(r.get("hash") or "")
        if (i + 1) % 50_000 == 0:
            print(f"  ...retrieved {i + 1:,} project/hash records")

    print(f"Total project records: {len(projects):,}")

    # 3. Project stats & stream ordering
    project_counts = Counter(projects)
    distinct_projects = len(project_counts)
    top_10 = project_counts.most_common(10)
    top_10_share = sum(cnt for _, cnt in top_10) / total_raw

    # Check ordering: count runs of identical consecutive projects
    consecutive_same = sum(1 for i in range(1, len(projects)) if projects[i] == projects[i - 1])
    # If file-ordered/grouped by project, consecutive_same would be very high (~ total - distinct)
    # If interleaved/randomized, consecutive_same is small
    stream_ordering = (
        "interleaved/random"
        if consecutive_same < (total_raw - distinct_projects) * 0.2
        else "project-grouped/file-ordered"
    )

    print(f"\nDistinct projects: {distinct_projects:,}")
    print(f"Consecutive identical project pairs: {consecutive_same:,} (of {total_raw - 1:,})")
    print(f"Stream ordering: {stream_ordering}")
    print("\nTop 10 projects by commit count:")
    top_10_report = []
    for p, cnt in top_10:
        share = cnt / total_raw
        print(f"  {p:40s}: {cnt:6,d} ({share * 100:.2f}%)")
        top_10_report.append({"project": p, "count": cnt, "share": round(share, 4)})
    print(f"Combined top 10 share: {top_10_share * 100:.2f}%\n")

    # 4. Identify labeled rows and python rows
    labeled_data = []
    python_indices = set()
    for i, row in enumerate(raw_rows):
        proj = projects[i]
        msg = row["message"]
        diff = row["diff"]
        is_py = is_python_diff(diff)
        if is_py:
            python_indices.add(i)

        lbl = extract_label(msg)
        if lbl in VALID_LABELS:
            labeled_data.append({
                "index": i,
                "project": proj,
                "label": lbl,
                "message_stripped": strip_prefix(msg),
                "message_raw": msg,
                "diff": diff,
                "is_python": is_py,
            })

    print(f"Total labeled rows: {len(labeled_data):,}")
    print(f"Total python rows: {len(python_indices):,}")

    # 5. Project-grouped Stratified Split for Classifier
    # No project should appear in more than one split!
    # Group labeled commits by project:
    project_to_items = defaultdict(list)
    project_label_counts = defaultdict(Counter)
    for item in labeled_data:
        p = item["project"]
        project_to_items[p].append(item)
        project_label_counts[p][item["label"]] += 1

    # Total targets: ~70% train, 15% val, 15% test
    # We use a greedy multi-objective bin packing approach sorted by project size
    rng = random.Random(SEED)
    project_list = list(project_to_items.keys())
    rng.shuffle(project_list)
    # Sort descending by number of labeled items so big projects are assigned first
    project_list.sort(key=lambda p: len(project_to_items[p]), reverse=True)

    target_train_total = int(len(labeled_data) * 0.70)
    target_val_total = int(len(labeled_data) * 0.15)
    target_test_total = len(labeled_data) - target_train_total - target_val_total

    total_by_label = Counter(item["label"] for item in labeled_data)
    target_train_label = {l: int(cnt * 0.70) for l, cnt in total_by_label.items()}
    target_val_label = {l: int(cnt * 0.15) for l, cnt in total_by_label.items()}
    target_test_label = {l: total_by_label[l] - target_train_label[l] - target_val_label[l] for l in total_by_label}

    train_projects = set()
    val_projects = set()
    test_projects = set()

    current_train = Counter()
    current_val = Counter()
    current_test = Counter()

    for p in project_list:
        p_counts = project_label_counts[p]
        p_total = len(project_to_items[p])

        # Evaluate score if added to train, val, test
        # Deficit score: how much this addition reduces remaining deficit
        def deficit(current, target):
            d = 0
            for l, c in p_counts.items():
                needed = target[l] - current[l]
                if needed > 0:
                    d += min(c, needed)
            return d

        d_train = deficit(current_train, target_train_label)
        d_val = deficit(current_val, target_val_label)
        d_test = deficit(current_test, target_test_label)

        # Scale by target sizes
        score_train = d_train / (sum(target_train_label.values()) or 1)
        score_val = d_val / (sum(target_val_label.values()) or 1)
        score_test = d_test / (sum(target_test_label.values()) or 1)

        # Prefer the bucket with highest normalized deficit fill
        scores = [(score_train, "train"), (score_val, "val"), (score_test, "test")]
        # Break ties by bucket that is furthest from capacity
        scores.sort(
            key=lambda x: (
                x[0],
                - (sum(current_train.values()) / target_train_total if x[1] == "train" else
                   sum(current_val.values()) / target_val_total if x[1] == "val" else
                   sum(current_test.values()) / target_test_total)
            ),
            reverse=True
        )

        chosen = scores[0][1]
        if chosen == "train":
            train_projects.add(p)
            current_train.update(p_counts)
        elif chosen == "val":
            val_projects.add(p)
            current_val.update(p_counts)
        else:
            test_projects.add(p)
            current_test.update(p_counts)

    # Compile the split rows
    train_rows = [item for p in train_projects for item in project_to_items[p]]
    val_rows = [item for p in val_projects for item in project_to_items[p]]
    test_rows = [item for p in test_projects for item in project_to_items[p]]

    print("\nProject-grouped Split Distribution:")
    print(f"  Train: {len(train_rows):,} rows ({len(train_projects):,} projects)")
    print(f"  Val:   {len(val_rows):,} rows ({len(val_projects):,} projects)")
    print(f"  Test:  {len(test_rows):,} rows ({len(test_projects):,} projects)")

    # Assert no project leakage
    assert len(train_projects & val_projects) == 0, "Train & Val project overlap!"
    assert len(train_projects & test_projects) == 0, "Train & Test project overlap!"
    assert len(val_projects & test_projects) == 0, "Val & Test project overlap!"

    train_label_dist = Counter(r["label"] for r in train_rows)
    val_label_dist = Counter(r["label"] for r in val_rows)
    test_label_dist = Counter(r["label"] for r in test_rows)

    print("\nTraining Split Class Counts (Project-Grouped):")
    thin_classes = {}
    for lbl in sorted(VALID_LABELS):
        cnt = train_label_dist.get(lbl, 0)
        status = "OK" if cnt >= 200 else "FAIL (<200)"
        print(f"  {lbl:10s}: {cnt:5d}  [{status}]")
        if cnt < 200:
            thin_classes[lbl] = cnt

    gate_passed = len(thin_classes) == 0

    if not gate_passed:
        print("\n[STOP] GATE FAILED in project-grouped split!")
        for lbl, cnt in thin_classes.items():
            print(f"  Class '{lbl}' has only {cnt} train examples (<200).")
        sys.exit(1)

    print("\nGate PASSED for project-grouped classifier split! (All classes >= 200).")

    # Write updated classifier splits
    fields_clf = ["project", "label", "message_stripped", "is_python"]
    write_csv(train_rows, DATA_PROC / "train_classifier.csv", fields_clf)
    write_csv(val_rows, DATA_PROC / "val_classifier.csv", fields_clf)
    write_csv(test_rows, DATA_PROC / "test_classifier.csv", fields_clf)

    # 6. Rebuild LM corpus
    # Requirement:
    # Use the ~191k unlabeled messages from the raw sample (prefix-stripped where a prefix exists),
    # EXCLUDING any row in python_inferred.csv, the classifier val/test splits.
    # Cap at ~150k messages, hold out 5k for perplexity evaluation.
    # Replace train_lm.csv with lm_train.csv and lm_heldout.csv.

    # Sets to exclude:
    # Indices in val/test classifier splits:
    val_test_indices = {item["index"] for item in val_rows} | {item["index"] for item in test_rows}
    # We also exclude train classifier rows just to ensure purity, or keep unlabeled only:
    labeled_indices = {item["index"] for item in labeled_data}

    # Gather candidate messages from raw sample:
    lm_candidates = []
    seen_messages = set()

    for i, row in enumerate(raw_rows):
        # Exclude python rows
        if i in python_indices:
            continue
        # Exclude val and test classifier splits
        if i in val_test_indices:
            continue
        # Exclude classifier labeled rows (so LM is purely from unlabeled stream)
        if i in labeled_indices:
            continue

        raw_msg = row.get("message", "")
        # Strip prefix if one exists
        clean_msg = strip_prefix(raw_msg).strip()
        # Collapse whitespace
        clean_msg = " ".join(clean_msg.split())
        if len(clean_msg) < 5:  # skip trivial/empty
            continue

        # Simple deduplication
        if clean_msg not in seen_messages:
            seen_messages.add(clean_msg)
            lm_candidates.append({"message": clean_msg})

    print(f"\nTotal candidate LM messages: {len(lm_candidates):,}")

    rng.shuffle(lm_candidates)
    CAP_LM = 150_000
    if len(lm_candidates) > CAP_LM:
        lm_selected = lm_candidates[:CAP_LM]
    else:
        lm_selected = lm_candidates

    # Hold out 5,000 for perplexity evaluation
    HELDOUT_SIZE = 5_000
    lm_heldout = lm_selected[:HELDOUT_SIZE]
    lm_train = lm_selected[HELDOUT_SIZE:]

    print(f"LM train rows: {len(lm_train):,}")
    print(f"LM heldout rows: {len(lm_heldout):,}")

    # Write lm_train.csv and lm_heldout.csv
    write_csv(lm_train, DATA_PROC / "lm_train.csv", ["message"])
    write_csv(lm_heldout, DATA_PROC / "lm_heldout.csv", ["message"])

    # Remove old train_lm.csv if exists
    old_train_lm = DATA_PROC / "train_lm.csv"
    if old_train_lm.exists():
        old_train_lm.unlink()
        print(f"Removed deprecated {old_train_lm.name}")

    # 7. Update results/phase1_data_audit.json
    audit_data = {
        "total_streamed": total_raw,
        "distinct_projects": distinct_projects,
        "top_10_projects": top_10_report,
        "top_10_combined_share": round(top_10_share, 4),
        "stream_ordering": stream_ordering,
        "consecutive_same_project_count": consecutive_same,
        "unlabeled_discarded": total_raw - len(labeled_data),
        "total_labeled": len(labeled_data),
        "python_inferred": len(python_indices),
        "label_distribution_total": dict(sorted(total_by_label.items())),
        "split_sizes": {
            "train": len(train_rows),
            "val": len(val_rows),
            "test": len(test_rows),
            "lm_train": len(lm_train),
            "lm_heldout": len(lm_heldout),
        },
        "project_counts": {
            "train_projects": len(train_projects),
            "val_projects": len(val_projects),
            "test_projects": len(test_projects),
        },
        "label_distribution_train": dict(sorted(train_label_dist.items())),
        "label_distribution_val": dict(sorted(val_label_dist.items())),
        "label_distribution_test": dict(sorted(test_label_dist.items())),
        "gate": {
            "passed": gate_passed,
            "threshold": 200,
            "thin_classes": thin_classes,
        },
    }

    results_path = RESULTS / "phase1_data_audit.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"\nUpdated results -> {results_path.relative_to(ROOT)}")
    print("=" * 60)
    print("Phase 1 Amendment completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
