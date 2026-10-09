# -*- coding: utf-8 -*-
"""bgfix8 一次性脚本：把被 `git checkout` 写成 CRLF 的两个语言文件还原成 **LF**（本仓约定）。

⚠ 根因（本轮实测）：本仓 `core.autocrlf=true` ⇒ `git checkout -- <path>` 会把工作区文件
   写成 **CRLF**（`git status` 看不出来，因为它按规范化后的内容比较）。
   ⇒ 临时改动一律用**字节复制**备份/复原，不要用 `git checkout`（与 ex/05 那条口径同源）。
"""
import os
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
LANG = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")
for name in ("zh_cn.json", "en_us.json"):
    p = os.path.join(LANG, name)
    raw = open(p, "rb").read()
    n_crlf = raw.count(b"\r\n")
    fixed = raw.replace(b"\r\n", b"\n")
    if n_crlf:
        with open(p, "wb") as fh:
            fh.write(fixed)
    raw2 = open(p, "rb").read()
    print("%-12s CRLF(before)=%d -> after=%d  size %d -> %d  BOM=%s last=%r"
          % (name, n_crlf, raw2.count(b"\r\n"), len(raw), len(raw2),
             raw2[:3] == b"\xef\xbb\xbf", raw2[-1:]))
