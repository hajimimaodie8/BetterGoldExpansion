# -*- coding: utf-8 -*-
"""第九轮扰动矩阵：4 个用例（3 红 + 1 绿），每个用例**逐字节复原 + SHA256 自证**。

跑法：
  C:\\Users\\Lenovo\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe gp9_perturb.py
（工作区自带 Python；关卡自己的 docstring 要求别用 `py -3`。）

用例（都对 GoldenPrisonStructure.java 动手）：
  P1 「关掉搬移」            —— 目的地搜索不再被调用 ⇒ [bgp-exit-air] 必须红
  P2 「让恢复 footprint 跳过」 —— 恢复那一次写永远不执行 ⇒ 必须红
  P3 「bbox 判据改成只看中心」  —— 空域判据退化成中心一格 ⇒ 必须红
  P4 「只改注释」             —— 追加一行注释 ⇒ 必须**保持绿**（正向 needle 跑在去注释源码上）
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

P1_OLD = ("        Destination dest = searchDestination(level, window, oldBox, reachable, seed, oldAir, cells, settings, mouth, origin,\n"
          "                protectedCells, otherBoxes, rec);\n")
P1_NEW = "        Destination dest = null; // P1: 关掉搬移（扰动）\n"

P2_OLD = "if (write(level, c.pos, natural, rec)) {"
P2_NEW = "if (write(level, c.pos, natural, rec) && false) {"

P3_OLD = "if (boxSum(pre, strideX, strideY, i1, j1, k1, i2, j2, k2) != vol) {"
P3_NEW = ("if (boxSum(pre, strideX, strideY, (i1 + i2) / 2, (j1 + j2) / 2, (k1 + k2) / 2, "
          "(i1 + i2) / 2, (j1 + j2) / 2, (k1 + k2) / 2) != 1) {")

CASES = [
    ("P1_关掉搬移", P1_OLD, P1_NEW, 1, "bgp-exit-air"),
    ("P2_恢复跳过", P2_OLD, P2_NEW, 1, "bgp-exit-air"),
    ("P3_判据只看中心", P3_OLD, P3_NEW, 1, "bgp-exit-air"),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_validator():
    p = subprocess.run([sys.executable, VALIDATOR], cwd=ROOT, capture_output=True)
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, out


def main():
    base = open(TARGET, "rb").read()
    base_sha = sha(base)
    print("baseline sha256 =", base_sha, "bytes =", len(base))

    rc, out = run_validator()
    print("baseline validator exit =", rc)
    if rc != 0:
        print(out[-2000:])
        print("!! baseline not green, abort")
        return 2

    results = []
    for name, old, new, want_rc, want_code in CASES:
        b = open(TARGET, "rb").read()
        ob, nb = old.encode("utf-8"), new.encode("utf-8")
        n = b.count(ob)
        if n != 1:
            print("!! %s: pattern count=%d (expect 1)" % (name, n))
            results.append((name, "PATTERN-MISS", want_rc, want_code))
            continue
        open(TARGET, "wb").write(b.replace(ob, nb))
        try:
            rc, out = run_validator()
            hit = ("NG [%s]" % want_code) in out or ("[%s]" % want_code) in out
            ok = (rc == want_rc) and hit
            tail = [l for l in out.splitlines() if "NG [" in l][-2:]
            print("%-22s exit=%d hit=%s %s => %s" % (name, rc, hit, tail, "PASS" if ok else "FAIL"))
            results.append((name, "exit=%d hit=%s" % (rc, hit), want_rc, want_code, ok))
        finally:
            open(TARGET, "wb").write(b)
            same = open(TARGET, "rb").read() == b
            print("   restored: bytes_equal=%s sha256=%s" % (same, sha(open(TARGET, "rb").read())))
            if not same:
                raise SystemExit("restore failed for " + name)

    # P4：只加一行注释 ⇒ 必须保持绿
    b = open(TARGET, "rb").read()
    open(TARGET, "wb").write(b + b"\n// P4 perturbation: comment only\n")
    try:
        rc, out = run_validator()
        ok = rc == 0
        print("%-22s exit=%d => %s（只改注释仍绿）" % ("P4_只改注释", rc, "PASS" if ok else "FAIL"))
        results.append(("P4_只改注释", "exit=%d" % rc, 0, "-", ok))
    finally:
        open(TARGET, "wb").write(b)
        same = open(TARGET, "rb").read() == b
        print("   restored: bytes_equal=%s sha256=%s" % (same, sha(open(TARGET, "rb").read())))
        if not same:
            raise SystemExit("restore failed for P4")

    final_sha = sha(open(TARGET, "rb").read())
    print("final sha256 =", final_sha, "== baseline:", final_sha == base_sha)

    bad = [r for r in results if len(r) == 5 and not r[-1]]
    bad += [r for r in results if len(r) < 5]
    print("cases =", len(results), "failed =", len(bad))
    for r in results:
        print("  ", r)
    return 1 if (bad or final_sha != base_sha) else 0


if __name__ == "__main__":
    sys.exit(main())
