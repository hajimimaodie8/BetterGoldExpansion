# -*- coding: utf-8 -*-
"""bgfix11 · 生成 Java 源里 EXPECT_ZH 的正确 \\uXXXX 分片（免得手抄错，例如 栏=U+6805? 实测是 U+680F）。"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
zh = json.load(open("src/main/resources/assets/bettergold/lang/zh_cn.json", encoding="utf-8"))
v = zh["bettergold.handbook.page.knowledge_1_summary"]
esc = "".join(("\\u%04x" % ord(c)) if ord(c) > 126 else (c if c != '"' else '\\"') for c in v)
print("len =", len(v))
print("单行:")
print('"%s"' % esc)
print()
print("分片（每片 90 个转义单元）:")
parts, cur = [], ""
for ch in v:
    cur += ("\\u%04x" % ord(ch)) if ord(ch) > 126 else (ch if ch != '"' else '\\"')
    if len(cur) >= 90:
        parts.append(cur)
        cur = ""
if cur:
    parts.append(cur)
for i, p in enumerate(parts):
    tail = '";' if i == len(parts) - 1 else '"'
    head = '            "' if i else '            "'
    print("%s%s%s" % (head, p, tail if i == len(parts) - 1 else '"'))
