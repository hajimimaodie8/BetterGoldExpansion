#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-book §八 扰动矩阵（一次性 harness，住在被 git 忽略的 build/ 下）。

契约（`mcmod_experience` `ex\03` §3.4 / §3.11）：
  本轮**每一处新增或改动的断言**都必须被证明"能红"。每个用例在磁盘上**逐字节**改坏一个文件、
  跑 `tools/asset-generator/validate_metal_data.py`，要求：
    * 输出里出现**期望的稳定 ASCII 断言 id**（只看 id，不看中文消息 —— 中文匹配会大面积 MISMATCH），且
    * `exit != 0`（**反向对照**那条必须仍 `exit 0`）；
  跑完**逐字节复原**并核对 SHA256（静默改坏会让整轮作废 —— bg-16 就发生过一次）。
  ⚠ 三条"用例本身失效"的陷阱都在这里防住了：
    ① 断言看调用点不看条件真假 -> 用例直接替换**那一行结构**；
    ② CRLF 下多行字面量匹配会静默不中 -> **所有 old/new 都不含换行**（只有"插一页"那条 new 里含 `\\n`）；
    ③ 改不成合法形状 -> 只做"合法但语义相反"的改动，并把"模式没找到"报成 `SETUP-FAIL`。

Run:  python build\\bgbook8-perturb.py
"""

import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
OUT = REPO / "build" / "bgbook8-perturb-result.txt"
RAW_LOG = REPO / "build" / "bgbook8-perturb-raw.txt"

ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
ENT = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries"
CAT = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/categories/gear_upgrade.json"
GEAR1 = ENT + "/gear_flamegold.json"
GEARL = ENT + "/gear_linkage.json"
GK = ENT + "/golden_knowledge.json"
GEN = "tools/asset-generator/generate_handbook_data.py"
MEV = "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java"
DOC = "docs/1.6-规格.md"

# (用例名, [edit, ...], 期望的 ASCII id 或 None=必须仍绿)
#   edit = (相对路径, old_bytes, new_bytes[, "create"])
#     old=None + flag "create" -> 新建该文件
CASES = [
    # ---------- ① 类别改名 ----------
    ("P01 类别中文名改回旧的「装备的升级」", [
        (ZH, u'"bettergold.handbook.category.gear_upgrade.name": "装备的强化"'.encode("utf-8"),
         u'"bettergold.handbook.category.gear_upgrade.name": "装备的升级"'.encode("utf-8"))],
     "bgbook8-gear-category"),
    ("P02 类别图标被改（id/图标应当不动）", [
        (CAT, b'"icon": "bettergold:sturdygold_sword"', b'"icon": "bettergold:sturdygold_ingot"')],
     "bgbook8-gear-category"),
    # ---------- ② 作废的旧条目不许回来 ----------
    ("P03 作废的 tools_per_family 又回到产物里", [
        (ENT + "/tools_per_family.json", None,
         b'{"name": "bettergold.handbook.entry.tools_per_family", '
         b'"category": "bettergold:gear_upgrade", "icon": "bettergold:sturdygold_sword", '
         b'"sortnum": 0, "pages": []}', "create")],
     "bgbook8-old-entries-gone"),
    # ---------- ③ 9 章结构 ----------
    ("P04 gear_flamegold 的 sortnum 被改", [
        (GEAR1, b'"sortnum": 1,', b'"sortnum": 3,')],
     "bgbook8-chapters"),
    ("P05 删掉 gear_illusiongold 条目（条目数 17->16）", [
        (ENT + "/gear_illusiongold.json", None, None)],
     "bgbook-entry-count"),
    ("P06 文案页的 text 键被改", [
        (GEAR1, b'"text": "bettergold.handbook.page.gear_flamegold_1_left"',
         b'"text": "bettergold.handbook.page.gear_flamegold_1_right"')],
     "bgbook8-page-types"),
    # ---------- ④ 锻造 14 件的顺序 / 死链 / 胚底配方 ----------
    ("P07 锻造页顺序被换（剑<->斧）", [
        (GEAR1, b'"recipe": "bettergold:smithing_flamegold_sword"',
         b'"recipe": "bettergold:smithing_flamegold_axe"')],
     "bgbook8-forge-order"),
    ("P08 锻造页指向不存在的配方（死链）", [
        (ENT + "/gear_thornsgold.json", b'"recipe": "bettergold:smithing_thornsgold_sword"',
         b'"recipe": "bettergold:smithing_thornsgold_sword9"')],
     "bgbook8-recipe-refs"),
    ("P09 章1 的胚底配方页被换", [
        (GEARL, b'"recipe": "bettergold:golden_mace_blank"',
         b'"recipe": "bettergold:golden_bow_blank"')],
     "bgbook8-blank-recipes"),
    # ---------- ⑤ 章3 第1页（汇总页）不许回来 ----------
    ("P10 又有页引用了 knowledge_1_summary（汇总页回来了）", [
        (GK, b'"text": "bettergold.handbook.page.knowledge_2_left"',
         b'"text": "bettergold.handbook.page.knowledge_1_summary"')],
     "bgbook8-k3-p1-gone"),
    # ---------- ⑥ 改动的既有期望 ----------
    ("P11 章3 多出一页（8->9）", [
        (GK, b'"pages": [',
         b'"pages": [\n    {\n      "type": "patchouli:text",\n'
         b'      "text": "bettergold.handbook.page.knowledge_5_right"\n    },')],
     "bgappend-book-k3-pages"),
    ("P12 章3 的页型被换（spotlight->text）", [
        (GK, b'"type": "patchouli:spotlight"', b'"type": "patchouli:text"', "first")],
     "bgbook2-chapter-pages"),
    # ---------- ⑦ 逐字文案 / 语言键 ----------
    ("P13 zh 里的一段逐字文案被改动", [
        (ZH, u'"bettergold.handbook.page.gear_flamegold_1_left": "使用烈燃金'.encode("utf-8"),
         u'"bettergold.handbook.page.gear_flamegold_1_left": "X使用烈燃金'.encode("utf-8"))],
     "bgbook8-texts-verbatim"),
    ("P14 en 缺一个 §八 语言键（键名被改）", [
        (EN, b'"bettergold.handbook.entry.gear_echogold"', b'"bettergold.handbook.entry.gear_echogoldX"')],
     "bgbook8-lang-bilingual"),
    # ---------- ⑧ 生成器覆盖 ----------
    ("P15 生成器的族清单被改（只长一边）", [
        (GEN, b'("flamegold", "blazing_rod"),', b'("flamegoldx", "blazing_rod"),')],
     "bgbook8-generator"),
    # ---------- ⑨ 代码侧（§8.11 第 8 条的真 bug 修复） ----------
    ("P16 巫毒整套免疫守卫被反转（>=4 -> <4）", [
        (MEV, b"if (voodooFamily != null && wornPieces(entity, voodooFamily) >= 4) {",
         b"if (voodooFamily != null && wornPieces(entity, voodooFamily) < 4) {")],
     "bgbook8-voodoo-poison-independent"),
    ("P17 结构回退：把结雷金改回「< 4 ⇒ return」的早退形状", [
        (MEV, b"if (family != null && wornPieces(entity, family) >= 4) {",
         b"if (family == null || wornPieces(entity, family) < 4) { return; } if (family != null) {")],
     "bgbook8-voodoo-poison-independent"),
    # ---------- ⑩ 文档口径 ----------
    ("P18 文档里的门禁口径句被改（全部出现处）", [
        (DOC, u"后页 = 7 页 × 2 配方".encode("utf-8"), u"后页 = 7 页 x 2 配方".encode("utf-8"), "all")],
     "bgbook8-doc"),
    # ---------- ⑪ 反向对照：只加注释必须仍绿 ----------
    ("P19 REVERSE CONTROL: 只加注释（必须仍绿）", [
        # Java：注释里写出被禁的旧形状（`< 4` / `POISON`）—— 判据必须跑在去注释后的源码上。
        #   ⚠ 注释里**不许**出现 `/*` 组合（那会喂坏关卡自己的 strip_comments，见 ex\03 §3.4 最后一行）
        (MEV, b"public static void onLivingTick(",
         b"// PERTURB comment: the old shape wornPieces(entity, family) < 4 and MobEffects.POISON\n"
         b"    public static void onLivingTick("),
        # 生成器：注释里写出被禁的字面量（recipe3 / 装备的升级 / knowledge_1_summary）
        (GEN, b"GEAR_CATEGORY = ",
         b"# PERTURB comment: recipe3 / \xe8\xa3\x85\xe5\xa4\x87\xe7\x9a\x84\xe5\x8d\x87\xe7\xba\xa7 "
         b"/ knowledge_1_summary are forbidden here\nGEAR_CATEGORY = "),
        # 文档：注释性补充（正向 needle 不受影响、负向判据也不该被它喂饱）
        (DOC, b"## 19.9 ", u"## 19.9 ".encode("utf-8") + b"PERTURB-comment "),
    ], None),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(name, edits, expected):
    backups, deleted, created = {}, {}, []
    try:
        for edit in edits:
            rel, old, new = edit[0], edit[1], edit[2]
            flag = edit[3] if len(edit) > 3 else None
            p = REPO / rel
            if flag == "create":
                created.append(rel)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(new)
                continue
            if rel not in backups:
                backups[rel] = p.read_bytes()
            if old is None:                      # 删除
                deleted[rel] = p.read_bytes()
                p.unlink()
                continue
            raw = p.read_bytes()
            if old not in raw:
                return name, "SETUP-FAIL", "pattern not found in %s (perturbation did not apply)" % rel, -1
            if flag == "first":
                p.write_bytes(raw.replace(old, new, 1))
                continue
            if flag == "all":
                p.write_bytes(raw.replace(old, new))
                continue
            if raw.count(old) != 1:
                return name, "SETUP-FAIL", "pattern occurs %d times in %s" % (raw.count(old), rel), -1
            p.write_bytes(raw.replace(old, new))
        rc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                            stdout=open(RAW_LOG, "wb"), stderr=subprocess.STDOUT).returncode
        text = RAW_LOG.read_bytes().decode("utf-8", "replace")
        if expected is None:
            ok = rc == 0
            detail = "exit=%d (must be 0)" % rc
        else:
            hit = expected in text
            ok = hit and rc != 0
            detail = "exit=%d expected-id-hit=%s" % (rc, hit)
        return name, "OK" if ok else "MISMATCH", detail, rc
    finally:
        for rel, raw in list(backups.items()) + list(deleted.items()):
            p = REPO / rel
            p.write_bytes(raw)
            if sha(p) != hashlib.sha256(raw).hexdigest():
                return name, "RESTORE-FAIL", "sha256 mismatch after restore: %s" % rel, -1
        for rel in created:
            p = REPO / rel
            if p.exists():
                p.unlink()


lines, mismatches = [], 0

rc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                    stdout=open(RAW_LOG, "wb"), stderr=subprocess.STDOUT).returncode
lines.append("BASELINE-1 exit=%d (expect 0) -> %s" % (rc, "OK" if rc == 0 else "MISMATCH"))
mismatches += 0 if rc == 0 else 1

for name, edits, expected in CASES:
    n, status, detail, _rc = run_case(name, edits, expected)
    if status != "OK":
        mismatches += 1
    lines.append("%-52s %-11s %s" % (n, status, detail))

rc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                    stdout=open(RAW_LOG, "wb"), stderr=subprocess.STDOUT).returncode
lines.append("BASELINE-2 exit=%d (expect 0) -> %s" % (rc, "OK" if rc == 0 else "MISMATCH"))
mismatches += 0 if rc == 0 else 1

lines.append("")
lines.append("cases=%d mismatches=%d" % (len(CASES) + 2, mismatches))
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
sys.exit(1 if mismatches else 0)
