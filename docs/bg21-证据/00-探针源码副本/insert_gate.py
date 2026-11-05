#!/usr/bin/env python3
"""Insert the bg21 gate section into tools/asset-generator/validate_metal_data.py (byte-safe, idempotent-guarded)."""
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VAL = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
BLOCK = (REPO / "probe" / "bg21" / "gate_section.py.txt").read_text(encoding="utf-8")

ANCHOR = "\n\n_EXIT_PROBLEM_LISTS = ("
TUPLE_OLD = "                       bg20_problems)"
TUPLE_NEW = ("                       # 2026-11-05 bg21：创造页 5 件「紧邻」顺序微调\n"
             "                       bg21_problems)")


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    raw = VAL.read_bytes()
    print("SHA BEFORE = %s (%d B)" % (sha(raw), len(raw)))
    txt = raw.decode("utf-8")
    if "bg21-summary" in txt:
        print("ERROR: already inserted")
        return 2
    if txt.count(ANCHOR) != 1 or txt.count(TUPLE_OLD) != 1:
        print("ERROR: anchors not unique: exit=%d tuple=%d"
              % (txt.count(ANCHOR), txt.count(TUPLE_OLD)))
        return 2
    txt = txt.replace(ANCHOR, "\n\n" + BLOCK.rstrip("\n") + ANCHOR, 1)
    txt = txt.replace(TUPLE_OLD, TUPLE_NEW, 1)
    out = txt.encode("utf-8")
    VAL.write_bytes(out)
    print("SHA AFTER  = %s (%d B, +%d B)" % (sha(out), len(out), len(out) - len(raw)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
