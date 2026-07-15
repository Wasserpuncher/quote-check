"""Check that a document's quotations really appear in the sources they cite.

A quotation is a promise: these exact words are written *there*. It is the part
of a document a machine can falsify -- so this falsifies it. A quote is bound to
its source in an HTML comment that renders as nothing:

    <!-- quote-check: "Power tends to corrupt" = ./sources/acton-1887.txt -->

The words on the left must appear in the source on the right, once whitespace and
quote glyphs are normalised and any `...` in the quote is read as an omission.

    >>> from quotecheck import verify
    >>> verify("Power tends to corrupt",
    ...        "Power tends to corrupt and absolute power corrupts absolutely.").ok
    True
    >>> verify("Power always corrupts the soul",
    ...        "Power tends to corrupt and absolute power corrupts absolutely.").ok
    False
"""

from .check import Result, Violation, check, check_document
from .match import Verdict, normalize, segments, verify
from .parse import Quote, parse
from .sources import fetch, is_url, strip_html

__all__ = ["parse", "check", "check_document", "verify", "normalize",
           "segments", "fetch", "is_url", "strip_html",
           "Quote", "Result", "Violation", "Verdict"]
__version__ = "1.0.0"
