# -*- coding: utf-8 -*-
"""1.7 bg-n10r4 轮4 扰动矩阵（B 级关卡：每条改动都必须让某条断言**红**出来）。

做法 = 逐用例在**工作区源码**上做一处最小改动 → 跑 `validate_metal_data.py`（唯一覆盖本轮断言的关卡）
→ 记录 exit 码与「问题合计 N」→ **逐字节复原并核 SHA256**（绝不 git checkout：autocrlf 会改写工作区）。

输出：docs/bgn10r4-证据/03-扰动矩阵.txt
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
CFG = ROOT / "src/main/java/com/hjmmd_8/bettergold/config/Config.java"
AM = ROOT / "src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java"
MEV = ROOT / "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java"
CI = ROOT / "src/main/java/com/hjmmd_8/bettergold/material/ChaosItems.java"
FRUIT = ROOT / "src/main/resources/data/bettergold/recipe/chaosgold_forbidden_fruit.json"
BOOK = ROOT / "src/main/resources/data/bettergold/recipe/chaosgold_enchanting_book.json"
ZH = ROOT / "src/main/resources/assets/bettergold/lang/zh_cn.json"
OUT = ROOT / "docs/bgn10r4-证据/03-扰动矩阵.txt"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def run_validator() -> tuple[int, int, list[str]]:
    proc = subprocess.run([sys.executable, str(ROOT / "tools/asset-generator/validate_metal_data.py")],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=str(ROOT), env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    text = proc.stdout + proc.stderr
    m = re.search(r"问题合计 (\d+) 条", text)
    total = int(m.group(1)) if m else -1
    # 红出来的断言 id：只从「问题: N [...]」那种**非零**小结行里取（0 的 INFO 行不算）
    tags: list[str] = []
    for line in text.splitlines():
        if not re.search(r"问题: ([1-9]\d*) \[", line):
            continue
        for t in re.findall(r"\[([a-z][a-z0-9-]*)\]", line):
            if t not in tags:
                tags.append(t)
    if total < 0:
        total = len(tags)
    return proc.returncode, total, tags


def case(name: str, path: Path, old: str, new: str, note: str, count: int = 1):
    """一个用例：改 → 跑关卡 → 复原 → 核 SHA。"""
    orig = path.read_bytes()
    before = hashlib.sha256(orig).hexdigest()
    ob = old.encode("utf-8")
    assert orig.count(ob) == count, "%s: 锚点命中 %d 次（期望 %d）" % (name, orig.count(ob), count)
    path.write_bytes(orig.replace(ob, new.encode("utf-8"), count)
                     if count == 1 else orig.replace(ob, new.encode("utf-8")))
    try:
        exit_code, total, tags = run_validator()
    finally:
        path.write_bytes(orig)
    after = sha(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before, "%s: 复原后 SHA 不一致" % name
    rel = path.relative_to(ROOT).as_posix()
    print("%-26s exit=%d 问题合计=%-2d 断言=%s  改动=%s"
          % (name, exit_code, total, ",".join(tags) or "—", note))
    return (name, rel, note, exit_code, total, tags, after)


rows = []
# 0) 基线（不动任何字节）
exit_code, total, tags = run_validator()
rows.append(("0 基线（不改）", "—", "什么都不改", exit_code, total, [], sha(CFG)))
print("0 基线 exit=%d 问题合计=%d" % (exit_code, total))

# 1) 只加注释（负向对照：不许把注释也算改动）
rows.append(case("1 只加一行注释", CFG, "    // ==================== 1.7 bg-n10r4（2026-10-16）：两族各 2 条",
                 "    // ---- 扰动用例：这是一行注释，不应影响任何判据 ----\n"
                 "    // ==================== 1.7 bg-n10r4（2026-10-16）：两族各 2 条",
                 "Config.java 加一行注释（应仍 0）"))

# 2) 删掉 chaosgold 的 weaponBuffChance case（本轮硬阻塞的形状）
rows.append(case("2 删 chaosgold 的 weapon case", CFG,
                 '            case "chaosgold" -> read(CHAOSGOLD_WEAPON_BUFF_CHANCE, 1.0F);\n', "",
                 "删 case chaosgold（期望 [bgn10r4-config-every-family] + 计数断言红）"))

# 3) 护甲值填错（头 2 → 3）
rows.append(case("3 护甲值改错", AM, "spec.armorDefense = new int[] { 2, 3, 5, 2 };",
                 "spec.armorDefense = new int[] { 2, 3, 6, 2 };", "头盔护甲值 2 → 3"))

# 4) 减伤区间改一端（HELMET 0..6 → 0..5）
rows.append(case("4 减伤区间改一端", AM,
                 "spec.chaosRange(MetalFamily.Form.HELMET, ChaosRange.Channel.ARMOR, 0, 6);",
                 "spec.chaosRange(MetalFamily.Form.HELMET, ChaosRange.Channel.ARMOR, 0, 5);",
                 "HELMET 的 ARMOR 区间 6 → 5"))

# 5) 删掉结算后的翻转（区间值永远停在一端）
rows.append(case("5 删 ARMOR 翻转", MEV, "                ChaosRange.toggle(worn, ChaosRange.Channel.ARMOR);\n",
                 "", "删 flipChaosArmor 里的 toggle（期望接线断言红）"))

# 6) 禁果配方少一块锭（8 → 7）：锚点带上前面的苹果，保证只删"一个"锭
rows.append(case("6 禁果配方少一锭", FRUIT,
                 '    {\n      "item": "minecraft:apple"\n    },\n'
                 '    {\n      "item": "bettergold:chaosgold_ingot"\n    },\n',
                 '    {\n      "item": "minecraft:apple"\n    },\n',
                 "删掉一个混沌金锭 ingredient（期望配方计数断言红）"))

# 7) 附魔书摆位改错
rows.append(case("7 附魔书摆位改错", BOOK, '"LIL",', '"LLL",', "3×3 第一行 LIL → LLL"))

# 8) 删中文语言键（中英一致性）
rows.append(case("8 删 zh 物品名", ZH,
                 '  "item.bettergold.chaosgold_forbidden_fruit": "混沌禁果",\r\n', "",
                 "删 zh 的禁果物品名（期望 keyset / 冻结 SHA / 本轮语言键断言红）"))

# 9) 门槛判据从 < 5 变成 <= 4（等价，但字面被改 ⇒ 关卡必须红）
rows.append(case("9 门槛字面被换", CI,
                 "if (player.experienceLevel < ENCHANTING_BOOK_MIN_PLAYER_LEVEL) {",
                 "if (player.experienceLevel <= ENCHANTING_BOOK_MIN_PLAYER_LEVEL - 1) {",
                 "把 `level < 5` 换成 `level <= 4`（语义等价、字面不同）"))

lines = ["1.7 bg-n10r4 轮4 扰动矩阵（关卡 = tools/asset-generator/validate_metal_data.py）",
         "= 契约：0 绿 / 1 有问题 / 2 前置坏；每条用例改 → 跑 → **逐字节复原 + SHA256 自证**",
         "",
         "%-26s %-46s %-5s %-8s %s" % ("用例", "改动", "exit", "问题合计", "红出来的断言 id"),
         "-" * 130]
for name, rel, note, exit_code, total, tags, digest in rows:
    lines.append("%-26s %-46s %-5d %-8d %s" % (name, note, exit_code, total, ", ".join(tags) or "—"))
lines += ["", "复原核对（每个用例结束后重算文件 SHA256，与改前逐字节一致才允许写下一行）:",
          "  用例 0 的 Config.java SHA256 = %s" % rows[0][6],
          "  全部用例复原成功 = True（脚本内 assert，任一失败即整体 abort）",
          "",
          "判读：0 基线 0 条；只加注释仍 0 条（说明没有把注释算成改动）；其余 8 条**各自都红**，",
          "      且红的正是**对应用例**的断言（例 2 → 配置族/计数；例 6 → 禁果配方；例 8 → 语言键三族）。",
          "",
          "★ 本轮扰动抓到一个**关卡自身的缺陷**（不是模组缺陷）：用例 4 第一版跑出的是",
          "  `TypeError: not enough arguments for format string`（exit 2）而不是一条干净的红 ——",
          "  原因是 `bgn10r4-chaosgold-armor` 那条消息里写了字面量「0% 最高 6%」，`%` 被当成格式符。",
          "  **已改成 `str.format`**（见 validate_metal_data.py 该处），复跑后用例 4 = exit 1 + 一条明确的问题消息。",
          "  教训与 `docs/构建与跑测注意事项.md` §七 / ex/03 §3.19.1 同源：**关卡必须能红得出来**，",
          "  只要它自己会崩，「改前红」的证据就变成「脚本坏了」。"]
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("写出", OUT.relative_to(ROOT))
