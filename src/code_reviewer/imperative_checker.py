"""Imperative mood checker module for CodeReviewer.NLP.

Reuses preprocessor.analyze_verb_inflection to verify that the commit message
starts with an imperative/base verb form.

Known limitation:
  This check is inflection/heuristic-based on the initial word and will miss
  non-verb openers (e.g. "login issue fix", "bug in auth") where the action
  verb or nominal phrase is inverted. A full statistical backoff POS tagger
  capable of analyzing full sentence structures is implemented in Milestone 2 (M2).
"""
from __future__ import annotations

import re
from typing import Any
from code_reviewer.preprocessor import (
    analyze_verb_inflection,
    IRREGULAR_PAST_TO_BASE,
    _get_lemmatizer,
)
from code_reviewer.status import compute_status


def _suggest_base_form(word: str, inflection: str) -> str:
    """Suggest an imperative base verb correction for non-base forms."""
    w = word.lower().strip()

    # Check irregular past table
    if w in IRREGULAR_PAST_TO_BASE:
        return IRREGULAR_PAST_TO_BASE[w]

    # Use WordNet verb lemmatizer
    lemmatizer = _get_lemmatizer()
    lemma_v = lemmatizer.lemmatize(w, pos="v")
    if lemma_v != w:
        return lemma_v

    # Heuristic suffix stripping
    if w.endswith("ed") and len(w) > 4:
        return w[:-2] if not w.endswith("ied") else w[:-3] + "y"
    if w.endswith("ing") and len(w) > 5:
        return w[:-3]
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and len(w) > 3:
        return w[:-1]

    return w


def check_imperative(message: str) -> dict[str, Any]:
    """Check if commit message opens with an imperative base verb.

    Returns:
      {
        "score": 1.0 (pass) or 0.0 (fail),
        "is_imperative": bool,
        "first_word": str,
        "inflection": str,
        "suggestion": str | None,
        "evidence": str,
      }
    """
    clean_msg = message.strip()
    # Strip any conventional commit prefix if present (e.g. 'fix: ')
    clean_msg = re.sub(r"^(?:feat|fix|docs|refactor|test|chore)(?:\([^)]*\))?[!]?:\s*", "", clean_msg)

    first_word_match = re.search(r"^[A-Za-z]+", clean_msg)
    first_word = first_word_match.group(0) if first_word_match else ""

    if not first_word:
        return {
            "score": 0.0,
            "status": "FAIL",
            "is_imperative": False,
            "first_word": "",
            "inflection": "unknown",
            "suggestion": None,
            "evidence": "Commit message is empty or starts with non-letter characters.",
            "ambiguous": False,
        }

    inflection, infl_ev = analyze_verb_inflection(first_word)
    is_ambiguous = bool(infl_ev.get("ambiguous", False))

    if inflection == "base":
        is_imperative = True
        score = 1.0
        suggestion = None
        evidence = f"Imperative convention satisfied: opening word '{first_word}' is in base verb form."
        if is_ambiguous:
            evidence += f" (Note: '{first_word}' is homographic between base and past tense; flagged as ambiguous)."
    else:
        is_imperative = False
        score = 0.0
        suggestion = _suggest_base_form(first_word, inflection)
        evidence = (
            f"Imperative convention violation: opening word '{first_word}' is {inflection}. "
            f"Suggested correction: '{suggestion}'."
        )

    return {
        "score": score,
        "status": compute_status(score, is_ambiguous=is_ambiguous),
        "is_imperative": is_imperative,
        "first_word": first_word,
        "inflection": inflection,
        "suggestion": suggestion,
        "evidence": evidence,
        "ambiguous": is_ambiguous,
    }
