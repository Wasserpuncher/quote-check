"""Matching: what is allowed to differ between a quote and its source, and what
is not. This is the whole design, so it is where the tests are densest."""

from __future__ import annotations

import pytest

from quotecheck import normalize, segments, verify

SOURCE = (
    "Power tends to corrupt and absolute power corrupts absolutely.\n"
    "Great men are almost always bad men.")


class TestWhatMatches:
    def test_a_verbatim_quote_is_found(self):
        assert verify("Power tends to corrupt", SOURCE).ok

    def test_a_quote_spanning_the_whole_famous_line(self):
        assert verify(
            "Power tends to corrupt and absolute power corrupts absolutely",
            SOURCE).ok


class TestWhitespaceIsTolerated:
    def test_a_newline_in_the_source_is_a_space(self):
        """The source wraps `absolutely.\\nGreat` across a line break; the quote
        runs the two clauses together with a single space. Same words."""
        assert verify("absolutely. Great men", SOURCE).ok

    def test_runs_of_spaces_collapse(self):
        assert verify("Power   tends    to  corrupt", SOURCE).ok

    def test_a_quote_can_carry_its_own_line_breaks(self):
        assert verify("Power tends\nto corrupt", SOURCE).ok

    def test_normalize_folds_all_whitespace_to_single_spaces(self):
        assert normalize("a  b\t\nc") == "a b c"


class TestQuoteGlyphsAreTolerated:
    def test_typographic_double_quotes_inside_the_source(self):
        assert verify('he said "yes"', 'he said “yes” to them').ok

    def test_an_apostrophe_variant(self):
        assert verify("it's here", "well, it’s here now").ok

    def test_normalize_folds_curly_quotes(self):
        assert normalize("“a” ‘b’") == '"a" \'b\''


class TestEllipsisMeansOmission:
    def test_an_abridged_quote_passes_if_the_parts_are_in_order(self):
        assert verify("Power tends to corrupt ... corrupts absolutely", SOURCE).ok

    def test_the_unicode_ellipsis_works_too(self):
        assert verify("Power tends to corrupt … absolutely", SOURCE).ok

    def test_a_leading_ellipsis_asks_only_for_the_tail(self):
        assert verify("... corrupts absolutely", SOURCE).ok

    def test_segments_splits_on_both_spellings(self):
        assert segments("a ... b … c") == ["a", "b", "c"]

    def test_a_quote_that_is_only_an_ellipsis_claims_nothing(self):
        assert verify("...", SOURCE).ok


class TestOrderIsEnforced:
    def test_a_reordered_quote_fails_even_though_the_words_are_present(self):
        """`absolute power` and `Power tends` both occur, but the quote asks for
        the second after the first, and the source has them the other way. A
        checker that shrugged at this would bless a quote stitched from a source
        it inverts."""
        verdict = verify("absolute power corrupts ... Power tends to corrupt",
                         SOURCE)
        assert not verdict.ok
        assert "reorder" in verdict.reason

    def test_the_ordinary_direction_is_fine(self):
        assert verify("Power tends ... absolute power corrupts", SOURCE).ok


class TestWhatDoesNotMatch:
    def test_a_fabrication_is_caught(self):
        verdict = verify("Power always corrupts the human soul", SOURCE)
        assert not verdict.ok
        assert "not in the source" in verdict.reason

    def test_case_is_not_folded(self):
        """A quiet misquotation -- the kind that changes a meaning by a letter --
        must not slip through. 'power tends' is not what the source says."""
        assert not verify("power tends to corrupt and", SOURCE).ok

    def test_a_partial_match_still_fails(self):
        assert not verify("Power tends to enable", SOURCE).ok

    def test_the_failure_shows_what_the_source_says(self):
        """A bare 'not found' sends the author back to read the whole source.
        The excerpt is the region where the quote begins to diverge."""
        verdict = verify("Power tends to enrich", SOURCE)
        assert not verdict.ok
        assert "Power tends to corrupt" in verdict.excerpt


@pytest.mark.parametrize("quote,ok", [
    ("Power tends to corrupt", True),
    ("absolute power corrupts absolutely", True),
    ("Power tends to corrupt ... bad men", True),
    ("bad men ... Power tends", False),          # reordered
    ("Power corrupts absolutely", False),        # words dropped, no ellipsis
    ("almost always good men", False),           # fabricated
])
def test_table(quote, ok):
    assert verify(quote, SOURCE).ok == ok
