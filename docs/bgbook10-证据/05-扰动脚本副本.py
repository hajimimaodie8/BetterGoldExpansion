#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-book §十 扰动矩阵（一次性 harness，住在被 git 忽略的 build/ 下）。

契约（`mcmod_experience` `ex\\03` §3.4 / §3.11 / §3.12）：
  本轮**每一处新增或改动的断言**都必须被证明"能红"。每个用例在磁盘上**逐字节**改坏一个文件、
  跑 `tools/asset-generator/validate_metal_data.py` 与（需要时）`validate_advancements.py`，要求：
    * 输出里出现**期望的稳定 ASCII 断言 id**（只看 id，不看中文消息），且
    * `exit != 0`（**反向对照**那条必须仍 `exit 0`）；
  跑完**逐字节复原**并核对 SHA256。

⚠ 行尾：本轮改的文件**全部是 LF**（`docs/1.6-规格.md` / `generate_handbook_data.py` /
  `validate_metal_data.py` / 两份 lang json / 手册 JSON / 冻结快照）。
  ⇒ 多行字面量在 LF 下可以安全使用。

Run:  python build\\bgbook10-perturb.py
"""

import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
OUT = REPO / "build" / "bgbook10-perturb-result.txt"
RAW_LOG = REPO / "build" / "bgbook10-perturb-raw.txt"

ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
ENT = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries"
ENTEN = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/en_us/entries"
CROPS = ENT + "/golden_feast_crops.json"
FOODS = ENT + "/golden_feast_foods.json"
STURDY = ENT + "/golden_feast_sturdy.json"
FDFOOD = ENT + "/golden_feast_fd_foods.json"
FDSTURDY = ENT + "/golden_feast_fd_sturdy.json"
GEN = "tools/asset-generator/generate_handbook_data.py"
SNAP = "tools/asset-generator/bgappend-requirements-snapshot/bg-book-10.md"
DOC = "docs/1.6-规格.md"

# (用例名, [edit, ...], 期望的 ASCII id 或 None=必须仍绿)
#   edit = (相对路径, old_bytes, new_bytes[, "create"|"all"|"first"])
CASES = [
    # ---------- ① 5 章结构 ----------
    ("P01 章1 的封面图标被换", [
        (CROPS, b'"icon": "bettergold:gold_infused_dirt"',
         b'"icon": "bettergold:golden_bone_meal"')],
     "bgbook10-chapters"),
    ("P02 删掉 golden_feast_foods 条目（条目数 20->19）", [
        (FOODS, None, None)],
     "bgbook-entry-count"),
    ("P03 golden_feast_crops 少一页（10->9）", [
        (CROPS, b',\n    {\n      "type": "patchouli:crafting",\n'
                b'      "recipe": "bettergold:golden_bone_meal"\n    }', b'')],
     "bgbook10-chapters"),
    ("P04 sortnum 被改（章2 1 -> 5）", [
        (FOODS, b'"sortnum": 1', b'"sortnum": 5')],
     "bgbook10-chapters"),
    # ---------- ② 页型 / 正文键 ----------
    ("P05 配方页的页型被换成 text", [
        (FOODS, b'"type": "patchouli:smelting"', b'"type": "patchouli:text"')],
     "bgbook10-page-types"),
    ("P06 正文键被改（1_left -> 2_left）", [
        (FOODS, b'"text": "bettergold.handbook.page.golden_feast_foods_1_left"',
         b'"text": "bettergold.handbook.page.golden_feast_foods_2_left"')],
     "bgbook10-page-types"),
    ("P07 ★G1 酿造页被改回配方页（spotlight -> crafting + recipe）", [
        (FOODS, b'    {\n      "type": "patchouli:spotlight",\n'
                b'      "item": "bettergold:brewed_hot_cocoa",\n'
                b'      "text": "bettergold.handbook.page.golden_feast_foods_1_right"\n    },',
         b'    {\n      "type": "patchouli:crafting",\n'
         b'      "recipe": "bettergold:golden_chocolate_bar",\n'
         b'      "text": "bettergold.handbook.page.golden_feast_foods_1_right"\n    },')],
     "bgbook10-page-types"),
    ("P08 ★G2 厨锅页被换页型（spotlight -> smelting）", [
        (FDFOOD, b'"type": "patchouli:spotlight",\n      "item": "bettergold:alchemical_meat"',
         b'"type": "patchouli:smelting",\n      "item": "bettergold:alchemical_meat"')],
     "bgbook10-page-types"),
    ("P09 一个门禁页消失（行整块删掉，页数 10->9）", [
        (FDFOOD, b'    {\n      "type": "patchouli:spotlight",\n'
                 b'      "item": "bettergold:golden_apple_cider",\n'
                 b'      "text": "bettergold.handbook.page.golden_feast_fd_foods_3_left"\n    },\n',
         b'')],
     "bgbook10-chapters"),
    # ---------- ③ 图标表 / 配方 ----------
    ("P10 章1 的轮换图标被换（数组里的一项）", [
        (CROPS, b'"minecraft:golden_carrot"', b'"minecraft:golden_apple"')],
     "bgbook10-spotlight"),
    ("P11 章3 的 spotlight 图标被换", [
        (STURDY, b'"item": "bettergold:sturdygold_brewed_hot_cocoa"',
         b'"item": "bettergold:sturdygold_brewed_hot_cocoaX"')],
     "bgbook10-spotlight"),
    ("P12 章1 第3页右的第二个配方被删（一页两配方上限用例）", [
        (CROPS, b',\n      "recipe2": "bettergold:golden_wheat_block"', b'')],
     "bgbook10-recipes"),
    ("P13 配方指向不存在的 id（死链）", [
        (FOODS, b'"recipe": "bettergold:golden_horse_feed"',
         b'"recipe": "bettergold:golden_horse_feed9"')],
     "bgbook10-recipe-refs"),
    ("P14 recipe3 越界键被塞进配方页（Patchouli 只有 recipe/recipe2 两槽）", [
        (FOODS, b'      "recipe": "bettergold:golden_chocolate_bar",',
         b'      "recipe": "bettergold:golden_chocolate_bar",\n'
         b'      "recipe3": "bettergold:golden_bread",')],
     "bgbook-page-recipe-cap"),
    # ---------- ④ 逐字文案 / 语言键 / 占位 ----------
    ("P15 zh 里的一段逐字文案被改动", [
        (ZH, u'"bettergold.handbook.page.golden_feast_crops_1_left": "该模组其实还提供了关于种植的玩法'
             .encode("utf-8"),
         u'"bettergold.handbook.page.golden_feast_crops_1_left": "X该模组其实还提供了关于种植的玩法'
             .encode("utf-8"))],
     "bgbook10-texts-verbatim"),
    ("P16 en 缺一个 §十 语言键（键名被改）", [
        (EN, b'"bettergold.handbook.entry.golden_feast_sturdy"',
         b'"bettergold.handbook.entry.golden_feast_sturdyX"')],
     "bgbook10-lang-bilingual"),
    ("P17 ★待补格被填成自编内容", [
        (ZH, u'"bettergold.handbook.page.golden_feast_fd_sturdy_5_right": "（作者未指定）"'.encode("utf-8"),
         u'"bettergold.handbook.page.golden_feast_fd_sturdy_5_right": "敬请期待"'.encode("utf-8"))],
     "bgbook10-todo-cell"),
    ("P18 ★章5 封面被自己填了一张（占位被替换）", [
        (FDSTURDY, b'"icon": "bettergold:alchemical_meat"',
         b'"icon": "bettergold:sturdygold_alchemical_meat"')],
     "bgbook10-ch5-cover-todo"),
    ("P19 冻结快照 §10.7 的「作者未给，待补」被删", [
        (SNAP, u"作者未给，待补".encode("utf-8"), b"", "all")],
     "bgbook10-ch5-cover-todo"),
    ("P20 冻结快照里一段作者原文被改动（逐字文案的期望值来源）", [
        (SNAP, u"它能为你完全减免摔落伤害".encode("utf-8"), b"", "all")],
     "bgbook10-texts-verbatim"),
    # ---------- ⑤ 生成器 / 作废条目 ----------
    ("P21 生成器里 §十 的 5 章清单被改名", [
        (GEN, b"FEAST_ENTRIES = [", b"FEAST_ENTRIES_X = [")],
     "bgbook10-generator"),
    ("P22 生成器的 ENTRIES 里又出现了旧占位 entry_golden_feast", [
        (GEN, u"    # ⛔ entry_tools_per_family / entry_armor_per_family".encode("utf-8"),
         u"    entry_golden_feast,\n    # ⛔ entry_tools_per_family / entry_armor_per_family".encode("utf-8"))],
     "bgbook10-generator"),
    ("P23 生成器里章5 封面的占位常量被改（作者还没给封面）", [
        (GEN, b'_BG10_COVER_PLACEHOLDER = "alchemical_meat"',
         b'_BG10_COVER_PLACEHOLDER = "sturdygold_alchemical_meat"')],
     "bgbook10-generator"),
    ("P24 生成器把旧占位从 RETIRED_ENTRIES 里摘掉（**代码行 + 注释里那一份都要改**）", [
        (GEN, u"RETIRED_ENTRIES = RETIRED_ENTRIES + [entry_golden_feast]".encode("utf-8"),
         u"RETIRED_ENTRIES = RETIRED_ENTRIES + []".encode("utf-8"), "all")],
     "bgbook10-generator"),
    ("P25 §十 作废的旧占位又回到产物里", [
        (ENT + "/golden_feast.json", None,
         '{"name": "bettergold.handbook.entry.golden_feast", '
         '"category": "bettergold:golden_feast", "icon": "bettergold:sturdygold_apple", '
         '"sortnum": 0, "pages": []}'.encode("utf-8"), "create")],
     "bgbook10-old-placeholder-gone"),
    # ---------- ⑥ 文档侧 ----------
    ("P26 docs §24 的门禁项字样被全部删掉", [
        (DOC, u"门禁项".encode("utf-8"), b"", "all")],
     "bgbook10-doc"),
    ("P27 docs §24 里 nutrition 的字样被全部删掉", [
        (DOC, b"nutrition", b"", "all")],
     "bgbook10-doc"),
    # ---------- ⑦ 反向对照：只改注释必须仍绿 ----------
    ("P28 ★反向对照：只加一行注释（必须仍 exit 0）", [
        (GEN, u"# --------------------------------------------------------------------------------------\n"
              u"# bg-book §十 追加轮".encode("utf-8"),
         u"# 本行是扰动反向对照用的注释\n"
         u"# --------------------------------------------------------------------------------------\n"
         u"# bg-book §十 追加轮".encode("utf-8"))],
     None),
    ("P29 ★反向对照：只改文档里的一句说明（必须仍 exit 0）", [
        (DOC, u"⇒ 落点集中在生成器的 `_BG10_SPOTLIGHT_DOWNGRADES`".encode("utf-8"),
         u"⇒ \u843d\u70b9\u96c6\u4e2d\u5728\u751f\u6210\u5668\u7684 `_BG10_SPOTLIGHT_DOWNGRADES`\uff08\u53cd\u5411\u5bf9\u7167\uff09".encode("utf-8"))],
     None),
    ("P30 ★反向对照：只改**注释里**那一份 needle，真正的代码行保留（必须仍 exit 0）—— "
     "这条钉住『正向 needle 必须跑在去注释源码上』的修正", [
        (GEN, u"见下方 §十 区块与 `RETIRED_ENTRIES = RETIRED_ENTRIES + [entry_golden_feast]`。".encode("utf-8"),
         u"见下方 §十 区块与 RETIRED_ENTRIES 的追加行。".encode("utf-8"))],
     None),
]

CHAINED = [
    # (用例名, 需要连带改的其它文件, [edit,...], 期望 id, 期望子串)
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def apply(edit):
    rel, old, new = edit[0], edit[1], edit[2]
    mode = edit[3] if len(edit) > 3 else "first"
    p = REPO / rel
    if old is None:
        if mode == "create":
            p.write_bytes(new)
            return ("delete", p)
        data = p.read_bytes()
        p.unlink()
        return ("restore", p, data)
    data = p.read_bytes()
    if mode == "all":
        if old not in data:
            raise SystemExit("needle not found (all): %s" % rel)
        p.write_bytes(data.replace(old, new))
        return ("restore", p, data)
    idx = data.find(old)
    if idx < 0:
        raise SystemExit("needle not found: %s :: %r" % (rel, old[:60]))
    p.write_bytes(data[:idx] + new + data[idx + len(old):])
    return ("restore", p, data)


def run_validator():
    r = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, cwd=str(REPO))
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace") + \
                         (r.stderr or b"").decode("utf-8", "replace")


def main():
    lines = []
    raw = []
    mismatches = 0

    def emit(s):
        print(s)
        lines.append(s)

    emit("=== bg-book §十 扰动矩阵 (%d 用例 + 2 基线) ===" % len(CASES))
    emit("行尾实测：全部用例改的文件均为 LF（本轮无 CRLF 用例）")

    integrity = {}
    for c in CASES:
        for e in c[1]:
            p = REPO / e[0]
            if p.exists():
                integrity.setdefault(e[0], sha(p))

    for label in ("基线（改前）",):
        code, out = run_validator()
        raw.append("---- %s exit=%d ----\n%s" % (label, code, out))
        ok = (code == 0)
        emit("[%s] exit=%d %s" % (label, code, "OK" if ok else "MISMATCH"))
        if not ok:
            mismatches += 1

    for name, edits, want in CASES:
        actions = [apply(e) for e in edits]
        try:
            code, out = run_validator()
        finally:
            for a in actions:
                p = a[1]
                if a[0] == "delete":
                    p.unlink()
                else:
                    p.write_bytes(a[2])
        raw.append("---- %s exit=%d ----\n%s" % (name, code, out))
        hit = (want is not None) and (want in out)
        if want is None:
            ok = (code == 0)
            verdict = "OK(仍绿)" if ok else "MISMATCH(应为绿却红)"
        else:
            ok = (code != 0 and hit)
            verdict = ("OK id=%s" % want) if ok else \
                      ("MISMATCH(exit=%d,id_hit=%s)" % (code, hit))
        if not ok:
            mismatches += 1
        emit("[%s] exit=%d %s" % (name, code, verdict))

    for label in ("基线（收尾）",):
        code, out = run_validator()
        raw.append("---- %s exit=%d ----\n%s" % (label, code, out))
        ok = (code == 0)
        emit("[%s] exit=%d %s" % (label, code, "OK" if ok else "MISMATCH"))
        if not ok:
            mismatches += 1

    emit("--- 逐字节复原核对（SHA256）---")
    for rel, h in sorted(integrity.items()):
        now = sha(REPO / rel)
        same = (now == h)
        if not same:
            mismatches += 1
        emit("  %-70s %s %s" % (rel, "SAME" if same else "DIFF!!!", now[:16]))

    emit("")
    emit("mismatches = %d" % mismatches)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    RAW_LOG.write_text("\n".join(raw), encoding="utf-8")
    sys.exit(1 if mismatches else 0)


if __name__ == "__main__":
    main()
