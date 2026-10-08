"""bg-fix4 §二：把 Config.java 的 8 族 × 2 条配置项**声明顺序**改成作者 2026-10-08 给的顺序。

真源 = `material/CreativeSections.METAL_ORDER`（一行）：
    烈燃金 → 万坚金 → 树棘金 → 幽咆金 → 靛海金 → 巫毒金 → 结雷金 → 幻惑金

做法 = **纯行重排 + 插入一段说明注释**：
  * 区域 = 16 个 `defineInRange(...)` 块（每族 2 块，顺序 = 文件里现在那样）；
  * 断言：重排前后 **非空行的多重集合完全相同**（只有顺序变）、键集合完全相同；
  * 断言：8 个族块各 2 个字面量键，键名逐条对得上族（防止切块切错）。

用法：python build/bgfix4_config_order.py [--apply]
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parent.parent
CFG = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "config" / "Config.java"

# 作者 2026-10-08 的顺序（= CreativeSections.METAL_ORDER）
ORDER = ["flamegold", "sturdygold", "thornsgold", "echogold",
         "indigoseagold", "voodoogold", "thundergold", "illusiongold"]

# 每族两个字面量键（sturdygold 的键名与众不同：Ability / IntervalMultiplier）
WANT_KEYS = {
    "flamegold": ["flamegoldWeaponBuffChance", "flamegoldArmorBuffChance"],
    "sturdygold": ["sturdygoldWeaponAbilityChance", "sturdygoldArmorAbilityIntervalMultiplier"],
    "thornsgold": ["thornsgoldWeaponBuffChance", "thornsgoldArmorBuffChance"],
    "echogold": ["echogoldWeaponBuffChance", "echogoldArmorBuffChance"],
    "indigoseagold": ["indigoseagoldWeaponBuffChance", "indigoseagoldArmorBuffChance"],
    "voodoogold": ["voodoogoldWeaponBuffChance", "voodoogoldArmorBuffChance"],
    "thundergold": ["thundergoldWeaponBuffChance", "thundergoldArmorBuffChance"],
    "illusiongold": ["illusiongoldWeaponBuffChance", "illusiongoldArmorBuffChance"],
}

# 区域（1-based，含两端）：从 flamegold 那段 javadoc 起，到 sturdygold 的最后一个 defineInRange 结束
REGION_START = 150
REGION_END = 260

# 插在区域前面的说明（新增内容；原文一行未删）
HEADER = '''    // ==================== bg-fix4 §二：16 条的**声明顺序** ====================
    //
    // ★ **顺序真源 = `CreativeSections.METAL_ORDER`**（那一行注释原文：「金属出场顺序只在这里维护一行」）。
    //   作者 2026-10-08 原话：「关于贵金进度的上下排版还需要重做,需要改成这种从上到下分别是:
    //   烈燃金 / 万坚金 / 树棘金 / 幽咆金 / 靛海金 / 巫毒金 / 结雷金 / 幻惑金。**模组设置也要用这种规律排序**」
    //   ⇒ 本类这 16 条**按那个列表逐族声明**：NeoForge 配置界面与 `bettergold-common.toml` 的条目顺序
    //     = 声明顺序 = 创造页金属顺序（`CreativeSections.METAL_ORDER`）。
    //
    // ⚠ **旧顺序（原文留档，已被 2026-10-08 取代）**：flamegold → voodoogold → thundergold →
    //   indigoseagold → illusiongold → thornsgold → echogold → sturdygold（1.6.0 的原样，未列过顺序，
    //   只是"谁先写的谁在前"）。
    // ⚠ **键名 / 默认值 / 取值范围 / .comment 文案一个字都没改**（配置键名是存档红线，见上）。
    // ⚠ 关卡 `[bgfix4-metal-order-single-source]` 守着"本类 16 键的声明顺序 == METAL_ORDER"
    //    （以及生成器侧 `generate_advancements.py` / `generate_handbook_data.py` 的 METALS 同序）。
'''


def key_of(block: list) -> str:
    m = re.search(r'\.defineInRange\(\s*"([^"]+)"', "\n".join(block))
    return m.group(1) if m else ""


def main() -> int:
    apply = "--apply" in sys.argv
    src = CFG.read_text(encoding="utf-8")
    lines = src.split("\n")
    total = len(lines)

    assert "烈燃金" in lines[REGION_START - 1], lines[REGION_START - 1]
    assert "sturdygoldArmorAbilityIntervalMultiplier" in lines[REGION_END - 1], lines[REGION_END - 1]

    region = lines[REGION_START - 1:REGION_END]
    assert all(l.strip() == "" or not l.startswith("    //") for l in region), "区域里混进了注释，切块会错"

    # 按空行切成 16 个块
    blocks, cur = [], []
    for ln in region:
        if ln.strip() == "":
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(ln)
    if cur:
        blocks.append(cur)
    if len(blocks) != 16:
        print("FATAL 块数不是 16：%d" % len(blocks))
        return 2

    keys = [key_of(b) for b in blocks]
    flat = [k for m in ORDER for k in WANT_KEYS[m]]
    if sorted(keys) != sorted(flat):
        print("FATAL 键集合不符\n  实际 %s\n  期望 %s" % (sorted(keys), sorted(flat)))
        return 2

    by_key = {key_of(b): b for b in blocks}
    new_region = []
    for i, m in enumerate(ORDER):
        for k in WANT_KEYS[m]:
            new_region.extend(by_key[k])
            new_region.append("")          # 块间空行（原样：16 块 = 15 个空行分隔）
    while new_region and new_region[-1] == "":
        new_region.pop()                   # 区域末尾不留空行（原形状：下一行是空行，不在区域内）

    # ★ 不变量：非空行的多重集合必须逐行相同（只有顺序变）
    old_nonblank = sorted(l for l in region if l.strip())
    new_nonblank = sorted(l for l in new_region if l.strip())
    if old_nonblank != new_nonblank:
        print("FATAL 非空行集合变了（不是纯重排）")
        for a, b in zip(old_nonblank, new_nonblank):
            if a != b:
                print("  第一处差异:\n   旧 %r\n   新 %r" % (a, b))
                break
        return 2

    header_lines = HEADER.split("\n")
    out = lines[:REGION_START - 1] + header_lines + new_region + lines[REGION_END:]
    print("Config.java: %d 行 -> %d 行（+%d：说明注释 %d 行）"
          % (total, len(out), len(out) - total, len(header_lines)))
    print("新顺序（键的首次出现序）:")
    order_now = [key_of([l]) or "?" for l in out]
    seen = []
    for ln in out:
        m = re.search(r'\.defineInRange\(\s*"([^"]+)"', ln)
        if m:
            seen.append(m.group(1))
    print("  " + " -> ".join(seen[:16]))
    if not apply:
        print("（演练模式：没有写盘；加 --apply 才写）")
        return 0
    CFG.write_bytes("\n".join(out).encode("utf-8"))
    print("已写入 %s" % CFG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
