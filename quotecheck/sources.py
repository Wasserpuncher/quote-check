"""Fetch a source so its words can be checked against a quotation.

A source is either a local file or a URL. A local file is read from disk,
relative to the document that cited it -- because a path in a README means "next
to this README", which is where the reader would look for it too. A URL is
fetched over HTTP with a timeout, and if it comes back as HTML, the tags are
taken out, because a quotation is about the words on the page and not the markup
around them.

Nothing here is trusted blindly: a fetch that fails -- a 404, a refused
connection, a timeout -- is not silently treated as "the quote is fine". It is
an error, reported as such, so that a source which has moved or died is caught
rather than waved through. A source you genuinely cannot check from a machine --
a paywall, a scanned PDF -- is what `skip=` is for, declared in the open.
"""

from __future__ import annotations

import html
import os
import re
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 15.0

# A source is a URL if it names a scheme we fetch. Everything else is a path.
URL = re.compile(r"^https?://", re.IGNORECASE)

# Cut whole <script> and <style> elements before stripping tags: their contents
# are not prose and would otherwise pollute the text a quote is matched against.
SCRIPT_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.IGNORECASE | re.DOTALL)
TAG = re.compile(r"<[^>]+>")


def is_url(source: str) -> bool:
    return bool(URL.match(source))


def strip_html(body: str) -> str:
    """Reduce an HTML page to its readable text.

    Deliberately small: drop scripts and styles, turn tags into spaces, unescape
    entities. It is not a browser and does not pretend to be one -- but a quote
    lives in the text, and this is enough to find it there.
    """
    body = SCRIPT_STYLE.sub(" ", body)
    body = TAG.sub(" ", body)
    return html.unescape(body)


def _looks_like_html(source: str, content_type: str, body: str) -> bool:
    if "html" in content_type.lower():
        return True
    if source.lower().endswith((".html", ".htm")):
        return True
    head = body[:4096].lower()
    return "<html" in head or "<!doctype html" in head or "<body" in head


def fetch(source: str, root: str, timeout: float = DEFAULT_TIMEOUT
          ) -> tuple[str, str | None]:
    """Return the text of a source, or an explanation of why it could not.

    On success: (text, None). On failure: ("", reason). The caller decides what
    a failure means -- here it is only reported, never guessed at.
    """
    if is_url(source):
        return _fetch_url(source, timeout)
    return _read_file(source, root)


def _read_file(source: str, root: str) -> tuple[str, str | None]:
    path = source if os.path.isabs(source) else os.path.join(root, source)
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read(), None
    except FileNotFoundError:
        return "", f"no such file: {source}"
    except OSError as exc:
        return "", f"could not read {source}: {exc}"


def _fetch_url(source: str, timeout: float) -> tuple[str, str | None]:
    request = urllib.request.Request(
        source, headers={"User-Agent": "quote-check"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read()
    except urllib.error.HTTPError as exc:
        return "", f"{source} returned HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return "", f"could not fetch {source}: {exc.reason}"
    except (TimeoutError, OSError) as exc:
        return "", f"could not fetch {source}: {exc}"

    try:
        body = raw.decode(charset, errors="replace")
    except LookupError:
        body = raw.decode("utf-8", errors="replace")

    if _looks_like_html(source, content_type, body):
        body = strip_html(body)
    return body, None
