# -*- coding: utf-8 -*-
"""第九轮收尾·改后扰动：4 用例（3 红 + 1 绿），逐字节复原 + SHA256。

跑法（工作区自带 Python）：
  <dsh python> gpn_perturb.py

用例：
  P1 「全部件 bbox 当墙去掉」 —— `new PieceWalls(...)` -> null ⇒ [bgp-exit-air] 红
  P2 「相邻禁止去掉」         —— `candBox.inflatedBy(1)` -> `candBox` ⇒ 红
  P3 「3×3×3 恢复改回 1 格」  —— 恢复只跳口位格 ⇒ 红
  P4 「只改注释」             —— 必须保持基线（绿）
"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
TARGET = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "worldgen",
                      "GoldenPrisonStructure.java")
VALIDATOR = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")

CASES = [
    ("P1_墙集去掉", "        PieceWalls walls = new PieceWalls(window, wallBoxes);",
     "        PieceWalls walls = null; // P1: 全部件 bbox 当墙去掉（扰动）", "bgp-exit-air"),
    ("P2_相邻禁止去掉", "                if (ob.intersects(candBox.inflatedBy(1))) {",
     "                if (ob.intersects(candBox)) { // P2: 相邻禁止去掉（扰动）", "bgp-exit-air"),
    ("P3_3x3x3改回1格", "            if (c.cell.air() || c.pos.equals(seed)) {",
     "            if (c.pos.equals(seed)) { // P3: 3x3x3 恢复改回 1 格（扰动）", "bgp-exit-air"),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_validator():
    p = subprocess.run([sys.executable, VALIDATOR], cwd=ROOT, capture_output=True)
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, out


def problems_of(out):
    for l in out.splitlines():
        if l.startswith("[bgp-fail]"):
            try:
                return int(l.split("problems=")[1].split()[0])
            except Exception:
                return -1
    return 0


def codes_of(out):
    s = set()
    for l in out.splitlines():
        if l.startswith("[bgp] NG ["):
            s.add(l.split("[", 2)[2].split("]", 1)[0])
    return s


def main():
    base = open(TARGET, "rb").read()
    base_sha = sha(base)
    print("baseline sha256 =", base_sha, "bytes =", len(base))

    rc, out = run_validator()
    base_problems = problems_of(out)
    base_codes = codes_of(out)
    print("baseline validator exit =", rc, "problems =", base_problems, "codes =", sorted(base_codes))
    if rc == 2:
        print("!! baseline exit 2 (前置坏)")
        return 2

    results = []
    for name, old, new, want_code in CASES:
        b = open(TARGET, "rb").read()
        ob, nb = old.encode("utf-8"), new.encode("utf-8")
        n = b.count(ob)
        if n != 1:
            print("!! %s: pattern count=%d (expect 1)" % (name, n))
            results.append((name, "PATTERN-MISS", False))
            continue
        open(TARGET, "wb").write(b.replace(ob, nb))
        try:
            rc2, out2 = run_validator()
            probs = problems_of(out2)
            codes = codes_of(out2)
            ok_case = (rc2 == 1) and (probs > base_problems) and (want_code in codes)
            tail = [l for l in out2.splitlines() if "NG [" in l][-2:]
            print("%-20s exit=%d problems=%d(+%d) codes=%s %s => %s"
                  % (name, rc2, probs, probs - base_problems, sorted(codes - base_codes), tail,
                     "PASS" if ok_case else "FAIL"))
            results.append((name, "exit=%d problems=%d" % (rc2, probs), ok_case))
        finally:
            open(TARGET, "wb").write(b)
            same = open(TARGET, "rb").read() == b
            print("   restored: bytes_equal=%s sha256=%s" % (same, sha(open(TARGET, "rb").read())))
            if not same:
                raise SystemExit("restore failed for " + name)

    b = open(TARGET, "rb").read()
    open(TARGET, "wb").write(b + b"\n// P4 perturbation: comment only\n")
    try:
        rc2, out2 = run_validator()
        probs = problems_of(out2)
        ok_case = rc2 == rc and probs == base_problems
        print("%-20s exit=%d problems=%d => %s（只改注释仍保持基线）"
              % ("P4_只改注释", rc2, probs, "PASS" if ok_case else "FAIL"))
        results.append(("P4_只改注释", "exit=%d problems=%d" % (rc2, probs), ok_case))
    finally:
        open(TARGET, "wb").write(b)
        same = open(TARGET, "rb").read() == b
        print("   restored: bytes_equal=%s sha256=%s" % (same, sha(open(TARGET, "rb").read())))
        if not same:
            raise SystemExit("restore failed for P4")

    final_sha = sha(open(TARGET, "rb").read())
    print("final sha256 =", final_sha, "== baseline:", final_sha == base_sha)
    bad = [r for r in results if not r[-1]]
    print("cases =", len(results), "failed =", len(bad))
    return 1 if (bad or final_sha != base_sha) else 0


if __name__ == "__main__":
    sys.exit(main())
