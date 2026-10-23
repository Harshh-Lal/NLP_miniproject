"""CLI Demonstration Script for CodeReviewer.NLP (M1 Slice).

Audits the standard fixture commit and prints an explainable console report.
Writes execution numbers to results/m1_fixture_audit.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from code_reviewer.auditor import audit_commit
from code_reviewer.status import compute_status

FIXTURE_MESSAGE = "fixed login issue"

FIXTURE_DIFF = """diff --git a/auth/session.py b/auth/session.py
index a1b2c3d..e4f5a6b 100644
--- a/auth/session.py
+++ b/auth/session.py
@@ -10,6 +10,10 @@ def validate_token(token):
     if not token:
         return False
+    if token.is_expired():
+        logger.warning("Token expired during validation")
+        raise TokenExpiredError("Token has expired")
     return True
diff --git a/controllers/user_controller.py b/controllers/user_controller.py
index 9876543..1234567 100644
--- a/controllers/user_controller.py
+++ b/controllers/user_controller.py
@@ -25,4 +25,8 @@ def login(request):
     user = authenticate(request.username, request.password)
     if not user:
         return Response("Unauthorized", status=401)
+    session.set_active(user.id)
+    return Response("OK")
"""


def format_score_badge(score: float | None, status: str | None = None, has_risk_flags: bool = False) -> str:
    if status is None:
        status = compute_status(score, has_risk_flags=has_risk_flags)
    if score is None:
        return f"[{status}] N/A"
    return f"[{status}] {score:.2f}"


def run_demo() -> dict:
    print("=" * 70)
    print("CodeReviewer.NLP — Consistency Audit Report (M1 Demo Slice)")
    print("=" * 70)
    print(f"Commit Message: \"{FIXTURE_MESSAGE}\"")
    print("-" * 70)

    report = audit_commit(FIXTURE_MESSAGE, FIXTURE_DIFF)

    scores = report["scores"]
    overall = report["overall_score"]
    overall_status = report["overall_status"]

    print(f"\nOVERALL CONSISTENCY SCORE: {format_score_badge(overall, status=overall_status)} / 1.00")
    print(f"Diff Inferred Type:       {report['diff_inferred_type']}")
    print(f"Message Stated Intent:    {report['message_intent']}")
    print("\nSUB-SCORE BREAKDOWN:")
    print("-" * 70)

    # 1. Imperative Mood
    imp = scores["imperative_mood"]
    print(f"1. Imperative Mood:        {format_score_badge(imp['score'], status=imp.get('status'))}")
    print(f"   First word:             '{imp['first_word']}' (inflection: {imp['inflection']})")
    if imp.get("suggestion"):
        print(f"   Suggested correction:   '{imp['suggestion']}'")
    print(f"   Evidence:               {imp['evidence']}")

    # 2. Symbol Coverage
    cov = scores["coverage"]
    print(f"\n2. Changed Symbol Coverage: {format_score_badge(cov['score'], status=cov.get('status'))}")
    print(f"   Mentioned in message:   {cov['mentioned_symbols']}")
    print(f"   Omitted symbols:        {cov['omitted_symbols']}")
    print(f"   Evidence:               {cov['evidence']}")

    # 3. Architectural Risk Flags
    risk = scores["risk_flags"]
    print(f"\n3. Architectural Risk:     {format_score_badge(risk['score'], status=risk.get('status'))}")
    print(f"   Sensitive files:        {risk['sensitive_files']}")
    print(f"   Layers triggered:       {risk['layers_triggered']}")
    if risk["flags"]:
        for flag in risk["flags"]:
            print(f"   [FLAG] {flag}")
    else:
        print("   No flags triggered.")

    # 4. Type Consistency
    tcons = scores["type_consistency"]
    print(f"\n4. Type Consistency:       {format_score_badge(tcons['score'], status=tcons.get('status'))}")
    print(f"   Evidence:               {tcons['evidence']}")

    print("\nDIFF DETAILS:")
    print("-" * 70)
    diff_sum = report["diff_summary"]
    print(f"Files Modified:  {len(diff_sum['files'])} ({', '.join(diff_sum['files'])})")
    print(f"Lines Changed:   +{diff_sum['added_lines']} / -{diff_sum['removed_lines']}")
    print(f"Symbols Found:   {diff_sum['symbols']}")

    # Save real output to results/m1_fixture_audit.json
    results_dir = ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "m1_fixture_audit.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("\n" + "=" * 70)
    print(f"Audit results written -> {out_file.relative_to(ROOT)}")
    print("=" * 70)

    return report


if __name__ == "__main__":
    run_demo()
