"""Consistency score aggregator module for CodeReviewer.NLP.

Combines sub-scores into an overall consistency score using configurable weights.
Gracefully skips and reports missing sub-scores, dynamically renormalizing
the remaining weights to guarantee overall score is always in [0.0, 1.0].
Never crashes on missing inputs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_WEIGHTS_PATH = ROOT / "config" / "weights.yaml"

DEFAULT_WEIGHTS = {
    "imperative_mood": 0.25,
    "coverage": 0.35,
    "risk_flags": 0.20,
    "type_consistency": 0.20,
    "fluency": 0.00,
    "alignment": 0.00,
}


def _load_weights(weights_path: Path | None = None) -> dict[str, float]:
    path = weights_path or DEFAULT_WEIGHTS_PATH
    if not path.exists():
        return dict(DEFAULT_WEIGHTS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            loaded = data.get("weights", {})
            return {k: float(v) for k, v in loaded.items()}
    except Exception:
        return dict(DEFAULT_WEIGHTS)


def aggregate_scores(
    sub_scores: dict[str, Any],
    weights_path: Path | None = None,
) -> dict[str, Any]:
    """Aggregate available sub-scores into an overall score in [0.0, 1.0].

    Args:
      sub_scores: Dict of sub-score objects or numeric floats, e.g.:
        {
          "imperative_mood": {"score": 0.0, ...},
          "coverage": {"score": 0.5, ...},
          "risk_flags": {"score": 0.8, ...},
          "type_consistency": {"score": 1.0, ...},
        }

    Returns:
      {
        "overall_score": float in [0.0, 1.0],
        "sub_scores": dict[str, float],
        "weights_used": dict[str, float],
        "missing_sub_scores": list[str],
      }
    """
    configured_weights = _load_weights(weights_path)

    # Extract numeric float for each sub-score
    numeric_scores: dict[str, float] = {}
    missing_scores: list[str] = []

    for key, weight in configured_weights.items():
        if weight <= 0.0:
            continue
        val = sub_scores.get(key)
        if val is None:
            missing_scores.append(key)
            continue

        if isinstance(val, (int, float)):
            numeric_scores[key] = max(0.0, min(1.0, float(val)))
        elif isinstance(val, dict) and "score" in val and val["score"] is not None:
            try:
                numeric_scores[key] = max(0.0, min(1.0, float(val["score"])))
            except (ValueError, TypeError):
                missing_scores.append(key)
        else:
            missing_scores.append(key)

    if not numeric_scores:
        return {
            "overall_score": 0.0,
            "sub_scores": {},
            "weights_used": {},
            "missing_sub_scores": missing_scores,
        }

    # Sum of weights for present scores
    active_weight_sum = sum(configured_weights.get(k, 0.0) for k in numeric_scores)
    if active_weight_sum <= 0:
        # Uniform fallback
        active_weight_sum = float(len(numeric_scores))
        weights_used = {k: 1.0 / active_weight_sum for k in numeric_scores}
    else:
        weights_used = {k: configured_weights.get(k, 0.0) / active_weight_sum for k in numeric_scores}

    overall = sum(numeric_scores[k] * weights_used[k] for k in numeric_scores)
    overall_clamped = round(max(0.0, min(1.0, overall)), 2)

    return {
        "overall_score": overall_clamped,
        "sub_scores": {k: round(v, 2) for k, v in numeric_scores.items()},
        "weights_used": {k: round(v, 3) for k, v in weights_used.items()},
        "missing_sub_scores": missing_scores,
    }
