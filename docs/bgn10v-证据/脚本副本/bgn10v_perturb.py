#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10 轮3 扰动实测（临时脚本，收尾删）。

口径（`docs/构建与跑测注意事项.md` §七）：
  * 每个用例：**逐字节**改一处 → 跑 `validate_metal_data.py` → 记 exit → **逐字节**复原 → 核 SHA256；
  * 期望：`exit 1` = 命中（关卡能红）；`exit 0` = 不该红（只改注释类）；`exit 2` = 前置坏（单独一例）；
  * 输出 `exit` 与 `hit_expected` 两列 + SHA256，任一不符 ⇒ 本脚本 exit 1。

用法：py -3 bgn10v_perturb.py
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

# Windows 控制台是 GBK：校验器输出里的非 GBK 字符会让 print 直接抛 UnicodeEncodeError
# （本仓踩过同款：`docs/构建与跑测注意事项.md` §七 的 bg-final 那次）。
try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

REPO = Path(r"E:\mc\mcmod\bettergold-template-1.21.1")
VALIDATOR = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
FORMS_PY = REPO / "tools" / "asset-generator" / "metal_forms.py"
ALLMETALS = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "material" / "AllMetals.java"
CHAOSRANGE = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "material" / "ChaosRange.java"
CHAOSWIRING = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "material" / "ChaosWiring.java"
BOOT = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "bettergold.java"
MIXIN = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "mixin" / "CrossbowChargeDurationMixin.java"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def run_validator() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = ""
    for line in (r.stdout or "").splitlines():
        if "问题" in line or "bgn10" in line:
            tail = line.strip()[:150]
    return r.returncode, tail


def apply_bytes(p: Path, old: bytes, new: bytes) -> None:
    data = p.read_bytes()
    if data.count(old) != 1:
        raise SystemExit(f"锚点不唯一（{p.name}）：出现 {data.count(old)} 次")
    p.write_bytes(data.replace(old, new))


def case(name: str, expect_exit: int, edits: list[tuple[Path, bytes, bytes]] | None) -> bool:
    """edits=None ⇒ 只跑一次基线（不碰任何文件）"""
    before = {p: p.read_bytes() for p, _, _ in (edits or [])}
    shas = {p: sha(p) for p in before}
    try:
        for p, old, new in (edits or []):
            apply_bytes(p, old, new)
        code, tail = run_validator()
    finally:
        for p, data in before.items():
            p.write_bytes(data)
    restored = all(sha(p) == s for p, s in shas.items())
    ok = (code == expect_exit) and restored
    print(f"{'OK ' if ok else 'BAD'} {name:<52} exit={code} want={expect_exit} "
          f"restored={restored} :: {tail}")
    return ok


def main() -> None:
    print(f"baseline sha256(validate_metal_data.py) = {sha(VALIDATOR)[:16]}")
    results = []

    # 0) 基线：本来就该绿
    results.append(case("0 基线（不动）", 0, None))

    # 1) 只改注释 ⇒ 仍绿
    results.append(case(
        "1 只在 ChaosRange 加一行注释（应仍 0）", 0,
        [(CHAOSRANGE, "public final class ChaosRange {".encode(),
          "public final class ChaosRange {\n    // bgn10v 扰动：纯注释，不该影响任何断言".encode())]))

    # 2) 改区间一端（剑 4..8 → 4..9）⇒ 红
    results.append(case(
        "2 改一端：剑 4..8 → 4..9", 1,
        [(ALLMETALS, "chaosRange(MetalFamily.Form.SWORD, ChaosRange.Channel.ATTACK, 4, 8)".encode(),
          "chaosRange(MetalFamily.Form.SWORD, ChaosRange.Channel.ATTACK, 4, 9)".encode())]))

    # 3) 把公式复制第二份到 ChaosWiring ⇒ 红（公式只许一处）
    #    ⚠ 扰动必须**逐字**复制那条公式（`current == range.min ? range.max : range.min`），
    #    否则命中的是"没生效"而不是"关卡没抓"（本仓 §3.11 的第一条陷阱）。
    results.append(case(
        "3 公式复制第二份（ChaosWiring 里再写一遍）", 1,
        [(CHAOSWIRING, b"public final class ChaosWiring {",
          b"public final class ChaosWiring {\n"
          b"    static float copied(float current, ChaosRange.Range range) "
          b"{ return current == range.min ? range.max : range.min; }")]))

    # 4) 把某件攻速改错（剑 1.6 → 1.7）⇒ 红
    results.append(case(
        "4 攻速改错：剑 1.6 → 1.7", 1,
        [(ALLMETALS, b"attackSpeed(MetalFamily.Form.SWORD, 1.6F)",
          b"attackSpeed(MetalFamily.Form.SWORD, 1.7F)")]))

    # 5) 拆掉接线层的注册 ⇒ 红
    results.append(case(
        "5 删掉 ChaosWiring 的注册", 1,
        [(BOOT, b"        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.material.ChaosWiring.class);\n",
          b"")]))

    # 6) 弩回到"不读本族蓄力"⇒ 红（24 tick 分支没了）
    results.append(case(
        "6 弩 mixin 不再走 chargeDuration（24 tick 分支没了）", 1,
        [(MIXIN, b"return MetalWeapons.MetalCrossbowItem.chargeDuration(stack, shooter);",
          b"return original; // bgn10v perturb")]))

    # 7) 删 metal_forms.py ⇒ 前置坏 = exit 2 / 1（脚本自身出错不许变 0）
    forms_backup = FORMS_PY.read_bytes()
    forms_sha = sha(FORMS_PY)
    try:
        FORMS_PY.unlink()
        code, tail = run_validator()
        ok = code in (1, 2)
        print(f"{'OK ' if ok else 'BAD'} {'7 前置缺失：删 metal_forms.py':<52} exit={code} "
              f"want=1或2 :: {tail}")
        results.append(ok)
    finally:
        FORMS_PY.write_bytes(forms_backup)
    print(f"{'OK ' if sha(FORMS_PY) == forms_sha else 'BAD'} 7b metal_forms.py 逐字节复原 "
          f"sha={sha(FORMS_PY)[:16]}")

    print()
    print(f"扰动矩阵：{sum(1 for r in results if r)}/{len(results)} 符合预期")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
