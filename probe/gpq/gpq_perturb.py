# -*- coding: utf-8 -*-
"""扰动矩阵（4 用例：3 红 + 1 绿；每次逐字节复原 + SHA256 自证）。

P1 ③ 把 8 族刀的 final 默认值改回 false     -> 必须红（[bgn10fix2-knife]）
P2 ④ 把战利品表改回 27 条 / 权重和 80        -> 必须红（[bgp-loot] + [bgp-loot-book]）
P3 ① 把崩乱合金耐久"修好"成 {1924,2220,2368,1628} -> 必须红（[bgn10r7-armor-durability-author]）
P4 只给 MetalFamily.java 加一行注释          -> 必须**绿**（反向对照：关卡不是靠"改了就红"）

跑法：<dsh python> probe\\gpq\\gpq_perturb.py
输出：控制台 + docs/gpq-证据/05-扰动矩阵.md
"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TG = os.path.join(ROOT, "tools", "asset-generator")
EVID = os.path.join(ROOT, "docs", "gpq-证据")

MF = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "material", "MetalFamily.java")
AM = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "material", "AllMetals.java")
LOOT = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "loot_table", "chests",
                    "golden_prison.json")


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def run_gate(name):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, os.path.join(TG, name)], cwd=ROOT, capture_output=True, env=env)
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, out


def case(title, path, old, new, gate, want_exit, want_hits, rows):
    base = open(path, "rb").read()
    h0 = sha(base)
    t = base.decode("utf-8")
    n = t.count(old)
    assert n == 1, "命中 %d 次（期望 1）：%r" % (n, old[:90])
    open(path, "wb").write(t.replace(old, new).encode("utf-8"))
    rc, out = run_gate(gate)
    open(path, "wb").write(base)          # 逐字节复原
    h1 = sha(open(path, "rb").read())
    hits = [k for k in want_hits if k in out]
    okc = (rc == want_exit) and (len(hits) == len(want_hits)) and (h0 == h1)
    rows.append((title, os.path.relpath(path, ROOT), rc, want_exit, ",".join(hits) or "-",
                 "YES" if h0 == h1 else "NO", "PASS" if okc else "FAIL"))
    print("[%s] %s  exit=%d(want %d) hits=%r restored=%s" % (
        "PASS" if okc else "FAIL", title, rc, want_exit, hits, h0 == h1), flush=True)
    if not okc:
        print(out[-2500:])
    return okc


def main():
    os.makedirs(EVID, exist_ok=True)
    rows = []
    ok = True
    ok &= case("P1 ③ 8 族刀 final 默认值 true->false", MF,
               "public boolean knifeValuesAreFinal = true;",
               "public boolean knifeValuesAreFinal = false;",
               "validate_metal_data.py", 1, ["bgn10fix2-knife"], rows)
    ok &= case("P2 ④ 战利品表删掉附魔书（回到 27 条 / 权重和 80）", LOOT,
               """        {
          "weight": 2,
          "type": "minecraft:item",
          "name": "bettergold:chaosgold_enchanting_book"
        },
""",
               "",
               "validate_golden_prison.py", 1, ["[bgp-loot]", "[bgp-loot-book]"], rows)
    ok &= case("P3 ① 把崩乱合金耐久改成「修好版」{1924,2220,2368,1628}", AM,
               "spec.armorDurability = new int[] { 2035, 2220, 2368, 1924 };",
               "spec.armorDurability = new int[] { 1924, 2220, 2368, 1628 };",
               "validate_metal_data.py", 1, ["bgn10r7-armor-durability-author"], rows)
    ok &= case("P4 只给 MetalFamily.java 加一行注释（反向对照：应保持绿）", MF,
               "public boolean knifeValuesAreFinal = true;",
               "// gpq control: only a comment\n        public boolean knifeValuesAreFinal = true;",
               "validate_metal_data.py", 0, ["[bg-data-ok]"], rows)

    lines = ["# 扰动矩阵（gpq 轮：3 红 + 1 绿，逐字节复原 + SHA256）", "",
             "| 用例 | 文件 | exit | 期望 exit | 命中的关卡 id | restored | 结论 |", "|---|---|---|---|---|---|---|"]
    lines += ["| %s | `%s` | **%d** | %d | %s | %s | %s |" % r for r in rows]
    lines.append("")
    lines.append("复原 = 用**改前字节**写回并复核 SHA256（逐字节相同）；P4 是反向对照：")
    lines.append("只加一行注释，关卡必须**仍然 exit 0**（证明断言不是「只要改了就红」）。")
    lines.append("")
    lines.append("全部 %d 用例：%s" % (len(rows), "**PASS**" if ok else "**FAIL**"))
    out = "\n".join(lines) + "\n"
    open(os.path.join(EVID, "05-扰动矩阵.md"), "w", encoding="utf-8", newline="\n").write(out)
    print(out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
