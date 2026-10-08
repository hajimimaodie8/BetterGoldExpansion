# -*- coding: utf-8 -*-
"""bgfix6 自证：六个校验器改前后「旧打印 / 旧注释」有没有被删（按去缩进后的行文本比对）。

判据：HEAD 版本里每一行 `print(...)` 或中文注释，去掉首尾空白后必须在工作区版本里**仍然找得到**。
（本轮纪律：旧行为 / 旧打印原文保留，如需改动就地标注。）
用法: python check-old-prints-kept.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FILES = ["check_jar_clean.py", "check_forced_chunks.py", "validate_metal_assets.py",
         "validate_metal_data.py", "validate_trim_assets.py", "validate_advancements.py"]

try:
    # 证据文件必须是 UTF-8（本机控制台是 GBK；重定向到文件时 GBK 会写成乱码）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

bad_total = 0
for name in FILES:
    head = subprocess.run(["git", "show", f"HEAD:tools/asset-generator/{name}"],
                          cwd=str(REPO), capture_output=True).stdout.decode("utf-8")
    now = (REPO / "tools" / "asset-generator" / name).read_text(encoding="utf-8")
    now_set = {ln.strip() for ln in now.splitlines()}
    # 只看"有语义的旧行"：print(...) 与含中文的行（注释/提示）
    old_keep = [ln.strip() for ln in head.splitlines()
                if ln.strip() and (ln.strip().startswith("print(") or re.search(r"[\u4e00-\u9fff]", ln))]
    missing = []
    for ln in old_keep:
        if ln in now_set:
            continue
        # 单行 docstring 会被扩写成多行：它的**正文**只要还在文件里就算保留
        if ln.startswith('"""') and ln.strip('"').strip() and ln.strip('"').strip() in now:
            continue
        missing.append(ln)
    # print(...) 可能被就地改写过（例如 L43 那行被合并进 f-string）⇒ 单独报"print 前缀"缺失
    old_prints = [ln.strip() for ln in head.splitlines() if ln.strip().startswith("print(")]
    lost_prints = [ln for ln in old_prints if ln not in now_set]
    bad_total += len(missing)
    print(f"{name:28s} 旧语义行 {len(old_keep):4d} 条；工作区找不到的 = {len(missing)}"
          f"（其中 print 行 {len(lost_prints)}）")
    for ln in missing[:6]:
        print(f"    MISSING: {ln[:110]}")

print(f"[bgfix6-old-lines-{'ok' if bad_total == 0 else 'fail'}] 旧行丢失总数 = {bad_total}")
sys.exit(0 if bad_total == 0 else 1)
