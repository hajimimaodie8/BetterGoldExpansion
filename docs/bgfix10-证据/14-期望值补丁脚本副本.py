# -*- coding: utf-8 -*-
"""bgfix10 · 同步 3 处「期望值来源」（快照 ×2 + 成就 manifest）。

作者 2026-10-11 替换 zh_cn.json 之后，基线有 7 条断言变红 —— 全部是"期望值来源还没跟上新 zh"。
本脚本只改期望值来源，**不改产物**（en_us.json 已由 apply_en.py 改完），
且**旧期望原文一律留档**（快照写成《快照搬运记录》里的一行；manifest 写成 `_bgfix10_old_title`）。
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LANG = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")
SNAP = os.path.join(REPO, "tools", "asset-generator", "bgappend-requirements-snapshot")
ZH = os.path.join(LANG, "zh_cn.json")
MANIFEST = os.path.join(REPO, "tools", "asset-generator", "advancement_manifest.json")

ZH_NEW_SHA = "695FA5A5347E1165F431A204D8CA6F1965D9D136DA0F4D560F299E8B3C972810"
ZH_OLD_SHA = "3FBB113E9FD23FDBD43A1191C0166145392D4038533BEABDE1B4F6B0101B48B4"

zh_new = json.loads(open(ZH, "rb").read().decode("utf-8"))
zh_old = json.loads(open(os.path.join(HERE, "zh_head.json"), "rb").read().decode("utf-8"))

LOG = []


def say(s):
    LOG.append(s)
    print(s)


def read(p):
    return open(p, "rb").read().decode("utf-8")


def write(p, t):
    open(p, "wb").write(t.encode("utf-8"))


def sub_once(text, old, new, tag):
    n = text.count(old)
    if n != 1:
        raise SystemExit("SETUP-FAIL %s 的旧串在文件里出现 %d 次（必须恰好 1 次）" % (tag, n))
    say("  replace %-42s %d 处" % (tag, n))
    return text.replace(old, new)


# ---------------- ① §6 冻结快照：core_4 ----------------
CORE4 = "bettergold.handbook.page.core_4"
p6 = os.path.join(SNAP, "bg-book-6.1-6.3.md")
t6 = read(p6)
say("① %s" % os.path.relpath(p6, REPO))
t6 = sub_once(t6, zh_old[CORE4], zh_new[CORE4], "core_4 正文")
ROW6 = ("| 2026-10-11（bgfix10） | **作者替换后的 zh_cn.json**（SHA256 `%s`，= 工作区现值；"
        "对照 HEAD 的 `%s`） | §6.2 第 **4** 行（`%s`，闪耀藤条那段）**就地更新**为作者新文案"
        "（键名不动、只有值变） | 作者 2026-10-11 直接替换了 zh 文件 ⇒ 逐字文案的期望值必须跟着走，"
        "否则 `[bgbook2-texts-verbatim]` 当场红（实测红过）。<br>⚠ **旧文案原文留档（不删）**："
        "`%s` |" % (ZH_NEW_SHA, ZH_OLD_SHA, CORE4, zh_old[CORE4]))
if "2026-10-11（bgfix10）" in t6:
    raise SystemExit("SETUP-FAIL §6 快照里已有 bgfix10 的搬运记录行")
t6 = t6.rstrip("\n") + "\n" + ROW6 + "\n"
write(p6, t6)
say("  搬运记录 +1 行")

# ---------------- ② §9 冻结快照：merchant_gift_box_2 左右两格 ----------------
# ⚠ 快照那两格里夹着 `**…**` 强调标记（`_clean()` 会先剥掉再比对），
#   所以**不能**拿整段 zh 值去做字符串替换 —— 改成只换「物品名」这 3 处
#   （2 右 的「中上边放」标签 1 处 + 2 左 正文 1 处 + 2 右 正文 1 处），
#   改完之后剥掉 `**` 的净文本正好等于作者的新 zh 值（下面有断言）。
p9 = os.path.join(SNAP, "bg-book-9.md")
t9 = read(p9)
say("② %s" % os.path.relpath(p9, REPO))
OLD_NAME = zh_old["item.bettergold.unwanted_antique"]
NEW_NAME = zh_new["item.bettergold.unwanted_antique"]
L2L = "bettergold.handbook.page.merchant_gift_box_2_left"
L2R = "bettergold.handbook.page.merchant_gift_box_2_right"
say("  物品名 %r → %r，全文命中 %d 处（应恰好 3）" % (OLD_NAME, NEW_NAME, t9.count(OLD_NAME)))
if t9.count(OLD_NAME) != 3:
    raise SystemExit("SETUP-FAIL §9 里旧物品名的出现次数不是 3")
t9 = t9.replace(OLD_NAME, NEW_NAME)
say("  replace %-42s %d 处" % (u"物品名（标签 1 + 正文 2）", 3))
ROW9 = ("| 2026-10-11（bgfix10） | **作者替换后的 zh_cn.json**（SHA256 `%s`；对照 HEAD 的 `%s`） | "
        "§9.3 章节 2 的 **2 左 / 2 右** 两格：`%s` → `%s`（含 2 右的「中上边放」标签；"
        "**键名与页结构不动**，只换物品名） | 同上（作者直接换文件 ⇒ 逐字文案期望值跟着走，"
        "否则 `[bgbook9-texts-verbatim]` 红，实测红过）。<br>⚠ **旧文案原文留档（不删）**："
        "2 左 = `%s`；2 右 = `%s` |" % (ZH_NEW_SHA, ZH_OLD_SHA, OLD_NAME, NEW_NAME,
                                        zh_old[L2L], zh_old[L2R]))
if "2026-10-11（bgfix10）" in t9:
    raise SystemExit("SETUP-FAIL §9 快照里已有 bgfix10 的搬运记录行")
t9 = t9.rstrip("\n") + "\n" + ROW9 + "\n"
write(p9, t9)
say("  搬运记录 +1 行")

# ---------------- ③ 成就 manifest：echogold_weapon.title ----------------
p3 = MANIFEST
t3 = read(p3)
say("③ %s" % os.path.relpath(p3, REPO))
OLD_T = zh_old["advancements.bettergold.echogold_weapon.title"]
NEW_T = zh_new["advancements.bettergold.echogold_weapon.title"]
snippet_old = "      \"title\": %s,\n" % json.dumps(OLD_T, ensure_ascii=False)
snippet_new = ("      \"_bgfix10_old_title\": %s,\n      \"title\": %s,\n"
               % (json.dumps(OLD_T, ensure_ascii=False), json.dumps(NEW_T, ensure_ascii=False)))
t3 = sub_once(t3, snippet_old, snippet_new, "echogold_weapon.title")
write(p3, t3)
m = json.loads(read(p3))
say("  manifest 条目数 %d，title 现值 %r" % (len(m["advancements"]), NEW_T))

# ---------------- 校验 ----------------
say("")
say("== 写后自证 ==")
ok = True


def chk(c, tag, msg):
    global ok
    say(("PASS " if c else "FAIL ") + tag + " :: " + msg)
    if not c:
        ok = False


t6b, t9b = read(p6), read(p9)


def _cell(line, idx):
    return line.split("|")[idx]


def _clean9(c):
    c = c.split(u"<br>⚠")[0]
    return re.sub(r"\*\*(.+?)\*\*", r"\1", c).strip()


def _prose9(c):
    b = _clean9(c)
    if b.startswith(u"（"):
        cut = b.find(u"）")
        if cut >= 0:
            b = b[cut + 1:].strip()
    return b


def _prose6(c):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", c).strip()


_line6 = [ln for ln in t6b.split("\n") if ln.startswith("| **4** | **闪耀藤条** |")]
chk(len(_line6) == 1, "snap6-row", "§6.2 第 4 行唯一命中（%d 行）" % len(_line6))
chk(bool(_line6) and _prose6(_cell(_line6[0], 2)) == zh_new[CORE4], "snap6-parsed",
    "解析后的净文本 == 作者的新 zh 值")
_line_l = [ln for ln in t9b.split("\n") if u"珍品古董盒" in ln]
_line_r = [ln for ln in t9b.split("\n") if u"没用的老古董可以作为" in ln]
chk(len(_line_l) == 1 and _prose9(_cell(_line_l[0], 2)) == zh_new[L2L], "snap9-parsed-left",
    "2 左：解析后的净文本 == 作者的新 zh 值")
chk(len(_line_r) == 1 and _prose9(_cell(_line_r[0], 2)) == zh_new[L2R], "snap9-parsed-right",
    "2 右：解析后的净文本 == 作者的新 zh 值（`<br>⚠` 批注仍在）")
chk(u"<br>⚠ **引号里是空的** ⇒ 见 §9.5" in t9b, "snap9-note", "§9 的旧批注（空引号 ⇒ 见 §9.5）仍在")
chk("\ufeff" not in t6b and "\r" not in t6b, "snap6-clean", "§6 快照 UTF-8 无 BOM / LF")
chk("\ufeff" not in t9b and "\r" not in t9b, "snap9-clean", "§9 快照 UTF-8 无 BOM / LF")
chk(zh_new[CORE4] in t6b and zh_old[CORE4] in t6b, "snap6-both", "§6：新文案在表里、旧文案在搬运记录里")
chk(zh_new[L2L] in t9b and zh_new[L2R] in t9b, "snap9-new", "§9：新文案两格都在")
chk(zh_old[L2L] in t9b and zh_old[L2R] in t9b, "snap9-old", "§9：旧文案留档在搬运记录里")
chk(OLD_NAME not in t9b.split("## 快照搬运记录")[0], "snap9-label", "§9 正文区已无旧名（正文区 = 搬运记录之前）")
chk(os.path.isfile(ZH) and hashlib.sha256(open(ZH, "rb").read()).hexdigest().upper() == ZH_NEW_SHA,
    "zh-untouched", "zh_cn.json 仍是作者那一份（字节未动）")
say("RESULT %s" % ("ALL-PASS" if ok else "HAS-FAIL"))

open(os.path.join(HERE, "patch_expectations.report.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(LOG) + "\n")
sys.exit(0 if ok else 1)
