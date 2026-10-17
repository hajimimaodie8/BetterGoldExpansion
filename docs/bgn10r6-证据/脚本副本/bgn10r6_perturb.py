# -*- coding: utf-8 -*-
"""轮6 扰动矩阵：只改注释仍绿 / 新关卡能红 / 逐字节复原 + SHA256。

判据两列：exit（0 绿 / 1 有问题 / 2 前置坏）与「命中预期」。
"""
import hashlib
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
REPO = pathlib.Path(__file__).resolve().parents[1]
VD = REPO / "tools" / "asset-generator"
PY = sys.executable

CASES = []


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def run_validator(name: str) -> int:
    p = subprocess.run([PY, str(VD / name)], cwd=str(REPO),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p.returncode


def perturb(case_id: str, path: pathlib.Path, mutate, validators, expected: int, note: str):
    before = path.read_bytes()
    before_sha = hashlib.sha256(before).hexdigest().upper()
    path.write_bytes(mutate(before))
    codes = {v: run_validator(v) for v in validators}
    path.write_bytes(before)
    after_sha = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    ok = all(code == expected for code in codes.values()) and before_sha == after_sha
    CASES.append((case_id, codes, expected, ok, note, before_sha == after_sha))
    print("[case] %-42s codes=%s expected=%d hit=%s restore_sha_ok=%s (%s)"
          % (case_id, codes, expected, ok, before_sha == after_sha, note))
    if not ok:
        raise SystemExit("[perturb] case failed: " + case_id)


ALL6 = ["validate_metal_assets.py", "validate_metal_data.py", "validate_trim_assets.py",
        "check_jar_clean.py", "check_forced_chunks.py", "validate_advancements.py"]

# 1) 只改注释：六个校验器必须仍绿（判据跑在去注释源码上）
mob = REPO / "src/main/java/com/hjmmd_8/bettergold/entity/MoneyGremlin.java"
perturb("01-only-comment", mob,
        lambda b: b.replace(b"public class MoneyGremlin extends Monster {",
                            b"// perturbation: comment only\r\npublic class MoneyGremlin extends Monster {", 1),
        ALL6, 0, "只加一行注释")

# 2) 贴图改 1 字节：贴图哈希锚点必须红
tex = REPO / "src/main/resources/assets/bettergold/textures/entity/money_gremlin.png"
perturb("02-texture-bit-flip", tex,
        lambda b: b[:-1] + bytes([b[-1] ^ 0x01]),
        ["validate_metal_data.py"], 1, "PNG 末字节翻转")

# 3) damage_type 的 scaling 改成会吃原版难度换算：必须红
dt = REPO / "src/main/resources/data/bettergold/damage_type/money_gremlin_melee.json"
perturb("03-scaling-not-never", dt,
        lambda b: b.replace(b'"scaling": "never"', b'"scaling": "when_caused_by_living_non_player"', 1),
        ["validate_metal_data.py"], 1, "scaling=when_caused_by_living_non_player")

# 4) 删一条语言键（zh）：语言键 + 文件 SHA 两道都必须红
lang = REPO / "src/main/resources/assets/bettergold/lang/zh_cn.json"
perturb("04-lang-key-removed", lang,
        lambda b: b.replace('  "entity.bettergold.money_gremlin": "金钱妖",\r\n'.encode("utf-8"), b"", 1),
        ["validate_metal_data.py"], 1, "删 entity.bettergold.money_gremlin（zh）")

# 5) 旧判定回到 MetalEvents：双倍伤害唯一入口必须红
me = REPO / "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java"
perturb("05-old-target-check-returns", me,
        lambda b: b.replace(b"family.isDoubleDamageTarget(target.getType())",
                            b"family.contactDamageTargets.contains(target.getType())", 1),
        ["validate_metal_data.py"], 1, "把唯一入口换回旧判定")

# 6) 弹幕节流常量改 121：字面断言必须红
perturb("06-barrage-interval-121", mob,
        lambda b: b.replace(b"BARRAGE_INTERVAL_TICKS = 120", b"BARRAGE_INTERVAL_TICKS = 121", 1),
        ["validate_metal_data.py"], 1, "弹幕间隔 120 -> 121")

print()
print("SUMMARY cases=%d all_hit=%s" % (len(CASES), all(c[3] for c in CASES)))
out = REPO / "docs" / "bgn10r6-证据" / "03-扰动矩阵.txt"
header = [
    "轮6 扰动矩阵（判据两列：exit / 命中预期）",
    "=" * 100,
    "脚本副本：docs/bgn10r6-证据/脚本副本/bgn10r6_perturb.py",
    "",
]
rows = []
for case_id, codes, expected, ok, note, sha_ok in CASES:
    rows.append("%-42s codes=%s expected=%d hit=%s restore_sha_ok=%s :: %s"
                % (case_id, codes, expected, ok, sha_ok, note))
out.write_bytes(("\r\n".join(header + rows) + "\r\n").encode("utf-8"))
print("[ev] wrote", out.relative_to(REPO))
