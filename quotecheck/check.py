"""Check every quotation in a document against the source it named.

This ties the three parts together: parse the document for quotations bound to
sources, fetch each source, and verify the words are really there. A source is
fetched once even if two quotations cite it, because a page is a page and
downloading it twice only makes the check slower and the server crosser.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .match import Verdict, verify
from .parse import Quote, parse
from .sources import DEFAULT_TIMEOUT, fetch


@dataclass
class Violation:
    """A quotation its source did not support -- or a source that would not load."""
    line: int
    quoted: str
    source: str
    reason: str
    excerpt: str = ""


@dataclass
class Result:
    checked: int = 0
    skipped: int = 0
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


def check(quotes: list[Quote], root: str,
          timeout: float = DEFAULT_TIMEOUT) -> Result:
    """Verify a parsed document's quotations. `root` is where local paths resolve."""
    result = Result()
    cache: dict[str, tuple[str, str | None]] = {}

    for quote in quotes:
        if quote.skip:
            result.skipped += 1
            continue

        result.checked += 1

        if quote.source not in cache:
            cache[quote.source] = fetch(
                quote.source, root, quote.timeout or timeout)
        text, error = cache[quote.source]

        if error:
            result.violations.append(Violation(
                line=quote.line, quoted=quote.quoted, source=quote.source,
                reason=error))
            continue

        verdict: Verdict = verify(quote.quoted, text)
        if not verdict.ok:
            result.violations.append(Violation(
                line=quote.line, quoted=quote.quoted, source=quote.source,
                reason=verdict.reason, excerpt=verdict.excerpt))

    return result


def check_document(markdown: str, root: str,
                   timeout: float = DEFAULT_TIMEOUT) -> Result:
    """Parse and check a document's text in one call."""
    return check(parse(markdown), root=root, timeout=timeout)
