# -*- coding: utf-8 -*-
"""收尾③：扰动矩阵（[bgp-exit-parent]）。

每个用例：改字节 → 跑关卡 → 记 exit 与命中行 → **逐字节复原** → SHA256 自证。
跑法（工作区自带 python，禁止 py -3）：
  <python> probe\\gps\\perturb.py
输出 build\\gps_perturb.txt
"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PY = sys.executable
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
OUT = os.path.join(ROOT, "build", "gps_perturb.txt")

LANE = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                    "template_pool", "golden_prison", "lane.json")
ROOM = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                    "template_pool", "golden_prison", "room.json")
FILES = (LANE, ROOM, GATE)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_gate():
    p = subprocess.run([PY, GATE], cwd=ROOT, capture_output=True)
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    hits = [l.strip() for l in out.splitlines() if "[bgp-exit-parent]" in l and "NG" in l]
    okline = [l.strip() for l in out.splitlines() if l.strip().startswith("[bgp-ok]")]
    failline = [l.strip() for l in out.splitlines() if l.strip().startswith("[bgp-fail]")]
    return p.returncode, hits, okline, failline


def sub_bytes(path, old, new):
    b = open(path, "rb").read()
    assert b.count(old) == 1, (os.path.basename(path), old, b.count(old))
    b = b.replace(old, new, 1)
    open(path, "wb").write(b)


def _lane_exit():
    sub_bytes(LANE, b'"fallback": "bettergold:golden_prison/room"',
              b'"fallback": "bettergold:golden_prison/exit"')


def _room_lane():
    sub_bytes(ROOM, b'"fallback": "bettergold:golden_prison/exit"',
              b'"fallback": "bettergold:golden_prison/lane"')


def _comment_only():
    b = open(GATE, "rb").read()
    marker = b'def check_exit_parent(pieces):'
    assert b.count(marker) == 1
    # 只加一行注释（不影响任何断言；若关卡把注释当实现，这里就会假绿/假红）
    b = b.replace(marker, b'# [perturb] \xe5\x8f\xaa\xe6\x94\xb9\xe6\xb3\xa8\xe9\x87\x8a\n' + marker, 1)
    open(GATE, "wb").write(b)


def _ws_only():
    sub_bytes(LANE, b'"fallback": "bettergold:golden_prison/room"',
              b'"fallback" :  "bettergold:golden_prison/room"')


CASES = [
    ("P1", "lane.fallback: room -> exit（= 回退到第十二轮口径）", _lane_exit, True),
    ("P2", "room.fallback: exit -> lane（方向搞反）", _room_lane, True),
    ("P3", "只加一行注释（validate_golden_prison.py）", _comment_only, False),
    ("P4", "只改空白（lane.json 冒号两侧加空格）", _ws_only, False),
]


def main():
    base = {p: open(p, "rb").read() for p in FILES}
    base_sha = {p: sha(v) for p, v in base.items()}
    L = ["# 扰动矩阵（[bgp-exit-parent] / 第十三轮）", "",
         "| 用例 | 改动 | 期望 | 实测 exit | 命中 / 计数行 | 复原 |",
         "|---|---|---|---|---|---|"]
    bad = 0
    for pid, desc, fn, want_red in CASES:
        fn()
        rc, hits, okline, failline = run_gate()
        for p in FILES:
            open(p, "wb").write(base[p])
        same = all(sha(open(p, "rb").read()) == base_sha[p] for p in FILES)
        red = rc != 0
        hit = hits[0][:170] if hits else (failline[0][:170] if failline else (okline[0][:170] if okline else "-"))
        good = (red == want_red) and (not want_red or bool(hits)) and same
        if not good:
            bad += 1
        L.append("| %s | %s | %s | **%d** | `%s` | %s |"
                 % (pid, desc, "红" if want_red else "绿", rc, hit,
                    "OK" if same else "**MISMATCH**"))
        print("%s exit=%d want=%s hit=%s restore=%s"
              % (pid, rc, "red" if want_red else "green", bool(hit), "OK" if same else "BAD"))
    L += ["", "复原后 SHA256（应与改前逐字节相同）：", ""]
    for p in FILES:
        L.append("- `%s` = `%s`" % (os.path.relpath(p, ROOT), base_sha[p]))
    L += ["", "结论：%d 个用例，失败 %d 个。" % (len(CASES), bad)]
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n[gps-perturb] wrote %s (bad=%d)" % (OUT, bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
