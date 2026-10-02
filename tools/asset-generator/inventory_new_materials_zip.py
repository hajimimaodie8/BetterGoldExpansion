# -*- coding: utf-8 -*-
"""只读清点「更有用的金 新约8.zip」（1.5 武器素材）：解到 build/新约8-清单/ 并打印清单。

用法:
    python inventory_new_materials_zip.py [<zip 路径>] [<解包目录>]
默认 zip = E:\\mc\\mc资料\\更有用的金 新约8.zip；默认解到 <仓库>/build/新约8-清单。
"""
import io
import os
import sys
import zipfile
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZIP = sys.argv[1] if len(sys.argv) > 1 else r"E:\mc\mc资料\更有用的金 新约8.zip"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "build", "新约8-清单")

os.makedirs(OUT, exist_ok=True)
print("ZIP exists:", os.path.isfile(ZIP))
zf = zipfile.ZipFile(ZIP)
entries = zf.infolist()
print("total entries:", len(entries))

dirs = [e for e in entries if e.is_dir()]
files = [e for e in entries if not e.is_dir()]
print("dirs:", len(dirs), "files:", len(files))

# 解包（保留目录结构）
zf.extractall(OUT)

ext = Counter()
for e in files:
    ext[os.path.splitext(e.filename)[1].lower()] += 1
print("ext counts:", dict(ext))

print()
print("=== FULL LIST (name | size) ===")
for e in entries:
    tag = "DIR " if e.is_dir() else "FILE"
    print(f"{tag} {e.filename} | {e.file_size}")

print()
print("=== PNG sizes (from header) ===")
def png_size(data):
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w = int.from_bytes(data[16:20], "big")
    h = int.from_bytes(data[20:24], "big")
    return (w, h)

for e in files:
    if not e.filename.lower().endswith(".png"):
        continue
    with zf.open(e) as fh:
        head = fh.read(33)
    size = png_size(head)
    print(f"PNG {e.filename} | {size}")

print()
print("=== per top dir ===")
buckets = defaultdict(list)
for e in files:
    parts = e.filename.replace("\\", "/").split("/")
    top = parts[0] if len(parts) > 1 else "(root)"
    buckets[top].append(e.filename)
for k, v in buckets.items():
    print(f"[{k}] {len(v)} files")
zf.close()
