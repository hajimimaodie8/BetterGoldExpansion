# -*- coding: utf-8 -*-
"""bgfix8 关卡扰动矩阵（可重跑）。

契约（`docs/构建与跑测注意事项.md` §七 + `ex/03` §3.11/§3.19）：
  * 每条用例都打印 **exit** 与 **hit_expected** 两列；
  * 目标串在目标文件里必须**恰好出现 1 次**（`occ == 1`），否则判 **SETUP-FAIL**（"用例失效"，不算命中）；
  * 「改坏 ⇒ 期望 id 命中」/「前置缺失 ⇒ exit 2」/「只改注释 ⇒ 仍绿」三类分开记；
  * 每个被改文件**逐字节复原**并核对 SHA256（先写回原字节，再比哈希）。
"""
import hashlib
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
VAL = os.path.join(REPO, "tools", "asset-generator", "validate_metal_data.py")
CFG = os.path.join(REPO, "src", "main", "java", "com", "hjmmd_8", "bettergold", "config",
                   "Config.java")
ZH = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang", "zh_cn.json")
EN = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang", "en_us.json")
SNAP = os.path.join(REPO, "tools", "asset-generator", "bgappend-requirements-snapshot",
                    "bg-book-6.1-6.3.md")
PZH = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "patchouli_books",
                   "alchemy_handbook", "zh_cn", "entries", "golden_knowledge.json")
SPEC = os.path.join(REPO, "docs", "1.6-\u89c4\u683c.md")

FILES = {}


def load():
    for p in (CFG, ZH, EN, SNAP, PZH, SPEC):
        with open(p, "rb") as fh:
            FILES[p] = fh.read()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def run_validator():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, VAL], capture_output=True, env=env, cwd=REPO)
    out = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    return r.returncode, out


def write_text(p, text):
    with open(p, "wb") as fh:
        fh.write(text.encode("utf-8"))


def restore():
    for p, b in FILES.items():
        with open(p, "wb") as fh:
            fh.write(b)


CASES = []


def case(cid, path, old, new, expect_exit, expect_ids, note="", mode="one"):
    CASES.append((cid, path, old, new, expect_exit, expect_ids, note, mode))


# ---------------- 改坏类（exit 1 + 期望 id 命中） ----------------
case("P01", ZH, u'"bettergold.configuration.flamegoldWeaponBuffChance": "烈燃金·武器工具盾牌触发Buff概率"',
     u'"bettergold.configuration.flamegoldWeaponBuffChance": "烈燃金 · 武器工具触发 Buff 概率"',
     1, ["bgfix8-config-label-zh"], u"zh 条目名退回旧字面")
case("P02", EN, u'"bettergold.configuration.flamegoldWeaponBuffChance": "Flamegold - Weapon/Tool/Shield Buff Chance"',
     u'"bettergold.configuration.flamegoldWeaponBuffChance": "Flamegold - Weapon/Tool Buff Chance"',
     1, ["bgfix8-config-label-en"], u"en 条目名退回旧字面")
case("P03", ZH, u'"bettergold.configuration.flamegoldArmorBuffChance": "烈燃金·盔甲触发buff概率"',
     u'"bettergold.configuration.flamegoldArmorBuffChance": "烈燃金·盔甲盾牌触发buff概率"',
     1, ["bgfix8-config-label-zh"], u"把「盾牌」塞回盔甲侧（语义回退）")
case("P04", CFG, u'.comment("万坚金【武器工具】触发能力（爆金：命中必定掉落一件金系物品）的概率。"',
     u'.comment("万坚金·武器工具盾牌触发Buff概率"',
     1, ["bgfix8-config-sturdygold-untouched"], u"顺手改了万坚金那条（作者明说除外）")
case("P05", CFG, u'.comment("烈燃金·武器工具盾牌触发Buff概率"',
     u'.comment("烈燃金【武器工具】触发 Buff（高燃）的概率。"',
     1, ["bgfix8-config-comment-zh", "bgfix8-config-comment-old-gone"], u"Config.java 提示行退回旧措辞")
case("P06", CFG, u'.defineInRange("illusiongoldArmorBuffChance", 0.04D, 0.0D, 1.0D)',
     u'.defineInRange("illusiongoldArmorBuffChance", 0.05D, 0.0D, 1.0D)',
     1, ["bgfix-config-defaults"], u"改默认值（既有负向断言必须红）")
case("P07", CFG, u'.defineInRange("flamegoldWeaponBuffChance", 1.0D, 0.0D, 1.0D)',
     u'.defineInRange("flamegoldWeaponBuffChance", 1.0D, 0.0D, 2.0D)',
     1, ["bgfix8-config-keys-frozen"], u"改取值范围（本轮新钉）")
case("P08", PZH, u'      "text": "bettergold.handbook.page.knowledge_1_right",\n', u'',
     1, ["bgfix8-book-right-text", "bgfix4-k3p1-restored"], u"删掉右页正文")
case("P09", PZH, u'      "title": "\\"贵金\\"装备的升级锻造模版"\n', u'      "title": ""\n',
     1, ["bgfix8-book-right-title", "bgfix4-k3p1-restored"],
     u"右页 title 置空（合法 JSON 但语义相反：Patchouli 会退化成物品名）")
case("P10", ZH, u'"bettergold.handbook.page.knowledge_1_right": "当然\\"贵金\\"也可以用于制作功能性强大的武装使用',
     u'"bettergold.handbook.page.knowledge_1_right": "本句是扰动用例自编的文字，用来打中逐字比对：当然\\"贵金\\"也可以用于制作功能性强大的武装使用',
     1, ["bgfix8-book-right-text", "bgfix8-book-right-text-source", "bgbook2-texts-verbatim"],
     u"右页正文换成自编文字（两条独立来源都该红）")
case("P11", SNAP, u'（随排版顺序变化）<br>当然"贵金"也可以用于制作功能性强大的武装使用',
     u'（随排版顺序变化）',
     1, ["bgfix8-book-right-text", "bgbook2-texts-verbatim"], u"冻结快照里删掉那一段（期望值来源缺失）")
case("P12", SNAP, u'图标：**"贵金"装备的升级锻造模版**', u'图标：**某段扰动字幕**',
     1, ["bgfix8-book-right-title", "bgfix4-k3p1-restored"], u"冻结快照里的字幕被改")
case("P13", PZH, u'      "text": "bettergold.handbook.page.knowledge_1_right",',
     u'      "text": "bettergold.handbook.page.knowledge_1_summary",',
     1, ["bgfix8-book-right-text"], u"右页正文换成左页那句（等于没加）")
case("P14", PZH, u'      "text": "bettergold.handbook.page.knowledge_1_right",',
     u'      "text": "bettergold.handbook.page.knowledge_1_left",',
     1, ["bgappend-book-k3-old-text-gone"], u"右页去引用仍被禁的 knowledge_1_left")
case("P15", SPEC, u"武器工具盾牌触发Buff概率", u"武器工具触发Buff概率",
     1, ["bgfix8-doc"], u"把规格里那条 needle 全部改掉（＝文档侧没落档）", mode="all")

# ---------------- 反向对照（必须仍绿 exit 0） ----------------
case("P16", CFG, u"    // ==================== bgfix8（作者 2026-10-09）",
     u"    // 【盔甲盾牌】反制 Buff（   ← 扰动反向对照：注释里写旧措辞**不许**影响判据\n"
     u"    // 烈燃金·武器工具盾牌触发Buff概率  ← 注释里重复新字面也不许影响判据\n"
     u"    // ==================== bgfix8（作者 2026-10-09）",
     0, [], u"只在注释里写旧措辞 / 重复新字面 ⇒ 必须仍绿（正向与负向 needle 都跑在去注释源码上）")
case("P17", ZH, u'"bettergold.configuration.voodoogoldArmorBuffChance": "巫毒金·盔甲触发buff概率",',
     u'"bettergold.configuration.voodoogoldArmorBuffChance": "巫毒金·盔甲触发buff概率",\n'
     u'  "bettergold.configuration.__perturb_extra__": "扰动用多余键（判据不看它）",',
     0, [], u"只往语言文件里加一个判据不看的键 ⇒ 必须仍绿")

# ---------------- 前置缺失（必须 exit 2，不是"命中"） ----------------
case("P18", SNAP, u"__RENAME__", u"", 2, ["bgfix8-anti-vacuum"],
     u"把冻结快照改名搬走（前置缺失 ⇒ 基线被破坏 ⇒ exit 2）", mode="rename")

SETUP_FAILS = []
RESULTS = []
load()
before = {p: sha(p) for p in FILES}

# 基线
rc, out = run_validator()
print("BASELINE exit=%d  (期望 0)" % rc)
print("  hit_none_expected =", "OK" if rc == 0 else "MISMATCH")
RESULTS.append(("BASELINE", 0, rc, [], []))

for cid, path, old, new, want_exit, want_ids, note, mode in CASES:
    restore()
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    if mode == "rename":
        os.replace(path, path + ".perturb-bak")
    else:
        occ = text.count(old)
        if mode == "one" and occ != 1:
            SETUP_FAILS.append((cid, "occ=%d" % occ, note))
            print("%s SETUP-FAIL occ=%d  (%s)" % (cid, occ, note))
            continue
        if occ < 1:
            SETUP_FAILS.append((cid, "occ=0", note))
            print("%s SETUP-FAIL occ=0  (%s)" % (cid, note))
            continue
        write_text(path, text.replace(old, new) if mode == "all" else text.replace(old, new, 1))
    try:
        rc, out = run_validator()
    finally:
        if mode == "rename" and os.path.exists(path + ".perturb-bak"):
            os.replace(path + ".perturb-bak", path)
    hit = sorted(set(i for i in want_ids if ("[%s]" % i) in out))
    hit_expected = (rc == want_exit) and (hit == sorted(set(want_ids)))
    RESULTS.append((cid, want_exit, rc, sorted(set(want_ids)), hit))
    print("%s exit=%d (want %d)  hit_expected=%s  hit=%s  %s"
          % (cid, rc, want_exit, hit_expected, hit, note))

restore()
# 逐字节复原自证
bad = [p for p in FILES if sha(p) != before[p]]
print("RESTORE identical:", not bad, ("mismatch=%s" % bad) if bad else "")
print("SETUP_FAILS = %d" % len(SETUP_FAILS))
mismatch = [r for r in RESULTS
            if r[0] != "BASELINE" and not (r[2] == r[1] and sorted(set(r[3])) == r[4])]
print("mismatches = %d  %s" % (len(mismatch), mismatch))
print("cases run = %d / %d" % (len(RESULTS) - 1, len(CASES)))
