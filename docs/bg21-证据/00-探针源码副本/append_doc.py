#!/usr/bin/env python3
"""Append the bg21 doc section (insertion only, 0 deletions) and fill in the line-count placeholders."""
import hashlib
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"
SEC = (REPO / "probe" / "bg21" / "doc_section.md").read_text(encoding="utf-8")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main():
    raw = DOC.read_bytes()
    before_lines = raw.decode("utf-8").count("\n")
    print("SHA BEFORE = %s (%d B, %d newlines)" % (sha(DOC), len(raw), before_lines))
    if "## 34." in raw.decode("utf-8"):
        print("ERROR: section already appended")
        return 2
    text = raw.decode("utf-8")
    if not text.endswith("\n"):
        print("ERROR: doc does not end with newline")
        return 2
    total = before_lines + 1 + SEC.count("\n")
    inserted = total - before_lines
    text2 = text + "\n" + SEC.replace("{{LINES}}", str(total)).replace("{{INSERTED}}", str(inserted))
    DOC.write_text(text2, encoding="utf-8")
    print("SHA AFTER  = %s (%d B, %d newlines, inserted=%d)"
          % (sha(DOC), DOC.stat().st_size, DOC.read_text(encoding="utf-8").count("\n"), inserted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
