# -*- coding: utf-8 -*-
"""bg-n10fix 扰动矩阵（11 用例：10 条各一 + 1 条"只改注释仍绿"）。

每个用例：读字节 -> 断言锚点存在 -> 改 -> 跑关卡 -> 逐字节复原 -> 校验 SHA256。
输出：用例 / 期望 / 关卡 exit / 命中 / SHA 复原。
"""
import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
GATE = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
J = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
RES = REPO / "src" / "main" / "resources"
DATA = RES / "data" / "bettergold"

CASES = [
    ("01-blast", DATA / "recipe" / "chaos_coin_blasting.json",
     b'"minecraft:blasting"', b'"minecraft:smelting"', 1),
    ("02-cutout", RES / "assets" / "bettergold" / "models" / "block" / "golden_torchflower.json",
     b'"render_type": "minecraft:cutout",', b'', 1),
    ("03-stew-ticks", J / "block" / "GoldenTorchflowerBlock.java",
     b"STEW_TICKS = 16 * 20", b"STEW_TICKS = 16 * 10", 1),
    ("03-stew-level", J / "event" / "ModEvents.java",
     b"GoldenTorchflowerBlock.STEW_TICKS, 2", b"GoldenTorchflowerBlock.STEW_TICKS, 1", 1),
    ("04-book-stack", J / "material" / "ChaosItems.java",
     b"stacksTo(16)", b"stacksTo(1)", 1),
    ("05-hardness", J / "material" / "AllMetals.java",
     b"55.0F * 2.0F / 3.0F", b"55.0F", 1),
    ("06-always-edible", J / "material" / "ChaosItems.java",
     b"alwaysEdible()", b"alwaysEdibleX()", 1),
    ("07-hover", J / "entity" / "MoneyGremlin.java",
     b"HOVER_OFFSET = 0.4D", b"HOVER_OFFSET = 0.0D", 1),
    ("08-barrage", J / "entity" / "MoneyGremlin.java",
     b"distanceSqr > BARRAGE_MIN_RANGE", b"distanceSqr < BARRAGE_MIN_RANGE", 1),
    ("09-coin-damage", J / "item" / "ChaosCoinItem.java",
     b"PLAYER_DAMAGE = 3.0F", b"PLAYER_DAMAGE = 2.0F", 1),
    ("10-random", J / "material" / "ChaosRange.java",
     b"random.nextInt(FRACTION_SCALE + 1)", b"random.nextInt(FRACTION_SCALE + 2)", 1),
    ("11-comment-only", J / "material" / "ChaosRange.java",
     b"public final class ChaosRange {", b"public final class ChaosRange { // perturb-control", 0),
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    bad = 0
    for name, path, old, new, want in CASES:
        before = path.read_bytes()
        h0 = sha(before)
        if before.count(old) < 1:
            print(f"{name} | 锚点不存在（用例坏了） | exit=- | hit=False | sha=NA")
            bad += 1
            continue
        path.write_bytes(before.replace(old, new, 1))
        try:
            proc = subprocess.run([sys.executable, str(GATE)], cwd=str(REPO),
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            code = proc.returncode
            hit = code == want
        finally:
            path.write_bytes(before)
        h1 = sha(path.read_bytes())
        ok = hit and h1 == h0
        if not ok:
            bad += 1
        print(f"{name} | 期望 exit={want} 实际 exit={code} | hit={hit} | 复原={'OK' if h1 == h0 else 'BAD'}")
    print(f"用例 {len(CASES)} 个 / 未命中或复原失败 {bad} 个")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
