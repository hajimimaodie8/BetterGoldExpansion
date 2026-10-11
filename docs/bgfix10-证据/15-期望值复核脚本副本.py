# -*- coding: utf-8 -*-
"""bgfix10 · 复核 3 处期望值来源的补丁（索引口径与 validate_metal_data.py 逐字一致）。"""
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
EN = os.path.join(LANG, "en_us.json")
MANIFEST = os.path.join(REPO, "tools", "asset-generator", "advancement_manifest.json")

ZH_NEW_SHA = "695FA5A5347E1165F431A204D8CA6F1965D9D136DA0F4D560F299E8B3C972810"
EN_AFTER_SHA = "7A7156E8D83C03BE9916D10A78AA8951FEF66F69F760AFADA2DB16E5433F1E57"

zh_new = json.loads(open(ZH, "rb").read().decode("utf-8"))
zh_old = json.loads(open(os.path.join(HERE, "zh_head.json"), "rb").read().decode("utf-8"))
LOG = []


def say(s):
    LOG.append(s)
    print(s)


def read(p):
    return open(p, "rb").read().decode("utf-8")


ok = True


def chk(c, tag, msg):
    global ok
    say(("PASS " if c else "FAIL ") + tag + " :: " + msg)
    if not c:
        ok = False


def cells(line):
    """与 validate_metal_data.py 同款：`[c for c in line.split('|')][1:-1]`"""
    return [c for c in line.split("|")][1:-1]


def clean6(c):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", c).strip()


def prose9(c):
    c = c.split(u"<br>⚠")[0]
    b = re.sub(r"\*\*(.+?)\*\*", r"\1", c).strip()
    if b.startswith(u"（"):
        cut = b.find(u"）")
        if cut >= 0:
            b = b[cut + 1:].strip()
    return b


# ---- §6 ----
t6 = read(os.path.join(SNAP, "bg-book-6.1-6.3.md"))
L4 = [ln for ln in t6.split("\n") if ln.startswith("| **4** | **闪耀藤条** |")]
chk(len(L4) == 1, "snap6-row-unique", "§6.2 第 4 行唯一命中（%d 行）" % len(L4))
if L4:
    got = clean6(cells(L4[0])[2])
    chk(got == zh_new["bettergold.handbook.page.core_4"], "snap6-parsed",
        "解析净文本 == 作者新 zh 值（%d 字）" % len(got))
chk(zh_old["bettergold.handbook.page.core_4"] in t6, "snap6-old-kept", "§6：旧文案原文仍在（搬运记录里）")
chk(u"2026-10-11（bgfix10）" in t6, "snap6-log", "§6：搬运记录 +1 行")
chk("\ufeff" not in t6 and "\r" not in t6, "snap6-clean", "§6：UTF-8 无 BOM / LF")

# ---- §9 ----
t9 = read(os.path.join(SNAP, "bg-book-9.md"))
LL = [ln for ln in t9.split("\n") if ln.startswith("| 2 左 |") and u"珍品古董盒" in ln]
LR = [ln for ln in t9.split("\n") if ln.startswith("| 2 右 |") and u"没用的老古董可以作为" in ln]
chk(len(LL) == 1, "snap9-row-left", "2 左 唯一命中（%d）" % len(LL))
chk(len(LR) == 1, "snap9-row-right", "2 右 唯一命中（%d）" % len(LR))
if LL:
    chk(prose9(cells(LL[0])[1]) == zh_new["bettergold.handbook.page.merchant_gift_box_2_left"],
        "snap9-parsed-left", "2 左 解析净文本 == 作者新 zh 值")
if LR:
    chk(prose9(cells(LR[0])[1]) == zh_new["bettergold.handbook.page.merchant_gift_box_2_right"],
        "snap9-parsed-right", "2 右 解析净文本 == 作者新 zh 值")
chk(u"（中上边放：没用的老古董）" in t9, "snap9-label-new", "2 右 的「中上边放」标签已换新名")
chk(zh_old["bettergold.handbook.page.merchant_gift_box_2_left"] in t9
    and zh_old["bettergold.handbook.page.merchant_gift_box_2_right"] in t9, "snap9-old-kept",
    "§9：两段旧文案原文仍在（搬运记录里）")
chk(u"<br>⚠ **引号里是空的** ⇒ 见 §9.5" in t9, "snap9-note", "§9 的空引号批注仍在")
chk(u"2026-10-11（bgfix10）" in t9, "snap9-log", "§9：搬运记录 +1 行")
chk("\ufeff" not in t9 and "\r" not in t9, "snap9-clean", "§9：UTF-8 无 BOM / LF")

# ---- manifest ----
m = json.loads(read(MANIFEST))
man = {a["key"]: a for a in m["advancements"]}
e = man["echogold_weapon"]
chk(e["title"] == zh_new["advancements.bettergold.echogold_weapon.title"], "manifest-title",
    "title == 作者新 zh 值 %r" % e["title"])
chk(e.get("_bgfix10_old_title") == zh_old["advancements.bettergold.echogold_weapon.title"],
    "manifest-old-kept", "旧期望原文以 `_bgfix10_old_title` 留档（JSON 无注释语法）")

# ---- 产物未被动 / zh 未被动 ----
chk(hashlib.sha256(open(ZH, "rb").read()).hexdigest().upper() == ZH_NEW_SHA, "zh-untouched",
    "zh_cn.json 仍是作者那一份（字节未动）")
chk(hashlib.sha256(open(EN, "rb").read()).hexdigest().upper() == EN_AFTER_SHA, "en-stable",
    "en_us.json 仍是 apply_en.py 的产物（本脚本没碰它）")
say("RESULT %s" % ("ALL-PASS" if ok else "HAS-FAIL"))
open(os.path.join(HERE, "verify_expectations.report.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(LOG) + "\n")
sys.exit(0 if ok else 1)
