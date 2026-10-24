# -*- coding: utf-8 -*-
"""bgbig 扰动矩阵：每个段至少 1 个"能红"的用例 + 1 个"只改注释仍绿"的反向对照。

跑法（工作区自带 Python）：
    <dsh python> probe\\bgbig\\perturb.py

纪律：
  * 每个用例改前记录 SHA256 → 故意弄脏 → 跑关卡 → **逐字节复原** → 复核 SHA256；
  * 判据 = `exit 1` **且**命中期望的稳定 ASCII tag（`exit 2` 一律算用例坏了）；
  * 反向对照（只改注释）= `exit 0`；
  * 失败文案里不出现裸百分号。
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
VD = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")
VA = os.path.join(ROOT, "tools", "asset-generator", "validate_advancements.py")
REC = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "recipe")
ADV = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "advancement")
BOOK = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold",
                    "patchouli_books", "alchemy_handbook", "zh_cn", "entries")
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang")
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold")
GEN = os.path.join(ROOT, "tools", "asset-generator", "generate_handbook_data.py")
OUT = os.path.join(ROOT, "docs", "bgbig-证据", "04-扰动矩阵.txt")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def run_validator(script):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, script], cwd=ROOT, capture_output=True, env=env)
    text = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, text


def case(name, path, mutate, script, expect_tag, expect_exit=1, tag="?"):
    before = sha(path)
    raw = open(path, "rb").read()
    result = None
    try:
        new = mutate(raw)
        if new == raw:
            result = (name, "CASE-BROKEN", "变更未生效")
        else:
            open(path, "wb").write(new)
            code, text = run_validator(script)
            hit = expect_tag in text
            ok = (code == expect_exit) and (hit if expect_exit == 1 else True)
            result = (name, "HIT" if ok else "MISS", "exit=%d hit=%s" % (code, hit))
    finally:
        open(path, "wb").write(raw)
    restored = before == sha(path)
    if not restored:
        print("!! 复原失败：", path)
    return (result[0], result[1], result[2], restored)


def case_absent(name, path, content, script, expect_tag):
    """用例 = "这个文件本来不该存在"：创建它 → 期望红 → 删掉并复核不存在。"""
    if os.path.exists(path):
        return (name, "CASE-BROKEN", "前置：文件本来就存在", False)
    try:
        open(path, "wb").write(content)
        code, text = run_validator(script)
        hit = expect_tag in text
        ok = (code == 1) and hit
        return (name, "HIT" if ok else "MISS", "exit=%d hit=%s" % (code, hit), True)
    finally:
        if os.path.exists(path):
            os.remove(path)
        restored = not os.path.exists(path)
        if not restored:
            print("!! 复原失败（文件还在）：", path)


def main():
    rows = []

    def sub_bytes(raw, old, new):
        assert raw.count(old) == 1, (old, raw.count(old))
        return raw.replace(old, new, 1)

    # ---- A1 盾牌 7 锭（改回 6 锭 + 苹果 → gpt9-shield-count 红）
    p = os.path.join(REC, "chaosgold_shield.json")
    rows.append(case("A1-shield-7-ingots", p,
                     lambda b: b.replace(b'"pattern": [\n    "XXX",\n    "XXX",\n    " X "\n  ]',
                                         b'"pattern": [\n    "XXX",\n    "XAX",\n    " X "\n  ]')
                     .replace(b'"key": {\n    "X": {', b'"key": {\n    "A": {\n      "item": "minecraft:apple"\n    },\n    "X": {'),
                     VD, "[gpt9-shield-count]"))

    # ---- A2 禁果中心苹果（中心换成锭 → gpt9-forbidden-fruit 红）
    p = os.path.join(REC, "chaosgold_forbidden_fruit.json")
    rows.append(case("A2-fruit-center-apple", p,
                     lambda b: sub_bytes(b, b'"pattern": [\n    "XXX",\n    "XAX",\n    "XXX"\n  ]',
                                         b'"pattern": [\n    "XXX",\n    "XXX",\n    "XXX"\n  ]'),
                     VD, "[gpt9-forbidden-fruit]"))

    # ---- A3 巫毒爆发类型（改回 damageSources().magic() → gpt6-voodoo-magic 红）
    p = os.path.join(JAVA, "material", "MetalEvents.java")
    rows.append(case("A3-voodoo-burst-type", p,
                     lambda b: sub_bytes(
                         b,
                         b"return com.hjmmd_8.bettergold.entity.ModDamageTypes.source(\n"
                         b"                serverLevel, com.hjmmd_8.bettergold.entity.ModDamageTypes.VOODOO_BURST, null, owner);",
                         b"return entity.damageSources().magic();"),
                     VD, "[gpt6-voodoo-magic]"))

    # ---- B1 金铸的牢狱逐字文案（改一个字 → bgbig-verbatim 红）
    p = os.path.join(LANG, "zh_cn.json")
    rows.append(case("B1-prison-verbatim", p,
                     lambda b: sub_bytes(b, "其名为金之牢狱".encode("utf-8"),
                                         "其名为金之牢房".encode("utf-8")),
                     VD, "[bgbig-verbatim]"))

    # ---- B2 旧章节产物（把旧条目文件放回来 → bgbig-old-chapters-gone 红）
    rows.append(case_absent("B2-old-chapter-product-back",
                            os.path.join(BOOK, "chaos_materials.json"),
                            b'{ "name": "x", "category": "bettergold:alchemy_start", '
                            b'"icon": "bettergold:chaos_coin", "sortnum": 0, "pages": [] }\n',
                            VD, "[bgbig-old-chapters-gone]"))

    # ---- C1 黄金火焰 requirements（把两组并成一组 = 变成"或" → 红）
    p = os.path.join(ADV, "agriculture", "golden_torchflower.json")
    rows.append(case("C1-torchflower-and", p,
                     lambda b: sub_bytes(b, b'"requirements": [\n    [\n      "have_seeds"\n    ],\n    [\n      "have_flower"\n    ]\n  ]',
                                         b'"requirements": [\n    [\n      "have_seeds",\n      "have_flower"\n    ]\n  ]'),
                     VA, "[bgn10r9-adv-chaos-chain]"))

    # ---- C2 被毙的成就（把 treasure/chaos_coin.json 放回来 → 红）
    back = open(os.path.join(ROOT, "docs", "bgbig-证据", "03-删除的旧成就原文",
                             "treasure_chaos_coin.json"), "rb").read()
    rows.append(case_absent("C2-retired-advancement-back",
                            os.path.join(ADV, "treasure", "chaos_coin.json"),
                            back, VA, "[bgn10r9-adv-chaos-chain]"))

    # ---- D1 语言文件（改 en 一个值 → bgfix11 SHA 红）
    p = os.path.join(LANG, "en_us.json")
    rows.append(case("D1-lang-sha", p,
                     lambda b: sub_bytes(b, b"Somewhere in the Nether hides a dungeon forged from gold.",
                                         b"Somewhere in the Nether hides a dungeon forged from gold!"),
                     VD, "[bgfix11-lang-k1s-en]"))

    # ---- 反向对照：只改注释仍绿
    p = GEN
    rows.append(case("Z-comment-only-still-green", p,
                     lambda b: b + b"\n# bgbig perturb: comment only, must stay green\n",
                     VD, "", expect_exit=0))

    lines = ["bgbig 扰动矩阵（判据 = exit + 命中期望 tag；逐字节复原 + SHA256）", ""]
    all_ok = True
    for name, verdict, detail, restored in rows:
        if verdict != "HIT" or not restored:
            all_ok = False
        lines.append("%-28s %-10s %-40s restored=%s" % (name, verdict, detail, restored))
    text = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
