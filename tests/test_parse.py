"""Parsing: which parts of a document are checkable quotations, and which are
prose about quotations."""

from __future__ import annotations

import textwrap

from quotecheck import parse


def quotes(markdown: str):
    return parse(textwrap.dedent(markdown))


class TestBinding:
    def test_a_quote_names_the_source_that_proves_it(self):
        [quote] = quotes("""
            He wrote <!-- quote-check: "Power tends to corrupt" = ./acton.txt -->
            "Power tends to corrupt".
        """)
        assert quote.quoted == "Power tends to corrupt"
        assert quote.source == "./acton.txt"

    def test_a_url_source(self):
        [quote] = quotes(
            '<!-- quote-check: "the exact words" = https://example.com/page -->\n')
        assert quote.source == "https://example.com/page"

    def test_typographic_quotes_are_stripped_like_straight_ones(self):
        [quote] = quotes(
            '<!-- quote-check: “Power tends to corrupt” = ./acton.txt -->\n')
        assert quote.quoted == "Power tends to corrupt"

    def test_german_low_quotes(self):
        [quote] = quotes(
            '<!-- quote-check: „Macht korrumpiert“ = ./x.txt -->\n')
        assert quote.quoted == "Macht korrumpiert"

    def test_the_line_number_is_recorded(self):
        [quote] = quotes(
            '\n\n<!-- quote-check: "words" = ./s.txt -->\n')
        assert quote.line == 3


class TestOptions:
    def test_skip_with_a_reason(self):
        [quote] = quotes(
            '<!-- quote-check: "words" = https://paywalled skip=paywall -->\n')
        assert quote.skip and quote.skip_reason == "paywall"
        assert quote.source == "https://paywalled"

    def test_timeout(self):
        [quote] = quotes(
            '<!-- quote-check: "words" = https://slow.example timeout=30 -->\n')
        assert quote.timeout == 30

    def test_no_options_is_the_common_case(self):
        [quote] = quotes('<!-- quote-check: "words" = ./s.txt -->\n')
        assert not quote.skip and quote.timeout is None


class TestExamplesAreNotClaims:
    def test_a_directive_in_a_fenced_block_is_documentation(self):
        """A README documents this syntax by showing it. If the parser could not
        tell an example from a claim, the tool would spend its life fetching
        example.com."""
        assert quotes("""
            ```markdown
            <!-- quote-check: "the exact words" = https://source-url -->
            ```
        """) == []

    def test_a_directive_in_backticks_is_documentation_too(self):
        assert quotes(
            'Bind it like `<!-- quote-check: "x" = ./y.txt -->` in your prose.\n'
        ) == []

    def test_a_real_claim_beside_an_example_still_counts(self):
        found = quotes("""
            Write `<!-- quote-check: "x" = ./y.txt -->` to bind a quote.

            As Acton put it, <!-- quote-check: "Power tends to corrupt" = ./a.txt -->
            "Power tends to corrupt".
        """)
        assert len(found) == 1
        assert found[0].source == "./a.txt"
