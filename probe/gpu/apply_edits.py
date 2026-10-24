# -*- coding: utf-8 -*-
"""第十四轮（2026-10-24）：金之牢狱 size 5 -> 4 的两处改动（JSON + 关卡）。

铁律：一切读写走 bytes（Windows + 中文/CRLF，禁止文本模式重写）。
本脚本只做三件事：
  ① structure/golden_prison.json 的 `"size": 5,` -> `"size": 4,`（全文件恰好 1 处）；
  ② validate_golden_prison.py 的 EXPECT_STRUCT_COMMON['size'] 5 -> 4 + 旧值原注释；
  ③ validate_golden_prison.py 的 MAX_DEPTH 5 -> 4 + 旧值原注释 + 新增两条断言（size 与 MAX_DEPTH 同步）。
改前 SHA256 记在 build/gp14_edits.txt。

跑法（工作区自带 python，禁 py -3）：
  <python> probe\\gpu\\apply_edits.py
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
STRUCT = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                      "structure", "golden_prison.json")
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
OUT = os.path.join(ROOT, "build", "gp14_edits.txt")
PROPS = os.path.join(ROOT, "run", "server.properties")
PROPS_BAK = os.path.join(ROOT, "run", "server.properties.gp14.bak")


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    rows = []
    # ---------- 备份 server.properties（逐字节，收尾复原用）
    if os.path.exists(PROPS):
        open(PROPS_BAK, "wb").write(open(PROPS, "rb").read())
        print("[gp14] server.properties.bak sha=%s" % sha(open(PROPS_BAK, "rb").read()))

    # ---------- ① structure JSON：size 5 -> 4
    b = open(STRUCT, "rb").read()
    old = b'"size": 5,'
    assert b.count(old) == 1, ("structure size 5 count", b.count(old))
    b2 = b.replace(old, b'"size": 4,', 1)
    assert len(b2) == len(b)
    open(STRUCT, "wb").write(b2)
    rows.append(("structure/golden_prison.json", sha(b), sha(b2), "%d B" % len(b2)))
    print("[gp14] JSON size 5 -> 4 : %s -> %s" % (sha(b), sha(b2)))

    # ---------- ② + ③ 关卡
    g = open(GATE, "rb").read()
    g0 = g

    # ② 期望值 + 旧值原文注释
    anc = (b"#   " + "旧期望原文留档（第一~六轮）：'size': 6".encode("utf-8") + b"\r\n")
    assert g.count(anc) == 1, ("expect comment anchor", g.count(anc))
    add2 = (
        "# ★★ 第十四轮（2026-10-24，作者选定）：size 5 → 4（出入口 25→64 / 落单口 77→36 / 被裁 5→0；"
        "A 级读数见 docs §19）。\r\n"
        "#   旧期望原文留档（第一~十三轮）：'size': 5（第七轮起；第一~六轮 = 6）\r\n"
    ).encode("utf-8")
    g = g.replace(anc, anc + add2, 1)
    old_size = b"'step': 'underground_decoration', 'size': 5,"
    assert g.count(old_size) == 1, ("EXPECT_STRUCT_COMMON size", g.count(old_size))
    g = g.replace(old_size, b"'step': 'underground_decoration', 'size': 4,", 1)

    # ③ MAX_DEPTH + 旧值原文注释
    assert g.count(b"MAX_DEPTH = 5") == 1
    g = g.replace(b"MAX_DEPTH = 5", b"MAX_DEPTH = 4", 1)
    oldc = (b"                       # " +
            "旧值 6（第一~六轮）留档：第七轮 6 → 5 修落单口，见 §13.2".encode("utf-8") + b"\r\n")
    assert g.count(oldc) == 1, ("MAX_DEPTH comment", g.count(oldc))
    newc = (
        "                       # 旧值 6（第一~六轮）留档：第七轮 6 → 5 修落单口，见 §13.2\r\n"
        "                       # 旧值 5（第七~十三轮）留档：第十四轮 2026-10-24 5 → 4（docs §19）\r\n"
    ).encode("utf-8")
    g = g.replace(oldc, newc, 1)

    # ③b 新增两条断言（插在 check_worldgen 的 start_pool 段之前）
    anchor = b"\r\n    # ---- " + "唯一一套：start_pool 指向 start".encode("utf-8")
    assert g.count(anchor) == 1, ("start_pool anchor", g.count(anchor))
    block = (
        "\r\n"
        "        # ---- size：第十四轮（2026-10-24，作者选定）5 → 4（旧值 5 留档在上面的注释）\r\n"
        "        if st.get('size') != EXPECT_STRUCT_COMMON['size']:\r\n"
        "            ng(code, '%s.size = %r != %r（第十四轮 2026-10-24：size 5 → 4）'\r\n"
        "               % (kind, st.get('size'), EXPECT_STRUCT_COMMON['size']))\r\n"
        "        ok()\r\n"
        "        # ---- MAX_DEPTH（静态拼件模拟）必须与真 size 同步，否则关卡会「按旧 size 验新品」\r\n"
        "        if MAX_DEPTH != EXPECT_STRUCT_COMMON['size']:\r\n"
        "            ng(code, 'MAX_DEPTH=%d != EXPECT_STRUCT_COMMON[\"size\"]=%d（模拟深度必须等于结构 size）'\r\n"
        "               % (MAX_DEPTH, EXPECT_STRUCT_COMMON['size']))\r\n"
        "        ok()\r\n"
    ).encode("utf-8")
    g = g.replace(anchor, block + anchor, 1)

    assert g != g0
    open(GATE, "wb").write(g)
    rows.append(("tools/asset-generator/validate_golden_prison.py", sha(g0), sha(g), "%d B" % len(g)))
    print("[gp14] gate %s -> %s" % (sha(g0), sha(g)))

    L = ["# 第十四轮改动（size 5 → 4）", "",
         "| 文件 | 改前 SHA256 | 改后 SHA256 | 大小 |", "|---|---|---|---|"]
    for r in rows:
        L.append("| `%s` | `%s` | `%s` | %s |" % r)
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("[gp14] wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
