#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Syntax validator for Operation Bifrost script files.

Checks structural rules on each non-empty line:
  1. Every line ends with exactly ``[%p]`` or ``[%e]``.
  2. Dialogue lines (starting with ``[name]...[line]``) have their spoken text
     wrapped in the curly quotes ``“`` ... ``”``.
  3. No straight double quote (``"``) outside of script tags ``[...]``, and no
     straight single quote (``'``) anywhere.
  4. Tag attribute values must be wrapped in double quotes, e.g.
     ``[margin top="228"]`` is valid but ``[margin top=228]`` is not.
  5. Every tag must be complete (i.e. every open bracket ``[`` must be closed
     with ``]``, and no nested tags or unmatched brackets).
  6. If a reference line (e.g. English CoZ Patch) is provided, the tags in the
     Thai translation line must match the reference tags.
  7. Inside phone text (opened with ``[color index="8A0000"]``), the color
     ``[color index="A0140000"]`` renders unreadably and must be
     ``[color index="800000"]`` instead.
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

# Rule 7: phone-text color readability. Phone text is opened with color index
# "8A0000"; inside it, color index "A0140000" renders unreadably and should be
# "800000" instead. Compared in _normalize_tag form (lowercase, no spaces).
PHONE_TEXT_COLOR = 'colorindex="8a0000"'
UNREADABLE_PHONE_COLOR = 'colorindex="a0140000"'


def _strip_tags(text: str) -> str:
    """Remove every ``[...]`` tag span so only displayed text remains."""
    return TAG_PATTERN.sub("", text)


def _normalize_tag(tag: str) -> str:
    """Normalize a ``[...]`` tag for comparison: drop the brackets and spaces,
    treat single quotes as double quotes, and lowercase the result."""
    return tag[1:-1].strip().replace(" ", "").replace("'", '"').lower()


def check_line(line: str, ref_line: str | None = None) -> list[str]:
    """Return a list of rule-violation messages for a single line."""
    errors = []

    # Rule 5: tag completeness (bracket matching)
    opened_bracket_idx = -1
    for i, char in enumerate(line):
        if char == '[':
            if opened_bracket_idx != -1:
                # Previous open bracket was never closed
                unclosed_context = line[opened_bracket_idx:i].strip()
                errors.append(f"incomplete tag: '{unclosed_context}' (missing ']')")
            opened_bracket_idx = i
        elif char == ']':
            if opened_bracket_idx == -1:
                # Closing bracket with no opening bracket
                start = i
                while start > 0 and line[start-1] not in (' ', '[', ']'):
                    start -= 1
                unopened_context = line[start:i+1]
                errors.append(f"incomplete tag: '{unopened_context}' (missing '[')")
            else:
                opened_bracket_idx = -1

    if opened_bracket_idx != -1:
        # End of line reached but bracket still open
        unclosed_context = line[opened_bracket_idx:]
        errors.append(f"incomplete tag: '{unclosed_context}' (missing ']')")

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


    # Rule 6: unmatched tags with CoZ Patch reference line (checking color index 8A0000)
    if ref_line is not None:
        ref_tags = [_normalize_tag(t) for t in TAG_PATTERN.findall(ref_line)]
        line_tags = [_normalize_tag(t) for t in TAG_PATTERN.findall(line)]

        ref_count = ref_tags.count(PHONE_TEXT_COLOR)
        line_count = line_tags.count(PHONE_TEXT_COLOR)

        if ref_count != line_count:
            if ref_count > line_count:
                diff = ref_count - line_count
                missing_str = ', '.join(['[color index="8A0000"]'] * diff)
                errors.append(f"unmatched tags with CoZ Patch (missing {missing_str})")
            else:
                diff = line_count - ref_count
                extra_str = ', '.join(['[color index="8A0000"]'] * diff)
                errors.append(f"unmatched tags with CoZ Patch (extra {extra_str})")

    # Rule 7: once phone text is opened with color index "8A0000", a following
    # color index "A0140000" is unreadable and must be "800000" instead.
    in_phone_text = False
    for tag in TAG_PATTERN.findall(line):
        norm = _normalize_tag(tag)
        if norm == PHONE_TEXT_COLOR:
            in_phone_text = True
        elif norm == UNREADABLE_PHONE_COLOR and in_phone_text:
            errors.append(
                'unreadable phone text color [color index="A0140000"] after '
                '[color index="8A0000"] (use [color index="800000"] instead)'
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
