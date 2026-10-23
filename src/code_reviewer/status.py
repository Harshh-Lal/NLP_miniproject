"""Status label definition and threshold evaluation for CodeReviewer.NLP."""
from __future__ import annotations

# Single centralized threshold definition
THRESHOLD_PASS = 0.80
THRESHOLD_WARN = 0.50


def compute_status(
    score: float | None,
    has_risk_flags: bool = False,
    is_ambiguous: bool = False,
) -> str:
    """Compute unified status label: 'PASS', 'WARN', 'FAIL', or 'N/A'.

    Rules:
      - None score -> 'N/A' (e.g. ambiguous type consistency or 0 symbols excluded from scoring)
      - score >= 0.80 -> 'PASS' (unless has_risk_flags=True or is_ambiguous=True, which forces at least 'WARN')
      - score >= 0.50 -> 'WARN'
      - score < 0.50  -> 'FAIL'
    """
    if score is None:
        return "N/A"

    if score >= THRESHOLD_PASS:
        if has_risk_flags or is_ambiguous:
            return "WARN"
        return "PASS"
    elif score >= THRESHOLD_WARN:
        return "WARN"
    else:
        return "FAIL"
