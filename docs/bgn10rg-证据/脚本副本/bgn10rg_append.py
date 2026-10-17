#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一段 markdown **追加**到指定文件末尾（UTF-8 / 无 BOM，按原文件的行尾风格）。

⚠ 为什么不用 PowerShell：`Add-Content` 会按 ANSI 解码 / UTF-16 写，把已有的中文整段写坏
（本仓踩过，见 AGENTS 红线 11 与 `docs/构建与跑测注意事项.md` §四）。
用法: python build/bgn10rg_append.py <目标文件> <片段文件> [<片段文件> ...]
"""
from __future__ import annotations

import hashlib
import sys

sys.stdout.reconfigure(errors="replace")


def sha(p: str) -> str:
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest().upper()


def main() -> None:
    target = sys.argv[1]
    parts = sys.argv[2:]
    with open(target, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    crlf = "\r\n" in text
    before_len = len(text)
    before_sha = sha(target)
    chunk = "".join(open(p, "rb").read().decode("utf-8") for p in parts)
    if crlf:
        chunk = chunk.replace("\r\n", "\n").replace("\n", "\r\n")
    if not text.endswith(("\n", "\r\n")):
        text += "\r\n" if crlf else "\n"
    text += chunk
    with open(target, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("[ok] 追加 %d 字符 → %s" % (len(chunk), target))
    print("     字符数 %d → %d / 行尾 %s" % (before_len, len(text), "CRLF" if crlf else "LF"))
    print("     sha256 %s → %s" % (before_sha[:16], sha(target)[:16]))


if __name__ == "__main__":
    main()
