"""Risk scorer module for CodeReviewer.NLP.

Analyzes modified file paths against sensitive architectural layers
(auth/security, database/migrations, billing/payment) defined in config/risk_rules.yaml.
Uses whole-path-component matching and layer synonym checks.
Produces score in [0.0, 1.0] where 1.0 = good (no risk).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import yaml
from code_reviewer.status import compute_status

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RULES_PATH = ROOT / "config" / "risk_rules.yaml"


def _load_risk_rules(rules_path: Path | None = None) -> dict[str, Any]:
    path = rules_path or DEFAULT_RULES_PATH
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_path_components(filepath: str) -> set[str]:
    """Extract whole directory and base filename components from a path."""
    cleaned = filepath.replace("\\", "/").strip("/")
    parts = re.split(r"[/.]+", cleaned)
    return {p.lower() for p in parts if p}


def score_risk(
    files: list[str],
    message: str,
    rules_path: Path | None = None,
) -> dict[str, Any]:
    """Compute risk score and audit flags for modified file paths against commit message.

    Returns:
      {
        "score": float in [0.0, 1.0],
        "flags": list[str],
        "sensitive_files": list[str],
        "layers_triggered": list[str],
        "evidence": str,
      }
    """
    rules_cfg = _load_risk_rules(rules_path)
    layers = rules_cfg.get("layers", {})

    msg_lower = message.lower()
    msg_words = set(re.findall(r"\w+", msg_lower))

    flags: list[str] = []
    sensitive_files: list[str] = []
    layers_triggered: set[str] = set()
    total_penalty = 0.0

    for file_path in files:
        components = _get_path_components(file_path)

        for layer_key, layer_info in layers.items():
            path_keywords = set(layer_info.get("path_components", []))
            matching_components = components & path_keywords

            if matching_components:
                sensitive_files.append(file_path)
                layers_triggered.add(layer_key)

                # Check if message mentions synonyms for this layer
                synonyms = set(layer_info.get("synonyms", []))
                has_general_synonym = bool(msg_words & synonyms)

                # Whole-path component justification:
                # If specific sensitive sub-component (like 'session' or 'token') is modified,
                # check if message mentions that specific component or general layer term
                unmentioned_components = matching_components - msg_words

                if not has_general_synonym:
                    # Message completely omits layer
                    penalty = layer_info.get("penalty", 0.4)
                    total_penalty += penalty
                    flags.append(
                        f"[{layer_info.get('name', layer_key)}] '{file_path}' touches sensitive {layer_key} layer, "
                        f"but commit message omits all {layer_key} synonyms."
                    )
                elif unmentioned_components:
                    # Message mentions one term (e.g. 'login') but touches other sensitive sub-modules (e.g. 'session')
                    penalty = layer_info.get("penalty", 0.4) * 0.5
                    total_penalty += penalty
                    flags.append(
                        f"[{layer_info.get('name', layer_key)}] '{file_path}' modified sensitive components "
                        f"{sorted(unmentioned_components)} not explicitly detailed in message."
                    )

    # Score in [0, 1] where 1.0 = good
    score = max(0.0, round(1.0 - min(total_penalty, 1.0), 2))

    if flags:
        evidence = f"Detected {len(flags)} risk warning(s) across layers: {', '.join(sorted(layers_triggered))}."
    else:
        evidence = "No sensitive architectural layers modified without justification."

    return {
        "score": score,
        "status": compute_status(score, has_risk_flags=bool(flags)),
        "flags": flags,
        "sensitive_files": sorted(set(sensitive_files)),
        "layers_triggered": sorted(layers_triggered),
        "evidence": evidence,
    }
