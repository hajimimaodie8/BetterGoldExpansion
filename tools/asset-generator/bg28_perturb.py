#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg28 扰动矩阵（1.8 阶段 3 · 段 0 + 段 B）。

每个用例：① 记录改前 SHA256 ② 写入 ③ 跑 `validate_metal_data.py` ④ 断言退出码与
结论码 ⑤ **逐字节复原** ⑥ 断言 SHA256 回到改前值。

用例（6 条，>= 5）：
  P1 马铠护甲值 24 → 25                     期望红 [bg28-horse-values]
  P2 万坚黄心上限 10 → 9                    期望红 [bg28-horse-mechanics]
  P3 矛配方形状改一格                       期望红 [bg28-spear-recipe-pattern]
  P4 矛配方材料改错                         期望红 [bg28-spear-recipe-material]
  P5 马铠贴图改 1 字节                      期望红 [bg28-horse-textures]
  P6 只加一行注释                           期望绿（exit 0）
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = r"C:\Users\Lenovo\AppData\Local\Python\bin\python.exe"
VALIDATOR = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")


def sha(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run_validator() -> tuple[int, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, VALIDATOR], capture_output=True, env=env, cwd=ROOT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def case(name: str, path: str, mutate, expected_code: str | None) -> bool:
    full = os.path.join(ROOT, path)
    before = sha(full)
    with open(full, "rb") as f:
        original = f.read()
    try:
        with open(full, "rb") as f:
            data = f.read()
        mutated = mutate(data)
        if mutated == data:
            print(f"[{name}] 变更未生效")
            return False
        with open(full, "wb") as f:
            f.write(mutated)
        code, out = run_validator()
        ok = (code == 0) if expected_code is None else (code == 1 and expected_code in out)
        print(f"[{name}] exit={code} hit_expected={ok}"
              + ("" if expected_code is None else f" expected={expected_code}"))
        return ok
    finally:
        with open(full, "wb") as f:
            f.write(original)
        restored = sha(full)
        good = restored == before
        print(f"[{name}] restore_sha256_ok={good} {restored[:16]}")


def main() -> int:
    results = []
    results.append(case(
        "P1-horse-defense-25",
        "src/main/java/com/hjmmd_8/bettergold/material/MetalHorseArmor.java",
        lambda b: b.replace(b"PRECIOUS_DEFENSE = 24", b"PRECIOUS_DEFENSE = 25"),
        "bg28-horse-values"))
    results.append(case(
        "P2-sturdy-heart-cap-9",
        "src/main/java/com/hjmmd_8/bettergold/material/HorseArmorEvents.java",
        lambda b: b.replace(b"STURDY_HEART_CAP = 10.0F * 2.0F", b"STURDY_HEART_CAP = 9.0F * 2.0F"),
        "bg28-horse-mechanics"))
    results.append(case(
        "P3-spear-pattern-one-cell",
        "src/main/resources/data/bettergold/recipe/flamegold_spear.json",
        lambda b: b.replace(b'"  a"', b'" a "', 1),
        "bg28-spear-recipe-pattern"))
    results.append(case(
        "P4-spear-material-wrong",
        "src/main/resources/data/bettergold/recipe/flamegold_spear.json",
        lambda b: b.replace(b"bettergold:flamegold_ingot", b"bettergold:windgold_ingot", 1),
        "bg28-spear-recipe-material"))
    results.append(case(
        "P5-horse-texture-one-byte",
        "src/main/resources/assets/bettergold/textures/item/windgold_horse_armor.png",
        lambda b: b[:-1] + bytes([b[-1] ^ 0x01]),
        "bg28-horse-textures"))
    results.append(case(
        "P6-comment-only",
        "src/main/java/com/hjmmd_8/bettergold/material/HorseArmorEvents.java",
        lambda b: b + b"\n// bg28 perturb: comment only\n",
        None))
    print(f"SUMMARY {sum(results)}/{len(results)} hit")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
