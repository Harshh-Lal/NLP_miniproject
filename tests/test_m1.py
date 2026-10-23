"""Unit tests for M1 Demo Slice modules in CodeReviewer.NLP."""
import pytest
from code_reviewer.diff_parser import parse_diff
from code_reviewer.diff_type_inference import infer_diff_type
from code_reviewer.risk_scorer import score_risk
from code_reviewer.coverage_scorer import score_coverage
from code_reviewer.imperative_checker import check_imperative
from code_reviewer.aggregator import aggregate_scores
from code_reviewer.auditor import evaluate_type_consistency
from code_reviewer.status import compute_status, THRESHOLD_PASS, THRESHOLD_WARN


class TestDiffParser:
    def test_parse_diff_symbols_and_files(self):
        diff = """diff --git a/auth/session.py b/auth/session.py
--- a/auth/session.py
+++ b/auth/session.py
@@ -10,4 +10,8 @@ def validate_token(token):
+    if token.is_expired():
+        return False
"""
        res = parse_diff(diff)
        assert "auth/session.py" in res["files"]
        assert "validate_token" in res["symbols"]
        assert res["added_lines"] >= 2

    def test_hunk_header_preceding_definition_limitation(self):
        """Document known limitation: Git hunk headers show the nearest preceding definition,
        even if added lines are module-level or outside the function body.
        """
        diff = """diff --git a/services/queue.py b/services/queue.py
--- a/services/queue.py
+++ b/services/queue.py
@@ -15,4 +15,6 @@ def function_a():
     pass
+
+# Module-level addition outside function_a
+GLOBAL_QUEUE_CONFIG = {"retry": 3}
"""
        res = parse_diff(diff)
        # Git hunk header named function_a, so diff_parser extracts function_a
        assert "function_a" in res["symbols"]


class TestDiffTypeInference:
    def test_tests_only(self):
        inferred, _ = infer_diff_type(["tests/test_api.py", "tests/unit/test_auth.py"])
        assert inferred == "test"

    def test_docs_only(self):
        inferred, _ = infer_diff_type(["docs/guide.md", "README.md"])
        assert inferred == "docs"

    def test_chore_only(self):
        inferred, _ = infer_diff_type([".github/workflows/ci.yml", "Dockerfile"])
        assert inferred == "chore"

    def test_code_ambiguous(self):
        inferred, _ = infer_diff_type(["src/app.py", "auth/session.py"])
        assert inferred == "ambiguous"


class TestRiskScorer:
    def test_auth_risk_flag(self):
        res = score_risk(["auth/session.py"], "fixed minor display issue")
        assert res["score"] < 1.0
        assert "auth" in res["layers_triggered"]
        assert len(res["flags"]) > 0
        assert res["status"] == "WARN"

    def test_no_risk_normal_file(self):
        res = score_risk(["utils/string_helper.py"], "clean up formatting")
        assert res["score"] == 1.0
        assert len(res["flags"]) == 0
        assert res["status"] == "PASS"


class TestCoverageScorer:
    def test_partial_coverage(self):
        res = score_coverage(["validate_token", "login"], "fixed login issue")
        assert res["score"] == 0.5
        assert "login" in res["mentioned_symbols"]
        assert "validate_token" in res["omitted_symbols"]
        assert res["status"] == "WARN"

    def test_full_coverage(self):
        res = score_coverage(["login"], "update login flow")
        assert res["score"] == 1.0
        assert "login" in res["mentioned_symbols"]
        assert res["status"] == "PASS"


class TestImperativeChecker:
    def test_past_tense_fails_with_suggestion(self):
        res = check_imperative("fixed login issue")
        assert res["score"] == 0.0
        assert res["status"] == "FAIL"
        assert res["is_imperative"] is False
        assert res["first_word"] == "fixed"
        assert res["suggestion"] == "fix"

    def test_base_verb_passes(self):
        res = check_imperative("fix login issue")
        assert res["score"] == 1.0
        assert res["status"] == "PASS"
        assert res["is_imperative"] is True
        assert res["suggestion"] is None

    @pytest.mark.xfail(strict=True, reason="requires M2 POS tagger")
    def test_non_verb_opener_login_issue_fix(self):
        # "login issue fix" is a nominal phrase opener, not an imperative verb clause.
        # The M1 inflection checker mistakenly treats 'login' as a base verb (PASS).
        # Correctly detecting this non-verb opener as non-imperative requires M2 POS tagger.
        res = check_imperative("login issue fix")
        assert res["is_imperative"] is False

    @pytest.mark.xfail(strict=True, reason="requires M2 POS tagger")
    def test_non_verb_opener_bug_in_auth(self):
        # "bug in auth" is a nominal phrase opener, not an imperative sentence.
        # The M1 inflection checker mistakenly treats 'bug' as a base verb (PASS).
        # Correctly detecting this non-verb opener as non-imperative requires M2 POS tagger.
        res = check_imperative("bug in auth")
        assert res["is_imperative"] is False


class TestStatusScheme:
    def test_status_boundaries(self):
        assert compute_status(1.0) == "PASS"
        assert compute_status(0.80) == "PASS"
        assert compute_status(0.79) == "WARN"
        assert compute_status(0.50) == "WARN"
        assert compute_status(0.49) == "FAIL"
        assert compute_status(0.0) == "FAIL"
        assert compute_status(None) == "N/A"

    def test_flag_forces_warn_rule(self):
        # Even with high score >= 0.80, if risk flags are present, status must be at least WARN
        assert compute_status(1.0, has_risk_flags=True) == "WARN"
        assert compute_status(0.85, has_risk_flags=True) == "WARN"
        assert compute_status(0.55, has_risk_flags=True) == "WARN"
        # If score is already FAIL (< 0.50), it remains FAIL
        assert compute_status(0.40, has_risk_flags=True) == "FAIL"


class TestTypeConsistency:
    def test_ambiguous_type_returns_none_and_na(self):
        res = evaluate_type_consistency("fix bug", "ambiguous")
        assert res["score"] is None
        assert res["status"] == "N/A"
        assert "neutral (excluded from scoring)" in res["evidence"]


class TestAggregator:
    def test_aggregation_with_missing_scores(self):
        sub_scores = {
            "imperative_mood": 0.0,
            "coverage": 0.5,
            # risk_flags and type_consistency missing
        }
        res = aggregate_scores(sub_scores)
        assert 0.0 <= res["overall_score"] <= 1.0
        assert "risk_flags" in res["missing_sub_scores"]
        assert "type_consistency" in res["missing_sub_scores"]

    def test_reweights_when_score_is_none(self):
        # Fixture arithmetic check: imperative=0.0, coverage=0.5, risk=0.75, type=None
        sub_scores = {
            "imperative_mood": 0.0,
            "coverage": 0.50,
            "risk_flags": 0.75,
            "type_consistency": None,
        }
        res = aggregate_scores(sub_scores)
        assert res["overall_score"] == 0.41
        assert "type_consistency" in res["missing_sub_scores"]

    def test_never_crashes_on_empty_or_none(self):
        res = aggregate_scores({})
        assert res["overall_score"] == 0.0


# ---------------------------------------------------------------------------
# Item 8: Tests for cleanup-pass-2 items (1–4 + per-file summaries)
# ---------------------------------------------------------------------------

class TestCleanupPass2:
    """Tests verifying M1-cleanup-pass-2 requirements (Items 1-5)."""

    # --- Item 1: Coverage with 0 symbols ---

    def test_zero_symbols_returns_na_score(self):
        """score_coverage([]) must return score=None, status='N/A'."""
        res = score_coverage([], "fix login issue")
        assert res["score"] is None
        assert res["status"] == "N/A"
        assert res["evidence"] == "No symbols changed; coverage not applicable"

    def test_zero_symbols_excluded_from_aggregation(self):
        """A None coverage score must be treated as missing by the aggregator."""
        sub_scores = {
            "imperative_mood": 1.0,
            "coverage": None,          # None = excluded
            "risk_flags": 1.0,
            "type_consistency": 1.0,
        }
        res = aggregate_scores(sub_scores)
        # overall_score reweights over the 3 non-None scores -> must equal 1.0
        assert res["overall_score"] == 1.0
        assert "coverage" in res["missing_sub_scores"]

    def test_zero_symbols_audit_excludes_coverage(self):
        """audit_commit on a config-only diff (no def/class) must yield coverage N/A."""
        from code_reviewer.auditor import audit_commit
        diff = (
            "diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml\n"
            "--- a/.github/workflows/ci.yml\n"
            "+++ b/.github/workflows/ci.yml\n"
            "@@ -1,3 +1,4 @@\n"
            " name: CI\n"
            "+  pytest: true\n"
        )
        report = audit_commit("Add pytest to CI", diff)
        cov = report["scores"]["coverage"]
        assert cov["score"] is None
        assert cov["status"] == "N/A"

    # --- Item 2: Type consistency – CI commit must not FAIL ---

    def test_ci_commit_on_workflow_diff_not_fail(self):
        """'Add pytest to CI' on a .github/workflows diff must score >= 0.5 (PASS or WARN)."""
        from code_reviewer.auditor import audit_commit
        diff = (
            "diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml\n"
            "--- a/.github/workflows/ci.yml\n"
            "+++ b/.github/workflows/ci.yml\n"
            "@@ -1,3 +1,4 @@\n"
            " name: CI\n"
            "+  pytest: true\n"
        )
        report = audit_commit("Add pytest to CI", diff)
        tc = report["scores"]["type_consistency"]
        assert tc["status"] != "FAIL", (
            f"Expected PASS or WARN but got {tc['status']} "
            f"(score={tc['score']}, evidence={tc['evidence']})"
        )
        if tc["score"] is not None:
            assert tc["score"] >= 0.5

    def test_compatibility_matrix_partial_score(self):
        """feat vs chore must yield 0.5 from the matrix."""
        res = evaluate_type_consistency("add new endpoint", "chore")
        # message intent: feat (opening verb 'add'), diff: chore -> partial 0.5
        assert res["score"] == 0.5
        assert res["status"] in ("PASS", "WARN")

    # --- Item 3: Hunk-header symbols + test file exclusion ---

    def test_test_file_symbols_excluded_from_coverage(self):
        """A diff touching only a test file must yield coverage symbols = []."""
        diff = (
            "diff --git a/tests/test_auth.py b/tests/test_auth.py\n"
            "--- a/tests/test_auth.py\n"
            "+++ b/tests/test_auth.py\n"
            "@@ -20,6 +20,10 @@ def test_login():\n"
            "+def test_logout():\n"
            "+    pass\n"
        )
        res = parse_diff(diff)
        # test_logout is found on added lines, but file is a test file
        # -> coverage symbols must be empty
        assert res["symbols"] == [], f"Expected [], got {res['symbols']}"
        # all_symbols still has it
        assert "test_logout" in res["all_symbols"]
        # test_login must NOT be credited (was only in the hunk header, and we have +def)
        assert "test_login" not in res["symbols"]

    def test_hunk_header_fallback_when_no_def_on_added_lines(self):
        """When no def/class on +/- lines, hunk-header symbol is used as fallback."""
        diff = (
            "diff --git a/services/queue.py b/services/queue.py\n"
            "--- a/services/queue.py\n"
            "+++ b/services/queue.py\n"
            "@@ -15,4 +15,6 @@ def function_a():\n"
            "  pass\n"
            "+\n"
            "+# Module-level addition outside function_a\n"
            "+GLOBAL_QUEUE_CONFIG = {'retry': 3}\n"
        )
        res = parse_diff(diff)
        # No +def on added lines -> hunk header 'function_a' is the fallback
        assert "function_a" in res["symbols"]

    # --- Item 4: Degenerate input ---

    def test_empty_diff_returns_na(self):
        """audit_commit with empty diff must return overall_score=None, overall_status='N/A'."""
        from code_reviewer.auditor import audit_commit
        report = audit_commit("fix login", "")
        assert report["overall_score"] is None
        assert report["overall_status"] == "N/A"
        assert report["evidence"] == "No valid diff detected"

    def test_no_valid_files_in_diff_returns_na(self):
        """A diff with no recognisable file headers returns overall_score=None."""
        from code_reviewer.auditor import audit_commit
        report = audit_commit("fix login", "random text with no diff headers")
        assert report["overall_score"] is None
        assert report["overall_status"] == "N/A"

    # --- Item 5: Per-file added lines sum == total ---

    def test_per_file_added_sum_equals_total(self):
        """sum(f['added'] for f in file_summaries) must equal added_lines."""
        diff = (
            "diff --git a/auth/session.py b/auth/session.py\n"
            "--- a/auth/session.py\n"
            "+++ b/auth/session.py\n"
            "@@ -10,4 +10,8 @@ def validate_token(token):\n"
            "+    if token.is_expired():\n"
            "+        return False\n"
            "diff --git a/utils/helpers.py b/utils/helpers.py\n"
            "--- a/utils/helpers.py\n"
            "+++ b/utils/helpers.py\n"
            "@@ -1,2 +1,5 @@ def helper():\n"
            "+    x = 1\n"
            "+    y = 2\n"
            "+    return x + y\n"
        )
        res = parse_diff(diff)
        total_from_files = sum(f["added"] for f in res["file_summaries"])
        assert total_from_files == res["added_lines"], (
            f"Sum of per-file added ({total_from_files}) != total added ({res['added_lines']})"
        )
