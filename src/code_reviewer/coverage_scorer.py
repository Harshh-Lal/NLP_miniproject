"""Coverage scorer module for CodeReviewer.NLP.

Evaluates how well a commit message covers the modified function and class symbols.
Reuses preprocessor functions (split_identifiers, tokenize, lemmatize) for soft matching.
"""
from __future__ import annotations

from typing import Any
from code_reviewer.preprocessor import (
    split_identifiers,
    tokenize,
    lemmatize,
    normalize,
)
from code_reviewer.status import compute_status


def score_coverage(
    symbols: list[str],
    message: str,
) -> dict[str, Any]:
    """Score the proportion of modified symbols mentioned in the commit message.

    Returns:
      {
        "score": float in [0.0, 1.0],
        "mentioned_symbols": list[str],
        "omitted_symbols": list[str],
        "total_symbols": int,
        "evidence": str,
      }
    """
    if not symbols:
        return {
            "score": None,
            "status": "N/A",
            "mentioned_symbols": [],
            "omitted_symbols": [],
            "total_symbols": 0,
            "evidence": "No symbols changed; coverage not applicable",
        }

    # Normalize, tokenize, and lemmatize commit message
    norm_msg, _ = normalize(message)
    msg_raw_tokens, _ = tokenize(norm_msg)
    msg_lemmas, _ = lemmatize(msg_raw_tokens)
    msg_lemmas_set = {t.lower() for t in msg_lemmas}

    mentioned: list[str] = []
    omitted: list[str] = []

    for sym in symbols:
        # Split symbol identifier (camelCase / snake_case) and lemmatize parts
        parts, _ = split_identifiers(sym)
        sym_lemmas, _ = lemmatize(parts)
        sym_lemmas_set = {s.lower() for s in sym_lemmas}

        # Check soft overlap: does any constituent lemma match the message lemmas?
        # Or exact full symbol match
        is_covered = bool(sym_lemmas_set & msg_lemmas_set) or (sym.lower() in norm_msg)

        if is_covered:
            mentioned.append(sym)
        else:
            omitted.append(sym)

    total = len(symbols)
    score = round(len(mentioned) / total, 2) if total > 0 else 1.0

    if omitted:
        evidence = (
            f"{len(mentioned)} of {total} changed symbol(s) mentioned in message. "
            f"Omitted: {omitted}."
        )
    else:
        evidence = f"All {total} changed symbol(s) mentioned in message."

    return {
        "score": score,
        "status": compute_status(score),
        "mentioned_symbols": mentioned,
        "omitted_symbols": omitted,
        "total_symbols": total,
        "evidence": evidence,
    }
