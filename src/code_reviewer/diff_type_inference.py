"""Diff type inference heuristic module for CodeReviewer.NLP.

Infers commit category purely from modified file path patterns:
- tests-only -> 'test'
- docs-only -> 'docs'
- config/CI-only -> 'chore'
- else -> 'ambiguous'
"""
from __future__ import annotations

import re
from typing import Any, Tuple

TEST_PATTERNS = [
    re.compile(r"(?:^|/)(?:tests?|spec|specs|__tests__|testing)/", re.IGNORECASE),
    re.compile(r"[_.-]tests?\.[a-zA-Z0-9]+$", re.IGNORECASE),
    re.compile(r"[_.-]spec\.[a-zA-Z0-9]+$", re.IGNORECASE),
    re.compile(r"^test_[^/]+\.py$", re.IGNORECASE),
]

DOCS_PATTERNS = [
    re.compile(r"(?:^|/)(?:docs?|documentation)/", re.IGNORECASE),
    re.compile(r"\.(?:md|markdown|rst|txt|adoc)$", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:README|LICENSE|CHANGELOG|AUTHORS|CONTRIBUTING)(?:\.[a-zA-Z]+)?$", re.IGNORECASE),
]

CHORE_PATTERNS = [
    re.compile(r"(?:^|/)\.(?:github|gitlab|circleci)/", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:Dockerfile|docker-compose|Makefile|Vagrantfile)$", re.IGNORECASE),
    re.compile(r"\.(?:ya?ml|toml|ini|cfg|env|editorconfig)$", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:requirements[^/]*\.txt|setup\.cfg|setup\.py|pyproject\.toml|package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|\.gitignore)$", re.IGNORECASE),
]


def _matches_any(path: str, patterns: list[re.Pattern]) -> bool:
    normalized = path.replace("\\", "/")
    return any(p.search(normalized) is not None for p in patterns)


def infer_diff_type(files: list[str]) -> Tuple[str, dict[str, Any]]:
    """Infer the commit type purely from file paths.

    Returns:
      (inferred_type, evidence_dict)
    """
    if not files:
        return "ambiguous", {
            "files": [],
            "reason": "No files provided in diff.",
            "is_tests_only": False,
            "is_docs_only": False,
            "is_chore_only": False,
        }

    is_all_tests = all(_matches_any(f, TEST_PATTERNS) for f in files)
    is_all_docs = all(_matches_any(f, DOCS_PATTERNS) for f in files)
    is_all_chore = all(_matches_any(f, CHORE_PATTERNS) for f in files)

    if is_all_tests:
        inferred = "test"
        reason = f"All {len(files)} modified file(s) are test files."
    elif is_all_docs:
        inferred = "docs"
        reason = f"All {len(files)} modified file(s) are documentation files."
    elif is_all_chore:
        inferred = "chore"
        reason = f"All {len(files)} modified file(s) are configuration/CI/build files."
    else:
        inferred = "ambiguous"
        reason = "Files touch implementation code or mixed categories."

    evidence = {
        "files": files,
        "inferred_type": inferred,
        "reason": reason,
        "is_tests_only": is_all_tests,
        "is_docs_only": is_all_docs,
        "is_chore_only": is_all_chore,
    }
    return inferred, evidence
