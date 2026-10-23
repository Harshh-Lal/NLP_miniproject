"""Diff parser module for CodeReviewer.NLP (Paste Mode).

Parses unified git diff text, extracting modified files, added/removed line metrics,
per-file summaries, and function/class symbols.

Key Rules:
  1. Hunk-header symbols are used only when NO def/class is found on added/removed lines.
  2. Symbols from test files are ignored for coverage.
  3. Per-file summaries accurately record added, removed, and symbols, with sum(added) == total_added.
"""
from __future__ import annotations

import re
from typing import Any

# Regex to detect function/class definitions on +/- lines
LINE_DEF_REGEX = re.compile(
    r"^[+-]\s*(?:async\s+def|def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    re.MULTILINE,
)

# Regex to detect symbols in hunk section header
HUNK_HEADER_SYMBOL_REGEX = re.compile(
    r"(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
)

# Test file path detector
TEST_FILE_PATTERN = re.compile(
    r"(?:^|[/\\])(?:tests?|__tests__)[/\\]|(?:\b|_)test_[^/\\]+\.py$|[^/\\]+_test\.py$",
    re.IGNORECASE,
)


def is_test_file(path: str) -> bool:
    """Return True if path points to a test file."""
    norm = path.replace("\\", "/").strip()
    return bool(TEST_FILE_PATTERN.search(norm))


def parse_diff(diff_text: str) -> dict[str, Any]:
    """Parse unified diff text and extract structural metadata and code symbols.

    Returns:
      {
        "files": list[str],
        "added_lines": int,
        "removed_lines": int,
        "symbols": list[str],            # Non-test symbols used for coverage
        "all_symbols": list[str],        # All symbols including test symbols
        "file_summaries": list[dict],    # [{path, added, removed, symbols}]
        "raw_hunks_count": int,
      }
    """
    if not diff_text or not diff_text.strip():
        return {
            "files": [],
            "added_lines": 0,
            "removed_lines": 0,
            "symbols": [],
            "all_symbols": [],
            "file_summaries": [],
            "raw_hunks_count": 0,
        }

    # Split into per-file chunks
    raw_chunks = re.split(r"(?m)(?=^diff --git )", diff_text.strip())
    file_chunks: list[str] = []
    for rc in raw_chunks:
        if not rc.strip():
            continue
        sub_chunks = re.split(r"(?m)(?=^--- [ab]/)", rc)
        for sc in sub_chunks:
            if sc.strip():
                file_chunks.append(sc)

    if not file_chunks:
        file_chunks = [diff_text]

    files: list[str] = []
    total_added = 0
    total_removed = 0
    file_summaries: list[dict[str, Any]] = []
    coverage_symbols: set[str] = set()
    all_symbols: set[str] = set()
    total_hunks = 0

    for chunk in file_chunks:
        # Extract filename
        m_plus = re.search(r"^\+\+\+\s+[ab]/(.*)", chunk, re.MULTILINE)
        m_diff = re.search(r"^diff --git\s+[ab]/(.*?)\s+[ab]/(.*)", chunk, re.MULTILINE)
        m_minus = re.search(r"^---\s+[ab]/(.*)", chunk, re.MULTILINE)

        if m_plus and m_plus.group(1).strip() != "/dev/null":
            fname = m_plus.group(1).strip()
        elif m_diff:
            fname = m_diff.group(2).strip() or m_diff.group(1).strip()
        elif m_minus and m_minus.group(1).strip() != "/dev/null":
            fname = m_minus.group(1).strip()
        else:
            m_any = re.search(r"(?:---|\+\+\+)\s+([^\s\n]+)", chunk)
            if m_any:
                fname = re.sub(r"^[ab]/", "", m_any.group(1).strip())
            else:
                continue

        fname = re.sub(r"\t.*$", "", fname).strip()
        if not fname or fname == "/dev/null":
            continue

        if fname not in files:
            files.append(fname)

        lines = chunk.splitlines()
        added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
        total_added += added
        total_removed += removed

        hunk_headers = re.findall(r"@@.*?@@(.*)", chunk)
        total_hunks += len(hunk_headers)

        # Symbol extraction:
        # Rule 1: Check added (+) and removed (-) lines for def / class
        line_symbols = LINE_DEF_REGEX.findall(chunk)
        file_symbols: set[str] = set()

        if line_symbols:
            # Found on added/removed lines -> ONLY use these, ignore hunk-header symbols!
            file_symbols.update(line_symbols)
        else:
            # NO def/class on added/removed lines -> use hunk-header symbols
            for hh in hunk_headers:
                m_sym = HUNK_HEADER_SYMBOL_REGEX.search(hh)
                if m_sym:
                    file_symbols.add(m_sym.group(1))

        all_symbols.update(file_symbols)

        # Rule 2: Ignore symbols from test files for coverage
        if not is_test_file(fname):
            coverage_symbols.update(file_symbols)

        file_summaries.append({
            "path": fname,
            "added": added,
            "removed": removed,
            "symbols": sorted(file_symbols),
        })

    return {
        "files": files,
        "added_lines": total_added,
        "removed_lines": total_removed,
        "symbols": sorted(coverage_symbols),
        "all_symbols": sorted(all_symbols),
        "file_summaries": file_summaries,
        "raw_hunks_count": total_hunks,
    }
