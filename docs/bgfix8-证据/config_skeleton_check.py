# -*- coding: utf-8 -*-
"""bgfix8 自证脚本：Config.java 的**代码骨架**（剥掉注释 + 所有字符串字面量）必须与 HEAD 逐字相同。

用途：证明本轮改的只有「注释」与「`.comment(...)` 的字符串」，键名 / 默认值 / 范围 / 顺序一字未动。
另附：把两个版本的 `.defineInRange("k", d, lo, hi)` 三元组逐个列出并比对。
"""
import re
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

PATH = "src/main/java/com/hjmmd_8/bettergold/config/Config.java"
old = subprocess.run(["git", "cat-file", "blob", "HEAD:" + PATH],
                     capture_output=True).stdout.decode("utf-8")
new = open(PATH, encoding="utf-8").read()


def skeleton(text):
    t = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    t = re.sub(r"//[^\n]*", "", t)
    t = re.sub(r'"(\\.|[^"\\])*"', '""', t)          # 所有字符串字面量 -> ""
    t = re.sub(r"\s+", "", t)                        # **连空白一起去掉**（注释行的空白不算改动）
    return t


print("skeleton identical (注释/空白已剥, 字面量已折叠) :", skeleton(old) == skeleton(new))
if skeleton(old) != skeleton(new):
    # 只报"差异出现在哪几处 .comment(...) 的字面量个数"——不打印整份骨架（几千字，没法读）
    co = re.findall(r"\.comment\(((?:\"\",?)+)\)", skeleton(old))
    cn = re.findall(r"\.comment\(((?:\"\",?)+)\)", skeleton(new))
    diff = [(i, a.count('""'), b.count('""'))
            for i, (a, b) in enumerate(zip(co, cn)) if a.count('""') != b.count('""')]
    print("  差异**只**出现在 .comment(...) 的字符串个数上：%d 处（第 N 处：旧段数 -> 新段数）" % len(diff))
    for i, a, b in diff:
        print("    comment[%d]  %d 段 -> %d 段" % (i, a, b))
    same_rest = re.sub(r"\.comment\((?:\"\",?)+\)", ".comment()", skeleton(old)) == \
        re.sub(r"\.comment\((?:\"\",?)+\)", ".comment()", skeleton(new))
    print("  把 .comment(...) 整块折叠后逐字相同 :", same_rest)

pat = re.compile(r'\.define(InRange|ListAllowEmpty)?\(\s*"([^"]+)"\s*(?:,\s*([^,)]+))?')
o = pat.findall(old)
n = pat.findall(new)
print("define-triples identical:", o == n, " count=%d/%d" % (len(o), len(n)))
for a, b in zip(o, n):
    if a != b:
        print("  DIFF", a, "->", b)

pats = re.compile(r'\.defineInRange\(\s*"([^"]+)"\s*,\s*([0-9.]+)D\s*,\s*([0-9.]+)D\s*,\s*([0-9.]+)D')
print("ranges identical:", pats.findall(old) == pats.findall(new),
      " count=%d" % len(pats.findall(new)))
print("key order (defineInRange/define 出现顺序) identical:",
      [m[1] for m in o] == [m[1] for m in n])
