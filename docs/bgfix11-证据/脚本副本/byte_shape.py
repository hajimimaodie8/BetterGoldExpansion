# -*- coding: utf-8 -*-
"""bgfix11 · 实测生成器脚本的字节形状（行尾 / 锚点 occ）。"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
p = "tools/asset-generator/validate_metal_data.py"
b = open(p, "rb").read()
print("bytes", len(b), "CRLF", b.count(b"\r\n"), "LF", b.count(b"\n"), "bareCR", b.count(b"\r") - b.count(b"\r\n"))
print("ends_with_nl", b.endswith(b"\n"))
anchors = [
    b'#     _BGFIX10_CJK_OK = {"bettergold.handbook.page.knowledge_1_summary"}',
    b'    if _bg10_k in _BGFIX10_CJK_OK:',
    b'bgfix11_problems: list[str] = []',
    b'_BGFIX11_K1S_NEW_EN = (',
]
for a in anchors:
    print("occ=%d  %r" % (b.count(a), a[:70]))
