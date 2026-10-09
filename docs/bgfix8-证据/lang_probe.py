# -*- coding: utf-8 -*-
"""bgfix8 一次性脚本：语言文件体检（BOM / 行尾 / 目标行现状），只读。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
LANGS = [os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang",
                      n) for n in ("zh_cn.json", "en_us.json")]

for p in LANGS:
    raw = open(p, "rb").read()
    print("=== %s ===" % os.path.basename(p))
    print("  size=%d  BOM=%s  CRLF=%d  LF=%d  last_byte=%r"
          % (len(raw), raw[:3] == b"\xef\xbb\xbf", raw.count(b"\r\n"), raw.count(b"\n"),
             raw[-1:]))
    txt = raw.decode("utf-8")
    # 解析结果与行数一致性（确保它是标准 JSON、行级替换安全）
    data = json.loads(txt)
    print("  json keys=%d  lines=%d" % (len(data), txt.count("\n")))
    for k in ("bettergold.handbook.page.knowledge_1_summary",
              "bettergold.handbook.page.knowledge_1_left",
              "bettergold.handbook.page.knowledge_1_right"):
        print("  key-present %-52s %s" % (k, k in data))
    # 目标行的实际字节形态
    for ln in txt.split("\n"):
        if "knowledge_1_summary" in ln:
            print("  LINE %r" % ln[:120])
