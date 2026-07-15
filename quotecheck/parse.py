"""Find the quotes in a document that name the source that proves them.

A document makes two kinds of claim. Prose ("this is well known", "as everyone
agrees") needs a human. But a quotation is a promise of a sharper kind: these
exact words were written *there*, at that source, and you can go and look. It is
the part of a document that can be falsified by a machine -- so this falsifies
it.

The binding is an HTML comment, which renders as nothing, placed next to the
quote it vouches for:

    <!-- quote-check: "Power tends to corrupt" = ./sources/acton-1887.txt -->

The left of the `=` is the quoted words, in quotes -- straight or typographic.
The right is where they come from: a URL fetched over HTTP, or a path to a local
file. A source that cannot be checked automatically -- a paywall, a scanned PDF
-- is exempted in the open, with the reason written down:

    <!-- quote-check: "..." = https://example.com/paywalled skip=paywall -->

The comment is invisible in the rendered document, which matters: the document
is the product, and a tool that forces you to scar it to be checked is a tool
nobody uses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# <!-- quote-check: "the words" = SOURCE [skip=reason] [timeout=30] -->
# The quote may be delimited by straight or by typographic quotes, because a
# writer's editor supplies whichever it likes and the writer rarely notices.
DIRECTIVE = re.compile(
    r'<!--\s*quote-check:\s*'
    r'(?P<quote>"[^"]*"|“[^”]*”|„[^“]*“)'
    r'\s*=\s*(?P<rest>.*?)\s*-->')

# A run of backticks is a code span; the syntax shown inside one is an example,
# not a claim. `<!-- quote-check: ... -->` in prose about the syntax must not be
# mistaken for the thing it describes.
CODE_SPAN = re.compile(r"`[^`]*`")

# Trailing options on the right-hand side: `skip=paywall`, `timeout=30`. A URL
# or a file path never contains a space, so the source is the first token and
# these are whatever follows.
OPTION = re.compile(r"^(?P<key>skip|timeout)=(?P<value>\S+)$")


@dataclass
class Quote:
    """A quotation, and the source that is supposed to contain it."""
    line: int                  # 1-based line of the directive in the document
    quoted: str                # the words, delimiters stripped
    source: str                # a URL or a local path
    skip: bool = False
    skip_reason: str = ""
    timeout: float | None = None


def _strip_delimiters(raw: str) -> str:
    """Drop the outer quote marks, whichever pair the writer used."""
    return raw[1:-1]


def _split_rest(rest: str) -> tuple[str, bool, str, float | None]:
    """Separate the source from the trailing options.

    The source is the first whitespace-delimited token. Everything after it is
    an option -- `skip=reason`, `timeout=30` -- because neither a URL nor a path
    has a space in it, and so the first space is an unambiguous boundary.
    """
    tokens = rest.split()
    if not tokens:
        return "", False, "", None

    source = tokens[0]
    skip = False
    skip_reason = ""
    timeout: float | None = None

    for token in tokens[1:]:
        option = OPTION.match(token)
        if not option:
            continue
        if option.group("key") == "skip":
            skip = True
            skip_reason = option.group("value")
        elif option.group("key") == "timeout":
            try:
                timeout = float(option.group("value"))
            except ValueError:
                pass

    return source, skip, skip_reason, timeout


def parse(markdown: str) -> list[Quote]:
    """Extract every quotation that named the source proving it.

    Fenced code blocks and inline code spans are stepped over. A document that
    documents this syntax has to show the syntax, and a parser that could not
    tell an example from a claim would spend its life fetching example.com. This
    tool's own README does document itself, and the first draft of this function
    duly tried to verify the illustration -- which is at least the tool failing
    in the direction it was built to fail in.
    """
    quotes: list[Quote] = []
    inside_fence = False

    for number, line in enumerate(markdown.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue

        spans = [(found.start(), found.end())
                 for found in CODE_SPAN.finditer(line)]

        for found in DIRECTIVE.finditer(line):
            if any(start <= found.start() < end for start, end in spans):
                continue                 # the directive sits inside backticks

            source, skip, skip_reason, timeout = _split_rest(found.group("rest"))
            quotes.append(Quote(
                line=number,
                quoted=_strip_delimiters(found.group("quote")),
                source=source,
                skip=skip,
                skip_reason=skip_reason,
                timeout=timeout,
            ))

    return quotes
