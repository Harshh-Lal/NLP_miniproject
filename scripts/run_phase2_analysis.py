"""Generate Phase 2 Preprocessing Analysis & Artifacts for CodeReviewer.NLP.

Item 6: False-merge groups are now data-derived:
  - Count word token frequencies across all training messages.
  - Group vocabulary by Porter stem; keep groups with >1 distinct lemma.
  - Rank groups by total corpus frequency (descending); pick top 15.
  - Sort differing_words_sample by corpus frequency (descending).
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from code_reviewer.preprocessor import (
    normalize,
    split_identifiers,
    tokenize,
    remove_stopwords,
    stem,
    lemmatize,
    compare_stem_lemma,
    analyze_verb_inflection,
    preprocess_pipeline,
)

DATA_PROC = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)


def _build_vocab_with_freq(rows: list[dict]) -> Counter:
    """Return word-frequency Counter over all training messages."""
    wf: Counter = Counter()
    for r in rows:
        norm, _ = normalize(r["message_stripped"])
        toks, _ = tokenize(norm)
        wf.update([t.lower() for t in toks if t.isalpha() and len(t) > 2])
    return wf


def _data_derived_false_merges(word_freq: Counter, n: int = 15) -> list[dict]:
    """Identify top-N stem groups where the stemmer conflates distinct lemmas.

    Steps:
      1. Stem and lemmatize every word in the vocabulary.
      2. Group words by their Porter stem.
      3. Keep groups with >1 distinct lemma.
      4. Rank groups by total corpus frequency of member words (descending).
      5. Return the top-N groups.
    """
    stem_groups: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for w in sorted(word_freq.keys()):
        s = stem([w])[0][0]
        l = lemmatize([w])[0][0]
        stem_groups[s].append((w, l, word_freq[w]))

    multi_lemma: list[tuple[int, str, list[str], list[str]]] = []
    for s, members in stem_groups.items():
        distinct_lemmas = sorted({l for w, l, c in members})
        if len(distinct_lemmas) > 1:
            total_freq = sum(c for w, l, c in members)
            words = [w for w, l, c in members]
            multi_lemma.append((total_freq, s, words, distinct_lemmas))

    multi_lemma.sort(key=lambda x: x[0], reverse=True)

    result = []
    for freq, s, words, distinct_lemmas in multi_lemma[:n]:
        result.append({
            "stem": s,
            "corpus_frequency": freq,
            "words": words,
            "distinct_lemmas": distinct_lemmas,
            "explanation": (
                f"Porter stem '{s}' conflates {len(words)} surface form(s) "
                f"({', '.join(words[:4])}{'...' if len(words) > 4 else ''}) "
                f"with {len(distinct_lemmas)} distinct lemmas: {', '.join(distinct_lemmas)}."
            ),
        })
    return result


def main():
    train_path = DATA_PROC / "train_classifier.csv"
    assert train_path.exists(), f"Missing {train_path}"

    with open(train_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        train_rows = list(reader)

    print(f"Loaded {len(train_rows):,} rows from {train_path.name}")

    # --- Corpus-wide word frequency (used for multiple metrics) ---
    word_freq = _build_vocab_with_freq(train_rows)
    vocab = sorted(word_freq.keys())
    total_vocab = len(vocab)
    print(f"Vocabulary size: {total_vocab:,} unique words")

    # 1. Normalization sample demonstration
    norm_examples = []
    for r in train_rows:
        msg = r["message_stripped"]
        if (("#" in msg or "http" in msg or len(msg.split()) > 10) and len(norm_examples) < 5):
            norm_text, ev = normalize(msg)
            norm_examples.append({
                "original": msg,
                "normalized": norm_text,
                "removed_urls": ev["removed_urls"],
                "removed_issues": ev["removed_issues"],
                "removed_trailers": ev["removed_trailers"],
            })

    # 2. Token counts before/after stopword removal
    total_tokens_before = 0
    total_tokens_after = 0
    token_counts_before = []
    token_counts_after = []
    stopwords_removed_counter: Counter = Counter()

    # 3. First-word verb inflection distribution
    inflection_counter: Counter = Counter()
    ambiguous_count = 0
    first_words_by_type: dict[str, Counter] = {
        "base": Counter(),
        "past": Counter(),
        "gerund": Counter(),
        "third_person": Counter(),
        "unknown": Counter(),
    }

    for r in train_rows:
        msg = r["message_stripped"]
        norm_text, _ = normalize(msg)
        tokens, _ = tokenize(norm_text)
        filtered, sw_ev = remove_stopwords(tokens)

        total_tokens_before += len(tokens)
        total_tokens_after += len(filtered)
        token_counts_before.append(len(tokens))
        token_counts_after.append(len(filtered))
        stopwords_removed_counter.update(sw_ev["removed_stopwords"])

        first_w = norm_text.split()[0] if norm_text.split() else ""
        m = re.match(r"^[a-z]+", first_w.lower())
        w_clean = m.group(0) if m else ""
        if w_clean:
            infl, infl_ev = analyze_verb_inflection(w_clean)
            inflection_counter[infl] += 1
            first_words_by_type[infl][w_clean] += 1
            if infl_ev.get("ambiguous"):
                ambiguous_count += 1
        else:
            inflection_counter["unknown"] += 1

    # 4. Stem vs Lemma — full vocabulary analysis
    differing: dict[str, dict] = {}
    for w in vocab:
        st, _ = stem([w])
        lm, _ = lemmatize([w])
        s_val = st[0]
        l_val = lm[0]
        if s_val != l_val:
            differing[w] = {"stem": s_val, "lemma": l_val}

    diff_count = len(differing)
    diff_pct = round(diff_count / total_vocab * 100, 2)
    print(f"Differing words (stem != lemma): {diff_count} / {total_vocab} = {diff_pct}%")

    # Sort differing_words_sample by corpus frequency descending (Item 6)
    sorted_diff = sorted(differing.items(), key=lambda kv: word_freq.get(kv[0], 0), reverse=True)
    differing_sample = dict(sorted_diff[:30])

    # Conflation metrics
    stem_to_words: dict[str, list] = defaultdict(list)
    lemma_to_words: dict[str, list] = defaultdict(list)
    for w in vocab:
        s = stem([w])[0][0]
        l = lemmatize([w])[0][0]
        stem_to_words[s].append(w)
        lemma_to_words[l].append(w)

    distinct_stems = len(stem_to_words)
    distinct_lemmas = len(lemma_to_words)
    avg_surface_per_stem = round(total_vocab / distinct_stems, 2)
    avg_surface_per_lemma = round(total_vocab / distinct_lemmas, 2)

    print(f"Distinct stems: {distinct_stems}, avg surface/stem: {avg_surface_per_stem}")
    print(f"Distinct lemmas: {distinct_lemmas}, avg surface/lemma: {avg_surface_per_lemma}")

    # --- Data-derived false merges (Item 6) ---
    false_merges_15 = _data_derived_false_merges(word_freq, n=15)
    print("\nTop 15 data-derived false-merge groups (by corpus frequency):")
    for i, grp in enumerate(false_merges_15, 1):
        print(f"  {i:2d}. stem='{grp['stem']}' freq={grp['corpus_frequency']} "
              f"words={grp['words'][:3]} distinct_lemmas={grp['distinct_lemmas']}")

    # 5. Compile metrics
    n_train = len(train_rows)
    avg_tokens_before = round(total_tokens_before / n_train, 2)
    avg_tokens_after = round(total_tokens_after / n_train, 2)
    reduction_pct = round((1 - total_tokens_after / total_tokens_before) * 100, 2)

    total_with_verb = sum(inflection_counter.values())
    inflection_dist = {
        k: {
            "count": inflection_counter[k],
            "percentage": round(inflection_counter[k] / total_with_verb * 100, 2),
            "top_words": dict(first_words_by_type[k].most_common(5)),
        }
        for k in ["base", "past", "gerund", "third_person", "unknown"]
    }

    imperative_adherence_pct = round(inflection_counter["base"] / total_with_verb * 100, 2)
    violation_pct = round(
        (inflection_counter["past"] + inflection_counter["gerund"] + inflection_counter["third_person"])
        / total_with_verb * 100,
        2,
    )

    # Keep hand-picked sample words table for course demo purposes
    sample_words = [
        "fixed", "fixes", "fixing", "added", "adding", "updates", "updated",
        "updating", "refactored", "refactoring", "dependencies", "organization",
        "matrices", "indices", "relational", "capabilities", "authorization",
        "authentication", "configured", "configuring", "clean", "cleaned",
        "cleaning", "deleted", "deleting", "prevented", "preventing", "improved",
        "improving", "simplified", "simplifying",
    ]
    stem_lemma_table = compare_stem_lemma(sample_words)

    results_data = {
        "dataset": "train_classifier.csv",
        "num_messages": n_train,
        "token_counts": {
            "total_before_stopwords": total_tokens_before,
            "total_after_stopwords": total_tokens_after,
            "mean_before_stopwords": avg_tokens_before,
            "mean_after_stopwords": avg_tokens_after,
            "reduction_percentage": reduction_pct,
            "top_removed_stopwords": dict(stopwords_removed_counter.most_common(10)),
        },
        "stem_vs_lemma": {
            "total_vocabulary_evaluated": total_vocab,
            "differing_word_count": diff_count,
            "differing_percentage": diff_pct,
            "distinct_stems": distinct_stems,
            "distinct_lemmas": distinct_lemmas,
            "avg_surface_forms_per_stem": avg_surface_per_stem,
            "avg_surface_forms_per_lemma": avg_surface_per_lemma,
            "differing_words_sample": {
                w: v for w, v in differing_sample.items()
            },
            "sample_table_note": "30 most-frequent differing words, sorted by corpus frequency descending",
            "stemmer_semantic_false_merges_15": false_merges_15,
            "false_merges_derivation": (
                "Data-derived: stem groups with >1 distinct lemma, ranked by total corpus frequency "
                f"(top 15 of {sum(1 for _, members in stem_to_words.items() if len(set(lemmatize([w])[0][0] for w in members)) > 1)} eligible groups)"
            ),
            "num_examples": len(stem_lemma_table),
            "examples": stem_lemma_table,
        },
        "inflection_analysis": {
            "total_evaluated": total_with_verb,
            "imperative_base_count": inflection_counter["base"],
            "imperative_adherence_percentage": imperative_adherence_pct,
            "convention_violations_percentage": violation_pct,
            "ambiguous_homographs_detected": ambiguous_count,
            "distribution": inflection_dist,
        },
        "normalization_samples": norm_examples,
    }

    out_file = RESULTS / "phase2_preprocessing.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"\nPhase 2 metrics written -> {out_file.relative_to(ROOT)}")
    print("\nSummary Statistics:")
    print(f"  Messages analyzed: {n_train:,}")
    print(f"  Mean tokens before stop-word removal: {avg_tokens_before}")
    print(f"  Mean tokens after stop-word removal:  {avg_tokens_after} (-{reduction_pct}%)")
    print("\nFirst-word Verb Inflection Distribution:")
    for infl_type, stats in inflection_dist.items():
        print(f"  {infl_type:14s}: {stats['count']:5,d} ({stats['percentage']:5.2f}%) | Top: {list(stats['top_words'].keys())}")
    print(f"\n  Imperative Adherence (base): {imperative_adherence_pct}%")
    print(f"  Convention Violations (past + gerund + 3rd): {violation_pct}%")
    print(f"  Ambiguous homographs (set/put/cut): {ambiguous_count}")


if __name__ == "__main__":
    main()
