# -*- coding: utf-8 -*-
"""bgfix8 一次性脚本：把 §29 追加进 `docs/1.6-规格.md`（UTF-8 无 BOM、LF）。"""
import os
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
SPEC = os.path.join(REPO, "docs", "1.6-规格.md")
PART = os.path.join(REPO, "probe", "bgfix8", "spec29.md")

raw = open(SPEC, "rb").read()
assert raw[:3] != b"\xef\xbb\xbf", "spec 有 BOM，先停下"
assert raw.count(b"\r\n") == 0, "spec 现在是 CRLF，先停下"
text = raw.decode("utf-8")
add = open(PART, encoding="utf-8").read()
if u"# 二十九、`bgfix8`" in text:
    raise SystemExit("SETUP-FAIL: §29 已经存在（不重复追加）")
before_lines = text.count("\n")
new = text.rstrip("\n") + "\n" + add
open(SPEC, "wb").write(new.encode("utf-8"))
raw2 = open(SPEC, "rb").read()
print("appended §29: %d -> %d lines, %d -> %d bytes, CRLF=%d, BOM=%s"
      % (before_lines, raw2.decode("utf-8").count("\n"), len(raw), len(raw2),
         raw2.count(b"\r\n"), raw2[:3] == b"\xef\xbb\xbf"))
