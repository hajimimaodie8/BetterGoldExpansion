#!/usr/bin/env python3
"""bg21 perturbation matrix (temporary; probe/bg21 is deleted at closeout).

3 cases: 2 red (a pin reverted / the frozen after-snapshot reordered) + 1 green (comment only).
Every case: assert the mutation actually landed, run validate_metal_data.py, print
[exit, hit_expected, key counts], restore bytes and verify SHA256, then re-run to confirm green.
"""

import hashlib
import os
import subprocess
import sys
import builtins
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JAVA = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "material" / "CreativeTabSections.java"
AFTER = REPO / "tools" / "asset-generator" / "bg21-creative-order-after.txt"
VAL = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
PY = sys.executable
_LOG = (REPO / "build" / "bg21-perturb.txt").open("w", encoding="utf-8")


def log(msg):
    _LOG.write(msg + "\n")
    _LOG.flush()
    # 控制台是 GBK：只打 ASCII（中文读文件），避免 UnicodeEncodeError
    builtins.print(msg.encode("ascii", "backslashreplace").decode("ascii"))


print = log  # noqa: A001  （本脚本里所有 print 都走 UTF-8 文件 + ASCII 控制台）


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def run_gate():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"   # 让子进程的中文按 UTF-8 落文件（控制台是 GBK）
    r = subprocess.run([PY, str(VAL)], cwd=str(REPO), capture_output=True, env=env)
    out = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    summary = next((ln.strip() for ln in out.splitlines() if "[bg21-summary]" in ln), "<no bg21-summary>")
    tags = sorted({t for t in ("bg21-creative-pins", "bg21-creative-order", "bg21-creative-ids",
                               "bg21-doc", "bg21-anti-vacuum") if "[%s]" % t in out})
    return r.returncode, summary, tags


def mutate_pin(raw: bytes):
    old = b'new Pin("golden_bone_meal", "golden_shield_blank", true)'
    new = b'new Pin("golden_bone_meal", "golden_shield_blank", false)'
    if raw.count(old) != 1:
        return None
    return raw.replace(old, new, 1)


def mutate_snapshot(raw: bytes):
    lines = raw.decode("utf-8").splitlines(keepends=True)
    idx_oil = next((k for k, ln in enumerate(lines) if "bettergold:refined_alchemic_oil" in ln), None)
    idx_shield = next((k for k, ln in enumerate(lines) if "bettergold:golden_shield_blank" in ln), None)
    if idx_oil is None or idx_shield is None:
        return None
    seq_oil, id_oil = lines[idx_oil].split(" ", 1)
    seq_shield, id_shield = lines[idx_shield].split(" ", 1)
    lines[idx_oil] = seq_oil + " " + id_shield
    lines[idx_shield] = seq_shield + " " + id_oil
    return "".join(lines).encode("utf-8")


def mutate_comment(raw: bytes):
    needle = "    // ==================== 顺序微调：5 条".encode("utf-8")
    if raw.count(needle) != 1:
        return None
    return raw.replace(needle, needle + b"\r\n    // bg21 perturbation: comment only (must stay green)", 1)


CASES = [
    ("A_pin_reverted", JAVA, mutate_pin, 1, "bg21-creative-pins"),
    ("B_snapshot_reordered", AFTER, mutate_snapshot, 1, "bg21-creative-order"),
    ("C_comment_only", JAVA, mutate_comment, 0, ""),
]


def main() -> int:
    base_java, base_after = sha(JAVA), sha(AFTER)
    print("BASELINE java=%s after=%s" % (base_java, base_after))
    code, summary, tags = run_gate()
    print("BASELINE gate exit=%d hits=%s\n  %s" % (code, tags, summary))
    if code != 0:
        print("ERROR: baseline is not green")
        return 2

    ok_all = True
    for name, path, fn, want_exit, want_tag in CASES:
        base = sha(path)
        raw = path.read_bytes()
        mutated = fn(raw)
        if mutated is None or mutated == raw:
            print("CASE %s: ERROR mutation would not land" % name)
            ok_all = False
            continue
        path.write_bytes(mutated)
        code, summary, tags = run_gate()
        hit = code == want_exit and (want_tag in tags if want_tag else not tags)
        print("CASE %-22s mutated=%s exit=%d expected_exit=%d hits=%s hit_expected=%s"
              % (name, sha(path)[:12], code, want_exit, tags, hit))
        print("   %s" % summary)
        ok_all = ok_all and hit
        path.write_bytes(raw)
        restored = sha(path) == base
        print("   restored=%s sha=%s" % (restored, sha(path)))
        ok_all = ok_all and restored

    print("FINAL java=%s (baseline=%s) after=%s (baseline=%s)"
          % (sha(JAVA), base_java, sha(AFTER), base_after))
    code, summary, tags = run_gate()
    print("FINAL gate exit=%d hits=%s\n  %s" % (code, tags, summary))
    ok_all = ok_all and code == 0 and sha(JAVA) == base_java and sha(AFTER) == base_after
    print("SUMMARY cases=%d all_ok=%s" % (len(CASES), ok_all))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
