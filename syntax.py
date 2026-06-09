#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Syntax validator for Operation Bifrost script files.

Checks three structural rules on each non-empty line:
  1. Every line ends with exactly ``[%p]`` or ``[%e]``.
  2. Dialogue lines (starting with ``[name]...[line]``) have their spoken text
     wrapped in the curly quotes ``“`` ... ``”``.
  3. No straight double quote (``"``) outside of script tags ``[...]``, and no
     straight single quote (``'``) anywhere.
  4. Tag attribute values must be wrapped in double quotes, e.g.
     ``[margin top="228"]`` is valid but ``[margin top=228]`` is not.
"""
from __future__ import annotations

import re
import sys

LINE_END = ("[%p]", "[%e]")
OPEN_QUOTE = "“"   # left double quotation mark
CLOSE_QUOTE = "”"  # right double quotation mark
TAG_PATTERN = re.compile(r"\[[^\[\]]*\]")
NAME_LINE_PATTERN = re.compile(r"^\[name\].*?\[line\]")
# An '=' inside a tag whose value is not immediately wrapped in double quotes.
UNQUOTED_ATTR_PATTERN = re.compile(r'=\s*"[^"]*"')


def _strip_tags(text: str) -> str:
    """Remove every ``[...]`` tag span so only displayed text remains."""
    return TAG_PATTERN.sub("", text)


def check_line(line: str) -> list[str]:
    """Return a list of rule-violation messages for a single line."""
    errors = []

    # Rule 1: line ending
    if not line.endswith(LINE_END):
        errors.append("does not end with [%p] or [%e]")
        ending = None
    else:
        ending = line[-4:]

    # Rule 3: straight " is allowed only inside [ ] tags; straight ' is never allowed
    if '"' in _strip_tags(line):
        errors.append("contains a straight double quote (\") outside a [ ] tag")
    if "'" in line:
        errors.append("contains a straight single quote (')")

    # Rule 4: every tag attribute value must be wrapped in double quotes
    for tag in TAG_PATTERN.findall(line):
        inner = tag[1:-1]  # drop the surrounding [ ]
        # An '=' that is not part of a valid name="value" pair is an error.
        if "=" in UNQUOTED_ATTR_PATTERN.sub("", inner):
            errors.append(f'unquoted attribute value in tag {tag}')

    # Rule 2: dialogue lines must wrap spoken text in curly quotes.
    # Inline tags (e.g. [color index="..."]) may surround the quotes, so strip
    # tags before checking that the visible text opens with “ and closes with ”.
    name_line = NAME_LINE_PATTERN.match(line)
    if name_line and ending is not None:
        spoken = _strip_tags(line[name_line.end():-len(ending)]).strip()
        if spoken and not (spoken.startswith(OPEN_QUOTE) and spoken.endswith(CLOSE_QUOTE)):
            errors.append(
                f"dialogue not wrapped in {OPEN_QUOTE} ... {CLOSE_QUOTE}"
            )

    return errors


def validate(script_file: str) -> int:
    """Validate a script file, print any problems, and return the error count."""
    error_count = 0
    with open(script_file, "r", encoding="utf8", errors="ignore") as f:
        for line_number, raw in enumerate(f, start=1):
            line = raw.rstrip("\n").rstrip("\r")
            if not line:
                continue
            for message in check_line(line):
                error_count += 1
                print("\033[91m" + f"  Line {line_number}: {message}" + "\033[0m")

    if error_count == 0:
        print("\033[92m" + "Syntax OK" + "\033[0m")
    else:
        print("\033[91m" + f"{error_count} syntax error(s) found" + "\033[0m")
    return error_count


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: syntax.py <file name>")
        print("Example: syntax.py SG06_01.SCX.txt")
        sys.exit()
    validate(sys.argv[1])
