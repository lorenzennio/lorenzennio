#!/usr/bin/env python3
"""Sync the 3 most recent news items from lorenzennio.github.io into README.md.

Reads _data/news.yml from the website repo (public, no auth needed) and
replaces the block between the NEWS:START/NEWS:END markers in README.md.
"""
import re
import sys
import urllib.request

import yaml

NEWS_URL = "https://raw.githubusercontent.com/lorenzennio/lorenzennio.github.io/master/_data/news.yml"
README_PATH = "README.md"
START = "<!-- NEWS:START -->"
END = "<!-- NEWS:END -->"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Matches inline LaTeX math like \(B^+\to K^+X\) so it can be shown as
# plain-ish inline code instead of raw, unrendered backslashes -- GitHub's
# README renderer has no MathJax/KaTeX support.
MATH_RE = re.compile(r"\\\((.+?)\\\)")


def fetch_news():
    with urllib.request.urlopen(NEWS_URL, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    items = yaml.safe_load(raw) or []
    return items[:3]


def clean_text(text):
    return MATH_RE.sub(lambda m: f"`{m.group(1)}`", text)


def format_item(item):
    date = item["date"]
    if hasattr(date, "month"):
        year, month = date.year, date.month
    else:
        year, month, _ = str(date).split("-")
        year, month = int(year), int(month)
    label = f"{MONTHS[month - 1]} {year}"
    return f"- {label} — {clean_text(item['text'])}"


def main():
    items = fetch_news()
    if not items:
        print("No news items fetched; leaving README.md untouched", file=sys.stderr)
        sys.exit(1)

    block = "\n".join(format_item(item) for item in items)

    with open(README_PATH, encoding="utf-8") as f:
        readme = f.read()

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(readme):
        print(f"Markers {START} / {END} not found in {README_PATH}", file=sys.stderr)
        sys.exit(1)

    # Use a callable replacement: re.sub on a *string* replacement decodes
    # backslash escapes (\t, \n, \b, ...), which would corrupt the literal
    # LaTeX backslashes now embedded in `block`.
    new_readme = pattern.sub(lambda _: f"{START}\n{block}\n{END}", readme)

    if new_readme != readme:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("README.md updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
