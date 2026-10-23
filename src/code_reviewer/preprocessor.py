"""CO1: Text Pre-processing module for CodeReviewer.NLP.

Provides text normalization, camelCase/snake_case/kebab-case identifier splitting,
tokenization, domain-aware stop-word removal, stemming vs lemmatization (verb-first),
and commit-verb inflection analysis (imperative mood checking).

Every public function complies with the (result, evidence: dict) contract.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Tuple

import nltk
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.corpus import stopwords as nltk_stopwords

# ---------------------------------------------------------------------------
# Lazy-loaded singletons & resources
# ---------------------------------------------------------------------------
_STEMMER: PorterStemmer | None = None
_LEMMATIZER: WordNetLemmatizer | None = None
_STOPWORDS: set[str] | None = None


def _get_stemmer() -> PorterStemmer:
    global _STEMMER
    if _STEMMER is None:
        _STEMMER = PorterStemmer()
    return _STEMMER


def _get_lemmatizer() -> WordNetLemmatizer:
    global _LEMMATIZER
    if _LEMMATIZER is None:
        _LEMMATIZER = WordNetLemmatizer()
    return _LEMMATIZER


# Commit / software action verbs that must NOT be removed as stopwords
PRESERVED_VERBS: set[str] = {
    "add", "adds", "added", "adding",
    "fix", "fixes", "fixed", "fixing",
    "remove", "removes", "removed", "removing",
    "update", "updates", "updated", "updating",
    "delete", "deletes", "deleted", "deleting",
    "create", "creates", "created", "creating",
    "clean", "cleans", "cleaned", "cleaning",
    "refactor", "refactors", "refactored", "refactoring",
    "change", "changes", "changed", "changing",
    "improve", "improves", "improved", "improving",
    "bump", "bumps", "bumped", "bumping",
    "support", "supports", "supported", "supporting",
    "move", "moves", "moved", "moving",
    "handle", "handles", "handled", "handling",
    "allow", "allows", "allowed", "allowing",
    "prevent", "prevents", "prevented", "preventing",
    "ensure", "ensures", "ensured", "ensuring",
    "avoid", "avoids", "avoided", "avoiding",
    "make", "makes", "made", "making",
    "build", "builds", "built", "building",
    "test", "tests", "tested", "testing",
    "run", "runs", "ran", "running",
    "use", "uses", "used", "using",
    "set", "sets", "setting",
    "get", "gets", "getting",
    "no", "not",
}


def _get_stopwords() -> set[str]:
    global _STOPWORDS
    if _STOPWORDS is None:
        try:
            base_sw = set(nltk_stopwords.words("english"))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            base_sw = set(nltk_stopwords.words("english"))
        # Exclude software action verbs and critical negations
        _STOPWORDS = base_sw - PRESERVED_VERBS
    return _STOPWORDS


# ---------------------------------------------------------------------------
# Irregular verbs and Ambiguous verbs tables
# ---------------------------------------------------------------------------
# Ambiguous verbs: base form == past tense form == past participle.
# In commit messages (e.g. "set default timeout"), these are almost always
# intended in the imperative (base) mood, but in English morphology they are homographs.
AMBIGUOUS_BASE_PAST_VERBS: dict[str, str] = {
    "set": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "put": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "cut": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "split": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "hit": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "read": "Identical base and past spelling (/ri:d/ vs /rɛd/). Defaulted to base.",
    "let": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "cost": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "bid": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "cast": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "shut": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "spread": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "quit": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "hurt": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "reset": "Identical base and past form. Defaulted to imperative/base for commit messages.",
    "upsert": "Identical base and past form. Defaulted to imperative/base for commit messages.",
}

# Known irregular past forms -> their base lemma
IRREGULAR_PAST_TO_BASE: dict[str, str] = {
    "made": "make",
    "built": "build",
    "wrote": "write",
    "ran": "run",
    "did": "do",
    "held": "hold",
    "went": "go",
    "found": "find",
    "sent": "send",
    "bought": "buy",
    "brought": "bring",
    "caught": "catch",
    "chose": "choose",
    "drove": "drive",
    "fell": "fall",
    "flew": "fly",
    "forgot": "forget",
    "gave": "give",
    "grew": "grow",
    "knew": "know",
    "led": "lead",
    "lost": "lose",
    "met": "meet",
    "paid": "pay",
    "rose": "rise",
    "saw": "see",
    "shook": "shake",
    "shot": "shoot",
    "sold": "sell",
    "spoke": "speak",
    "spent": "spend",
    "stood": "stand",
    "stole": "steal",
    "took": "take",
    "taught": "teach",
    "told": "tell",
    "thought": "think",
    "threw": "throw",
    "wore": "wear",
    "won": "win",
    "began": "begin",
    "broke": "break",
    "came": "come",
    "drew": "draw",
    "drank": "drink",
    "ate": "eat",
    "froze": "freeze",
    "hid": "hide",
    "kept": "keep",
    "left": "leave",
    "slept": "sleep",
    "swam": "swim",
    "understood": "understand",
    "bound": "bind",
    "wound": "wind",
    "sought": "seek",
}

# Common software imperative verbs (to recognize valid base forms)
COMMON_IMPERATIVE_VERBS: set[str] = {
    "add", "fix", "remove", "update", "delete", "create", "clean", "refactor",
    "change", "improve", "bump", "support", "move", "handle", "allow", "prevent",
    "ensure", "avoid", "make", "build", "test", "run", "use", "implement",
    "enable", "disable", "enhance", "optimize", "simplify", "format", "upgrade",
    "downgrade", "rename", "revert", "merge", "sync", "drop", "extract",
    "initialize", "init", "configure", "setup", "install", "publish", "release",
    "expose", "hide", "validate", "check", "verify", "parse", "render", "load",
    "save", "write", "read", "show", "hide", "fetch", "send", "receive",
    "include", "exclude", "start", "stop", "restart", "attach", "detach",
    "align", "adjust", "correct", "replace", "deprecate", "isolate", "reorganize",
    "document", "doc", "rework", "polish", "migrate", "apply", "strip",
}


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
URL_REGEX = re.compile(r"https?://\S+|ftp://\S+|www\.\S+", re.IGNORECASE)

ISSUE_REF_REGEX = re.compile(
    r"(?i)\b(?:fixes|closes|resolves|refs)?\s*(?:#\d+|[A-Z][A-Z0-9]+-\d+|GH-\d+)\b",
)

TRAILER_REGEX = re.compile(
    r"(?mi)^\s*(?:Signed-off-by|Co-authored-by|Acked-by|Reviewed-by|Tested-by|"
    r"Reported-by|Helped-by|Suggested-by|Mentored-by|Cc|Refs|Change-Id|"
    r"Git-commit|Fixes|Closes|Resolves):\s*.*$",
)


# ---------------------------------------------------------------------------
# 1. Normalization
# ---------------------------------------------------------------------------
def normalize(text: str) -> Tuple[str, dict[str, Any]]:
    """Normalize commit text.

    Steps:
      1. Unicode NFC normalization
      2. Strip URLs (recorded in evidence)
      3. Strip Git trailers like Signed-off-by, Co-authored-by (recorded in evidence)
      4. Strip issue references like #123, GH-45, PROJ-10 (recorded in evidence)
      5. Lowercase
      6. Collapse whitespace

    Returns:
      (normalized_text, evidence_dict)
    """
    if not text:
        return "", {
            "original": text,
            "removed_urls": [],
            "removed_trailers": [],
            "removed_issues": [],
        }

    # 1. Unicode NFC
    nfc_text = unicodedata.normalize("NFC", text)

    # 2. Extract and strip URLs
    removed_urls = URL_REGEX.findall(nfc_text)
    clean_text = URL_REGEX.sub(" ", nfc_text)

    # 3. Extract and strip Git trailers
    removed_trailers = TRAILER_REGEX.findall(clean_text)
    clean_text = TRAILER_REGEX.sub(" ", clean_text)

    # 4. Extract and strip Issue references
    removed_issues = ISSUE_REF_REGEX.findall(clean_text)
    clean_text = ISSUE_REF_REGEX.sub(" ", clean_text)

    # 5. Lowercase
    clean_text = clean_text.lower()

    # 6. Collapse whitespace
    normalized = re.sub(r"\s+", " ", clean_text).strip()

    evidence = {
        "original": text,
        "removed_urls": removed_urls,
        "removed_trailers": removed_trailers,
        "removed_issues": removed_issues,
        "char_count_before": len(text),
        "char_count_after": len(normalized),
    }
    return normalized, evidence


# ---------------------------------------------------------------------------
# 2. Identifier Splitting
# ---------------------------------------------------------------------------
def split_identifiers(token: str) -> Tuple[list[str], dict[str, Any]]:
    """Split programming identifiers into constituent words.

    Handles:
      - camelCase: 'getUserById' -> ['get', 'user', 'by', 'id']
      - PascalCase: 'UserController' -> ['user', 'controller']
      - snake_case: 'get_user_by_id' -> ['get', 'user', 'by', 'id']
      - kebab-case: 'user-service-client' -> ['user', 'service', 'client']
      - digits: 'utf8String' -> ['utf', '8', 'string'], 'file123name' -> ['file', '123', 'name']
      - acronyms: 'HTTPServer' -> ['http', 'server'], 'OAuth2Token' -> ['oauth', '2', 'token']

    Keeps the original token in evidence.
    """
    if not token:
        return [], {"original": token, "was_split": False, "parts": []}

    original = token

    # First split on delimiters: _, -, ., /, \
    delimiters_split = re.split(r"[-_./\\]+", token)

    parts: list[str] = []
    for chunk in delimiters_split:
        if not chunk:
            continue

        # Split acronyms preceding words: HTTPServer -> HTTP Server, HTMLParser -> HTML Parser
        chunk = re.sub(r"([A-Z]{2,})([A-Z][a-z])", r"\1 \2", chunk)
        # Split lower/digit to upper: camelCase -> camel Case
        chunk = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", chunk)
        # Split letter to digit and digit to letter: utf8 -> utf 8, 8bit -> 8 bit
        chunk = re.sub(r"([a-zA-Z])([0-9])", r"\1 \2", chunk)
        chunk = re.sub(r"([0-9])([a-zA-Z])", r"\1 \2", chunk)

        sub_parts = [p.lower() for p in chunk.split() if p]
        parts.extend(sub_parts)

    was_split = (len(parts) > 1) or (len(parts) == 1 and parts[0] != original.lower())

    evidence = {
        "original": original,
        "was_split": was_split,
        "parts": parts,
    }
    return parts, evidence


# ---------------------------------------------------------------------------
# 3. Tokenize
# ---------------------------------------------------------------------------
def tokenize(text: str) -> Tuple[list[str], dict[str, Any]]:
    """Tokenize normalized text, splitting code identifiers into constituent tokens.

    Returns:
      (tokens, evidence_dict)
    """
    if not text:
        return [], {"raw_tokens": [], "token_count": 0, "identifier_splits": {}}

    # Split on whitespace and non-alphanumeric punctuation (preserving hyphens/underscores initially)
    raw_words = re.findall(r"[A-Za-z0-9_\-]+|[^\s\w]", text)

    tokens: list[str] = []
    splits_evidence: dict[str, list[str]] = {}

    for w in raw_words:
        # Ignore purely punctuation tokens
        if not re.search(r"[A-Za-z0-9]", w):
            continue

        sub_parts, split_ev = split_identifiers(w)
        if split_ev["was_split"]:
            splits_evidence[w] = sub_parts
        tokens.extend(sub_parts)

    evidence = {
        "raw_word_count": len(raw_words),
        "token_count": len(tokens),
        "identifier_splits": splits_evidence,
    }
    return tokens, evidence


# ---------------------------------------------------------------------------
# 4. Stop-word Removal
# ---------------------------------------------------------------------------
def remove_stopwords(tokens: list[str]) -> Tuple[list[str], dict[str, Any]]:
    """Remove standard English stopwords while strictly preserving commit action verbs.

    Returns:
      (filtered_tokens, evidence_dict)
    """
    sw = _get_stopwords()
    filtered: list[str] = []
    removed: list[str] = []

    for t in tokens:
        if t.lower() in sw:
            removed.append(t)
        else:
            filtered.append(t)

    evidence = {
        "original_count": len(tokens),
        "retained_count": len(filtered),
        "removed_stopwords": removed,
    }
    return filtered, evidence


# ---------------------------------------------------------------------------
# 5. Stemming (Porter)
# ---------------------------------------------------------------------------
def stem(tokens: list[str]) -> Tuple[list[str], dict[str, Any]]:
    """Stem tokens using the Porter Stemmer.

    Returns:
      (stemmed_tokens, evidence_dict)
    """
    stemmer = _get_stemmer()
    stemmed = [stemmer.stem(t.lower()) for t in tokens]
    stems_map = {t: s for t, s in zip(tokens, stemmed)}

    evidence = {
        "stemmer": "PorterStemmer",
        "stems_map": stems_map,
    }
    return stemmed, evidence


# ---------------------------------------------------------------------------
# 6. Lemmatization (WordNet verb-first)
# ---------------------------------------------------------------------------
def lemmatize(tokens: list[str]) -> Tuple[list[str], dict[str, Any]]:
    """Lemmatize tokens with WordNet, trying verb POS first.

    Trying verb POS first ensures past/participle forms like 'fixed' -> 'fix',
    'added' -> 'add', which standard noun-default lemmatization leaves unchanged.

    Returns:
      (lemmatized_tokens, evidence_dict)
    """
    lemmatizer = _get_lemmatizer()
    lemmatized: list[str] = []
    lemmas_map: dict[str, dict[str, str]] = {}

    for t in tokens:
        tok_lower = t.lower()
        # 1. Try verb
        lemma_v = lemmatizer.lemmatize(tok_lower, pos="v")
        if lemma_v != tok_lower:
            lemmatized.append(lemma_v)
            lemmas_map[t] = {"lemma": lemma_v, "pos": "v"}
            continue

        # 2. Try noun
        lemma_n = lemmatizer.lemmatize(tok_lower, pos="n")
        if lemma_n != tok_lower:
            lemmatized.append(lemma_n)
            lemmas_map[t] = {"lemma": lemma_n, "pos": "n"}
            continue

        # 3. Try adjective
        lemma_a = lemmatizer.lemmatize(tok_lower, pos="a")
        if lemma_a != tok_lower:
            lemmatized.append(lemma_a)
            lemmas_map[t] = {"lemma": lemma_a, "pos": "a"}
            continue

        # Default unchanged
        lemmatized.append(tok_lower)
        lemmas_map[t] = {"lemma": tok_lower, "pos": "default"}

    evidence = {
        "lemmatizer": "WordNetLemmatizer",
        "priority": "verb-first",
        "lemmas_map": lemmas_map,
    }
    return lemmatized, evidence


# ---------------------------------------------------------------------------
# 7. Stem vs Lemma Comparison
# ---------------------------------------------------------------------------
def compare_stem_lemma(tokens: list[str]) -> dict[str, dict[str, Any]]:
    """Produce side-by-side stem vs lemma comparison table for tokens.

    Returns:
      {token: {'stem': ..., 'lemma': ..., 'pos_used': ..., 'different': bool}}
    """
    stemmer = _get_stemmer()
    lemmatizer = _get_lemmatizer()

    results: dict[str, dict[str, Any]] = {}
    for t in sorted(set(tokens)):
        t_low = t.lower()
        s = stemmer.stem(t_low)

        # Verb-first lemma
        lv = lemmatizer.lemmatize(t_low, pos="v")
        if lv != t_low:
            lem = lv
            pos = "v"
        else:
            ln = lemmatizer.lemmatize(t_low, pos="n")
            if ln != t_low:
                lem = ln
                pos = "n"
            else:
                lem = t_low
                pos = "none"

        results[t] = {
            "stem": s,
            "lemma": lem,
            "pos_used": pos,
            "different": s != lem,
        }
    return results


# ---------------------------------------------------------------------------
# 8. Verb Inflection Analysis (Imperative Mood Check)
# ---------------------------------------------------------------------------
def analyze_verb_inflection(first_word: str) -> Tuple[str, dict[str, Any]]:
    """Analyze the grammatical inflection of the first word in a commit message.

    Classes returned:
      - 'base': Imperative/base verb form (e.g. 'fix', 'add', 'update', 'refactor')
      - 'past': Past tense (ends with -ed or known irregular: 'fixed', 'added', 'built')
      - 'gerund': Present participle / gerund (ends with -ing: 'fixing', 'adding')
      - 'third_person': 3rd person singular present (ends with -s/-es: 'fixes', 'adds')
      - 'non_verb' / 'unknown': Not identified as a typical action verb

    Ambiguity Note:
      Verbs like 'set', 'put', 'cut', 'split', 'hit', 'read', 'let', 'cost'
      have identical base and past forms. In Git commits, they are defaulted
      to 'base' (imperative mood), but flagged as ambiguous in evidence.

    Returns:
      (inflection_type, evidence_dict)
    """
    if not first_word:
        return "unknown", {"word": "", "ambiguous": False, "explanation": "Empty first word"}

    w = first_word.strip().lower()

    # 1. Check for homographic ambiguous base/past verbs
    if w in AMBIGUOUS_BASE_PAST_VERBS:
        return "base", {
            "word": w,
            "ambiguous": True,
            "explanation": AMBIGUOUS_BASE_PAST_VERBS[w],
            "detected_as": "base",
        }

    # 2. Check known irregular past forms
    if w in IRREGULAR_PAST_TO_BASE:
        base_form = IRREGULAR_PAST_TO_BASE[w]
        return "past", {
            "word": w,
            "ambiguous": False,
            "explanation": f"Irregular past tense of '{base_form}'",
            "base_lemma": base_form,
        }

    # 3. Regular past tense: ends with -ed (e.g. fixed, added, updated)
    if w.endswith("ed") and len(w) > 3:
        # Exclude non-verbs that end with ed (e.g. 'speed', 'seed', 'need', 'red', 'bed')
        if w not in {"speed", "seed", "need", "red", "bed", "bleed", "feed"}:
            return "past", {
                "word": w,
                "ambiguous": False,
                "explanation": "Regular past tense suffix -ed",
            }

    # 4. Present participle / gerund: ends with -ing (e.g. fixing, adding)
    if w.endswith("ing") and len(w) > 4:
        # Exclude non-verbs ending in ing like 'string', 'ring', 'spring', 'thing'
        if w not in {"string", "spring", "thing", "ring", "king", "wing"}:
            return "gerund", {
                "word": w,
                "ambiguous": False,
                "explanation": "Present participle / gerund suffix -ing",
            }

    # 5. Third-person singular present: ends with -s / -es (e.g. fixes, adds, updates)
    if (w.endswith("s") or w.endswith("es")) and len(w) > 3:
        # Avoid words ending in double 's' like 'pass', 'process', 'access', 'express'
        if not w.endswith("ss"):
            return "third_person", {
                "word": w,
                "ambiguous": False,
                "explanation": "Third-person singular present suffix -s/-es",
            }

    # 6. Check common imperative / base verbs
    if w in COMMON_IMPERATIVE_VERBS:
        return "base", {
            "word": w,
            "ambiguous": False,
            "explanation": "Recognized common commit imperative verb",
        }

    # 7. Fallback: check WordNet verb lemmatizer
    lemmatizer = _get_lemmatizer()
    lemma_v = lemmatizer.lemmatize(w, pos="v")
    if lemma_v == w:
        # If WordNet treats it as valid base verb form
        return "base", {
            "word": w,
            "ambiguous": False,
            "explanation": "WordNet recognized base verb",
        }

    return "unknown", {
        "word": w,
        "ambiguous": False,
        "explanation": "Not recognized as a typical action verb",
    }


# ---------------------------------------------------------------------------
# 9. Master Pipeline
# ---------------------------------------------------------------------------
def preprocess_pipeline(
    text: str,
    mode: str = "lemma",
) -> Tuple[list[str], dict[str, Any]]:
    """Full preprocessing pipeline orchestrator.

    Args:
      text: Raw commit message text
      mode: 'lemma' (WordNet verb-first), 'stem' (Porter), or 'none' (tokens only)

    Returns:
      (final_tokens, combined_evidence)
    """
    if mode not in {"lemma", "stem", "none"}:
        raise ValueError(f"Invalid mode '{mode}'. Choose 'lemma', 'stem', or 'none'.")

    # 1. Normalize
    norm_text, norm_ev = normalize(text)

    # 2. Extract first word for verb inflection analysis
    first_word_match = re.search(r"^[A-Za-z]+", norm_text)
    first_word = first_word_match.group(0) if first_word_match else ""
    inflection_type, inflection_ev = analyze_verb_inflection(first_word)

    # 3. Tokenize and split identifiers (use cased text with URLs/trailers/issues stripped to preserve camelCase)
    cased_clean = URL_REGEX.sub(" ", text)
    cased_clean = TRAILER_REGEX.sub(" ", cased_clean)
    cased_clean = ISSUE_REF_REGEX.sub(" ", cased_clean)
    tokens, tok_ev = tokenize(cased_clean)

    # 4. Remove stopwords
    filtered_tokens, sw_ev = remove_stopwords(tokens)

    # 5. Stem or Lemmatize according to mode
    if mode == "stem":
        final_tokens, red_ev = stem(filtered_tokens)
    elif mode == "lemma":
        final_tokens, red_ev = lemmatize(filtered_tokens)
    else:
        final_tokens = filtered_tokens
        red_ev = {"reduction": "none"}

    combined_evidence = {
        "raw_text": text,
        "mode": mode,
        "normalized_text": norm_text,
        "normalization": norm_ev,
        "first_word_inflection": {
            "first_word": first_word,
            "inflection": inflection_type,
            "evidence": inflection_ev,
        },
        "tokenization": tok_ev,
        "stopwords": sw_ev,
        "reduction": red_ev,
    }

    return final_tokens, combined_evidence
