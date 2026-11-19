#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1.8 阶段 3 · 段 A（§G 长矛）的**扰动自证**：每条用例改一处 → 跑数据关卡 → 复原 → SHA256 自证。

判据（docs/构建与跑测注意事项.md §七）：
* 期望红的用例：关卡 **exit=1** 且输出里出现该用例的 `[bg27-…]` 代码（= 命中了那条断言，不是脚本自己坏）；
* 期望绿的用例（只改注释）：关卡 **exit=0**；
* 每轮结束都用**读入时的原始字节**写回，并核对 SHA256 == 改动前；
* `exit=2` 一律算用例坏（脚本自身 / 前置缺失），不算命中。

用法：``python tools/asset-generator/bg27_perturb.py``
"""

from __future__ import annotations

import hashlib
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
VALIDATOR = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")

REG = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "spear",
                   "SpearRegistration.java")
CREATIVE = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "material",
                        "CreativeSections.java")
FAMILY = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "material",
                      "MetalFamily.java")
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures", "item",
                   "flamegold_spear.png")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def run_validator() -> tuple[int, str]:
    proc = subprocess.run([PY, VALIDATOR], cwd=ROOT, capture_output=True)
    out = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    return proc.returncode, out


CASES = [
    # (id, 文件, 原文, 替换, 期望 exit, 期望命中的关卡代码, 说明)
    ("R1-family-damage", REG, "FAMILY_DAMAGE = 7.0F", "FAMILY_DAMAGE = 7.5F", 1,
     "bg27-spear-values", "贵金属矛伤害 7 → 7.5（某族矛数值改错）"),
    ("R2-chaosalloy-phase", REG, "CHAOSALLOY_DISMOUNT_TICK = 40", "CHAOSALLOY_DISMOUNT_TICK = 35", 1,
     "bg27-spear-values", "崩乱合金矛「发动 2 秒」40 → 35 tick"),
    ("R3-creative-order", CREATIVE, 'Map.entry("spear", 1)', 'Map.entry("spear", 4)', 1,
     "bg27-creative", "长矛从剑与重锤之间挪到弩后面"),
    ("R4-metal-weapon", FAMILY, "|| this.extraWeapons.contains(item)", "|| false", 1,
     "bg27-metal-weapon", "isWeapon 不再认识长矛（贵金属矛双触发失效）"),
    ("R5-texture-byte", TEX, None, None, 1,
     "bg27-textures", "改一个贴图字节（1:1 复制的锚点）"),
    ("R6-comment-only", REG, "    /** §G-30 贵金属矛（10 族各一）：7 / 1.1 / 1.4 */",
     "    /** §G-30 贵金属矛（10 族各一）：7 / 1.1 / 1.4 —— 只改注释，行为不变 */", 0,
     None, "只改注释（必须仍然绿）"),
]


def main() -> int:
    lines = []
    ok = 0
    for cid, path, old, new, want_exit, want_code, why in CASES:
        original = io.open(path, "rb").read()
        before = sha(original)
        if old is not None:
            text = original.decode("utf-8")
            if old not in text:
                lines.append("%s SKIP：原文没找到（脚本坏了）" % cid)
                continue
            mutated = text.replace(old, new, 1).encode("utf-8")
        else:
            mutated = bytearray(original)
            mutated[100] ^= 0xFF           # 翻一个字节（PNG 仍能读，但 SHA 变了）
            mutated = bytes(mutated)
        if mutated == original:
            lines.append("%s SKIP：改动没生效" % cid)
            continue
        try:
            io.open(path, "wb").write(mutated)
            exit_code, out = run_validator()
        finally:
            io.open(path, "wb").write(original)
        after = sha(io.open(path, "rb").read())
        restored = "OK" if after == before else "FAILED"
        hit = (want_code is None) or (want_code in out)
        passed = (exit_code == want_exit) and hit and restored == "OK"
        ok += 1 if passed else 0
        lines.append("%s %s :: exit=%d（期望 %d） hit=%s 复原=%s\n    %s"
                     % (cid, "PASS" if passed else "FAIL", exit_code, want_exit,
                        "yes" if hit else "no", restored, why))
    lines.append("SUMMARY pass=%d/%d" % (ok, len(CASES)))
    report = "\n".join(lines)
    print(report)
    out_dir = os.path.join(ROOT, "docs", "bg27-证据")
    os.makedirs(out_dir, exist_ok=True)
    io.open(os.path.join(out_dir, "03-扰动.txt"), "w", encoding="utf-8", newline="\n").write(report + "\n")
    return 0 if ok == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
