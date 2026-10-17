#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rg **扰动矩阵**：每个用例都必须「真扰动 ⇒ 本段红（exit 1 且点名 tag）」、
「只改注释 ⇒ 本段仍 0 条」，并且**逐字节复原 + SHA256 自证**。

⚠ 为什么判据是「本段」而不是「整个脚本的 exit」：
   同一轮有**另一个会话**正在往 `validate_metal_data.py` 里追加他自己的关卡段
   （`[bgn10d-doc]` 那条此刻是红的，因为他自己的文档还没落）⇒ 整个脚本的 exit 目前恒为 1。
   所以本脚本两个列都记：`script_exit`（整脚本）与 `my_section`（`1.7 bg-n10rg…问题: N [tags]`）。
   判据用后者，前者只作参考 —— 并且**不修改**别人的段落（改前先读、唯一锚点、只动自己那几行，
   注释型扰动因此改的是 Java 源码，不是这个共享文件）。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

VMD = "tools/asset-generator/validate_metal_data.py"
JAVA = "src/main/java/com/hjmmd_8/bettergold/recipe/RawSturdygoldRecipe.java"
REC = "src/main/resources/data/bettergold/recipe"
BOOK_ZH = ("src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/"
           "zh_cn/entries/gear_chaosgold.json")
GEN = "tools/asset-generator/generate_chaosgold_recipes.py"

SECTION = re.compile(r"bg-n10rg.*?:\s*(\d+)\s+\[(.*)\]\s*（")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()


def run_validator() -> tuple[int, int, str]:
    # ⚠ 子进程的输出编码：不强制 UTF-8 的话 Windows 会按 GBK 写出，Pipe 里再按 UTF-8 读就全是 '?'
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, VMD], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    out = (p.stdout or "") + (p.stderr or "")
    m = SECTION.search(out.replace("\n", " "))
    if not m:
        return p.returncode, -1, "<找不到本段结论行>"
    return p.returncode, int(m.group(1)), m.group(2)


def mutate_json(path: str, fn) -> bytes:
    raw = open(path, "rb").read()
    obj = json.loads(raw.decode("utf-8"))
    fn(obj)
    open(path, "wb").write((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return raw


def mutate_text(path: str, old: str, new: str, count: int = 1) -> bytes:
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    if text.count(old) != count:
        raise SystemExit("[用例坏了] %s 里 %r 命中 %d 次（期望 %d）"
                         % (path, old[:40], text.count(old), count))
    open(path, "wb").write(text.replace(old, new).encode("utf-8"))
    return raw


def restore(path: str, raw: bytes) -> bool:
    open(path, "wb").write(raw)
    now = open(path, "rb").read()
    return sha(now) == sha(raw)


# ---------------------------------------------------------------------------------------
# 用例： (名字, 期望命中的 tag 关键字, 施加函数 -> (路径, 原始字节))
# ---------------------------------------------------------------------------------------
def case_grid_swap():
    p = REC + "/chaosgold_axe.json"

    def mut(o):
        o["pattern"][1] = "XX"          # 第2行第2列：棍 → 锭（换一格）
    return [(p, mutate_json(p, mut))]


def case_result_count():
    p = REC + "/chaosgold_sword.json"

    def mut(o):
        o["result"]["count"] = 2
    return [(p, mutate_json(p, mut))]


def case_doubled_catalyst():
    p = REC + "/raw_echogold_doubled.json"

    def mut(o):
        o["catalyst"] = "bettergold:alchemic_fuel"
    return [(p, mutate_json(p, mut))]


def case_doubled_count():
    p = REC + "/raw_echogold_doubled.json"

    def mut(o):
        o["count"] = 1
    return [(p, mutate_json(p, mut))]


def case_base_mutated():
    p = REC + "/raw_echogold.json"

    def mut(o):
        o["catalyst"] = "bettergold:refined_alchemic_oil"
    return [(p, mutate_json(p, mut))]


def case_java_fuel():
    # 把「按催化剂那一格判」改回「按炼金燃油判」⇒ 高阶炼金油那格就不返瓶了
    return [(JAVA, mutate_text(JAVA, "stack.is(this.catalyst)",
                               "stack.is(AllItems.ALCHEMIC_FUEL.get())", 2))]


def case_java_count():
    # 产物不带数量 ⇒ 结果格永远显示 1
    return [(JAVA, mutate_text(JAVA, "new ItemStack(this.result, this.count)",
                               "new ItemStack(this.result)", 2))]


def case_handbook_page():
    p = BOOK_ZH

    def mut(o):
        del o["pages"][3]               # 删掉一页配方页（13 → 12）
    return [(p, mutate_json(p, mut))]


def case_generator_gear():
    return [(GEN, mutate_text(GEN,
                              '        "helmet", "chestplate", "leggings", "boots", "shield", "crossbow"]',
                              '        "helmet", "chestplate", "leggings", "boots", "shield", "crossbow", "bow"]',
                              1))]


def case_comment_only():
    # 只加注释：注释里**逐字**写出必须被判红的两串（正向 needle 跑在去注释源码上 ⇒ 必须仍绿）
    add = ("// 扰动用例（只改注释）：下面这两串如果被当真，本段会假红 —— "
           "stack.is(AllItems.ALCHEMIC_FUEL.get()) / new ItemStack(this.result)\n")
    anchor = "public class RawSturdygoldRecipe extends CustomRecipe {\n"
    return [(JAVA, mutate_text(JAVA, anchor, anchor + add, 1))]


CASES = [
    ("grid-swap（换一格：斧 第2行第2列 棍→锭）", "bgn10rg-gear-cell", case_grid_swap, 1),
    ("result-count（剑 产物 1→2）", "bgn10rg-gear-result", case_result_count, 1),
    ("doubled-catalyst（双倍版 催化剂→炼金燃油）", "bgn10rg-doubled-catalyst", case_doubled_catalyst, 1),
    ("doubled-count（双倍版 数量 2→1）", "bgn10rg-doubled-count", case_doubled_count, 1),
    ("base-mutated（基础版被写进 catalyst）", "bgn10rg-doubled-base-untouched", case_base_mutated, 1),
    ("java-fuel（返瓶改回按 ALCHEMIC_FUEL 判）", "bgn10rg-bottle", case_java_fuel, 1),
    ("java-count（产物不带数量）", "bgn10rg-doubled-count", case_java_count, 1),
    ("handbook-page（删一页配方页 13→12）", "bgn10rg-handbook", case_handbook_page, 1),
    ("generator-gear（真源 GEAR 多一件 bow）", "bgn10rg-generator", case_generator_gear, 1),
    ("comment-only（只在 Java 里加注释，注释里写出被禁的两串）", "", case_comment_only, 0),
]


def main() -> None:
    rows = []
    for name, tag, fn, want_red in CASES:
        touched = fn()
        try:
            code, n, detail = run_validator()
        finally:
            ok = all(restore(p, raw) for p, raw in touched)
        hit = (tag in detail) if tag else None
        good = (n > 0 and hit) if want_red else (n == 0)
        rows.append((name, code, n, hit if tag else "—", ok, good))
        print("{:<52} script_exit={} 本段问题={:<3} 命中={!s:<6} 复原={} 判定={}"
              .format(name, code, n, hit if tag else "—", ok, "PASS" if good else "FAIL"))
        if not good:
            print("    detail: " + detail)

    bad = [r for r in rows if not r[5]]
    print("\n" + "=" * 100)
    print("扰动用例 {} 条：命中 {} / 未命中 {}；逐字节复原全部成功={}"
          .format(len(rows), len(rows) - len(bad), len(bad), all(r[4] for r in rows)))
    open("build/bgn10rg-perturb.txt", "w", encoding="utf-8", newline="\n").write(
        "\n".join("%s | script_exit=%s | 本段问题=%s | 命中=%s | 复原=%s | %s"
                  % (r[0], r[1], r[2], r[3], r[4], "PASS" if r[5] else "FAIL") for r in rows) + "\n")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
