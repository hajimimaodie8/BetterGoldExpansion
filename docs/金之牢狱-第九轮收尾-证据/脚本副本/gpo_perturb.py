# -*- coding: utf-8 -*-
"""第十轮扰动（4 用例：3 红 + 1 绿），逐字节复原 + SHA256 自证。

跑法（工作区自带 Python）：<dsh python> probe\\gpo\\gpo_perturb.py

用例：
  P1 「全部件 bbox 当墙」去掉：删掉 floodAir 里的 `if (walls != null && walls.blocked(n)) { continue; }`
  P2 「相邻禁止」去掉：`candBox.inflatedBy(1)` -> `candBox`
  P3 「旧 3×3 通道可走」改回旧口径：oldBlocked 循环的 `!"minecraft:air".equals(...)` -> `!c.pos.equals(seed)`
  P4 只改注释：末尾追加一行 `// P4 perturbation: comment only`
"""
import hashlib
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "worldgen",
                    "GoldenPrisonStructure.java")
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
PY = sys.executable

CASES = [
    ("P1_去墙集", """                if (walls != null && walls.blocked(n)) {
                    continue;
                }
""", "", "red"),
    ("P2_去相邻禁止", "candBox.inflatedBy(1)", "candBox", "red"),
    ("P3_旧通道改回全挡", """            if (!"minecraft:air".equals(c.cell.placedBlockId())) {
                oldBlocked.add(pack(c.pos));
            }""", """            if (!c.pos.equals(seed)) {
                oldBlocked.add(pack(c.pos));
            }""", "red"),
    ("P4_只改注释", "    /** 已处理过的件", "    // P4 perturbation: comment only\n    /** 已处理过的件", "green"),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_gate():
    p = subprocess.run([PY, GATE], cwd=ROOT, capture_output=True)
    out = ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "replace")
    line = ""
    for l in out.splitlines():
        if l.startswith("[bgp-fail]") or l.startswith("[bgp-ok]"):
            line = l.strip()
    codes = sorted(set(re.findall(r"\[bgp\] NG \[([a-z0-9-]+)\]", out)))
    return p.returncode, line, codes


def main():
    base = open(JAVA, "rb").read()
    base_sha = sha(base)
    print("baseline", len(base), "B", base_sha)
    rc0, line0, codes0 = run_gate()
    print("baseline gate: exit=%d %s codes=%s" % (rc0, line0, codes0))
    if rc0 != 0:
        print("!! 基线不是全绿，扰动只能做差分判读")
    rows = []
    ok_all = True
    for name, old, new, want in CASES:
        text = base.decode("utf-8")
        n = text.count(old)
        if n != 1:
            print("!! %s 命中 %d 次（期望 1）" % (name, n))
            ok_all = False
            continue
        open(JAVA, "wb").write(text.replace(old, new, 1).encode("utf-8"))
        rc, line, codes = run_gate()
        open(JAVA, "wb").write(base)  # 逐字节复原
        back = open(JAVA, "rb").read()
        equal = back == base and sha(back) == base_sha
        if want == "red":
            good = rc == 1 and "bgp-exit-air" in codes and (not codes0 or rc > rc0 or len(codes) > len(codes0)
                                                           or line != line0)
        else:
            good = rc == rc0 and codes == codes0
        ok_all &= good and equal
        rows.append("| %s | %s | exit=%d %s codes=%s | bytes_equal=%s SHA256=%s | %s |"
                    % (name, "红" if want == "red" else "绿", rc, line, codes, equal, sha(back) == base_sha,
                       "PASS" if good and equal else "FAIL"))
        print(rows[-1])
    print("\n".join(rows))
    out = os.path.join(ROOT, "build", "gpo_perturb.txt")
    open(out, "w", encoding="utf-8", newline="\n").write(
        "baseline bytes=%d sha256=%s; gate exit=%d %s\n\n" % (len(base), base_sha, rc0, line0)
        + "\n".join(rows) + "\n\nall_pass=%s\n" % ok_all)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
