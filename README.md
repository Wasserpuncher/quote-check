# quote-check

**Your document puts words in someone's mouth. This checks they said them.**

On my own website there was a sentence in quotation marks, attributed to Lord
Acton, that Lord Acton never wrote. It was not a paraphrase and it was not a
mistake of memory that a reader could forgive. It was a fabrication in his
cadence, sitting inside quotation marks, with his name under it — and it had been
there long enough for me to have read the page a dozen times without once going
to the letter it claimed to come from.

Nobody had checked it against the source. That is the whole failure, and it is a
small one to describe and an easy one to commit: a quotation *looks* checked. The
quotation marks are the claim, and the claim is that somewhere there is a source
with these exact words in it. Almost nobody opens the source, because opening the
source is work and the marks already look like the work was done.

So now a machine opens the source.

<!-- readme-check: skip=illustration -->
```console
$ quote-check
✗ README.md:42  "Power corrupts the mind, and absolute power the soul"
  = ./sources/acton-creighton-1887.txt
  these words are not in the source
  --- you quoted
  | Power corrupts the mind, and absolute power the soul
  --- the source says
  | …the power increases. Power tends to corrupt and absolute power corrupts absolutely. Great men…

1 of 3 quote(s) unverified, 0 skipped
```

It is the twin of [readme-check](https://github.com/Wasserpuncher/readme-check),
which binds the numbers in a README to the commands that produce them. This binds
the **quotations** in a document to the **sources** that contain them. The same
idea underneath: a claim a reader could check in thirty seconds should be checked
in four by a machine that does not get tired and does not want the quote to be
real.

## How you bind a quote to its source

Next to the quote, in an HTML comment that renders as nothing, name the source:

```markdown
As Acton warned,
<!-- quote-check: "Power tends to corrupt and absolute power corrupts absolutely" = ./sources/acton-creighton-1887.txt -->
"Power tends to corrupt and absolute power corrupts absolutely."
```

The words on the left of the `=` must appear in the source on the right. The
source is either a **local file** — read from beside the document — or a **URL**,
fetched over HTTP and, if it comes back as HTML, reduced to its text before the
search. The comment is invisible in the rendered document, which is the point: the
document is the product, and a tool that made you scar it to be checked is a tool
nobody would use.

## What is allowed to differ

A quotation is not a byte-for-byte copy of its source, and a tool that demanded
one would fail every honest quote ever typed. Three things, and only three, are
allowed to differ.

**Whitespace.** A source wraps its lines; a quote runs them together. In the Acton
letter the words `absolute` and `power corrupts` fall on two different printed
lines, and the quotation of them is still faithful. Every run of spaces, tabs and
newlines is folded to a single space before the comparison, on both sides.

**Quote glyphs.** A straight `"` and a typographic `"` are the same character to a
reader, and an editor swaps one for the other without asking. They are folded
together, as are `'` and `'`, and the German `„ "`.

**Omissions.** A fair quotation is often abridged, and `...` (or `…`) in the quote
marks where. The parts that remain must still appear in the source, **in the order
given** — so an abridged quote passes and a *reordered* one does not:

<!-- readme-check: skip=illustration -->
```console
$ quote-check
✗ README.md:88  "absolute power corrupts ... Power tends to corrupt"
  = ./sources/acton-creighton-1887.txt
  these words are in the source, but earlier than the part quoted before them -- the quote reorders the source

1 of 3 quote(s) unverified, 0 skipped
```

Everything else is held exactly, **including case**. `power tends` is not what the
source says, and the quiet one-letter misquotation is precisely the kind that
changes a meaning while looking innocent. A checker that folded case would wave it
through.

## Sources that cannot be checked

Some sources a machine cannot read: a paywall, a scanned PDF, a book on a shelf.
Do not pretend to check them and do not silently trust them either — say so, in
the open, with the reason written down:

```markdown
<!-- quote-check: "the words as printed" = https://example.com/paywalled skip=paywall -->
```

A skipped quote is counted and named as skipped, never as verified. What you
exempt, you are trusting — and the tool makes you write down what you trusted and
why, where a reader can see it.

And a source that was *supposed* to load but did not — a dead link, a 404, a
timeout — is **not** treated as a pass. "Cannot verify" is not "fine". It is
reported, so a citation that has rotted is caught rather than waved through.

## The quote that started it

The fabrication on my site was attributed to Acton. The remedy was to find what
Acton actually wrote, and where. He wrote it to Bishop Mandell Creighton on 5
April 1887, and the source sits in this repository as a plain text file. So the
real line passes against the real letter:

As Acton wrote to Creighton,
<!-- quote-check: "Power tends to corrupt and absolute power corrupts absolutely" = ./sources/acton-creighton-1887.txt -->
"Power tends to corrupt and absolute power corrupts absolutely."

He went on, in the same breath,
<!-- quote-check: "Great men are almost always bad men" = ./sources/acton-creighton-1887.txt -->
"Great men are almost always bad men" — and closed the thought with
<!-- quote-check: "There is no worse heresy than that the office sanctifies the holder of it" = ./sources/acton-creighton-1887.txt -->
"there is no worse heresy than that the office sanctifies the holder of it."

Every quotation in the three paragraphs above is bound to that file, and this
README is run against itself in CI. If any quote here ever drifts from the source
it names, the build goes red — which would be a particularly embarrassing way for
a tool about misquotation to be caught misquoting.

## Verified

The test suite is the audit, and the first two tests are the story: the real
Acton line, checked against the real letter, must **pass**; the fabrication,
checked against the same letter, must be **caught**. If the fabrication ever
passed, the tool would have failed at the one thing it exists to do.

```console
$ python -m pytest -q
53 passed
```

This is <!-- readme-check: 570 = cat quotecheck/*.py | wc -l --> 570 lines of
Python, no dependencies, and that number is checked by
[readme-check](https://github.com/Wasserpuncher/readme-check) — the twin tool —
counting the files it describes.

And quote-check checks itself:

```console
$ quote-check
3 quote(s) verified, 0 skipped
```

## Install

<!-- readme-check: skip=would-install -->
```console
$ pip install git+https://github.com/Wasserpuncher/quote-check
$ quote-check                         # checks ./README.md
$ quote-check docs/essay.md
$ quote-check docs/essay.md --timeout 30
```

Python 3.10+, no dependencies.

The twin tool installs the same way, from git, and it matters that it is written
this way and not as a bare package name:

<!-- readme-check: skip=would-install -->
```console
$ pip install git+https://github.com/Wasserpuncher/readme-check
```

> **Not `pip install readme-check`.** That name belongs to an unrelated package on
> PyPI, by someone else; it installs cleanly and then is not this tool. Always the
> `git+https://` form above.

**It fetches the URLs your document cites.** For any source that is a URL, this
tool makes an HTTP request to it, which is a thing your document told it to do. It
does not execute anything and it does not follow links beyond the ones you named,
but if you would not want those requests made, mark the source `skip` or point it
at a local copy instead.

## Use it in CI

There is a GitHub Action, so a build can verify every quotation on every push.
It pins the tool at the moving `@v1` tag and defaults `path` to `README.md`.

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.x'
- uses: Wasserpuncher/quote-check@v1
  # with:
  #   path: README.md
  #   args: '--timeout 30'
```

## License

MIT
