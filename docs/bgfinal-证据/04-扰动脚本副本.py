#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-final 关卡扰动实测（临时物，放 build/ 不进版本库）。

做法照 mcmod_experience §3.4：**逐条把源码改坏 ⇒ 必须命中它该命中的 ASCII 断言 id ⇒ 再字节级复原并核对 SHA256**；
外加 ① 一条基线（未扰动必须 exit 0）② 一条"只改注释必须仍绿"的反向对照 ③ 收尾基线。

不改工作树的最终状态：每个用例都先把**原始字节**存下来，用例结束立刻写回并核对 SHA256；
任何一次复原失败 → 立即停止（不许带着改坏的源码继续）。
"""
from __future__ import annotations

import hashlib
import io
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

REPO = pathlib.Path(__file__).resolve().parents[1]
MEV = REPO / "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java"
MF = REPO / "src/main/java/com/hjmmd_8/bettergold/material/MetalFamily.java"
FX = REPO / "src/main/java/com/hjmmd_8/bettergold/registry/AllEffects.java"
EN = REPO / "src/main/resources/assets/bettergold/lang/en_us.json"
SPEC = REPO / "docs/1.6-规格.md"
GEN = REPO / "tools/asset-generator/generate_advancements.py"

VMD = "tools/asset-generator/validate_metal_data.py"
VADV = "tools/asset-generator/validate_advancements.py"

results: list[tuple[str, str, str]] = []


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(script: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, script], cwd=str(REPO), capture_output=True)
    out = proc.stdout.decode("gbk", errors="replace") + proc.stderr.decode("gbk", errors="replace")
    return proc.returncode, out


def case(name: str, path: pathlib.Path, old: str, new: str, script: str, expect: list[str],
         expect_ok: bool = False, count: int = 1) -> None:
    raw = path.read_bytes()
    before = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8")
    variants = [old, old.replace("\n", "\r\n")]
    hit = next((v for v in variants if v in text), None)
    if hit is None:
        results.append((name, "MISS", "扰动串在源码里找不到（用例本身写错）"))
        return
    repl = new.replace("\n", "\r\n" if "\r\n" in hit else "\n")
    # count=0 在 str.replace 里是"替换 0 次"（不是"全部"）⇒ 这里显式分流
    patched = text.replace(hit, repl) if count == 0 else text.replace(hit, repl, count)
    path.write_bytes(patched.encode("utf-8"))
    code, out = run(script)
    path.write_bytes(raw)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    if after != before:
        results.append((name, "RESTORE-FAIL", f"{path.name} 复原后 SHA256 不一致"))
        raise SystemExit("复原失败，立即停止（不许带着改坏的源码继续）")
    if expect_ok:
        ok = code == 0
        results.append((name, "OK" if ok else "MISMATCH",
                        f"exit={code}（期望 0：只改注释必须仍绿）"))
        return
    hit_ids = [e for e in expect if e in out]
    if code != 0 and len(hit_ids) == len(expect):
        results.append((name, "OK", f"exit={code} 命中 {hit_ids}"))
    else:
        results.append((name, "MISMATCH",
                        f"exit={code} 期望 {expect} 实际命中 {hit_ids}"))


def baseline(name: str) -> None:
    c1, o1 = run(VMD)
    c2, o2 = run(VADV)
    bad = [l for l in o1.splitlines() if "bg-final" in l or "bgfinal" in l]
    ok = c1 == 0 and c2 == 0
    results.append((name, "OK" if ok else "MISMATCH",
                    f"validate_metal_data exit={c1} / validate_advancements exit={c2}；bg-final 行: {bad[:2]}"))


# ---------------------------------------------------------------- 用例表
baseline("00 基线（未扰动）")

case("01 删掉击退调用（改前形状）", MEV,
     "            applyBlockSonicKnockback(victim, center);",
     "", VMD, ["bgfinal-sonic-knockback-present"])

case("02 删掉 hurt 闸门（免疫也会被推）", MEV,
     "            if (!victim.hurt(sonicBoomSource(level), MetalFamily.CONTACT_SONIC_DAMAGE)) {\n"
     "                continue;\n"
     "            }\n",
     "", VMD, ["bgfinal-sonic-knockback-damage-gated"])

case("03 helper 里推两次（不是只推一次）", MEV,
     "        victim.push(dir.x() * MetalFamily.CONTACT_SONIC_KNOCKBACK_HORIZONTAL * scale,\n",
     "        victim.push(dir.x() * MetalFamily.CONTACT_SONIC_KNOCKBACK_HORIZONTAL * scale,\n"
     "        victim.push(dir.x() * MetalFamily.CONTACT_SONIC_KNOCKBACK_HORIZONTAL * scale,\n",
     VMD, ["bgfinal-sonic-knockback-once"])

case("04 把击退写进共用的 applyContact（别的族被顺手加上）", MEV,
     "            entity.hurt(entity.damageSources().cactus(), 1.0F);\n        }",
     "            entity.hurt(entity.damageSources().cactus(), 1.0F);\n        }\n"
     "        entity.push(1.0D, 1.0D, 1.0D);",
     VMD, ["bgfinal-sonic-knockback-single-site"])

case("05 幅度常量被改成拍脑袋的数", MF,
     "    public static final double SONIC_BOOM_KNOCKBACK_HORIZONTAL = 2.5D;",
     "    public static final double SONIC_BOOM_KNOCKBACK_HORIZONTAL = 1.5D;",
     VMD, ["bgfinal-sonic-knockback-magnitude"])

case("06 只改注释（反向对照：必须仍绿）", MEV,
     "            applyBlockSonicKnockback(victim, center);",
     "            // 反向对照：注释里提到 push( / CONTACT_SONIC_KNOCKBACK_HORIZONTAL / "
     "setRemainingFireTicks，判据必须看不见它们\n"
     "            applyBlockSonicKnockback(victim, center);",
     VMD, [], expect_ok=True)

case("07 高燃 1 级又点燃：守卫条件被放宽成恒真", FX,
     "                        if (damage > 0.0F) {",
     "                        if (true) {",
     VMD, ["bgfinal-highburn-zero-no-fire"])

case("08 高燃在守卫块之外又多刷一次燃烧", FX,
     "                            entity.setRemainingFireTicks(HIGH_BURN_FIRE_TICKS);\n"
     "                        }",
     "                            entity.setRemainingFireTicks(HIGH_BURN_FIRE_TICKS);\n"
     "                        }\n"
     "                        entity.setRemainingFireTicks(20);",
     VMD, ["bgfinal-highburn-zero-no-fire"])

case("09 沉淀被顺手加上点燃", FX,
     "                        entity.hurt(serverLevel.damageSources().inWall(), shiftedDamage(amplifier));",
     "                        entity.hurt(serverLevel.damageSources().inWall(), shiftedDamage(amplifier));\n"
     "                        entity.setRemainingFireTicks(20);",
     VMD, ["bgfinal-highburn-sediment-untouched"])

case("10 规格里「已选 (b)」的标注被删", SPEC, "已选 (b)", "未裁定", VMD, ["bgfinal-doc"], count=0)

case("11 en_us 里一条英文值改回中文原文", EN,
     '"advancements.bettergold.root.title": "Heir to the Old Alchemy"',
     '"advancements.bettergold.root.title": "\u65e7\u65f6\u4ee3\u70bc\u91d1\u672f\u7684\u7ee7\u627f\u8005"',
     VADV, ["bgfinal-adv-lang-translated"])

case("12 en_us 少一个键（中英键集不齐）", EN,
     '  "advancements.bettergold.root.title": "Heir to the Old Alchemy",\n',
     "", VADV, ["bgfinal-adv-lang-parity"])

case("13 en_us 某条英文值为空", EN,
     '"advancements.bettergold.root.title": "Heir to the Old Alchemy"',
     '"advancements.bettergold.root.title": ""',
     VADV, ["bgfinal-adv-lang-empty"])

case("14 en_us 某条英文值里没有 ASCII 字母", EN,
     '"advancements.bettergold.root.title": "Heir to the Old Alchemy"',
     '"advancements.bettergold.root.title": "\u2605\u2605\u2605"',
     VADV, ["bgfinal-adv-lang-en-shape"])

# ---------------------------------------------------------------- 15 号单独跑（生成器侧守卫）
raw = GEN.read_bytes()
before = sha(GEN)
text = raw.decode("utf-8")
old = '    "root": ("Heir to the Old Alchemy",'
GEN.write_bytes(text.replace(old, '    "root_missing": ("Heir to the Old Alchemy",', 1).encode("utf-8"))
proc = subprocess.run([sys.executable, "tools/asset-generator/generate_advancements.py", "--lang"],
                      cwd=str(REPO), capture_output=True)
GEN.write_bytes(raw)
out = proc.stdout.decode("gbk", errors="replace") + proc.stderr.decode("gbk", errors="replace")
ok = proc.returncode != 0 and "EN" in out and "root" in out
results.append(("15 生成器 EN 表漏一条（生成器侧守卫）", "OK" if ok else "MISMATCH",
                f"exit={proc.returncode}（期望非 0 + 报出漏键）"))
if sha(GEN) != before:
    results.append(("15-restore", "RESTORE-FAIL", "生成器复原失败"))
    raise SystemExit("复原失败，立即停止")

baseline("99 收尾基线（全部复原之后）")

# ---------------------------------------------------------------- 报告
print("=" * 100)
print("bg-final 关卡扰动实测：%d 条用例" % len(results))
print("=" * 100)
mismatch = 0
for n, st, d in results:
    if st != "OK":
        mismatch += 1
    print(f"{st:14s} {n}\n               {d}")
print("=" * 100)
print("mismatches =", mismatch)
raise SystemExit(1 if mismatch else 0)
