# -*- coding: utf-8 -*-
"""bgfix8：把 §29.4~§29.8 追加进 `docs/1.6-规格.md`（UTF-8 无 BOM、LF）。"""
import os
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
SPEC = os.path.join(REPO, "docs", "1.6-\u89c4\u683c.md")
PART = os.path.join(REPO, "probe", "bgfix8", "spec29b.md")

raw = open(SPEC, "rb").read()
assert raw[:3] != b"\xef\xbb\xbf", "spec 有 BOM"
assert raw.count(b"\r\n") == 0, "spec 现在是 CRLF"
text = raw.decode("utf-8")
add = open(PART, encoding="utf-8").read()
if u"29.4 \u6270\u52a8\u5b9e\u6d4b" in text:
    raise SystemExit("SETUP-FAIL: §29.4~§29.8 已经追加过（不重复）")
new = text.rstrip("\n") + "\n" + add
open(SPEC, "wb").write(new.encode("utf-8"))
raw2 = open(SPEC, "rb").read()
print("appended §29.4~29.8: %d -> %d bytes; lines=%d; CRLF=%d; BOM=%s"
      % (len(raw), len(raw2), raw2.decode("utf-8").count("\n"), raw2.count(b"\r\n"),
         raw2[:3] == b"\xef\xbb\xbf"))
