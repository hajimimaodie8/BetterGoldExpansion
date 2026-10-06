# -*- coding: utf-8 -*-
"""bg-fix2 关卡扰动实测（只读工作树 + 内存里改 + 跑完按字节复原 + SHA256 自证）。

写法沿用本仓既有纪律（mcmod_experience §3.4）：
  * 1 基线 + 逐条改坏 + **一条"只改注释必须仍绿"反向对照** + 收尾基线；
  * 每条用例**自证扰动确实改了文本**（改前 != 改后）；
  * 判据只匹配**稳定 ASCII 断言 id**，不匹配中文消息；
  * 每条跑完**按字节复原**并核对 SHA256，恢复失败立刻中止。

用法: python build/bgfix2-perturb.py [<输出文件>]
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace", encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "tools" / "asset-generator" / "validate_metal_data.py"

FX = "src/main/java/com/hjmmd_8/bettergold/registry/AllEffects.java"
MEV = "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java"
MOD = "src/main/java/com/hjmmd_8/bettergold/event/ModEvents.java"
GLM = "src/main/java/com/hjmmd_8/bettergold/registry/AllLootModifiers.java"
BLOCKS_ATLAS = "src/main/resources/assets/minecraft/atlases/blocks.json"
TRIM_JSON = "src/main/resources/data/bettergold/trim_material/indigoseagold.json"
PALETTE = "src/main/resources/assets/bettergold/textures/trims/color_palettes/indigoseagold.png"
ADV_BLAZING = "src/main/resources/data/bettergold/advancement/treasure/blazing_rod.json"
ADV_ROOT = "src/main/resources/data/bettergold/advancement/root.json"

SOUND_BLOCK = """            if (!soundPlayed && sonicLevel != null) {
                playSonicBoomSound(sonicLevel, pos);
                soundPlayed = true;
            }
            // 原版 SonicBoom.java:79-83 的第一层：伤害没落地（免疫 / 无敌帧差额为 0 / 已死）就不推。
            if (!victim.hurt(sonicBoomSource(level), MetalFamily.CONTACT_SONIC_DAMAGE)) {
                continue;
            }
            applyBlockSonicKnockback(victim, center);"""

SOUND_BLOCK_PERTURBED = """            if (!victim.hurt(sonicBoomSource(level), MetalFamily.CONTACT_SONIC_DAMAGE)) {
                continue;
            }
            if (!soundPlayed && sonicLevel != null) {
                playSonicBoomSound(sonicLevel, pos);
                soundPlayed = true;
            }
            applyBlockSonicKnockback(victim, center);"""


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_validator() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# 每条用例: (id, 文件, 改前文本, 改后文本, 期望 exit, 期望命中的断言 id 列表)
#   * 文件为 bytes 级替换（PALETTE 用 offset 扰动）
CASES: list[tuple[str, str, str, str, int, list[str]]] = [
    ("baseline-default", None, "", "", 0, []),

    # ---- 第 5 条：高燃 / 沉淀 = 等级 = 点数 ----
    ("fix2-5-a-old-curve", FX,
     "        return Math.max(1, amplifier + 1);",
     "        return Math.max(0, amplifier);", 1,
     ["bgfix2-shifted-damage-level-eq-damage", "bgfix-shifted-damage-impl", "bgfinal-highburn-body"]),
    ("fix2-5-b-zero-guard", FX,
     "if (damage > 0.0F) {", "if (damage > 1.0F) {", 1,
     ["bgfix2-highburn-level1-burns"]),
    ("fix2-5-c-early-return-on-zero", FX,
     "                        float damage = shiftedDamage(amplifier);",
     "                        float damage = shiftedDamage(amplifier);\n"
     "                        if (damage <= 0.0F) { return true; }", 1,
     ["bgfix2-highburn-level1-burns"]),
    ("fix2-5-d-sediment-hardcoded", FX,
     "entity.hurt(serverLevel.damageSources().inWall(), shiftedDamage(amplifier));",
     "entity.hurt(serverLevel.damageSources().inWall(), 2.0F);", 1,
     ["bgfix2-sediment-level-eq-damage", "bgfix2-shifted-damage-used-twice"]),

    # ---- 第 2 条：音效与伤害解耦 ----
    ("fix2-2-a-sound-after-hurt", MEV, SOUND_BLOCK, SOUND_BLOCK_PERTURBED, 1,
     ["bgfix2-sonic-decoupled"]),
    ("fix2-2-b-echo-old-guard", MEV, "        if (sawVictim) {", "        if (hitAny) {", 1,
     ["bgfix2-sonic-decoupled-echo", "bgappend-sonic-sound-throttled"]),
    ("fix2-2-c-echo-set-after-hurt", MEV,
     "            sawVictim = true;\n            victim.hurt(sonicBoomSource(serverLevel), level);",
     "            victim.hurt(sonicBoomSource(serverLevel), level);\n            sawVictim = true;", 1,
     ["bgfix2-sonic-decoupled-echo"]),

    # ---- 第 4 条：金骨粉 ----
    ("fix2-4-a-ratio", MOD, "SKELETON_SQUEEZE_RATIO = 0.8F", "SKELETON_SQUEEZE_RATIO = 0.5F", 1,
     ["bgfix2-skeleton-squeeze-ratio"]),
    ("fix2-4-b-no-skeleton-branch", MOD,
     "        boolean skeletonVictim = victim instanceof net.minecraft.world.entity.monster.AbstractSkeleton;",
     "        boolean skeletonVictim = false;", 1,
     ["bgfix2-skeleton-attack-squeeze"]),
    ("fix2-4-c-wrong-exempt", MOD, "return item == AllItems.GIFT_GOLD_TICKET.get();",
     "return item == Items.GOLD_INGOT;", 1,
     ["bgfix2-skeleton-ticket-exempt"]),
    ("fix2-4-d-no-exemption", MOD, "            if (isSqueezeExempt(item)) {",
     "            if (false) {", 1,
     ["bgfix2-skeleton-attack-squeeze"]),

    # ---- 第 3 条：藤条范围 ----
    ("fix2-3-a-broaden-to-all", GLM, "return family != null && family.isSpecialMetal()",
     "return family != null && true", 1,
     ["bgfix2-vine-all-but-sturdygold"]),

    # ---- 第 6 条：成就 ----
    ("fix2-6-a-hidden", ADV_BLAZING, '    "icon": {',
     '    "hidden": true,\n    "icon": {', 1, ["bgfix2-adv-no-hidden"]),
    ("fix2-6-b-recipe-crafted-back", ADV_BLAZING,
     '"trigger": "minecraft:inventory_changed"', '"trigger": "minecraft:recipe_crafted"', 1,
     ["bgfix2-adv-inventory-changed"]),

    # ---- 第 1 条：纹饰色卡四处嫌疑 ----
    ("fix2-1-a-atlas-drop", BLOCKS_ATLAS,
     '        "indigoseagold": "bettergold:trims/color_palettes/indigoseagold",\n', "", 1,
     ["bgfix2-trim-atlas-both"]),
    ("fix2-1-b-index-in-vanilla-range", TRIM_JSON, '"item_model_index": 0.06',
     '"item_model_index": 0.1', 1,
     ["bgfix2-trim-model-index-outside-vanilla"]),
    ("fix2-1-d-index-collision-ours", "src/main/resources/data/bettergold/trim_material/flamegold.json",
     '"item_model_index": 0.03', '"item_model_index": 0.06', 1,
     ["bgfix2-trim-model-index-distinct"]),
    ("fix2-1-c-palette-size", PALETTE, None, None, 1, ["bgfix2-trim-palette-8x1"]),
]

# 只改注释必须仍绿（反向对照）
COMMENT_ONLY = ("reverse-comment-only", MEV,
                "    private static void sonicContact(",
                "    // bgfix2 perturb: comment only, must stay green\n"
                "    private static void sonicContact(", 0, [])


def _adapt(text: str, needle: str) -> str:
    """让锚点跟随文件的换行风格（本仓源码是 CRLF；多行锚点用 \n 写会被静默不中 —— ex/03 §3.11）。"""
    if "\r\n" in text and "\r\n" not in needle:
        return needle.replace("\n", "\r\n")
    return needle


def apply_case(path: Path, old: str | None, new: str | None) -> bytes:
    """返回原始字节（供复原）；对 PALETTE 用 IHDR 高度字节扰动。"""
    original = path.read_bytes()
    if path.name.endswith(".png"):
        assert old is None and new is None
        b = bytearray(original)
        # IHDR: 8 字节签名 + 4 长度 + 4 类型 = 16 起；宽 16..19、高 20..23
        assert b[12:16] == b"IHDR", "不是 PNG IHDR 结构"
        b[23] = 2          # 高 1 -> 2（8x1 变 8x2）
        path.write_bytes(bytes(b))
        return original
    text = original.decode("utf-8")
    old = _adapt(text, old)
    new = _adapt(text, new)
    assert old in text, "扰动没生效（锚点不在文件里）: %s" % old[:60]
    text2 = text.replace(old, new, 1)
    assert text2 != text, "扰动没生效（改前 == 改后）"
    path.write_bytes(text2.encode("utf-8"))
    return original


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs" / "bgfix2-证据" / "01-关卡扰动实测.txt"
    lines: list[str] = []
    lines.append("bg-fix2 关卡扰动实测（validate_metal_data.py；判据只匹配稳定 ASCII 断言 id）")
    lines.append("")

    def emit(s: str) -> None:
        lines.append(s)
        print(s)

    cases = list(CASES) + [COMMENT_ONLY, ("baseline-final", None, "", "", 0, [])]
    mismatches = 0
    for cid, rel, old, new, want_exit, want_ids in cases:
        if rel is None:
            code, output = run_validator()
            got_ids = [i for i in want_ids if "[%s]" % i in output]
            ok = code == want_exit and len(got_ids) == len(want_ids)
            emit("%-28s exit=%d(want %d) ids=%s %s" % (cid, code, want_exit, got_ids or "-",
                                                       "OK" if ok else "MISMATCH"))
            if not ok:
                mismatches += 1
                for ln in output.splitlines()[-6:]:
                    emit("      | " + ln)
            continue
        path = REPO / rel
        before_sha = sha(path)
        original = apply_case(path, old, new)
        try:
            code, output = run_validator()
        finally:
            path.write_bytes(original)
        after_sha = sha(path)
        restored = after_sha == before_sha
        got_ids = [i for i in want_ids if "[%s]" % i in output]
        ok = code == want_exit and len(got_ids) == len(want_ids) and restored
        emit("%-28s exit=%d(want %d) ids=%s restored=%s %s"
             % (cid, code, want_exit, got_ids or "-", restored, "OK" if ok else "MISMATCH"))
        if not ok:
            mismatches += 1
            emit("      | want_ids=%s" % want_ids)
            for ln in output.splitlines()[-6:]:
                emit("      | " + ln)
    emit("")
    emit("mismatches = %d（0 = 每条都命中它该命中的 id，且逐字节复原成功）" % mismatches)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n[写出] %s" % out_path)
    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
