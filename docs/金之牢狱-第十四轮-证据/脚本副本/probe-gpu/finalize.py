# -*- coding: utf-8 -*-
"""收尾归档刷新：把最终态读数 / 构建日志 / 文档 SHA / 全部脚本复制进证据目录，并重写清单。"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
E14 = os.path.join(ROOT, "docs", "金之牢狱-第十四轮-证据")
SCRIPTS = os.path.join(E14, "脚本副本")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


rows = []


def cp(src, dst):
    if not os.path.exists(src):
        print("[skip]", os.path.relpath(src, ROOT))
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    rows.append((os.path.relpath(dst, ROOT), os.path.getsize(dst), sha(dst)))


cp(os.path.join(ROOT, "build", "gp14_gates.txt"), os.path.join(E14, "03-八关卡读数.txt"))
cp(os.path.join(ROOT, "build", "gp14_build2.log"), os.path.join(E14, "05b-构建日志-收尾.txt"))
cp(os.path.join(ROOT, "build", "gp14_doc_sha.txt"), os.path.join(E14, "09-文档SHA.txt"))
for f in os.listdir(os.path.join(ROOT, "probe", "gpu")):
    if f.endswith(".py"):
        cp(os.path.join(ROOT, "probe", "gpu", f), os.path.join(SCRIPTS, "probe-gpu", f))

# 已有的大件也计入清单（不重复复制）
for f in ("01-探针报告.json", "02-A级读数.md", "04-扰动矩阵.txt", "05-构建日志.txt",
          "06-runServer日志.txt", "07-改动SHA.txt", "08-探针error.txt"):
    p = os.path.join(E14, f)
    if os.path.exists(p):
        rows.append((os.path.relpath(p, ROOT), os.path.getsize(p), sha(p)))
for f in ("GprProbe.java.txt",):
    p = os.path.join(SCRIPTS, f)
    if os.path.exists(p):
        rows.append((os.path.relpath(p, ROOT), os.path.getsize(p), sha(p)))

rows = sorted(set(rows))
L = ["# 第十四轮证据归档清单（size 5 → 4）", "",
     "| 文件 | 大小 | SHA256 |", "|---|---|---|"]
for p, n, h in rows:
    L.append("| `%s` | %d B | `%s` |" % (p, n, h))
open(os.path.join(E14, "00-归档清单.md"), "w", encoding="utf-8", newline="\n").write(
    "\n".join(L) + "\n")
print("[gp14] archive list: %d entries" % len(rows))
