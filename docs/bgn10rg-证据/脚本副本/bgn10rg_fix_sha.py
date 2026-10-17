#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修上一个脚本的误伤：`re.search` 命中了**注释里**的旧常量（第 6124 行），
把一行留档注释写坏 + 生成了一行带多余反引号的赋值（会把关口变成 SyntaxError）。

修复三件事（逐字节写回）：
  1. 第 6124 行恢复成 `git HEAD` 里的原文（旧值留档，不删）；
  2. 删掉误生成的那一行（带多余反引号的 `_BGN10_ZH_AFTER_SHA = "432A…"``）；
  3. 把**真正生效**的那个常量（在 §bg-n10r8 那一组注释下面的赋值）改成当前 zh 的 SHA，
     并在上方加一行"本轮第二次改（弩的材料数）"的记账。

教训：改常量脚本必须**锚在行首**（`^_BGN10_ZH_AFTER_SHA`，MULTILINE），
      不能 `re.search` 任意位置 —— 这个文件里同一个名字在注释里出现过 6 次。
"""
from __future__ import annotations

import hashlib
import re
import sys

sys.stdout.reconfigure(errors="replace")

TARGET = "tools/asset-generator/validate_metal_data.py"
ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
ORIG_COMMENT = ('#   `_BGN10_ZH_AFTER_SHA = '
                '"BF9DA6E316C087D68C934790CDEB6FAD36FA3804219AA174DCB289B4DCE7561A"`')


def main() -> None:
    with open(TARGET, "rb") as fh:
        text = fh.read().decode("utf-8")
    new_zh = hashlib.sha256(open(ZH, "rb").read()).hexdigest().upper()

    # 1) 恢复被写坏的那行注释
    broken = re.search(r"^#   `# 旧值（bg-n10rg 修正弩的材料数后[^\n]*\n", text, re.M)
    if not broken:
        raise SystemExit("[失败] 找不到被写坏的那行注释")
    text = text[:broken.start()] + text[broken.end():]
    # 原来那行注释现在没了（被覆盖）⇒ 在 §bg-n10r4 收尾那段后面补回原文
    anchor = "# ⇒ 文件 SHA 与上一轮中断时那次写入不同。旧常量原文留档（当时那次的落点/文案已无法逐字节复现）：\n"
    if text.count(anchor) != 1:
        raise SystemExit("[失败] 找不到插入原文的锚点")
    text = text.replace(anchor, anchor + ORIG_COMMENT + "\n", 1)

    # 2) 删掉误生成的那一行（行首是赋值、行尾多一个反引号）
    bad = re.search(r'^_BGN10_ZH_AFTER_SHA = "432A5297852A47B7[0-9A-F]*"`\n', text, re.M)
    if not bad:
        raise SystemExit("[失败] 找不到误生成的那一行")
    text = text[:bad.start()] + text[bad.end():]

    # 3) 真正生效的常量 = 行首那个（没被注释掉的）
    active = re.search(r'^_BGN10_ZH_AFTER_SHA = "([0-9A-F]{64})"$', text, re.M)
    if not active:
        raise SystemExit("[失败] 找不到生效中的 _BGN10_ZH_AFTER_SHA")
    old = active.group(1)
    note = ("# 旧值（bg-n10rg 把手册正文里弩的材料数写错后改正，原文留档、不删）：zh " + old[:32] + "…\n")
    text = text.replace(active.group(0), note + '_BGN10_ZH_AFTER_SHA = "%s"' % new_zh, 1)
    with open(TARGET, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("[ok] 注释已恢复，误生成的行已删，生效常量 %s → %s" % (old[:16], new_zh[:16]))
    # 4) 自证：编译一遍（语法错会在这里暴露）
    import py_compile
    py_compile.compile(TARGET, cfile="build/bgn10rg_vmd.pyc", doraise=True)
    print("[ok] py_compile 通过")


if __name__ == "__main__":
    main()
