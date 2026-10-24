# -*- coding: utf-8 -*-
"""第十四轮扰动矩阵（size 5 → 4 的两道闸）。

用例（≥2，本轮 4 个：3 红 + 1 绿）：
  P1  structure JSON 的 size: 4 -> 5（回退到上一轮值，**核心闸**）      期望红
  P2  structure JSON 的 size: 4 -> 3（越界到另一档）                     期望红
  P3  关卡 MAX_DEPTH: 4 -> 5（模拟深度与真 size 脱钩）                   期望红
  P4  只加一行注释（validate_golden_prison.py）                          期望绿

每个用例：改字节 → 跑关卡（工作区 python）→ 记 exit + 命中行 → **逐字节复原** → SHA256 自证。
跑法：<python> probe\\gpu\\perturb.py
输出 build\\gp14_perturb.txt
"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PY = sys.executable
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
STRUCT = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                      "structure", "golden_prison.json")
OUT = os.path.join(ROOT, "build", "gp14_perturb.txt")
FILES = (STRUCT, GATE)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def sub_bytes(path, old, new):
    b = open(path, "rb").read()
    assert b.count(old) == 1, (os.path.basename(path), old, b.count(old))
    open(path, "wb").write(b.replace(old, new, 1))


def run_gate():
    p = subprocess.run([PY, GATE], cwd=ROOT, capture_output=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    hits = [l.strip() for l in out.splitlines()
            if ("[bgp-worldgen]" in l and "!=" in l) or l.strip().startswith("[bgp-fail]")]
    okline = [l.strip() for l in out.splitlines() if l.strip().startswith("[bgp-ok]")]
    return p.returncode, hits, okline


def _json(old, new):
    def fn():
        sub_bytes(STRUCT, old, new)
    return fn


def _maxdepth():
    sub_bytes(GATE, b"MAX_DEPTH = 4", b"MAX_DEPTH = 5")


def _comment_only():
    b = open(GATE, "rb").read()
    marker = b"def check_worldgen():"
    assert b.count(marker) == 1
    open(GATE, "wb").write(b.replace(
        marker, b"# [perturb] \xe5\x8f\xaa\xe6\x94\xb9\xe6\xb3\xa8\xe9\x87\x8a\r\n" + marker, 1))


CASES = [
    ("P1", "structure JSON 的 size: 4 -> 5（回退上一轮值）", _json(b'"size": 4,', b'"size": 5,'), True),
    ("P2", "structure JSON 的 size: 4 -> 3（越界另一档）", _json(b'"size": 4,', b'"size": 3,'), True),
    ("P3", "关卡 MAX_DEPTH: 4 -> 5（模拟深度脱钩）", _maxdepth, True),
    ("P4", "只加一行注释（validate_golden_prison.py）", _comment_only, False),
]


def main():
    base = {p: open(p, "rb").read() for p in FILES}
    base_sha = {p: sha(v) for p, v in base.items()}
    L = ["# 扰动矩阵（第十四轮 size 5 → 4）", "",
         "| 用例 | 改动 | 期望 | 实测 exit | 命中 / 计数行 | 复原 |", "|---|---|---|---|---|---|"]
    bad = 0
    for pid, desc, fn, want_red in CASES:
        fn()
        rc, hits, okline = run_gate()
        for p in FILES:
            open(p, "wb").write(base[p])
        same = all(sha(open(p, "rb").read()) == base_sha[p] for p in FILES)
        red = rc != 0
        hit = (hits[0] if hits else (okline[0] if okline else "-"))[:180]
        good = (red == want_red) and (not want_red or bool(hits)) and same
        if not good:
            bad += 1
        L.append("| %s | %s | %s | **%d** | `%s` | %s |"
                 % (pid, desc, "红" if want_red else "绿", rc, hit,
                    "OK" if same else "**MISMATCH**"))
        print("%s exit=%d want=%s hit=%s restore=%s"
              % (pid, rc, "red" if want_red else "green", bool(hit), "OK" if same else "BAD"))
        print("    hit:", hit)
    L += ["", "复原后 SHA256（应与改前逐字节相同）：", ""]
    for p in FILES:
        L.append("- `%s` = `%s`" % (os.path.relpath(p, ROOT), base_sha[p]))
    L += ["", "结论：%d 个用例，失败 %d 个。" % (len(CASES), bad)]
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n[gp14-perturb] wrote %s (bad=%d)" % (OUT, bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
