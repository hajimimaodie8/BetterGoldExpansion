# -*- coding: utf-8 -*-
"""掉落大样本探针：证据搬运 + 整块删除 + bettergold.java/server.properties 逐字节复原。"""
import hashlib
import pathlib
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
REPO = pathlib.Path(__file__).resolve().parents[1]
ev = REPO / "docs" / "bgn10r6-证据"

probe = REPO / "src/main/java/com/hjmmd_8/bettergold/probe/BgN10r6DropsProbe.java"
shutil.copyfile(probe, ev / "脚本副本" / "BgN10r6DropsProbe.java.txt")
print("[ev] probe copy", (ev / "脚本副本" / "BgN10r6DropsProbe.java.txt").stat().st_size, "B")

log = (REPO / "build/bgn10r6d_runserver.out").read_bytes().splitlines()


def dec(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gbk", errors="replace")


lines = [dec(l) for l in log if b"BGN10R6DROPS" in l]
(ev / "01b-A级-掉落大样本.txt").write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
print("[ev] readings 01b", len(lines), "lines")

probe.unlink()
print("[del] probe", probe.relative_to(REPO))
pdir = probe.parent
if pdir.exists() and not any(pdir.iterdir()):
    pdir.rmdir()
    print("[del] empty dir")

target = REPO / "src/main/java/com/hjmmd_8/bettergold/bettergold.java"
backup = REPO / "build/bgn10r6_bettergold.java.bak"
shutil.copyfile(backup, target)
sha = hashlib.sha256(target.read_bytes()).hexdigest().upper()
print("[restore] bettergold.java", sha)
assert sha == "9B639100D4F307875357BA0AC9B2BD94449E3C1E809DFA0210F955EED4FA8755"

switch = REPO / "run/bgn10r6d-probe.enabled"
if switch.exists():
    switch.unlink()
    print("[del] switch")

props = REPO / "run/server.properties"
bak = REPO / "run/server.properties.bgn10r6d.bak"
print("[props] before", hashlib.sha256(props.read_bytes()).hexdigest().upper()[:16])
shutil.copyfile(bak, props)
print("[props] after ", hashlib.sha256(props.read_bytes()).hexdigest().upper())
