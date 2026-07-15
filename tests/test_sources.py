"""Fetching sources: telling a URL from a path, and reducing HTML to its words.

These do not touch the network. The network-dependent path -- actually fetching
a URL -- is exercised by the tool against real pages, not pinned in a unit test,
because a test that fails when a far-off server is slow is a test that teaches
you to ignore red. The logic that *can* be pinned without the network is here.
"""

from __future__ import annotations

from quotecheck import fetch, is_url, normalize, strip_html


class TestIsURL:
    def test_http_and_https_are_urls(self):
        assert is_url("http://example.com")
        assert is_url("https://example.com/page")

    def test_a_path_is_not_a_url(self):
        assert not is_url("./sources/acton.txt")
        assert not is_url("/etc/quotes.txt")
        assert not is_url("acton.txt")


class TestStripHTML:
    def test_tags_become_spaces(self):
        """A tag becomes whitespace, not nothing: `to<em>corrupt` must not weld
        into `tocorrupt`. The leftover spacing is what normalize (in verify)
        collapses, so the check sees one clean phrase."""
        stripped = strip_html("<p>Power tends to <em>corrupt</em></p>")
        assert normalize(stripped) == "Power tends to corrupt"

    def test_scripts_and_styles_are_dropped_whole(self):
        text = strip_html(
            "<style>p{color:red}</style><p>real words</p>"
            "<script>var x = 'not real words'</script>")
        assert "real words" in text
        assert "not real words" not in text
        assert "color" not in text

    def test_entities_are_unescaped(self):
        assert "Tom & Jerry" in strip_html("<p>Tom &amp; Jerry</p>")

    def test_a_quote_survives_the_markup_around_it(self):
        page = ('<html><body><blockquote>Power tends to corrupt and '
                'absolute&nbsp;power corrupts absolutely.</blockquote></body></html>')
        # strip_html leaves the &nbsp; as a character; normalize (in verify)
        # folds it to a space, which is why the quote is still found.
        from quotecheck import verify
        assert verify("Power tends to corrupt and absolute power corrupts absolutely",
                      strip_html(page)).ok


class TestFetchLocalFile:
    def test_a_missing_file_is_an_error_not_an_exception(self):
        text, error = fetch("does-not-exist.txt", root=".")
        assert text == ""
        assert error and "no such file" in error
