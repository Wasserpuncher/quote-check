"""The reason this tool exists.

On Kai's own site, a quotation was once attributed to Lord Acton that Lord Acton
never wrote -- a fabrication nobody had checked against the source. quote-check
is the tool that would have caught it. So the first test is that story, pinned:

    the real words, in the real source        -> verified
    the fabricated words, in the real source   -> caught

The source is the genuine one -- Acton's letter to Bishop Mandell Creighton of
5 April 1887 -- stored verbatim in tests/sources/acton-letter.txt, with the
line-wrapping it has in print, so the check has to survive real whitespace and
not a version smoothed out to make the test pass.

The line that is really Acton's, confirmed against the source:

    "Power tends to corrupt and absolute power corrupts absolutely."
     -- Lord Acton, letter to Mandell Creighton, 5 April 1887.
"""

from __future__ import annotations

import os
import textwrap

from quotecheck import check, parse, verify

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(HERE, "sources")
LETTER = os.path.join(SOURCES, "acton-letter.txt")


def _letter() -> str:
    with open(LETTER, encoding="utf-8") as handle:
        return handle.read()


class TestTheRealQuote:
    def test_the_famous_line_is_really_in_the_letter(self):
        """The positive case. These are Acton's actual words, and the source is
        his actual letter. It must pass, or the tool cries wolf at the truth --
        which is the failure that gets a checker switched off."""
        assert verify(
            "Power tends to corrupt and absolute power corrupts absolutely",
            _letter()).ok

    def test_the_line_survives_the_source_being_wrapped(self):
        """In the file, `absolute` and `power corrupts` fall on two different
        lines. A tool that demanded the newline be a newline would fail an honest
        quotation of a typeset source -- so whitespace is normalised, and this
        passes."""
        assert verify("absolute power corrupts absolutely", _letter()).ok

    def test_an_abridged_but_faithful_quote_passes(self):
        assert verify(
            "I cannot accept your canon ... Power tends to corrupt", _letter()).ok


class TestTheFabrication:
    def test_the_invented_quote_is_caught(self):
        """The negative case, and the whole point. This sentence is written in
        Acton's cadence and attributed to him across the web, but it is not in
        his letter, and no rewording makes it appear there. It MUST be caught --
        if this ever passes, the tool has failed at the one job it was built for,
        and the build is right to go red."""
        fabricated = "Power corrupts the mind, and absolute power corrupts the soul"
        verdict = verify(fabricated, _letter())
        assert not verdict.ok
        assert "not in the source" in verdict.reason

    def test_a_genuine_quote_by_the_wrong_author_is_caught(self):
        """Misattribution is the same failure wearing a disguise. William Pitt
        the Elder really did say 'Unlimited power is apt to corrupt the minds of
        those who possess it' -- but Acton did not, and bound to Acton's letter
        it fails, because the words are not there."""
        pitt = "Unlimited power is apt to corrupt the minds of those who possess it"
        assert not verify(pitt, _letter()).ok


class TestEndToEndThroughADocument:
    def test_a_document_that_quotes_acton_honestly_passes(self):
        markdown = textwrap.dedent("""
            Acton warned that <!-- quote-check: "Power tends to corrupt" = acton-letter.txt -->
            "Power tends to corrupt".
        """)
        result = check(parse(markdown), root=SOURCES)
        assert result.ok
        assert result.checked == 1

    def test_a_document_that_fabricates_a_quote_fails(self):
        markdown = textwrap.dedent("""
            Acton supposedly said <!-- quote-check: "Power corrupts the soul entirely" = acton-letter.txt -->
            "Power corrupts the soul entirely".
        """)
        result = check(parse(markdown), root=SOURCES)
        assert not result.ok
        assert result.violations[0].line > 0
        assert "acton-letter.txt" in result.violations[0].source

    def test_a_skipped_quote_is_not_checked(self):
        markdown = (
            'Behind a paywall: <!-- quote-check: "something unverifiable" '
            '= https://example.com/x skip=paywall -->\n')
        result = check(parse(markdown), root=SOURCES)
        assert result.ok
        assert result.skipped == 1 and result.checked == 0


class TestASourceThatWillNotLoad:
    def test_a_missing_local_source_is_a_violation_not_a_pass(self):
        """A citation to a source that is not there cannot be verified, and
        'cannot verify' is not 'fine'. It is reported, so a dead citation is
        caught rather than waved through."""
        markdown = ('<!-- quote-check: "anything" = ./no-such-file.txt -->\n')
        result = check(parse(markdown), root=SOURCES)
        assert not result.ok
        assert "no such file" in result.violations[0].reason
