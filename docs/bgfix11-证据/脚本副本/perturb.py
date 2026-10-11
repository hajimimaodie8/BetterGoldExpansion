# -*- coding: utf-8 -*-
"""bgfix11 扰动实测矩阵（一次性脚本；判据 = **exit + 命中 id** 两列）。

铁律（`docs/构建与跑测注意事项.md` §六/§七 + `ex/03` §3.11）：
  * 每条扰动都要先断言"变更真的生效了"（`occ` 命中数 == 1），否则记为 SETUP-FAIL（用例坏了，不算命中）；
  * exit 2 = 脚本自身出错 ⇒ 一律当作用例坏了；
  * 跑完每个文件**逐字节复原 + SHA256** 自证。

关卡：tools/asset-generator/validate_metal_data.py（跑它一次约 20~40 s）。
"""
import hashlib
import os
import subprocess
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EN = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang", "en_us.json")
ZH = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang", "zh_cn.json")
VAL = os.path.join(REPO, "tools", "asset-generator", "validate_metal_data.py")
OUT = os.path.join(REPO, "build", "bgfix11", "perturb-validator.txt")
PY = sys.executable

KEY = '"bettergold.handbook.page.knowledge_1_summary": '
NEW_EN = ("Smelt \\\"noble gold\\\" raw material into ingots in a furnace or blast furnace to make building "
          "blocks (ingot block / bricks / pillar / stairs / slab / brick wall / bars / door / trapdoor / "
          "chain / lantern), or combine them with the matching core material's smithing template to "
          "upgrade golden gear.")
OLD_ZH = (u"把\\\"贵金\\\"原料丢进熔炉或高炉烧成锭，即可制成建材（建筑方块：锭块 / 砖块 / 柱 / 楼梯 / "
          u"台阶 / 砖墙 / 栏杆 / 门 / 活板门 / 链 / 灯笼），或与其对应核心材料做成的锻造模版升级金装备。")
OTHER_EN = "Smelt noble gold ore in a furnace to make shiny building blocks."

# 校验器里的锚点（按分支判断要在**字节**上匹配，别走文本往返）
# ⚠ 行尾**实测**：本文件是 **LF**（5917 个 \n / 0 个 \r\n）—— 承 `ex/03` §3.11 ②（CRLF 会静默不中）
VAL_EXC_COMMENT = b'#     _BGFIX10_CJK_OK = {"bettergold.handbook.page.knowledge_1_summary"}'
VAL_ANCHOR = b"bgfix11_problems: list[str] = []\n"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def run_validator():
    with open(OUT, "wb") as fh:
        rc = subprocess.call([PY, VAL], stdout=fh, stderr=subprocess.STDOUT, cwd=REPO)
    txt = open(OUT, "rb").read().decode("utf-8", "replace")
    return rc, txt


def check(name, path, mutate, expect_exit, expect_ids, must_be_absent=None, append=False):
    """mutate(bytes) -> (new_bytes, occ)。occ != 1 ⇒ SETUP-FAIL。"""
    before = open(path, "rb").read()
    bsha = hashlib.sha256(before).hexdigest().upper()
    if append:
        new = before + mutate
        occ = 1
    else:
        new, occ = mutate(before)
    if occ != 1:
        print("P %-42s SETUP-FAIL（变更未生效 occ=%d）" % (name, occ))
        return False
    open(path, "wb").write(new)
    t0 = time.time()
    rc, txt = run_validator()
    dt = time.time() - t0
    hit = {i: (i in txt) for i in expect_ids}
    ok_ids = all(hit.values())
    if must_be_absent:
        for i in must_be_absent:
            if i in txt:
                ok_ids = False
                hit[i] = True  # 命名为"意外命中"
    open(path, "wb").write(before)
    asha = sha(path)
    restored = asha == bsha
    ok = (rc == expect_exit) and ok_ids and restored
    print("P %-42s exit=%-3d expect=%d %s ids=%s restore=%s (%.1fs)  -> %s"
          % (name, rc, expect_exit,
             "OK " if rc == expect_exit else "**EXIT-MISS**",
             hit, "OK" if restored else "**RESTORE-FAIL**", dt,
             "PASS" if ok else "FAIL"))
    return ok


def main():
    all_ok = True
    base_en, base_zh, base_val = sha(EN), sha(ZH), sha(VAL)
    print("基线 SHA256: en=%s zh=%s val=%s" % (base_en[:16], base_zh[:16], base_val[:16]))
    rc, txt = run_validator()
    print("基线 exit=%d（期望 0）" % rc)
    if rc != 0:
        print("SETUP-FAIL 基线不绿，扰动矩阵没意义")
        return 2

    def rep(needle, repl):
        def f(b):
            return b.replace(needle, repl), b.count(needle)
        return f

    # P1 该键 en 值改回中文
    all_ok &= check("P1 en 值改回中文", EN,
                    rep(NEW_EN.encode("utf-8"), OLD_ZH.encode("utf-8")), 1,
                    ["[bgfix11-lang-k1s-en]", "[bgfix10-lang-en-not-zh]"])
    # P2 该键 en 值改成空串
    #   ⚠ 铁律（`ex/03` §3.11 ③）：**不能**只把"值文本"换成 `""` —— 那会留下 `""""`，
    #     变成"解析不了的形状" ⇒ 关卡崩成 **exit 2**（用例坏了，不是命中）。
    #     正确做法 = 连同**两侧的 JSON 引号**一起换掉。首版就是这么踩的（实测 exit 2）。
    all_ok &= check("P2 en 值改成空串", EN,
                    rep(b'"' + NEW_EN.encode("utf-8") + b'"', b'""'), 1,
                    ["[bgfix11-lang-k1s-en]", "[bgfix10-lang-no-empty]"])
    # P3 该键 en 值换成另一句真英文
    all_ok &= check("P3 en 值换成另一句真英文", EN,
                    rep(NEW_EN.encode("utf-8"), OTHER_EN.encode("utf-8")), 1,
                    ["[bgfix11-lang-k1s-en]"], must_be_absent=["[bgfix10-lang-en-not-zh]"])
    # P4 把例外表当代码塞回去
    all_ok &= check("P4 例外表塞回代码", VAL,
                    rep(VAL_ANCHOR, VAL_ANCHOR
                        + b'_BGFIX10_CJK_OK = {"bettergold.handbook.page.knowledge_1_summary"}\n'), 1,
                    ["[bgfix11-lang-exception-gone]"])
    # P5 删掉注释里的旧代码留档行
    all_ok &= check("P5 删掉注释里的旧代码留档", VAL,
                    rep(VAL_EXC_COMMENT + b"\n", b""), 1,
                    ["[bgfix11-lang-exception-gone]"])
    # P6 只加空白（en_us.json 末尾加一个空行）—— 反向对照，必须仍绿
    all_ok &= check("P6 只加空白（en 末尾加空行）", EN, b"\n", 0, [], append=True)
    # P7 只在关卡里加一行 # 注释（内容逐字提到例外表旧代码）—— 反向对照，必须仍绿
    all_ok &= check("P7 只在关卡里加 # 注释", VAL,
                    rep(VAL_ANCHOR,
                        b"# P7 \xe5\x8e\xbb\xe6\xb3\xa8\xe9\x87\x8a\xe5\xaf\xb9\xe7\x85\xa7\xef\xbc\x9a"
                        b'_BGFIX10_CJK_OK = {"bettergold.handbook.page.knowledge_1_summary"}\n'
                        + VAL_ANCHOR), 0, [])

    # P8 前置缺失（lang/en_us.json 临时改名）⇒ exit 2
    before = open(EN, "rb").read()
    bak = EN + ".p8bak"
    os.replace(EN, bak)
    try:
        rc, txt = run_validator()
        ok = (rc == 2) and ("[bg-data-crash]" in txt)
        print("P %-42s exit=%-3d expect=2 %s [bg-data-crash]=%s  -> %s"
              % ("P8 前置缺失（en_us.json 改名）", rc, "OK " if rc == 2 else "**EXIT-MISS**",
                 "[bg-data-crash]" in txt, "PASS" if ok else "FAIL"))
        all_ok &= ok
    finally:
        os.replace(bak, EN)
    print("P8 restore=%s" % ("OK" if open(EN, "rb").read() == before else "**FAIL**"))
    all_ok &= open(EN, "rb").read() == before

    print("--- 终态 SHA256 复核 ---")
    for tag, p, want in (("en", EN, base_en), ("zh", ZH, base_zh), ("validate", VAL, base_val)):
        got = sha(p)
        ok = got == want
        all_ok &= ok
        print("%-9s %s %s" % (tag, got[:32], "OK" if ok else "**DRIFT** want " + want[:32]))
    print("RESULT %s" % ("ALL-PASS" if all_ok else "HAS-FAIL"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
