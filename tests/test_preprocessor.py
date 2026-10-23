"""Tests for CO1: Text Pre-processing (src/code_reviewer/preprocessor.py)."""
import pytest
from code_reviewer.preprocessor import (
    normalize,
    split_identifiers,
    tokenize,
    remove_stopwords,
    stem,
    lemmatize,
    compare_stem_lemma,
    analyze_verb_inflection,
    preprocess_pipeline,
)


class TestNormalize:
    def test_unicode_and_lowercase(self):
        text = "FIX: Café and naïve RESUME"
        norm, ev = normalize(text)
        assert "café" in norm
        assert "naïve" in norm
        assert norm == norm.lower()
        assert ev["original"] == text

    def test_strip_urls(self):
        text = "Fix authentication bug see https://github.com/org/repo/issues/404 for details"
        norm, ev = normalize(text)
        assert "https://" not in norm
        assert "issues/404" not in norm
        assert len(ev["removed_urls"]) == 1
        assert "https://github.com/org/repo/issues/404" in ev["removed_urls"][0]

    def test_strip_git_trailers(self):
        text = (
            "Add oauth endpoint\n\n"
            "Signed-off-by: Alice Developer <alice@example.com>\n"
            "Co-authored-by: Bob Coder <bob@example.com>\n"
            "Reviewed-by: Carol Lead <carol@example.com>"
        )
        norm, ev = normalize(text)
        assert norm == "add oauth endpoint"
        assert len(ev["removed_trailers"]) == 3
        assert any("alice@example.com" in t for t in ev["removed_trailers"])

    def test_strip_issue_refs(self):
        text = "Fix crash when parsing null payload (fixes #1234, GH-56, PROJ-89)"
        norm, ev = normalize(text)
        assert "#1234" not in norm
        assert "GH-56" not in norm
        assert "PROJ-89" not in norm
        assert len(ev["removed_issues"]) >= 3

    def test_collapse_whitespace(self):
        text = "  Update   docs   \n\n   with   new   examples\t\t"
        norm, _ = normalize(text)
        assert norm == "update docs with new examples"


class TestIdentifierSplitting:
    def test_camel_and_pascal_case(self):
        parts_camel, ev1 = split_identifiers("getUserById")
        assert parts_camel == ["get", "user", "by", "id"]
        assert ev1["was_split"] is True
        assert ev1["original"] == "getUserById"

        parts_pascal, ev2 = split_identifiers("UserController")
        assert parts_pascal == ["user", "controller"]
        assert ev2["was_split"] is True

    def test_snake_and_kebab_case(self):
        parts_snake, _ = split_identifiers("calculate_tax_rate")
        assert parts_snake == ["calculate", "tax", "rate"]

        parts_kebab, _ = split_identifiers("user-service-client")
        assert parts_kebab == ["user", "service", "client"]

    def test_digits_and_acronyms(self):
        parts_acronym, _ = split_identifiers("HTTPServer")
        assert parts_acronym == ["http", "server"]

        parts_oauth, _ = split_identifiers("OAuth2Token")
        assert parts_oauth == ["oauth", "2", "token"]

        parts_utf, _ = split_identifiers("utf8Encoding")
        assert parts_utf == ["utf", "8", "encoding"]

        parts_file, _ = split_identifiers("file123name")
        assert parts_file == ["file", "123", "name"]

    def test_plain_word_not_split(self):
        parts, ev = split_identifiers("database")
        assert parts == ["database"]
        assert ev["was_split"] is False


class TestTokenize:
    def test_tokenize_with_identifiers(self):
        text = "Refactor parseHTTPResponse to handle null_pointer in ApiClient"
        tokens, ev = tokenize(text)
        assert "parse" in tokens
        assert "http" in tokens
        assert "response" in tokens
        assert "null" in tokens
        assert "pointer" in tokens
        assert "api" in tokens
        assert "client" in tokens
        assert ev["token_count"] == len(tokens)


class TestStopwordRemoval:
    def test_standard_stopwords_removed(self):
        tokens = ["this", "is", "a", "simple", "test", "of", "the", "pipeline"]
        filtered, ev = remove_stopwords(tokens)
        assert "this" not in filtered
        assert "is" not in filtered
        assert "a" not in filtered
        assert "the" not in filtered
        assert "pipeline" in filtered
        assert "test" in filtered
        assert len(ev["removed_stopwords"]) > 0

    def test_action_verbs_preserved(self):
        critical_verbs = ["add", "fix", "remove", "update", "delete", "create", "refactor", "clean"]
        filtered, ev = remove_stopwords(critical_verbs)
        for v in critical_verbs:
            assert v in filtered, f"Action verb '{v}' should not be removed as a stopword!"
        assert len(ev["removed_stopwords"]) == 0


class TestStemAndLemma:
    def test_stemming(self):
        tokens = ["fixing", "fixed", "fixes", "connective", "organizing"]
        stemmed, ev = stem(tokens)
        assert stemmed[0] == "fix"
        assert stemmed[1] == "fix"
        assert stemmed[2] == "fix"
        assert ev["stemmer"] == "PorterStemmer"

    def test_lemmatization_verb_first(self):
        # Crucial test: standard noun-default leaves 'fixed' as 'fixed'.
        # Verb-first lemmatizer MUST reduce 'fixed' -> 'fix'
        tokens = ["fixed", "fixes", "fixing", "added", "updating"]
        lemmatized, ev = lemmatize(tokens)
        assert lemmatized[0] == "fix", f"Expected 'fix', got '{lemmatized[0]}'"
        assert lemmatized[1] == "fix"
        assert lemmatized[2] == "fix"
        assert lemmatized[3] == "add"
        assert lemmatized[4] == "update"
        assert ev["lemmas_map"]["fixed"]["pos"] == "v"

    def test_compare_stem_lemma(self):
        tokens = ["organization", "fixed", "database", "indices"]
        comparison = compare_stem_lemma(tokens)
        assert "organization" in comparison
        assert comparison["organization"]["stem"] == "organ"
        assert comparison["organization"]["lemma"] == "organization"
        assert comparison["organization"]["different"] is True


class TestVerbInflection:
    def test_imperative_base_form(self):
        for verb in ["fix", "add", "update", "remove", "refactor", "create", "implement"]:
            inflection, ev = analyze_verb_inflection(verb)
            assert inflection == "base", f"'{verb}' should be classified as base/imperative, got '{inflection}'"
            assert ev["ambiguous"] is False

    def test_past_tense_regular_and_irregular(self):
        for past_verb in ["fixed", "added", "updated", "made", "built", "wrote", "ran", "held"]:
            inflection, ev = analyze_verb_inflection(past_verb)
            assert inflection == "past", f"'{past_verb}' should be classified as past, got '{inflection}'"

    def test_gerund_form(self):
        for gerund in ["fixing", "adding", "updating", "refactoring", "cleaning"]:
            inflection, ev = analyze_verb_inflection(gerund)
            assert inflection == "gerund", f"'{gerund}' should be classified as gerund, got '{inflection}'"

    def test_third_person_form(self):
        for third in ["fixes", "adds", "updates", "removes", "creates"]:
            inflection, ev = analyze_verb_inflection(third)
            assert inflection == "third_person", f"'{third}' should be third-person, got '{inflection}'"

    def test_ambiguous_verbs(self):
        for amb in ["set", "put", "cut", "split", "hit", "read"]:
            inflection, ev = analyze_verb_inflection(amb)
            assert inflection == "base", f"'{amb}' should default to base/imperative"
            assert ev["ambiguous"] is True, f"'{amb}' should be flagged as ambiguous"
            assert "Identical base and past" in ev["explanation"] or "spelling" in ev["explanation"]


class TestPreprocessPipeline:
    def test_pipeline_lemma_mode(self):
        raw = "Fixed bug in parseJsonPayload() to prevent crash on null #123\n\nSigned-off-by: Dev <d@e.com>"
        tokens, ev = preprocess_pipeline(raw, mode="lemma")
        assert "fix" in tokens
        assert "bug" in tokens
        assert "json" in tokens
        assert "payload" in tokens
        assert "prevent" in tokens
        assert "crash" in tokens
        assert "null" in tokens
        assert "#123" not in tokens
        assert ev["first_word_inflection"]["first_word"] == "fixed"
        assert ev["first_word_inflection"]["inflection"] == "past"
        assert ev["mode"] == "lemma"

    def test_pipeline_stem_mode(self):
        raw = "Update documentation for API endpoints"
        tokens, ev = preprocess_pipeline(raw, mode="stem")
        assert ev["mode"] == "stem"
        assert "updat" in tokens or "update" in tokens

    def test_pipeline_invalid_mode(self):
        with pytest.raises(ValueError):
            preprocess_pipeline("some text", mode="invalid_mode")
