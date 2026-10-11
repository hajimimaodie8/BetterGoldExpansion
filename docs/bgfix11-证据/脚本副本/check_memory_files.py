# -*- coding: utf-8 -*-
"""bgfix11 · 经验层文件完整性检查（行数 / UTF-8 / 新行插入位置）。"""
import hashlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
for p in (r"E:\mc\mcmod\mod_experience\mcmod_experience.md",
          r"E:\mc\mcmod\mod_experience\ex\03-验证与证据.md",
          r"E:\mc\mcmod\mod_experience\ex\06-贴图模型素材.md"):
    b = open(p, "rb").read()
    t = b.decode("utf-8")
    lines = t.split("\n")
    print("%-24s bytes=%d lines=%d CRLF=%d ends_nl=%s sha=%s"
          % (p.rsplit("\\", 1)[-1], len(b), len(lines), b.count(b"\r\n"), t.endswith("\n"),
             hashlib.sha256(b).hexdigest().upper()[:16]))
m = open(r"E:\mc\mcmod\mod_experience\mcmod_experience.md", encoding="utf-8").read().split("\n")
rows = [i + 1 for i, l in enumerate(m) if l.startswith("| 2026-10-11 | bettergold")]
print("2026-10-11 bettergold 行号:", rows)
for i in rows:
    print("  L%d 前 70 字: %s" % (i, m[i - 1][:70]))
    print("  L%d 行尾 40 字: ...%s" % (i, m[i - 1][-40:]))
    print("  L%d 竖线数: %d" % (i, m[i - 1].count("|")))
print("bgfix10 行里 '第 0 页' 之外的完整性锚点：")
for needle in ("三方比对逐条清单与行号", "23 份", "bgfix10-证据"):
    hits = [i + 1 for i, l in enumerate(m) if needle in l]
    print("  %-22s -> %s" % (needle, hits))
