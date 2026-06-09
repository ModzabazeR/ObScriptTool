#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract the Thai translation column from CSV working files into .txt scripts.

For every CSV matched by the glob, write a sibling .txt file (same folder, same
base name) containing just the Thai column — one row per line, in source order.
These .txt files are the in-game script files that main.py / alphabet.py encode.

The Thai column header is matched against "แปลไทย", "Translation", or "Thai"
(in that priority order). The stdlib csv reader unescapes CSV-doubled quotes, so
tag attributes like [color index=""820000""] come out as [color index="820000"].

Usage:
  python extract_thai.py                            # default glob input/**/*.csv
  python extract_thai.py "input/0_Prologue/*.csv"   # custom glob
  python extract_thai.py "input/**/*.csv" --skip-empty
"""
import argparse
import csv
import glob
import os

# Candidate header names for the Thai translation column, in priority order.
THAI_COLUMNS = ("แปลไทย", "Translation", "Thai")


def find_thai_column(header):
    """Index of the Thai column in a header row, or -1 if none is present."""
    for name in THAI_COLUMNS:
        if name in header:
            return header.index(name)
    return -1


def extract_file(path, skip_empty=False):
    """Write the Thai column of one CSV to a sibling .txt.

    Returns (line_count, out_path), or None if the file has no Thai column.
    """
    with open(path, encoding="utf8", errors="ignore", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return None
    col = find_thai_column(rows[0])
    if col < 0:
        return None

    lines = []
    for row in rows[1:]:
        cell = row[col] if col < len(row) else ""
        if skip_empty and not cell.strip():
            continue
        lines.append(cell)

    out_path = os.path.splitext(path)[0] + ".txt"
    with open(out_path, "w", encoding="utf8") as f:
        for line in lines:
            f.write(line + "\n")
    return len(lines), out_path


def main():
    ap = argparse.ArgumentParser(
        description="Extract the Thai column from CSV working files into sibling .txt scripts.")
    ap.add_argument("glob", nargs="?", default="input/**/*.csv",
                    help="glob for input CSV files (default: input/**/*.csv)")
    ap.add_argument("--skip-empty", action="store_true",
                    help="omit rows whose Thai cell is empty (default: keep them as blank lines)")
    args = ap.parse_args()

    files = sorted(glob.glob(args.glob, recursive=True))
    written = skipped = total_lines = 0
    for path in files:
        result = extract_file(path, skip_empty=args.skip_empty)
        if result is None:
            print(f"  skip (no Thai column): {path}")
            skipped += 1
            continue
        count, out_path = result
        print(f"  {count:>5} line(s) -> {out_path}")
        written += 1
        total_lines += count

    print()
    print(f"Wrote {written} .txt file(s), {total_lines} total line(s) | "
          f"{skipped} CSV(s) skipped | {len(files)} matched")


if __name__ == "__main__":
    main()
