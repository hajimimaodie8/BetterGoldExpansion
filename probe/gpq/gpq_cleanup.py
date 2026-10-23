# -*- coding: utf-8 -*-
"""收尾：探针删前留档 → 整块删除 → 开关/结果文件删除 → grep 零命中。

留档：docs/gpq-证据/07-GpqProbe.java.txt（源码副本）+ 08-探针清理.txt（grep 与删除清单）
⚠ 只删本轮的探针文件：src 下的 GpqProbe.java、run/gpq-probe.enabled、run/probe/gpq/ 目录。
"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVID = os.path.join(ROOT, "docs", "gpq-证据")
SRC = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "GpqProbe.java")
PROBE_DIR = os.path.dirname(SRC)
SWITCH = os.path.join(ROOT, "run", "gpq-probe.enabled")
RUN_OUT = os.path.join(ROOT, "run", "probe", "gpq")
MASTER = os.path.join(HERE, "GpqProbe.java.txt")

report = []


def log(s):
    print(s, flush=True)
    report.append(s)


def main():
    os.makedirs(EVID, exist_ok=True)
    assert SRC.startswith(ROOT) and SWITCH.startswith(ROOT) and RUN_OUT.startswith(ROOT)
    # ---- 1) 删前留档
    dest = os.path.join(EVID, "07-GpqProbe.java.txt")
    shutil.copyfile(MASTER, dest)
    log("留档 %s  %d B  SHA256 %s" % (os.path.relpath(dest, ROOT), os.path.getsize(dest),
                                       hashlib.sha256(open(dest, "rb").read()).hexdigest().upper()))
    if os.path.exists(SRC):
        log("src 里的探针与留档一致 = %s" % (
            hashlib.sha256(open(SRC, "rb").read()).hexdigest()
            == hashlib.sha256(open(MASTER, "rb").read()).hexdigest()))
    # ---- 2) 删除
    if os.path.exists(SRC):
        os.remove(SRC)
        log("deleted " + os.path.relpath(SRC, ROOT))
    # probe 包目录：只有在空的时候才删（别误删别人的东西）
    if os.path.isdir(PROBE_DIR) and not os.listdir(PROBE_DIR):
        os.rmdir(PROBE_DIR)
        log("rmdir " + os.path.relpath(PROBE_DIR, ROOT))
    elif os.path.isdir(PROBE_DIR):
        log("!! probe 目录非空，保留：" + repr(os.listdir(PROBE_DIR)))
    if os.path.exists(SWITCH):
        os.remove(SWITCH)
        log("deleted " + os.path.relpath(SWITCH, ROOT))
    if os.path.isdir(RUN_OUT):
        shutil.rmtree(RUN_OUT)
        log("rmtree " + os.path.relpath(RUN_OUT, ROOT))
    # ---- 3) grep 零命中
    needles = ("GpqProbe", "gpq-probe", "BG-PROBE", "probe/gpq")
    hits = []
    for base, dirs, files in os.walk(os.path.join(ROOT, "src")):
        dirs[:] = [d for d in dirs if d not in ("build", ".git")]
        for f in files:
            p = os.path.join(base, f)
            try:
                data = open(p, "rb").read()
            except OSError:
                continue
            for n in needles:
                if n.encode() in data:
                    hits.append((os.path.relpath(p, ROOT), n))
    for n in needles:
        log("grep %-12s in src/ = %d" % (n, sum(1 for h in hits if h[1] == n)))
    for h in hits:
        log("  !! hit %r %r" % h)
    out = os.path.join(EVID, "08-探针清理.txt")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(report) + "\n")
    log("wrote " + os.path.relpath(out, ROOT))
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
