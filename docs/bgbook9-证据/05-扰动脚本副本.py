#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-book §九 扰动矩阵（一次性 harness，住在被 git 忽略的 build/ 下）。

契约（`mcmod_experience` `ex\\03` §3.4 / §3.11）：
  本轮**每一处新增或改动的断言**都必须被证明"能红"。每个用例在磁盘上**逐字节**改坏一个文件、
  跑 `tools/asset-generator/validate_metal_data.py`，要求：
    * 输出里出现**期望的稳定 ASCII 断言 id**（只看 id，不看中文消息），且
    * `exit != 0`（**反向对照**那条必须仍 `exit 0`）；
  跑完**逐字节复原**并核对 SHA256。

⚠ 行尾实测（本轮的机器证明，脚本开头会打印）：本轮改的文件**全部是 LF**
  （`docs/1.6-规格.md` / `generate_handbook_data.py` / `validate_metal_data.py` /
   `ModEvents.java` / 两份 lang json / 手册 JSON / 冻结快照）；
  唯一的 CRLF 是 `run/server.properties`（不在本 harness 的用例里）。
  ⇒ 多行字面量在 LF 下可以安全使用；仍然：**只有 P03 一条**的 new/old 含 `\\n`。

Run:  python build\\bgbook9-perturb.py
"""

import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
OUT = REPO / "build" / "bgbook9-perturb-result.txt"
RAW_LOG = REPO / "build" / "bgbook9-perturb-raw.txt"

ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
ENT = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries"
INTRO = ENT + "/merchant_intro.json"
GIFT = ENT + "/merchant_gift_box.json"
ANTQ = ENT + "/merchant_antique_gear.json"
GEN = "tools/asset-generator/generate_handbook_data.py"
SNAP = "tools/asset-generator/bgappend-requirements-snapshot/bg-book-9.md"
MEV = "src/main/java/com/hjmmd_8/bettergold/event/ModEvents.java"
DOC = "docs/1.6-规格.md"

# (用例名, [edit, ...], 期望的 ASCII id 或 None=必须仍绿)
#   edit = (相对路径, old_bytes, new_bytes[, "create"|"all"|"first"])
CASES = [
    # ---------- ① 3 章结构 ----------
    ("P01 merchant_intro 的封面图标被改", [
        (INTRO, b'"icon": "bettergold:gold_exchange_counter"',
         b'"icon": "bettergold:treasure_gift_box"')],
     "bgbook9-chapters"),
    ("P02 删掉 merchant_gift_box 条目（条目数 18->17）", [
        (GIFT, None, None)],
     "bgbook-entry-count"),
    ("P03 merchant_intro 少一页（3->2）", [
        (INTRO, b'    {\n      "type": "patchouli:text",\n'
                b'      "text": "bettergold.handbook.page.merchant_intro_1_left"\n    },\n',
         b'')],
     "bgbook9-chapters"),
    # ---------- ② 页型 / 正文键 ----------
    ("P04 配方页的页型被换成 text", [
        (INTRO, b'"type": "patchouli:crafting"', b'"type": "patchouli:text"')],
     "bgbook9-page-types"),
    ("P05 正文键被改（2_left -> 1_left）", [
        (INTRO, b'"text": "bettergold.handbook.page.merchant_intro_2_left"',
         b'"text": "bettergold.handbook.page.merchant_intro_1_left"')],
     "bgbook9-page-types"),
    # ---------- ③ 图标表 / 配方 ----------
    ("P06 章2 的 spotlight 图标被换", [
        (GIFT, b'"item": "bettergold:curio_box"', b'"item": "bettergold:treasure_gift_box"')],
     "bgbook9-icons"),
    ("P07 章3 六件器具的配方顺序被换（剑<->斧）", [
        (ANTQ, b'"recipe": "bettergold:upgrade_netherite_antique_sword"',
         b'"recipe": "bettergold:upgrade_netherite_antique_axe"')],
     "bgbook9-recipes"),
    ("P08 配方指向不存在的 id（死链）", [
        (ANTQ, b'"recipe": "bettergold:netherite_dust_to_small_scrap"',
         b'"recipe": "bettergold:netherite_dust_to_small_scrap9"')],
     "bgbook9-recipe-refs"),
    # ---------- ④ 逐字文案 / 语言键 / 占位 ----------
    ("P09 zh 里的一段逐字文案被改动", [
        (ZH, u'"bettergold.handbook.page.merchant_intro_1_left": "易金商人是我们炼金术师们的最大供应商'.encode("utf-8"),
         u'"bettergold.handbook.page.merchant_intro_1_left": "X易金商人是我们炼金术师们的最大供应商'.encode("utf-8"))],
     "bgbook9-texts-verbatim"),
    ("P10 en 缺一个 §九 语言键（键名被改）", [
        (EN, b'"bettergold.handbook.entry.merchant_gift_box"',
         b'"bettergold.handbook.entry.merchant_gift_boxX"')],
     "bgbook9-lang-bilingual"),
    ("P11 空引号那处被填成自编章节名（占位被覆盖）", [
        (ZH, u"「〔待补〕」".encode("utf-8"), u"「古董器具」".encode("utf-8"))],
     "bgbook9-todo-placeholder"),
    ("P12 冻结快照里的作者原文被改动（逐字文案的期望值来源）", [
        (SNAP, u"不会在该礼品盒内开出锻造模板".encode("utf-8"), b"", "all")],
     "bgbook9-texts-verbatim"),
    # ---------- ⑤ 生成器 / 作废条目 ----------
    ("P13 生成器的六件器具顺序被换", [
        (GEN, b'ANTIQUE_TRUE_ORDER = ["sword", "axe", "pickaxe"',
         b'ANTIQUE_TRUE_ORDER = ["sword", "pickaxe", "axe"')],
     "bgbook9-generator"),
    ("P14 §九 作废的旧占位又回到产物里", [
        (ENT + "/merchant.json", None,
         b'{"name": "bettergold.handbook.entry.merchant", '
         b'"category": "bettergold:merchant_antiques", "icon": "bettergold:gold_exchange_counter", '
         b'"sortnum": 0, "pages": []}', "create")],
     "bgbook9-old-placeholders-gone"),
    # ---------- ⑥ §9.7 代码侧 ----------
    ("P15 §9.7 的例外守卫被反转（!conversionExempt -> conversionExempt）", [
        (MEV, b"if (!conversionExempt) {", b"if (conversionExempt) {")],
     "bgbook9-dust-convert-exempt"),
    ("P16 §9.7 的例外集合改成写死方块名（不再走家族索引）", [
        (MEV, b"|| com.hjmmd_8.bettergold.material.MetalFamily.of(state.getBlock()) != null;",
         b'|| state.getBlock().toString().contains("_bricks");')],
     "bgbook9-dust-convert-exempt"),
    ("P17 §9.7 把「尘埃照掉」那一行删掉", [
        (MEV, b"            dropItem(level, event.getPos().getX() + 0.5D, "
              b"event.getPos().getY() + 0.5D, event.getPos().getZ() + 0.5D,\n"
              b"                    new ItemStack(AllItems.NETHERITE_DUST.get(), count));\n",
         b"")],
     "bgbook9-dust-extra-drop"),
    # ---------- ⑦ 文档口径 ----------
    ("P18 文档里的门禁口径句被改（不就地转换 -> 就地转换）", [
        (DOC, u"不就地转换".encode("utf-8"), u"就地转换".encode("utf-8"), "all")],
     "bgbook9-doc"),
    # ---------- ⑧ 被退回的那版改写不许回到快照正文（现行值必须是作者原文） ----------
    ("P20 把被退回的改写塞回快照正文", [
        (SNAP, u"（不过**不会在该礼品盒内开出锻造模板**，且**不联通第三方模组所塞入以下遗迹战利品表的物品**）".encode("utf-8"),
         u"（不过**并不能保证避开锻造模板**，**第三方模组塞进那些表的物品同样可能开出**）".encode("utf-8"))],
     "bgbook9-texts-verbatim"),
    # ---------- ⑨ 反向对照：只加注释必须仍绿 ----------
    ("P19 REVERSE CONTROL: 只加注释（必须仍绿）", [
        # Java：注释里写出被禁的旧形状 —— 判据必须跑在**去注释后**的源码上。
        #   ⚠ 注释里**不许**出现 `/*` 组合（那会喂坏关卡自己的 strip_comments）
        (MEV, b"    private static boolean isDustConversionExempt(",
         b"    // PERTURB comment: event.getDrops().clear(); if (!conversionExempt) { "
         b"_bricks MetalFamily.of(state.getBlock()) != null\n"
         b"    private static boolean isDustConversionExempt("),
        # 生成器：注释里写出被禁的字面量
        (GEN, b"MERCHANT_CATEGORY = ",
         b"# PERTURB comment: isDustConversionExempt \xe4\xb8\x8d\xe5\x9c\xa8\xe8\xbf\x99\xe9\x87\x8c\n"
         b"MERCHANT_CATEGORY = "),
        # 快照：注释性补充（草稿里的旧口径不该被当成"正文里的旧口径"）
        (SNAP, b"## \xe5\xbf\xab\xe7\x85\xa7\xe6\x90\xac\xe8\xbf\x90\xe8\xae\xb0\xe5\xbd\x95",
         b"## \xe5\xbf\xab\xe7\x85\xa7\xe6\x90\xac\xe8\xbf\x90\xe8\xae\xb0\xe5\xbd\x95 PERTURB-comment"),
        # 文档：注释性补充（正向 needle 不受影响、负向判据也不该被它喂饱）
        (DOC, b"## 21.13 ", b"## 21.13 PERTURB-comment "),
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
            if old is None:                      # 删除文件
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
    lines.append("%-56s %-11s %s" % (n, status, detail))

rc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                    stdout=open(RAW_LOG, "wb"), stderr=subprocess.STDOUT).returncode
lines.append("BASELINE-2 exit=%d (expect 0) -> %s" % (rc, "OK" if rc == 0 else "MISMATCH"))
mismatches += 0 if rc == 0 else 1

lines.append("")
lines.append("cases=%d mismatches=%d" % (len(CASES) + 2, mismatches))
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
sys.exit(1 if mismatches else 0)
