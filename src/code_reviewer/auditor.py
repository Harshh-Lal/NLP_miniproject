"""Auditor orchestrator for CodeReviewer.NLP.

Combines diff parsing, type inference, imperative checking, symbol coverage,
risk scoring, and score aggregation into a unified audit pipeline.
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any
import yaml

from code_reviewer.diff_parser import parse_diff
from code_reviewer.diff_type_inference import infer_diff_type
from code_reviewer.imperative_checker import check_imperative
from code_reviewer.coverage_scorer import score_coverage
from code_reviewer.risk_scorer import score_risk
from code_reviewer.aggregator import aggregate_scores
from code_reviewer.status import compute_status

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_COMPAT_PATH = ROOT / "config" / "type_compatibility.yaml"

CONVENTIONAL_PREFIX_REGEX = re.compile(
    r"^(feat|fix|docs|refactor|test|chore)(?:\([^)]*\))?[!]?:\s*",
    re.IGNORECASE,
)

# Object noun hints and their target conventional type
OBJECT_NOUN_PATTERNS = [
    (re.compile(r"\b(?:ci|workflow|workflows|github[_-]?actions?)\b", re.IGNORECASE), "chore"),
    (re.compile(r"\b(?:readme|docs?|documentation|guide|manual)\b", re.IGNORECASE), "docs"),
    (re.compile(r"\b(?:deps?|dependencies|dependency|package\.json|requirements)\b", re.IGNORECASE), "chore"),
    (re.compile(r"\b(?:tests?|pytest|unittest|specs?)\b", re.IGNORECASE), "test"),
]

DEFAULT_COMPATIBILITY_MATRIX = {
    "feat": {"chore": 0.5, "test": 0.5, "refactor": 0.5},
    "chore": {"feat": 0.5, "test": 0.5, "docs": 0.5, "refactor": 0.5},
    "fix": {"test": 0.5, "refactor": 0.5, "chore": 0.3},
    "test": {"feat": 0.5, "fix": 0.5, "chore": 0.5},
    "docs": {"chore": 0.5},
    "refactor": {"feat": 0.5, "fix": 0.5, "chore": 0.5},
}


def _load_type_compatibility(path: Path | None = None) -> dict[str, dict[str, float]]:
    cfg_path = path or DEFAULT_COMPAT_PATH
    if not cfg_path.exists():
        return DEFAULT_COMPATIBILITY_MATRIX
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            matrix = data.get("matrix", {})
            return matrix or DEFAULT_COMPATIBILITY_MATRIX
    except Exception:
        return DEFAULT_COMPATIBILITY_MATRIX


def _infer_message_intent(message: str, diff_type: str | None = None) -> str:
    """Extract stated commit type prefix or keyword intent from message.

    Object-noun hints (ci, workflow, readme, docs, deps, test) override
    opening-verb intent to accurately capture commits like 'Add pytest to CI'.
    """
    m = CONVENTIONAL_PREFIX_REGEX.match(message.strip())
    if m:
        return m.group(1).lower()

    msg_lower = message.lower()

    # 1. Collect all matching object-noun hints
    detected_noun_hints: list[str] = []
    for pattern, target_type in OBJECT_NOUN_PATTERNS:
        if pattern.search(msg_lower):
            detected_noun_hints.append(target_type)

    if detected_noun_hints:
        # If diff_type matches one of the noun hints (e.g. diff is chore and 'ci' hint is present)
        if diff_type and diff_type in detected_noun_hints:
            return diff_type
        # Otherwise, the object noun hint overrides the opening verb
        return detected_noun_hints[-1]

    # 2. Opening-verb intent fallback
    first_w = msg_lower.split()[0] if msg_lower.split() else ""

    if any(w in first_w for w in ["fix", "bug", "patch", "resolve"]):
        return "fix"
    if any(w in first_w for w in ["add", "feat", "implement", "support", "new"]):
        return "feat"
    if any(w in first_w for w in ["doc", "readme", "comment"]):
        return "docs"
    if any(w in first_w for w in ["test", "spec"]):
        return "test"
    if any(w in first_w for w in ["refactor", "clean", "simplify"]):
        return "refactor"
    if any(w in first_w for w in ["chore", "bump", "ci", "build"]):
        return "chore"

    return "ambiguous"


def evaluate_type_consistency(
    message: str,
    diff_type: str,
    compat_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate consistency between inferred diff type and commit message intent.

    When diff_inferred_type is 'ambiguous', returns score=None so it is excluded
    from weighted score aggregation rather than granting a free 1.00 score.
    Uses a compatibility matrix for related cross-type actions (e.g. feat vs chore = 0.5).
    """
    msg_intent = _infer_message_intent(message, diff_type=diff_type)

    if diff_type == "ambiguous" or msg_intent == "ambiguous":
        # Excluded from aggregation instead of free 1.00
        score = None
        status = "N/A"
        evidence = f"Type consistency neutral (excluded from scoring): diff is {diff_type}, message intent is {msg_intent}."
    elif diff_type == msg_intent:
        score = 1.0
        status = "PASS"
        evidence = f"Type consistency matched: both diff and message indicate '{diff_type}'."
    else:
        matrix = _load_type_compatibility(compat_path)
        score = float(matrix.get(diff_type, {}).get(msg_intent, 0.0))
        status = compute_status(score)
        if score > 0.0:
            evidence = (
                f"Type compatibility partial match ({score:.2f}): "
                f"diff indicates '{diff_type}', but message indicates '{msg_intent}'."
            )
        else:
            evidence = f"Type mismatch: diff indicates '{diff_type}', but message indicates '{msg_intent}'."

    return {
        "score": score,
        "status": status,
        "predicted_message_type": msg_intent,
        "diff_inferred_type": diff_type,
        "evidence": evidence,
    }


def audit_commit(message: str, diff_text: str) -> dict[str, Any]:
    """Execute end-to-end consistency audit on commit message and diff.

    Returns complete audit report.
    """
    # 1. Parse diff
    diff_data = parse_diff(diff_text)
    files = diff_data["files"]
    symbols = diff_data["symbols"]

    # Degenerate input check: if no files parsed from diff
    if not files:
        imperative_res = check_imperative(message)
        return {
            "commit_message": message,
            "overall_score": None,
            "overall_status": "N/A",
            "diff_inferred_type": "ambiguous",
            "message_intent": _infer_message_intent(message),
            "evidence": "No valid diff detected",
            "scores": {
                "imperative_mood": imperative_res,
                "coverage": {
                    "score": None,
                    "status": "N/A",
                    "mentioned_symbols": [],
                    "omitted_symbols": [],
                    "total_symbols": 0,
                    "evidence": "No symbols changed; coverage not applicable",
                },
                "risk_flags": {
                    "score": None,
                    "status": "N/A",
                    "flags": [],
                    "sensitive_files": [],
                    "layers_triggered": [],
                    "evidence": "No valid files detected in diff.",
                },
                "type_consistency": {
                    "score": None,
                    "status": "N/A",
                    "predicted_message_type": _infer_message_intent(message),
                    "diff_inferred_type": "ambiguous",
                    "evidence": "Type consistency neutral (excluded from scoring): no valid diff detected.",
                },
            },
            "aggregation": {
                "weights_used": {},
                "missing_sub_scores": ["coverage", "risk_flags", "type_consistency"],
            },
            "diff_summary": {
                "files": [],
                "added_lines": 0,
                "removed_lines": 0,
                "symbols": [],
                "file_summaries": [],
            },
        }

    # 2. Heuristic type inference from diff files
    diff_type, diff_type_ev = infer_diff_type(files)

    # 3. Imperative mood check on commit message
    imperative_res = check_imperative(message)

    # 4. Coverage of changed symbols
    coverage_res = score_coverage(symbols, message)

    # 5. Risk score for sensitive architecture layers
    risk_res = score_risk(files, message)

    # 6. Type consistency
    type_res = evaluate_type_consistency(message, diff_type)

    # 7. Aggregate
    sub_scores = {
        "imperative_mood": imperative_res,
        "coverage": coverage_res,
        "risk_flags": risk_res,
        "type_consistency": type_res,
    }
    agg_res = aggregate_scores(sub_scores)

    has_risk = bool(risk_res.get("flags"))
    overall_status = compute_status(agg_res["overall_score"], has_risk_flags=has_risk)

    return {
        "commit_message": message,
        "overall_score": agg_res["overall_score"],
        "overall_status": overall_status,
        "diff_inferred_type": diff_type,
        "message_intent": type_res["predicted_message_type"],
        "scores": {
            "imperative_mood": imperative_res,
            "coverage": coverage_res,
            "risk_flags": risk_res,
            "type_consistency": type_res,
        },
        "aggregation": {
            "weights_used": agg_res["weights_used"],
            "missing_sub_scores": agg_res["missing_sub_scores"],
        },
        "diff_summary": {
            "files": files,
            "added_lines": diff_data["added_lines"],
            "removed_lines": diff_data["removed_lines"],
            "symbols": symbols,
            "file_summaries": diff_data["file_summaries"],
        },
    }
