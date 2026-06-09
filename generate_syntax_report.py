#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the ObScriptTool syntax report.

Runs syntax.check_line over the Thai (แปลไทย) column of every CSV matched by the
input glob and emits:
  * a self-contained, design-led HTML report (default: syntax_report.html), which
    also embeds a copy-paste plain-text version of the report, and
  * the same report as a standalone .txt file (default: syntax_report.txt).

Usage:
  python generate_syntax_report.py                         # default glob input/**/*.csv
  python generate_syntax_report.py "input/6_*/*.csv"       # custom glob
  python generate_syntax_report.py "input/**/*.csv" -o out.html -t out.txt
  python generate_syntax_report.py "input/**/*.csv" -t ""   # skip the .txt file

Visual direction: muted retro-futurist lab terminal (Steins;Gate worldline scan),
serif dialogue lines, and a suggested fix beside every anomaly.
"""
import argparse
import csv
import glob
import html
import os
import re

import syntax

THAI_COLUMN = "แปลไทย"
OPEN_Q, CLOSE_Q = syntax.OPEN_QUOTE, syntax.CLOSE_QUOTE

TAG_SPLIT = re.compile(r"(\[[^\[\]]*\])")

# category slug -> (label, tier, hue)  tier here is only a default hue grouping;
# the authoritative per-entry tier is derived from the suggested-fix kind.
CATS = {
    "bad-ending (not [%p]/[%e])": ("Malformed page break", "real", "ending"),
    "straight single quote '": ("Straight single quote", "real", "squote"),
    'straight double quote "': ("Straight double quote", "real", "dquote"),
    "dialogue: missing both quotes": ("Unquoted speaker line", "wrap", "both"),
    "dialogue: opens “ but never closes ” (continuation?)":
        ("Opens “ — no close (continues?)", "wrap", "open"),
    "dialogue: closes ” but never opens “": ("Closes ” — no open", "wrap", "close"),
}


def classify(msg, cell):
    if "does not end" in msg:
        return "bad-ending (not [%p]/[%e])"
    if "single quote" in msg:
        return "straight single quote '"
    if "double quote" in msg:
        return 'straight double quote "'
    if "dialogue not wrapped" in msg:
        spoken = syntax._strip_tags(cell)
        o, c = OPEN_Q in spoken, CLOSE_Q in spoken
        if o and not c:
            return "dialogue: opens “ but never closes ” (continuation?)"
        if c and not o:
            return "dialogue: closes ” but never opens “"
        return "dialogue: missing both quotes"
    return msg


def _spoken_after_line(cell):
    """The visible dialogue text: after [line] (if any), minus tags and the
    trailing page-break tag — so the first glyph is the real opening mark."""
    m = syntax.NAME_LINE_PATTERN.match(cell)
    seg = cell[m.end():] if m else cell
    seg = re.sub(r"\[%[pe]\]$", "", seg)
    return syntax._strip_tags(seg).strip()


def suggest_fix(cell, cat):
    """Return (kind, text) where kind is 'fix' (actionable) or 'note' (advisory).
    Backtick-wrapped tokens in text get rendered as inline code chips in HTML."""
    spoken = _spoken_after_line(cell)
    if cat.startswith("bad-ending"):
        m = re.search(r"%[pe]\]?$", cell)
        token = m.group(0) if m else "%p"
        proper = "[%e]" if "e" in token else "[%p]"
        return "fix", f"Malformed page break `{token}`. Replace it with the proper tag `{proper}`."
    if cat.startswith("straight single"):
        return "fix", "Straight `'` is never allowed. Use curly single quotes `‘ ’` for an inner quote."
    if "double quote" in cat:
        if spoken.startswith('"'):
            return "fix", 'The opening mark is a straight `"` — replace it with the curly `“` (and close with `”`).'
        return "fix", 'Straight `"` is only allowed inside tag attributes. Use `“ ”` for the quote, or `‘ ’` for a quote-within-a-quote.'
    if "missing both" in cat:
        return "note", "If this is spoken dialogue, wrap it in `“ … ”`. For a letter or narration read aloud this is expected — leave it."
    if cat.startswith("dialogue: opens"):
        return "note", "Add the closing `”` at the end — unless the line intentionally continues onto the next `[%p]` page."
    if cat.startswith("dialogue: closes"):
        if spoken.startswith(CLOSE_Q):
            return "fix", "The opening mark is `”` (a closing quote) — it should be the opening `“`."
        return "note", "Add an opening `“` before the first word — unless this continues a quote from a previous page."
    return "note", ""


def fmt_fix(text):
    esc = html.escape(text)
    return re.sub(r"`([^`]+)`", r'<code class="kbd">\1</code>', esc)


def render_line(cell, cat):
    """Tokenize a script line into styled spans, highlighting the fault."""
    parts = TAG_SPLIT.split(cell)
    out = []
    last_text_idx = max((i for i, p in enumerate(parts)
                         if p and not (p.startswith("[") and p.endswith("]"))),
                        default=-1)
    for idx, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("[") and part.endswith("]"):
            inner = part[1:-1]
            cls = "tok tok-end" if inner.startswith("%") else (
                "tok tok-struct" if inner in ("name", "line", "center", "linebreak")
                else "tok")
            out.append(f'<span class="{cls}">{html.escape(part)}</span>')
            continue
        seg = html.escape(part)
        seg = seg.replace("&#x27;", '<span class="bad">&#x27;</span>')
        seg = seg.replace("&quot;", '<span class="bad">&quot;</span>')
        seg = seg.replace(OPEN_Q, f'<span class="q">{OPEN_Q}</span>')
        seg = seg.replace(CLOSE_Q, f'<span class="q">{CLOSE_Q}</span>')
        if idx == last_text_idx and cat.startswith("bad-ending"):
            seg = re.sub(r"(%[pe]\]?)$", r'<span class="err-end">\1</span>', seg)
        out.append(seg)
    return "".join(out)


def chapter_meta(path):
    base = os.path.basename(os.path.dirname(path))
    m = re.match(r"(\d+)_(.*)", base)
    if m:
        return int(m.group(1)), m.group(2)
    return -1, "Loose files"


def collect(pattern):
    files = sorted(glob.glob(pattern, recursive=True))
    by_file = {}
    cat_counts = {k: 0 for k in CATS}
    total = 0
    for path in files:
        with open(path, encoding="utf8", errors="ignore", newline="") as f:
            rows = list(csv.reader(f))
        if not rows or THAI_COLUMN not in rows[0]:
            continue
        col = rows[0].index(THAI_COLUMN)
        for i, row in enumerate(rows[1:], start=2):
            if col >= len(row):
                continue
            cell = row[col].strip()
            if not cell:
                continue
            for msg in syntax.check_line(cell):
                cat = classify(msg, cell)
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
                total += 1
                by_file.setdefault(path, []).append((i, cat, cell))
    return len(files), by_file, cat_counts, total


def tally_real(by_file):
    """Count entries whose suggested fix is actionable (kind == 'fix')."""
    n = 0
    for entries in by_file.values():
        for (_, cat, cell) in entries:
            if suggest_fix(cell, cat)[0] == "fix":
                n += 1
    return n


def build_text_report(scanned, by_file, cat_counts, total):
    real = tally_real(by_file)
    wrap = total - real
    out = [
        "ObScriptTool — Syntax Scan",
        f"Total anomalies: {total}   Confirmed: {real}   Review: {wrap}",
        f"Files flagged: {len(by_file)} / {scanned} scanned",
        "",
        "=== Counts by category ===",
    ]
    for slug, n in sorted(cat_counts.items(), key=lambda x: -x[1]):
        if n:
            out.append(f"  {n:>4}  {slug}")
    out += ["", "=== Details by file ==="]
    for path in sorted(by_file):
        entries = by_file[path]
        out += ["", f"### {path} ({len(entries)} error(s))"]
        for (row, cat, cell) in entries:
            kind, fix = suggest_fix(cell, cat)
            out.append(f"  R{row}  [{cat}]")
            out.append(f"    {cell}")
            if fix:
                out.append(f"    -> {kind.upper()}: {fix.replace('`', '')}")
    if not by_file:
        out += ["", "No anomalies found."]
    return "\n".join(out)


def build_html(scanned, by_file, cat_counts, total, raw_text):
    files_with = len(by_file)
    clean_pct = (scanned - files_with) / scanned * 100 if scanned else 100
    real = 0  # tallied per entry below: "confirmed" == has an actionable FIX

    chapters = {}
    for path in by_file:
        num, name = chapter_meta(path)
        chapters.setdefault((num, name), []).append(path)

    legend = []
    for slug, (label, tier, hue) in CATS.items():
        n = cat_counts.get(slug, 0)
        legend.append(
            f'<button class="chip" data-cat="{hue}" data-tier="{tier}">'
            f'<span class="dot h-{hue}"></span>{html.escape(label)}'
            f'<span class="chip-n">{n}</span></button>'
        )

    sections = []
    for (num, name) in sorted(chapters, key=lambda x: x[0]):
        paths = sorted(chapters[(num, name)])
        ch_total = sum(len(by_file[p]) for p in paths)
        cards = []
        for p in paths:
            entries = by_file[p]
            fname = os.path.basename(p).replace(".SCX.csv", "")
            rel = p.replace("\\", "/")
            rows_html = []
            for (rownum, cat, cell) in entries:
                label, _cat_tier, hue = CATS[cat]
                kind, fix = suggest_fix(cell, cat)
                tier = "real" if kind == "fix" else "wrap"
                if tier == "real":
                    real += 1
                fix_html = (f'<div class="fix {kind}"><span class="fix-k">'
                            f'{"FIX" if kind == "fix" else "NOTE"}</span>'
                            f'<span>{fmt_fix(fix)}</span></div>') if fix else ""
                rows_html.append(
                    f'<li class="entry" data-tier="{tier}" data-cat="{hue}" '
                    f'data-search="{html.escape((fname + " " + cell).lower(), quote=True)}">'
                    f'<div class="meta"><span class="row">R{rownum}</span>'
                    f'<span class="tag h-{hue}">{html.escape(label)}</span></div>'
                    f'<div class="body"><div class="line">{render_line(cell, cat)}</div>'
                    f'{fix_html}</div></li>'
                )
            cards.append(
                f'<details class="file" open><summary>'
                f'<span class="fname">{html.escape(fname)}</span>'
                f'<span class="fpath">{html.escape(rel)}</span>'
                f'<span class="fcount">{len(entries)}</span></summary>'
                f'<ul class="entries">{"".join(rows_html)}</ul></details>'
            )
        sections.append(
            f'<section class="chapter" data-count="{ch_total}">'
            f'<header class="ch-head"><span class="ch-idx">'
            f'{num if num >= 0 else "·"}</span>'
            f'<h2>{html.escape(name)}</h2>'
            f'<span class="ch-count">{ch_total}</span></header>'
            f'{"".join(cards)}</section>'
        )

    body = "".join(sections) or (
        '<div class="allclear">// NO ANOMALIES — SCRIPT IS CLEAN</div>')
    wrap = total - real

    return PAGE.replace("__TOTAL__", str(total)) \
        .replace("__REAL__", str(real)) \
        .replace("__WRAP__", str(wrap)) \
        .replace("__FILESWITH__", str(files_with)) \
        .replace("__SCANNED__", str(scanned)) \
        .replace("__CLEANPCT__", f"{clean_pct:.1f}") \
        .replace("__LEGEND__", "".join(legend)) \
        .replace("__SECTIONS__", body) \
        .replace("__RAWTXT__", html.escape(raw_text))  # must stay LAST


PAGE = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Syntax Scan · ObScriptTool</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600&family=Maitree:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0e0f12; --bg2:#14151a; --panel:#16181e; --panel2:#1a1d24;
  --line:#262a33; --ink:#ddd9cf; --ink-dim:#9a9ea7; --ink-faint:#646973;
  --amber:#c6a36b; --teal:#74a294; --red:#c98577;
  --h-ending:#c98577; --h-squote:#c79877; --h-dquote:#c6a36b;
  --h-both:#bda873; --h-open:#74a294; --h-close:#8b99bd;
  --grid:rgba(198,163,107,.025);
  --mono:"JetBrains Mono",ui-monospace,monospace;
  --disp:"Chakra Petch",system-ui,sans-serif;
  --serif:"Maitree",Georgia,"Times New Roman",serif;
  --thai:"Maitree",system-ui,sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;background:var(--bg);color:var(--ink);
  font-family:var(--disp);line-height:1.6;
  background-image:
    radial-gradient(1200px 700px at 80% -10%, rgba(198,163,107,.05), transparent 60%),
    radial-gradient(900px 600px at 0% 100%, rgba(116,162,148,.035), transparent 55%),
    linear-gradient(var(--grid) 1px,transparent 1px),
    linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:auto,auto,64px 64px,64px 64px;
  background-attachment:fixed;
}
body::before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:9;
  background:repeating-linear-gradient(0deg,rgba(0,0,0,.10) 0 1px,transparent 1px 4px);
  opacity:.35;
}
.wrap{max-width:1080px;margin:0 auto;padding:0 22px 120px}

.hero{position:relative;padding:64px 0 30px}
.kicker{font-family:var(--mono);font-size:12px;letter-spacing:.4em;
  text-transform:uppercase;color:var(--amber);margin:0 0 18px;
  display:flex;align-items:center;gap:12px}
.kicker::before{content:"";width:34px;height:1px;background:var(--amber);opacity:.7}
.blink{width:7px;height:7px;border-radius:2px;background:var(--red);
  animation:blink 1.8s steps(1) infinite}
@keyframes blink{50%{opacity:.2}}
h1{font-family:var(--disp);font-weight:600;letter-spacing:-.01em;
  font-size:clamp(34px,6vw,64px);line-height:1;margin:0 0 6px;color:var(--ink)}
h1 .alt{color:var(--ink-dim)}
.sub{color:var(--ink-dim);font-family:var(--mono);font-size:12.5px;
  letter-spacing:.02em;line-height:1.7;margin:14px 0 0;max-width:62ch}

.readout{display:grid;grid-template-columns:auto 1fr;gap:30px;align-items:end;
  margin-top:40px;padding-top:30px;border-top:1px solid var(--line)}
.meter{font-family:var(--disp);font-weight:600;
  font-size:clamp(72px,15vw,140px);line-height:.82;
  color:var(--amber);letter-spacing:-.02em;
  font-variant-numeric:tabular-nums;position:relative}
.meter span{font-size:.24em;color:var(--ink-dim);
  display:block;letter-spacing:.32em;text-transform:uppercase;
  font-family:var(--mono);font-weight:500;margin-top:12px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;
  background:var(--line);border:1px solid var(--line)}
.stat{background:var(--panel);padding:15px 18px}
.stat b{font-family:var(--disp);font-size:26px;font-weight:600;display:block;
  font-variant-numeric:tabular-nums;line-height:1;color:var(--ink)}
.stat small{font-family:var(--mono);font-size:10px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--ink-faint);display:block;margin-top:8px}
.stat.real b{color:var(--red)} .stat.wrap b{color:var(--amber)}
.stat.clean b{color:var(--teal)}

.toolbar{position:sticky;top:0;z-index:20;margin:34px 0 26px;
  background:rgba(14,15,18,.86);backdrop-filter:blur(11px);
  border:1px solid var(--line);border-radius:3px;padding:14px 14px 12px}
.tiers{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.tier{font-family:var(--mono);font-size:11.5px;letter-spacing:.1em;
  text-transform:uppercase;padding:8px 14px;border:1px solid var(--line);
  background:var(--panel);color:var(--ink-dim);cursor:pointer;border-radius:2px;
  transition:.16s}
.tier:hover{color:var(--ink);border-color:var(--ink-faint)}
.tier.on{background:var(--ink);color:var(--bg);border-color:var(--ink);font-weight:700}
.tier.on[data-tier="real"]{background:var(--red);border-color:var(--red);color:#241010}
.tier.on[data-tier="wrap"]{background:var(--amber);border-color:var(--amber);color:#231b0c}
.legend{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}
.chip{font-family:var(--mono);font-size:11px;letter-spacing:.02em;
  display:inline-flex;align-items:center;gap:8px;padding:6px 10px;
  border:1px solid var(--line);background:var(--panel2);color:var(--ink-dim);
  cursor:pointer;border-radius:2px;transition:.16s}
.chip:hover{color:var(--ink);border-color:var(--ink-faint)}
.chip.off{opacity:.32;text-decoration:line-through}
.chip .dot{width:9px;height:9px;border-radius:50%}
.chip-n{color:var(--ink-faint);font-weight:700}
.dot.h-ending{background:var(--h-ending)} .dot.h-squote{background:var(--h-squote)}
.dot.h-dquote{background:var(--h-dquote)} .dot.h-both{background:var(--h-both)}
.dot.h-open{background:var(--h-open)} .dot.h-close{background:var(--h-close)}
.search{display:flex;align-items:center;gap:10px;border:1px solid var(--line);
  background:var(--bg2);padding:9px 13px;border-radius:2px}
.search input{flex:1;background:none;border:0;color:var(--ink);outline:none;
  font-family:var(--mono);font-size:13px}
.search input::placeholder{color:var(--ink-faint)}
.search svg{flex:none;stroke:var(--amber);opacity:.8}
#hits{font-family:var(--mono);font-size:11px;color:var(--ink-faint);white-space:nowrap}

.chapter{margin:0 0 28px}
.ch-head{display:flex;align-items:center;gap:14px;margin:0 0 12px;
  padding-bottom:9px;border-bottom:1px solid var(--line)}
.ch-idx{font-family:var(--disp);font-weight:600;font-size:13px;color:var(--bg);
  background:var(--amber);min-width:26px;height:26px;display:grid;place-items:center;
  border-radius:2px}
.ch-head h2{font-family:var(--disp);font-weight:500;font-size:18px;margin:0;
  letter-spacing:.01em;flex:1;color:var(--ink)}
.ch-count{font-family:var(--mono);font-size:12px;color:var(--ink-faint)}

.file{border:1px solid var(--line);background:var(--panel);margin-bottom:9px;
  border-radius:3px;overflow:hidden}
.file summary{list-style:none;cursor:pointer;display:flex;align-items:center;
  gap:14px;padding:13px 16px;transition:.16s;user-select:none}
.file summary::-webkit-details-marker{display:none}
.file summary:hover{background:var(--panel2)}
.file[open] summary{border-bottom:1px solid var(--line);background:var(--panel2)}
.fname{font-family:var(--mono);font-weight:700;font-size:14px;color:var(--ink);
  letter-spacing:.02em}
.fname::before{content:"▸";color:var(--amber);margin-right:10px;display:inline-block;
  transition:.2s}
.file[open] .fname::before{transform:rotate(90deg)}
.fpath{font-family:var(--mono);font-size:11px;color:var(--ink-faint);flex:1;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fcount{font-family:var(--disp);font-weight:600;font-size:13px;color:var(--amber);
  background:rgba(198,163,107,.08);border:1px solid rgba(198,163,107,.22);
  min-width:24px;text-align:center;padding:1px 7px;border-radius:2px}
.entries{list-style:none;margin:0;padding:0}
.entry{display:grid;grid-template-columns:140px 1fr;gap:16px;
  padding:15px 16px;border-bottom:1px solid rgba(38,42,51,.5)}
.entry:last-child{border-bottom:0}
.entry:hover{background:var(--bg2)}
.meta{display:flex;flex-direction:column;gap:7px;align-items:flex-start}
.row{font-family:var(--mono);font-size:11px;color:var(--ink-dim);
  border:1px solid var(--line);padding:1px 7px;border-radius:2px;letter-spacing:.05em}
.tag{font-family:var(--mono);font-size:10px;letter-spacing:.03em;line-height:1.35;
  padding:3px 7px;border-radius:2px;border-left:2px solid;background:var(--panel2)}
.tag.h-ending{border-color:var(--h-ending);color:#d6a99f}
.tag.h-squote{border-color:var(--h-squote);color:#d4b29c}
.tag.h-dquote{border-color:var(--h-dquote);color:#d3bd96}
.tag.h-both{border-color:var(--h-both);color:#cdbd95}
.tag.h-open{border-color:var(--h-open);color:#a3c5ba}
.tag.h-close{border-color:var(--h-close);color:#b3bdd6}
.body{align-self:center;min-width:0}
.line{font-family:var(--serif);font-size:16px;line-height:1.72;color:var(--ink);
  word-break:break-word}
.tok{font-family:var(--mono);font-size:.72em;color:var(--ink-faint);
  background:rgba(255,255,255,.025);border:1px solid var(--line);
  padding:0 4px;border-radius:2px;margin:0 1px;white-space:nowrap;
  vertical-align:.08em}
.tok-struct{color:var(--teal);border-color:rgba(116,162,148,.28)}
.tok-end{color:var(--ink-dim);border-color:rgba(198,163,107,.22)}
.q{color:var(--amber)}
.bad{color:var(--ink);background:rgba(201,133,119,.18);
  border-bottom:1.5px solid var(--red);padding:0 2px;border-radius:2px}
.err-end{color:var(--ink);background:rgba(201,133,119,.18);
  border-bottom:1.5px solid var(--red);padding:0 3px;border-radius:2px;
  font-family:var(--mono);font-size:.85em}

.fix{font-family:var(--mono);font-size:11.5px;line-height:1.55;color:var(--ink-dim);
  margin-top:10px;padding:8px 11px;border-left:2px solid var(--line);
  background:var(--bg2);border-radius:0 2px 2px 0;display:flex;gap:10px;
  align-items:baseline}
.fix-k{font-size:9px;letter-spacing:.16em;font-weight:700;padding:2px 6px;
  border-radius:2px;flex:none}
.fix.fix{border-left-color:var(--red)}
.fix.fix .fix-k{background:rgba(201,133,119,.16);color:#d6a99f;
  border:1px solid rgba(201,133,119,.3)}
.fix.note{border-left-color:var(--teal)}
.fix.note .fix-k{background:rgba(116,162,148,.14);color:#a3c5ba;
  border:1px solid rgba(116,162,148,.28)}
.kbd{font-family:var(--mono);font-size:.94em;background:rgba(255,255,255,.05);
  border:1px solid var(--line);padding:0 4px;border-radius:2px;color:var(--ink)}

.allclear{text-align:center;font-family:var(--mono);color:var(--teal);
  padding:70px;border:1px dashed rgba(116,162,148,.4);letter-spacing:.12em;
  background:rgba(116,162,148,.05);border-radius:3px}
.empty{display:none;text-align:center;font-family:var(--mono);color:var(--ink-faint);
  padding:60px;border:1px dashed var(--line);letter-spacing:.1em}
.empty.show{display:block}

/* ---------- RAW TEXT PANEL ---------- */
.raw{margin:42px 0 0;border:1px solid var(--line);border-radius:3px;
  background:var(--panel);overflow:hidden}
.raw-head{display:flex;align-items:center;justify-content:space-between;gap:12px;
  padding:13px 16px;border-bottom:1px solid var(--line);background:var(--panel2)}
.raw-head h3{margin:0;font-family:var(--disp);font-weight:500;font-size:15px;color:var(--ink)}
.raw-head .sub2{font-family:var(--mono);font-size:11px;color:var(--ink-faint);
  margin-left:10px}
.copybtn{font-family:var(--mono);font-size:11px;letter-spacing:.1em;
  text-transform:uppercase;padding:8px 14px;border:1px solid var(--amber);
  background:rgba(198,163,107,.1);color:var(--amber);cursor:pointer;
  border-radius:2px;transition:.16s}
.copybtn:hover{background:rgba(198,163,107,.2)}
.copybtn.done{border-color:var(--teal);color:var(--teal);background:rgba(116,162,148,.12)}
#raw{width:100%;height:340px;resize:vertical;border:0;outline:none;display:block;
  background:var(--bg);color:var(--ink-dim);font-family:var(--mono);font-size:12px;
  line-height:1.65;padding:14px 16px}

footer{margin-top:50px;padding-top:20px;border-top:1px solid var(--line);
  font-family:var(--mono);font-size:11px;color:var(--ink-faint);
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
@media(max-width:680px){
  .readout{grid-template-columns:1fr}
  .entry{grid-template-columns:1fr;gap:10px}
  .meta{flex-direction:row}
  .fpath{display:none}
}
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <p class="kicker"><span class="blink"></span>Worldline Integrity Scan · ObScriptTool</p>
    <h1>Syntax anomalies<br><span class="alt">in the Thai script</span></h1>
    <p class="sub">// Per-line validation of the แปลไทย column across the Operation Bifrost
    script corpus. Quote-wrap flags are advisory — letters &amp; multi-page dialogue
    trip them by design, so each carries a note rather than a fix.</p>

    <div class="readout">
      <div class="meter">__TOTAL__<span>Anomalies</span></div>
      <div class="stats">
        <div class="stat real"><b>__REAL__</b><small>Confirmed</small></div>
        <div class="stat wrap"><b>__WRAP__</b><small>Review</small></div>
        <div class="stat"><b>__FILESWITH__</b><small>Files flagged</small></div>
        <div class="stat"><b>__SCANNED__</b><small>Files scanned</small></div>
        <div class="stat clean"><b>__CLEANPCT__%</b><small>Files clean</small></div>
        <div class="stat"><b>4</b><small>Rule set</small></div>
      </div>
    </div>
  </header>

  <div class="toolbar">
    <div class="tiers">
      <button class="tier on" data-tier="all">All anomalies</button>
      <button class="tier" data-tier="real">Confirmed errors</button>
      <button class="tier" data-tier="wrap">Quote-wrap review</button>
    </div>
    <div class="legend">__LEGEND__</div>
    <div class="search">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke-width="2.4"
        stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
      <input id="q" type="text" placeholder="filter by file name or text…" autocomplete="off">
      <span id="hits"></span>
    </div>
  </div>

  __SECTIONS__
  <div class="empty" id="empty">// NO MATCHING ANOMALIES</div>

  <section class="raw">
    <div class="raw-head">
      <div><h3 style="display:inline">Plain-text report</h3>
        <span class="sub2">copy &amp; paste fallback</span></div>
      <button id="copy" class="copybtn">Copy to clipboard</button>
    </div>
    <textarea id="raw" readonly spellcheck="false" wrap="off">__RAWTXT__</textarea>
  </section>

  <footer>
    <span>ObScriptTool · syntax.py rule set v1</span>
    <span>El Psy Kongroo</span>
  </footer>
</div>

<script>
const entries=[...document.querySelectorAll('.entry')];
const tiers=[...document.querySelectorAll('.tier')];
const chips=[...document.querySelectorAll('.chip')];
const q=document.getElementById('q');
const hits=document.getElementById('hits');
const empty=document.getElementById('empty');
let tier='all';
const offCats=new Set();

function apply(){
  const term=q.value.trim().toLowerCase();
  let shown=0;
  for(const e of entries){
    const okTier = tier==='all' || e.dataset.tier===tier;
    const okCat  = !offCats.has(e.dataset.cat);
    const okText = !term || e.dataset.search.includes(term);
    const vis = okTier && okCat && okText;
    e.style.display = vis ? '' : 'none';
    if(vis) shown++;
  }
  for(const f of document.querySelectorAll('.file')){
    const any=[...f.querySelectorAll('.entry')].some(x=>x.style.display!=='none');
    f.style.display=any?'':'none';
  }
  for(const c of document.querySelectorAll('.chapter')){
    const any=[...c.querySelectorAll('.file')].some(x=>x.style.display!=='none');
    c.style.display=any?'':'none';
  }
  hits.textContent=shown+' / '+entries.length;
  empty.classList.toggle('show',shown===0 && entries.length>0);
}
tiers.forEach(t=>t.onclick=()=>{
  tiers.forEach(x=>x.classList.remove('on'));
  t.classList.add('on'); tier=t.dataset.tier; apply();
});
chips.forEach(c=>c.onclick=()=>{
  const k=c.dataset.cat;
  if(offCats.has(k)){offCats.delete(k);c.classList.remove('off');}
  else{offCats.add(k);c.classList.add('off');}
  apply();
});
q.oninput=apply;
apply();

const copy=document.getElementById('copy');
copy.onclick=async()=>{
  const ta=document.getElementById('raw');
  try{ await navigator.clipboard.writeText(ta.value); }
  catch(e){ ta.focus(); ta.select(); try{ document.execCommand('copy'); }catch(_){} }
  copy.textContent='Copied ✓'; copy.classList.add('done');
  setTimeout(()=>{ copy.textContent='Copy to clipboard'; copy.classList.remove('done'); },1600);
};
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(
        description="Generate the ObScriptTool syntax report (HTML + embedded text).")
    ap.add_argument("glob", nargs="?", default="input/**/*.csv",
                    help="glob for input CSV files (default: input/**/*.csv)")
    ap.add_argument("-o", "--out", default="syntax_report.html",
                    help="HTML output path (default: syntax_report.html)")
    ap.add_argument("-t", "--txt", default="syntax_report.txt",
                    help="plain-text output path; pass '' to skip (default: syntax_report.txt)")
    args = ap.parse_args()

    scanned, by_file, cat_counts, total = collect(args.glob)
    text = build_text_report(scanned, by_file, cat_counts, total)
    html_out = build_html(scanned, by_file, cat_counts, total, text)

    with open(args.out, "w", encoding="utf8") as f:
        f.write(html_out)
    if args.txt:
        with open(args.txt, "w", encoding="utf8") as f:
            f.write(text)

    print(f"Scanned {scanned} files | {len(by_file)} flagged | {total} anomalies")
    print(f"Wrote {args.out}" + (f" and {args.txt}" if args.txt else ""))


if __name__ == "__main__":
    main()
