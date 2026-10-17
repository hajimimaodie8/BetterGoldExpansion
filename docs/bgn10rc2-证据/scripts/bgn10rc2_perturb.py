# -*- coding: utf-8 -*-
"""bg-n10rc2 扰动矩阵：6 个用例，逐例跑关卡、记录**本段**问题数与命中的 tag，跑完逐字节复原 + SHA256。

判据（与 bgn10rg 那一轮同一套口径）：
  * 真扰动 ⇒ `[bgn10rc2-*]` 段必须变红、且点名对应 tag；
  * 只改注释 ⇒ 本段仍 0 条（证明正向 needle 跑在**去注释源码**上）；
  * 每例跑完逐字节复原 + SHA256 复核一致。

⚠ 记录两列：`script_exit`（整脚本 exit，参考）+ `my_section`（判据：本段问题数）。
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
PROBE = REPO / "probe" / "bgn10rc2"
RECIPES = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"
JAVA = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
VALIDATOR = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
OUT = REPO / "docs" / "bgn10rc2-证据" / "03-扰动矩阵.txt"

SECTION_RE = re.compile(r"^1\.7 bg-n10rc2（4 件补齐 \+ 返瓶扩到物品级）问题: (\d+) .*$", re.M)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def run_validator() -> tuple[int, int, list]:
    cp = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True,
                        cwd=str(REPO), env=None)
    text = cp.stdout.decode("utf-8", errors="replace")
    m = SECTION_RE.search(text)
    if not m:
        return cp.returncode, -1, ["<解析不到本段那一行>"]
    n = int(m.group(1))
    tags = sorted(set(re.findall(r"\[(bgn10rc2-[a-z0-9-]+)\]", m.group(0))))
    return cp.returncode, n, tags


class Case:
    def __init__(self, name, path: Path, mutate, note: str):
        self.name = name
        self.path = path
        self.mutate = mutate
        self.note = note


def rec(name: str, path: Path, old: str, new: str, count: int = 1) -> Case:
    def mutate(text: str) -> str:
        assert text.count(old) >= 1, "%s: 找不到锚点 %r" % (name, old[:60])
        return text.replace(old, new, count)
    return Case(name, path, mutate, "把 %r 换成 %r" % (old[:48], new[:48]))


def main() -> None:
    PROBE.mkdir(parents=True, exist_ok=True)
    cases = [
        # ① 换一格：三叉戟 第2行 中列（锭 → 棍）
        rec("grid-swap", RECIPES / "chaosgold_trident.json",
            '    " X ",\n    " # "\n', '    " # ",\n    " # "\n'),
        # ② 换数量：弓 产物 1 → 2
        rec("result-count", RECIPES / "chaosgold_bow.json",
            '"count": 1', '"count": 2'),
        # ③ 去掉 FD 条件：乐事刀
        rec("drop-fd-condition", RECIPES / "chaosgold_knife.json",
            '  "neoforge:conditions": [\n'
            '    {\n'
            '      "type": "neoforge:mod_loaded",\n'
            '      "modid": "farmersdelight"\n'
            '    }\n'
            '  ],\n', ''),
        # ④ 把 remainder 加成两个：配方层给兑换物那格也塞一个玻璃瓶（模拟双返）
        rec("double-bottle", JAVA / "recipe" / "RawSturdygoldRecipe.java",
            "                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE)); //",
            "                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE));\n"
            "            } else if (stack.is(this.exchange)) {\n"
            "                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE)); //"),
        # ⑤ 只改注释：把被禁的两串写进注释（源码行为一字未改）
        rec("comment-only", JAVA / "recipe" / "RawSturdygoldRecipe.java",
            "public class RawSturdygoldRecipe extends CustomRecipe {",
            "public class RawSturdygoldRecipe extends CustomRecipe {\n"
            "    // 只改注释：Recipe.super.getRemainingItems / craftRemainder(Items.GLASS_BOTTLE)\n"
            "    // 以及 getCraftingRemainingItem —— 这三串都只写在注释里，关卡不该因此变红"),
        # ⑥ 换一件：重锤 混沌金块 → 混沌金锭
        rec("mace-block-to-ingot", RECIPES / "chaosgold_mace.json",
            '"item": "bettergold:chaosgold_block"', '"item": "bettergold:chaosgold_ingot"'),
    ]

    lines = []
    lines.append("bg-n10rc2 扰动矩阵（判据 = 本段问题数 + 命中 tag；每例逐字节复原 + SHA256）")
    lines.append("")
    lines.append("%-22s %-9s %-7s %-9s %s" % ("用例", "script_exit", "my_section", "复原", "命中的 tag"))
    ok_all = True
    for c in cases:
        orig = c.path.read_bytes()
        sha_before = sha(c.path)
        bak = PROBE / (c.name + "__" + c.path.name + ".orig")
        if not bak.exists():
            shutil.copyfile(c.path, bak)
        try:
            text = orig.decode("utf-8")
            new_text = c.mutate(text)
            assert new_text != text, "%s: 扰动没有生效" % c.name
            c.path.write_bytes(new_text.encode("utf-8"))
            code, n, tags = run_validator()
        finally:
            c.path.write_bytes(orig)
            restored = sha(c.path) == sha_before
        ok_all = ok_all and restored
        expect_green = c.name == "comment-only"
        passed = (n == 0) if expect_green else (n > 0)
        ok_all = ok_all and passed and restored
        lines.append("%-22s %-9d %-7d %-9s %s   [%s]"
                     % (c.name, code, n, "逐字节✓" if restored else "失败",
                        ",".join(tags) if tags else "-",
                        "绿" if n == 0 else "红"))
        lines.append("    动作: " + c.note)
    lines.append("")
    lines.append("全部用例符合预期（真扰动必红 / 只改注释必绿 / 复原逐字节一致）: %s" % ok_all)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if not ok_all:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
