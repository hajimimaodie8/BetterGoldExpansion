#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 文档补丁 2：把 §19.5 ~ §19.9（扰动 / 构建与六校验器 / A 级 / 共享文件 / 人眼）追加到立档末尾。

**只追加**（CRLF 与插进去那一节一致），不碰任何既有行。

用法：py -3 bgn10rc_write_docs2.py [--apply]
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"
SECTION = Path(__file__).with_name("bgn10rc_doc_section2.md.txt")


def main() -> None:
    apply = "--apply" in sys.argv
    raw = DOC.read_bytes()
    text = raw.decode("utf-8")
    print("改前: %d B  sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))
    if "### 19.5" in text:
        raise SystemExit("§19.5 已经写过 —— 不要重复追加")
    if "### 19.4" not in text:
        raise SystemExit("前置缺失：§19.4 不在文件里（先跑 bgn10rc_write_docs.py）")
    body = SECTION.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\n", "\r\n")
    out = text
    if not out.endswith("\r\n"):
        out += "\r\n"
    out += body
    data = out.encode("utf-8")
    print("改后: %d B（+%d B，+%d 行）" % (len(data), len(data) - len(raw),
                                          out.count("\n") - text.count("\n")))
    if apply:
        DOC.write_bytes(data)
        print("写盘后 sha256=%s" % hashlib.sha256(DOC.read_bytes()).hexdigest())
    else:
        print("（演练，未写盘）")


if __name__ == "__main__":
    main()
