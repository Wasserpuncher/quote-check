"""CLI: check a document's quotations against the sources they name."""

from __future__ import annotations

import argparse
import os
import sys

from .check import check
from .parse import parse
from .sources import DEFAULT_TIMEOUT

RED = "\033[31m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"


def _colour(enabled: bool):
    if enabled:
        return RED, GREEN, DIM, RESET
    return "", "", "", ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quote-check",
        description="Check that every quotation in a document really appears in "
                    "the source it cites.")
    parser.add_argument("document", nargs="?", default="README.md")
    parser.add_argument("--root", default=None,
                        help="resolve local source paths here "
                             "(default: the document's directory)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"seconds to wait on a URL (default: {DEFAULT_TIMEOUT:g})")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)

    red, green, dim, reset = _colour(
        not args.no_color and sys.stdout.isatty())

    if not os.path.exists(args.document):
        print(f"quote-check: {args.document}: no such file", file=sys.stderr)
        return 2

    with open(args.document, encoding="utf-8") as handle:
        markdown = handle.read()

    root = args.root or os.path.dirname(os.path.abspath(args.document)) or "."
    result = check(parse(markdown), root=root, timeout=args.timeout)

    for bad in result.violations:
        print(f"{red}✗{reset} {args.document}:{bad.line}  \"{bad.quoted}\"")
        print(f"{dim}  = {bad.source}{reset}")
        print(f"  {bad.reason}")
        if bad.excerpt:
            print(f"{dim}  --- you quoted{reset}")
            print(f"  | {bad.quoted}")
            print(f"{dim}  --- the source says{reset}")
            print(f"  | {bad.excerpt}")
        print()

    total = result.checked
    broken = len(result.violations)

    if broken:
        print(f"{red}{broken} of {total} quote(s) unverified{reset}"
              f"{dim}, {result.skipped} skipped{reset}")
        return 1

    print(f"{green}{total} quote(s) verified{reset}"
          f"{dim}, {result.skipped} skipped{reset}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
