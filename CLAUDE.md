# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

ObScriptTool — a Thai text encoder/decoder for **Operation Bifrost**, the Thai fan-translation of *Steins;Gate*. The game's font cannot render Thai natively, so each Thai string is mapped to a single substitution glyph (a CJK "kan" character the game *can* render). **Encoding** rewrites a script file's Thai → kan glyphs for use in-game; **decoding** reverses kan → Thai for editing.

## Running

No build step. Requires Python 3 with `pandas` (and `tkinter`, bundled with most CPython installs).

```bash
python main.py        # interactive entry point: opens a folder picker, recursively encode/decode .txt files per config.json
python add.py         # standalone: grow the mapping table only
python alphabet.py <file> <encode|decode>   # standalone: encode/decode one file without the menu
python syntax.py <file>                     # standalone: validate one script file's syntax
python generate_syntax_report.py            # scan input/ CSVs → syntax_report.html + .txt
python extract_thai.py [glob]               # extract the Thai column from input/ CSVs → sibling .txt scripts
```

`main.py` is interactive: it reads `config.json`, optionally prompts to add new mappings, then opens a Tk **folder** dialog. It walks the chosen folder recursively, processing every `.txt` script file (pruning `output/` and `.git/`), and writes results to `output/<relative/path>` — mirroring the source folder structure so same-named files in different subfolders don't collide. There are no automated tests, linters, or CI configured.

> Console note: Thai/CJK glyphs may not render in the default Windows terminal. If output looks broken, run in a Unicode-capable console — this is a display issue, not a data bug.

## Core architecture

The whole pipeline is driven by one mapping table (the "TOC") and a pool of substitution glyphs.

- **`config.json`** — selects `mode` (`encode`/`decode`), the TOC file (`encoding_toc.csv`), and the glyph pool (`kan_charset.utf8`). `main.py` reads this at startup.
- **The TOC (`encoding_toc.csv`)** — the source of truth. Three columns: `# id`, `thai`, `kan`. Each row maps one Thai string to one kan glyph. This file is read on every run and rewritten when new mappings are added.
- **Glyph pools (`kan_charset.utf8`, `charset.utf8`)** — single lines of candidate substitution glyphs. New mappings draw the next unused glyph by index: `charset[len(entries)]`.

### Modules

- **`main.py`** — orchestrator. Loads config + TOC, optionally calls `add`, runs `alphabet.encode/decode` over selected files, optionally rearranges the TOC. Tracks pass/fail counts (a file "fails" if encoding leaves leftover Thai vowels).
- **`alphabet.py`** — the encode/decode engine. `encode()` first normalizes vowels via `vowels.fix_sara_um`, then for each line replaces every `thai` substring with its `kan` glyph; afterward `vowels.detect_vowel` counts leftover Thai combining marks **and** `syntax.validate` adds any structural-syntax violations — both fold into the file's error count. `decode()` does the reverse replacement. Also runnable standalone via CLI args.
- **`add.py`** — interactively appends Thai strings to the TOC, assigning each the next glyph from the charset pool. Enter `-1` to stop. **Ordering matters:** strings of length ≥ 3 are *inserted at the front* and shorter ones *appended*, so multi-character sequences get matched before their substrings during the linear replace pass (greedy longest-first behavior depends on this row order).
- **`vowels.py`** — Thai-specific text handling. `fix_sara_um` reorders the *sara am* (ำ) composition and its tone-mark variants into the order the game expects before encoding. `detect_vowel` is the QA check: it counts standalone Thai combining vowels/tone marks remaining after encoding — a nonzero count means some Thai wasn't mapped and is the file's error count.
- **`rearrange.py`** — sorts the TOC by `# id` into `ordered_encoding_toc.csv` (the working TOC is kept in match-priority order, not id order).

### Data flow when encoding

```
config.json → load TOC (encoding_toc.csv) + glyph pool
   → [optional] add.add_str → add.update_toc (rewrites encoding_toc.csv)
   → pick files (Tk dialog)
   → per file: vowels.fix_sara_um → replace thai→kan → vowels.detect_vowel (error count)
   → write output/<file>
   → [optional] rearrange.create_ordered_toc → ordered_encoding_toc.csv
```

## Syntax checking & reporting

Separate from encoding, there's a structural-syntax linter for the translated script.

- **`syntax.py`** — validates one line at a time. `check_line(line, ref_line=None)` returns a list of violation messages; `validate(file)` prints them and returns the count. Seven rules:
  1. Every non-empty line ends with exactly `[%p]` or `[%e]`.
  2. Dialogue lines (`[name]…[line]…`) must wrap their spoken text in curly quotes `“ … ”`. Inline tags (e.g. `[color index="…"]`) may surround the quotes, so the check strips tags before testing the first/last visible glyph.
  3. Straight `"` is allowed **only inside** `[…]` tags (it's used for attribute values); straight `'` is **never** allowed.
  4. Tag attribute values must be double-quoted: `[margin top="228"]` is valid, `[margin top=228]` is not.
  5. Every tag must be complete — each `[` is closed by a matching `]`, with no nested or unmatched brackets.
  6. *(Reference-line check, only when `ref_line` is passed.)* The count of `[color index="8A0000"]` (phone-text) tags in the Thai line must match the reference (e.g. English CoZ Patch) line; a mismatch is reported as missing/extra tags.
  7. Inside phone text (opened by `[color index="8A0000"]`), a later `[color index="A0140000"]` renders unreadably and must be `[color index="800000"]` instead. Only flagged when the `A0140000` follows an `8A0000` on the same line.

  `alphabet.encode()` calls `syntax.validate` on the source file so encoding surfaces syntax errors too (see above).

- **`generate_syntax_report.py`** — batch-lints the **`แปลไทย`** (Thai translation) column of the CSV working files under `input/` and emits a styled, self-contained `syntax_report.html` (with an embedded copy-paste plain-text version) plus a `syntax_report.txt`. CLI: `python generate_syntax_report.py [glob] [-o out.html] [-t out.txt]` (default glob `input/**/*.csv`; `-t ""` skips the text file). Each hit is sorted into a category and a tier — **Confirmed** (actionable, shown as a FIX with a concrete correction) vs **Review** (advisory NOTE). The quote-wrap rule is noisy by design on this corpus: letters and multi-page dialogue read aloud (e.g. SG06_23, the Suzuha letter) legitimately lack `“ ”`, so they surface as NOTEs, not errors.

> The `input/` CSVs are *translation working files*, not the `.txt` script files. Columns: `ต้นฉบับ` (source JP), `Steam Patch`, `CoZ Patch`, `แปลไทย` (Thai). The `แปลไทย` column is what becomes the in-game script, so that's the only column linted.

- **`extract_thai.py`** — the bridge from working CSVs to script files. Extracts the Thai column (`แปลไทย` → `Translation` → `Thai`, first header match wins) from every CSV matched by the glob and writes a sibling `.txt` (same folder, same base name, e.g. `SG00_01.SCX.csv` → `SG00_01.SCX.txt`) — one row per line, in source order, ready for `main.py`/`alphabet.py` to encode. Uses the stdlib `csv` reader so CSV-doubled quotes in tag attributes (`[color index=""…""]`) are unescaped to `[color index="…"]`. CLI: `python extract_thai.py [glob] [--skip-empty]` (default glob `input/**/*.csv`; `--skip-empty` drops rows whose Thai cell is empty instead of writing a blank line).

## Conventions specific to this repo

- Replacement is plain substring `str.replace` over each line, applied in TOC row order — **row order in `encoding_toc.csv` is functional, not cosmetic.** Don't sort the working TOC by id; that's what `ordered_encoding_toc.csv` is for.
- All file I/O uses `encoding="utf8"`; encode/decode read with `errors="ignore"`.
- `*.txt`, `output/`, and `*.old.py` are gitignored — script files and generated output are not committed.
