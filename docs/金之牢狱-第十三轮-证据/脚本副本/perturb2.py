# -*- coding: utf-8 -*-
"""第十三轮 A 方案 扰动矩阵（[bgp-exit-parent] 新口径）。

用例：exit.name lane→room（核心闸）/ room.fallback→lane / lane.fallback→room / 只加注释。
每个用例：改字节 → 跑关卡 → 记 exit 与命中行 → **逐字节复原** → SHA256 自证。
跑法（工作区自带 python，禁止 py -3）：
  <python> probe\\gps\\perturb2.py
输出 build\\gps_perturb2.txt
"""
import gzip
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PY = sys.executable
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
OUT = os.path.join(ROOT, "build", "gps_perturb2.txt")

NBT = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "structure",
                   "golden_prison", "exit.nbt")
LANE = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                    "template_pool", "golden_prison", "lane.json")
ROOM = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                    "template_pool", "golden_prison", "room.json")
FILES = (NBT, LANE, ROOM, GATE)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_gate():
    p = subprocess.run([PY, GATE], cwd=ROOT, capture_output=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    hits = [l.strip() for l in out.splitlines() if "[bgp-exit-parent]" in l and "NG" in l]
    okline = [l.strip() for l in out.splitlines() if l.strip().startswith("[bgp-ok]")]
    failline = [l.strip() for l in out.splitlines() if l.strip().startswith("[bgp-fail]")]
    return p.returncode, hits, okline, failline


TAG = b"\x08\x00\x04name\x00\x04"


def nbt_set(value):
    raw = open(NBT, "rb").read()
    dec = gzip.decompress(raw)
    assert dec.count(TAG) == 1
    i = dec.find(TAG) + len(TAG)
    dec2 = dec[:i] + value + dec[i + 4:]
    open(NBT, "wb").write(gzip.compress(dec2, compresslevel=9, mtime=0))


def sub_bytes(path, old, new):
    b = open(path, "rb").read()
    assert b.count(old) == 1, (os.path.basename(path), old, b.count(old))
    open(path, "wb").write(b.replace(old, new, 1))


def _exit_room():
    nbt_set(b"room")


def _room_lane():
    sub_bytes(ROOM, b'"fallback": "bettergold:golden_prison/exit"',
              b'"fallback": "bettergold:golden_prison/lane"')


def _lane_room():
    sub_bytes(LANE, b'"fallback": "bettergold:golden_prison/exit"',
              b'"fallback": "bettergold:golden_prison/room"')


def _comment_only():
    b = open(GATE, "rb").read()
    marker = b'def check_exit_parent(pieces):'
    assert b.count(marker) == 1
    open(GATE, "wb").write(b.replace(
        marker, b'# [perturb] \xe5\x8f\xaa\xe6\x94\xb9\xe6\xb3\xa8\xe9\x87\x8a\n' + marker, 1))


CASES = [
    ("P1", "exit.nbt 的 jigsaw name: lane -> room（= 第十二轮口径；本轮核心闸）", _exit_room, True),
    ("P2", "room.fallback: exit -> lane（方向搞反）", _room_lane, True),
    ("P3", "lane.fallback: exit -> room（出入口会 0 座）", _lane_room, True),
    ("P4", "只加一行注释（validate_golden_prison.py）", _comment_only, False),
]


def main():
    base = {p: open(p, "rb").read() for p in FILES}
    base_sha = {p: sha(v) for p, v in base.items()}
    L = ["# 扰动矩阵（[bgp-exit-parent] 新口径 / 第十三轮 A 方案）", "",
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
        hit = (hits[0] if hits else (failline[0] if failline else (okline[0] if okline else "-")))[:175]
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
    print("\n[gps-perturb2] wrote %s (bad=%d)" % (OUT, bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
