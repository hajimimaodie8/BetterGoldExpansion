# -*- coding: utf-8 -*-
"""轮5 A 级探针：install / cleanup 两用（一律走 bytes，逐字节复原）。
用法：
  py -3 bgn10r5_install_probe.py install
  py -3 bgn10r5_install_probe.py cleanup
"""
import hashlib
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
TARGET = SRC / "bettergold.java"
PROBE_SRC = REPO / "probe" / "bgn10r5" / "BgN10r5Probe.java"
PROBE_DST = SRC / "probe" / "BgN10r5Probe.java"
BAK = REPO / "build" / "bgn10r5_bettergold.java.bak"

ANCHOR = ("        NeoForge.EVENT_BUS.register("
          "com.hjmmd_8.bettergold.event.VillageTrades.class);\n")
INJECT = ANCHOR + ("        // TEMP PROBE (轮5 A 级) —— 收尾整块删除\n"
                   "        com.hjmmd_8.bettergold.probe.BgN10r5Probe.install();\n")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def install():
    if not BAK.exists():
        shutil.copyfile(TARGET, BAK)
    print("[bak] target sha256 =", sha(BAK))
    PROBE_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PROBE_SRC, PROBE_DST)
    print("[probe] copied ->", PROBE_DST.relative_to(REPO), "sha256 =", sha(PROBE_DST))
    text = TARGET.read_bytes().decode("utf-8")
    if INJECT in text:
        print("[install] already present")
    elif ANCHOR in text:
        TARGET.write_bytes(text.replace(ANCHOR, INJECT, 1).encode("utf-8"))
        print("[install] injected")
    else:
        raise SystemExit("[install] anchor not found")
    print("[now] bettergold.java sha256 =", sha(TARGET))


def cleanup():
    if not BAK.exists():
        raise SystemExit("[cleanup] 备份不存在，拒绝复原")
    shutil.copyfile(BAK, TARGET)
    print("[cleanup] bettergold.java 已按备份逐字节复原 sha256 =", sha(TARGET))
    if PROBE_DST.exists():
        PROBE_DST.unlink()
        print("[cleanup] 探针源已删除 ->", PROBE_DST.relative_to(REPO))
    probe_dir = PROBE_DST.parent
    if probe_dir.is_dir() and not any(probe_dir.iterdir()):
        probe_dir.rmdir()
        print("[cleanup] 空目录已删除 ->", probe_dir.relative_to(REPO))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"install": install, "cleanup": cleanup}.get(cmd, lambda: print("usage: install|cleanup"))()
