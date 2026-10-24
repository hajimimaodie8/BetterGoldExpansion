# -*- coding: utf-8 -*-
"""bgbig D 段：用作者的 zh_cn.json 替换项目语言文件（**只换这一个文件**；en 同步键集）。

跑法（工作区自带 Python）：
    <dsh python> probe\\bgbig\\d_replace.py --check     # 只做校验 / 差异报告（不写盘）
    <dsh python> probe\\bgbig\\d_replace.py --apply     # 留档 → 替换 → 删 en 里的旧键

口径（父代理 D 段指令）：
  1. 作者文件先**逐字节**留档到 `docs\\zh-json-替换证据\\zh_cn.before-replace.json`；
  2. 校验：JSON 合法；键集 ⊇ **HEAD 版** src/zh_cn.json 的全部键（缺的必须**恰好**是本轮删掉的
     旧条目 —— 用 HEAD 作基线，因为 B/C 在这之后又加了本轮新键，作者文件不可能有它们）；
  3. 替换 src 的 zh_cn.json；en_us.json 删掉同一批旧键（键集随后由 inject_lang + advancements
     `--lang` 补齐到一致）；
  4. 报告：键数 / 缺失清单 / 差异值清单 / SHA256。
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang")
ZH = os.path.join(SRC, "zh_cn.json")
EN = os.path.join(SRC, "en_us.json")
AUTHOR = r"E:\mc\mc资料\zh_cn.json"
EVID = os.path.join(ROOT, "docs", "zh-json-替换证据")
ARCHIVE = os.path.join(EVID, "zh_cn.before-replace.json")

# 本轮删掉的旧条目（HEAD 有、作者文件没有；B 的旧四条手册章节 + C 的两条成就）
RETIRED = {
    "advancements.bettergold.chaos_coin.title",
    "advancements.bettergold.chaos_coin.description",
    "advancements.bettergold.chaosalloy_supply.title",
    "advancements.bettergold.chaosalloy_supply.description",
    "bettergold.handbook.entry.chaos_feast",
    "bettergold.handbook.entry.chaos_materials",
    "bettergold.handbook.entry.gear_chaosalloy",
    "bettergold.handbook.entry.gear_chaosgold",
    "bettergold.handbook.page.chaos_feast_1_left",
    "bettergold.handbook.page.chaos_feast_2_left",
    "bettergold.handbook.page.chaos_materials_1_left",
    "bettergold.handbook.page.chaos_materials_2_right",
    "bettergold.handbook.page.chaos_materials_3_left_title",
    "bettergold.handbook.page.chaos_materials_4_left",
    "bettergold.handbook.page.chaos_materials_5_left_title",
    "bettergold.handbook.page.chaos_materials_upstream_smelt",
    "bettergold.handbook.page.chaos_materials_upstream_string",
    "bettergold.handbook.page.gear_chaosalloy_1_left",
    "bettergold.handbook.page.gear_chaosalloy_1_right",
    "bettergold.handbook.page.gear_chaosalloy_2_left",
    "bettergold.handbook.page.gear_chaosgold_1_left",
    "bettergold.handbook.page.gear_chaosgold_1_right",
    "bettergold.handbook.page.gear_chaosgold_2_left",
    "bettergold.handbook.page.gear_chaosgold_3_left_title",
    "bettergold.handbook.page.gear_chaosgold_3_right_title",
    "bettergold.handbook.page.gear_chaosgold_4_left",
}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def head_zh():
    raw = subprocess.check_output(
        ["git", "show", "HEAD:src/main/resources/assets/bettergold/lang/zh_cn.json"], cwd=ROOT)
    return json.loads(raw.decode("utf-8"))


def main():
    apply = "--apply" in sys.argv
    if not os.path.isfile(AUTHOR):
        print("!! 作者文件不存在：", AUTHOR)
        return 2
    with io.open(AUTHOR, encoding="utf-8") as f:
        author = json.load(f)
    head = head_zh()
    cur = json.load(io.open(ZH, encoding="utf-8"))
    en = json.load(io.open(EN, encoding="utf-8"))
    print("author keys =", len(author), "HEAD keys =", len(head), "current zh =", len(cur),
          "en =", len(en))

    missing = sorted(set(head) - set(author))
    extra = sorted(set(author) - set(head))
    print("HEAD -> author: missing", len(missing), "extra", len(extra))
    bad_missing = [k for k in missing if k not in RETIRED]
    print("missing 不是本轮删掉的旧条目：", len(bad_missing), bad_missing[:10])
    print("author 比 HEAD 多出来的键：", len(extra), extra[:10])
    diffs = sorted(k for k in author if k in head and author[k] != head[k])
    print("与 HEAD 值不同的键：", len(diffs))
    for k in diffs:
        print("  DIFF", k)
    print("archive exists?", os.path.isfile(ARCHIVE), "SHA =", sha(ARCHIVE) if os.path.isfile(ARCHIVE) else "-")
    print("author SHA =", sha(AUTHOR))

    if bad_missing:
        print("!! 键集不满足 D2（缺了非旧条目的键）⇒ 停下报告")
        return 1
    if apply:
        os.makedirs(EVID, exist_ok=True)
        shutil.copyfile(AUTHOR, ARCHIVE)
        if sha(ARCHIVE) != sha(AUTHOR):
            print("!! 留档与源文件不一致")
            return 2
        print("archived ->", ARCHIVE, sha(ARCHIVE))
        # 1) zh 直接换成作者那份（逐字节）
        shutil.copyfile(AUTHOR, ZH)
        print("zh replaced; SHA =", sha(ZH))
        # 2) en 删掉同一批旧键（B/C 新增的键**不**动）
        removed = 0
        for k in RETIRED:
            if k in en:
                del en[k]
                removed += 1
        with io.open(EN, "w", encoding="utf-8", newline="\n") as f:
            json.dump(en, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("en: removed", removed, "retired keys; keys =", len(en))
    return 0


if __name__ == "__main__":
    sys.exit(main())
