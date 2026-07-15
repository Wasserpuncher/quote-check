"""Decide whether the quoted words are really in the source.

The hard part is not searching for a string. It is deciding *what is allowed to
differ* between the quote and the source, and that decision is the whole design.

Compare byte-for-byte and the tool is useless: a source wraps its lines at
column 70, the quote runs them together, and an honest, verbatim quotation fails
because a newline landed where a space was expected. Compare too loosely and the
tool is worthless: it blesses a fabrication because half the words happened to
turn up somewhere on the page.

So the rule is narrow and stated in one breath: **the quoted words must appear
in the source, in order, once whitespace and quote glyphs are normalised.** Three
things are allowed to differ, and only three:

    whitespace   A newline, a tab, a run of spaces in the source is the same as
                 a single space. Line-wrapping is the typesetter's, not a claim.

    quote glyphs A straight " and a typographic “ are the same character to a
                 reader and should be to the checker. Same for ' and ’, and for
                 the German „ “.

    ellipsis     `...` or `…` in the *quote* means "words omitted here". The
                 quote may be abridged -- as a fair quotation often is -- so long
                 as the parts that remain appear in the source in the order given.

Everything else is held exactly, including case. "Power" is not "power"; a
checker that shrugged at that would miss the quiet misquotation, which is the
kind that does the damage.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Typographic marks that a reader hears as an ordinary quote. The source and the
# quotation are each folded to the straight forms before they are compared, so a
# smart-quotes editor on one side and a plain-text file on the other still agree.
QUOTE_GLYPHS = {
    "“": '"', "”": '"', "„": '"', "‟": '"',  # “ ” „ ‟
    "‘": "'", "’": "'", "‚": "'", "‛": "'",  # ‘ ’ ‚ ‛
    "«": '"', "»": '"',                                # « »
}

# `...` or the single ellipsis character, with any spaces hugging it. In the
# quote this is the mark of an omission; the words on either side must survive,
# the gap between them need not.
ELLIPSIS = re.compile(r"\s*(?:\.\s*\.\s*\.|…)\s*")


def normalize(text: str) -> str:
    """Fold a piece of text to the form the comparison happens in.

    NFC first, so a composed é and a decomposed e-plus-accent are one string;
    then the quote glyphs; then every run of whitespace becomes a single space.
    What comes back is what both the source and the quotation are reduced to
    before either is searched for in the other.
    """
    text = unicodedata.normalize("NFC", text)
    for glyph, plain in QUOTE_GLYPHS.items():
        text = text.replace(glyph, plain)
    text = text.replace(" ", " ")             # non-breaking space
    return re.sub(r"\s+", " ", text).strip()


def segments(quoted: str) -> list[str]:
    """Split a quotation at its ellipses into the parts that must be found.

    `"the beginning ... the end"` becomes `["the beginning", "the end"]`: two
    fragments that must both appear in the source, and in that order. An empty
    fragment -- a quote that starts or ends with an ellipsis -- is dropped, so
    `"... corrupts absolutely"` asks only that the tail be present.
    """
    parts = [normalize(part) for part in ELLIPSIS.split(quoted)]
    return [part for part in parts if part]


@dataclass
class Verdict:
    """The outcome of checking one quotation against one source."""
    ok: bool
    reason: str = ""
    missing: str = ""          # the fragment the source did not contain, in order
    excerpt: str = ""          # what the source says where that fragment was sought


def _excerpt(haystack: str, needle: str, width: int = 90) -> str:
    """Show the reader what the source actually says where the quote failed.

    A bare "not found" makes the author go and read the whole source themselves,
    which is the work the tool was meant to save. So we locate the region: the
    longest opening run of words of the missing fragment that *does* occur, and
    return the source around it. If not even the first word is there, the quote
    is a stranger to this source, and we show where the source begins instead.
    """
    words = needle.split()
    for count in range(len(words), 0, -1):
        prefix = " ".join(words[:count])
        at = haystack.find(prefix)
        if at != -1:
            start = max(0, at - width // 3)
            end = min(len(haystack), at + len(prefix) + width)
            snippet = haystack[start:end]
            if start:
                snippet = "…" + snippet
            if end < len(haystack):
                snippet = snippet + "…"
            return snippet
    head = haystack[:width]
    return head + "…" if len(haystack) > width else head


def verify(quoted: str, source: str) -> Verdict:
    """Is every fragment of the quotation present in the source, in order?

    The search advances: once a fragment is found, the next is looked for only
    in what remains after it. That is what makes an abridged quote honest and a
    reordered one a lie. `"absolute power ... Power tends"` fails not because the
    words are absent -- they are both there -- but because the second is asked
    for after the first, and in the source it comes before.
    """
    hay = normalize(source)
    parts = segments(quoted)

    if not parts:
        # A quotation that is nothing but ellipses and spaces claims nothing.
        return Verdict(ok=True)

    position = 0
    for fragment in parts:
        found = hay.find(fragment, position)
        if found == -1:
            # Distinguish the two failures, because they mean different things
            # to the author. Absent anywhere: the source does not support this
            # quote at all -- the fabrication case. Present, but earlier than
            # the last fragment: the quote has been stitched out of order.
            if hay.find(fragment) != -1:
                reason = ("these words are in the source, but earlier than the "
                          "part quoted before them -- the quote reorders the source")
            else:
                reason = "these words are not in the source"
            return Verdict(ok=False, reason=reason, missing=fragment,
                           excerpt=_excerpt(hay, fragment))
        position = found + len(fragment)

    return Verdict(ok=True)
