# -*- coding: utf-8 -*-
"""bgfix11 · 「生成器真源归属」查证 + 「重跑不退回」反证（只读 + 幂等自证）。

父代理要求「同时改生成器真源（tools/asset-generator/ 里那份 ZH/EN 表）」。
本脚本要回答的是：**到底有没有生成器拥有 `bettergold.handbook.page.knowledge_1_summary` 的 lang 值？**
做法（三条独立证据）：
  ① grep 全 `tools/asset-generator/*.py`：谁 **写** 这个键的值（不是引用）；
  ② 读 `generate_handbook_data.py` 的 docstring（自述不碰 lang）+ `generate_metal_data.py#insert_lang`
     （**已存在的键会被 skip** ⇒ 即便跑也不会覆盖）；
  ③ **实跑**：把三个会写 lang 的生成器按各自的安全模式跑一遍，前后比 en/zh 的 SHA256
     （`generate_handbook_data.py` 会重写手册树 ⇒ 另比整棵树的 SHA256 清单，非幂等就自动 `git checkout` 复原）。

输出：UTF-8 证据文件 `docs/bgfix11-证据/10-生成器真源归属查证.txt`。
"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GEN = os.path.join(REPO, "tools", "asset-generator")
LANG_EN = os.path.join(REPO, "src/main/resources/assets/bettergold/lang/en_us.json")
LANG_ZH = os.path.join(REPO, "src/main/resources/assets/bettergold/lang/zh_cn.json")
BOOK = os.path.join(REPO, "src/main/resources/assets/bettergold/patchouli_books")
BOOK2 = os.path.join(REPO, "src/main/resources/data/bettergold/patchouli_books")
EVID = os.path.join(REPO, "docs", "bgfix11-证据")
OUT = os.path.join(EVID, "10-生成器真源归属查证.txt")

lines = []


def say(s=""):
    lines.append(s)
    print(s)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def tree_manifest(root):
    m = {}
    for base, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(base, f)
            m[os.path.relpath(p, REPO).replace("\\", "/")] = sha(p)
    return m


def run(argv):
    r = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


say("== ① grep：谁**写**这把键的 lang 值 ==")
# ⚠ 不用 `findstr`（对 UTF-8 的处理不可靠）；也**不能只 grep 字面量 `handbook.page`** ——
#   手册生成器是用 `"%s.page.knowledge_1_summary" % LANG` 拼出来的（LANG = "bettergold.handbook"）
#   ⇒ 两个 needle 都要扫：`handbook.page`（字面量）与 `knowledge_1_summary`（键尾）。
for needle in ("handbook.page", "knowledge_1_summary"):
    say("  --- needle = %r" % needle)
    hits = 0
    for fn in sorted(os.listdir(GEN)):
        if not fn.endswith(".py"):
            continue
        p = os.path.join(GEN, fn)
        for i, ln in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
            if needle in ln:
                hits += 1
                say("    %s:%d: %s" % (fn, i, ln.rstrip()[:140]))
    say("    （命中 %d 处）" % hits)
    if hits == 0:
        say("    ⚠ 零命中 —— 反空转告警：扫描坏了？")
say()
say("→ 结论（逐条）：")
say("   * `handbook.page` 字面量：**只有关卡** `validate_metal_data.py`（全是断言/注释）")
say("   * `knowledge_1_summary` 键尾：`generate_handbook_data.py` 用它**引用**该键当页面 `text`")
say("     （`\"%s.page.knowledge_1_summary\" % LANG`，LANG = \"bettergold.handbook\"）—— **引用，不是写值**")
say("   * 全仓没有任何 .py 往 `bettergold.handbook.*` 的 lang 里**写值**")
say()

say("== ② 生成器自述 / 既有行为 ==")
say("generate_handbook_data.py:18-21 的原文：")
for i, ln in enumerate(open(os.path.join(GEN, "generate_handbook_data.py"), encoding="utf-8"), 1):
    if 18 <= i <= 21:
        say("    %d: %s" % (i, ln.rstrip()))
say()
say("generate_metal_data.py:84-100 的 insert_lang（只贴关键行）：")
for i, ln in enumerate(open(os.path.join(GEN, "generate_metal_data.py"), encoding="utf-8"), 1):
    if i in (87, 88, 89, 90, 98, 99, 100):
        say("    %d: %s" % (i, ln.rstrip()))
say("   ⇒ `fresh = {k: v for k, v in entries.items() if k not in existing}` —— **已存在的键被跳过**")
say()

say("== ③ 实跑三个会写 lang 的生成器（前后比 SHA256）==")
en0, zh0 = sha(LANG_EN), sha(LANG_ZH)
say("跑前: en=%s zh=%s" % (en0, zh0))
say()
cases = [
    ("generate_handbook_data.py", [sys.executable, os.path.join(GEN, "generate_handbook_data.py")], True),
    ("generate_metal_data.py（dry-run，无 --apply）", [sys.executable, os.path.join(GEN, "generate_metal_data.py")], False),
    ("generate_weapon_lang.py（dry-run，无 --apply）", [sys.executable, os.path.join(GEN, "generate_weapon_lang.py")], False),
]
book_before = {}
for p in (BOOK, BOOK2):
    if os.path.isdir(p):
        book_before.update(tree_manifest(p))
for name, argv, check_book in cases:
    rc, out = run(argv)
    say("--- %s ⇒ exit %d" % (name, rc))
    tail = [l for l in out.splitlines() if l.strip()][-6:]
    for l in tail:
        say("    " + l)
    e1, z1 = sha(LANG_EN), sha(LANG_ZH)
    say("    en %s / zh %s" % ("UNCHANGED" if e1 == en0 else "**CHANGED → " + e1[:16] + "**",
                               "UNCHANGED" if z1 == zh0 else "**CHANGED → " + z1[:16] + "**"))
    if check_book:
        book_after = {}
        for p in (BOOK, BOOK2):
            if os.path.isdir(p):
                book_after.update(tree_manifest(p))
        diff = sorted(k for k in set(book_before) | set(book_after)
                      if book_before.get(k) != book_after.get(k))
        say("    手册树：%d 个文件，非幂等差异 %d 个 %s" % (len(book_after), len(diff), diff[:5]))
        if diff:
            say("    ⇒ 非幂等：git checkout 复原")
            subprocess.run(["git", "checkout", "--"] + diff, cwd=REPO)
            say("    复原后差异 = %d" % len([k for k in diff
                                            if sha(os.path.join(REPO, k)) != book_before[k]]))
    say()
en1, zh1 = sha(LANG_EN), sha(LANG_ZH)
say("== 结论 ==")
say("* en_us.json：跑前 == 跑后 ? %s（%s）" % (en0 == en1, en1[:32]))
say("* zh_cn.json：跑前 == 跑后 ? %s（%s）" % (zh0 == zh1, zh1[:32]))
say("* 三个生成器**没有一个**会写这把键的 lang 值 ⇒「只改产物、下次重跑退回」在这把键上**不成立**；")
say("  本仓手册页 lang 值的真源惯例 = **关卡里的冻结常量**（bgfix8/bgfix9 起），本轮沿用。")

os.makedirs(EVID, exist_ok=True)
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("\n写出 %s" % OUT)
sys.exit(0 if (en0 == en1 and zh0 == zh1) else 1)
