#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_run_prep.py —— 轮9 A 级探针的 install / cleanup / prep / verify 四用。

用法：
  py -3 bgn10r9_run_prep.py prep      # 跑前留档（server.properties 字节备份 + run/saves 清单摘要）+ 开关文件
  py -3 bgn10r9_run_prep.py install   # 把两个探针拷进 src 并注入 bettergold.java（逐字节复原靠 .bak）
  py -3 bgn10r9_run_prep.py cleanup   # 按备份逐字节复原 + 删探针 + 删开关文件 + 复核 SHA
  py -3 bgn10r9_run_prep.py verify    # 复核：src 里 grep 零命中 / server.properties SHA 一致 / saves 清单一致

纪律：一律走 bytes（PowerShell 5.1 会把中文注释双重编码写坏）。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
TARGET = SRC / "bettergold.java"
PROBE_DIR = REPO / "probe" / "bgn10r9"
DST_DIR = SRC / "probe"
PROBE_FILES = ("BgN10r9Probe.java", "BgN10r9ClientProbe.java")
BAK = REPO / "build" / "bgn10r9_bettergold.java.bak"
SP = REPO / "run" / "server.properties"
SP_BAK = REPO / "run" / "server.properties.bgn10r9.bak"
SWITCH = REPO / "run" / "bgn10r9-probe.enabled"
SAVES = REPO / "run" / "saves"
RECORD = REPO / "docs" / "bgn10r9-证据" / "04-跑前留档.json"

ANCHOR = "        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.material.ImbalanceEffects.class);\n"
INJECT = ANCHOR + ("        // TEMP PROBE (轮9 A 级) —— 收尾整块删除\n"
                   "        com.hjmmd_8.bettergold.probe.BgN10r9Probe.install();\n")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def saves_digest() -> dict:
    out = {}
    if SAVES.is_dir():
        for d in sorted(p for p in SAVES.iterdir() if p.is_dir()):
            h = hashlib.sha256()
            files = sorted(q for q in d.rglob("*") if q.is_file())
            for q in files:
                h.update(str(q.relative_to(d)).encode("utf-8"))
                h.update(b"\0")
                h.update(hashlib.sha256(q.read_bytes()).digest())
            out[d.name] = {"entries": len(files), "digest": h.hexdigest().upper()}
    return out


def prep() -> None:
    if not SP_BAK.exists():
        shutil.copyfile(SP, SP_BAK)
        print("[prep] server.properties 字节备份 ->", SP_BAK.name)
    rec = {
        "server_properties_sha256": sha(SP),
        "server_properties_bytes": SP.stat().st_size,
        "saves": saves_digest(),
        "backup": SP_BAK.name,
    }
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_bytes((json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    SWITCH.write_bytes(b"")
    print("[prep] 开关文件 ->", SWITCH)
    print("[prep] 留档 ->", RECORD.relative_to(REPO), json.dumps(rec["saves"], ensure_ascii=False))


def install() -> None:
    if not BAK.exists():
        shutil.copyfile(TARGET, BAK)
    print("[install] bettergold.java 备份 sha256 =", sha(BAK))
    DST_DIR.mkdir(parents=True, exist_ok=True)
    for name in PROBE_FILES:
        shutil.copyfile(PROBE_DIR / name, DST_DIR / name)
        print("[install] probe ->", (DST_DIR / name).relative_to(REPO), sha(DST_DIR / name))
    text = TARGET.read_bytes().decode("utf-8")
    if INJECT in text:
        print("[install] already injected")
    elif ANCHOR in text:
        TARGET.write_bytes(text.replace(ANCHOR, INJECT, 1).encode("utf-8"))
        print("[install] injected")
    else:
        raise SystemExit("[install] anchor not found")
    print("[install] bettergold.java sha256 =", sha(TARGET))


def cleanup() -> None:
    # ① 先删探针源（**删前留档**：源码副本已在 docs/bgn10r9-证据/脚本副本/）
    for name in PROBE_FILES:
        p = DST_DIR / name
        if p.exists():
            p.unlink()
            print("[cleanup] 删除探针源", p.relative_to(REPO))
    if DST_DIR.is_dir() and not any(DST_DIR.iterdir()):
        DST_DIR.rmdir()
        print("[cleanup] 删除空目录", DST_DIR.relative_to(REPO))
    # ② bettergold.java 逐字节复原
    if not BAK.exists():
        raise SystemExit("[cleanup] 备份不存在，拒绝复原")
    shutil.copyfile(BAK, TARGET)
    print("[cleanup] bettergold.java 复原 sha256 =", sha(TARGET))
    # ③ server.properties 逐字节复原
    if SP_BAK.exists():
        shutil.copyfile(SP_BAK, SP)
        print("[cleanup] server.properties 复原 sha256 =", sha(SP))
    # ④ 开关文件
    if SWITCH.exists():
        SWITCH.unlink()
        print("[cleanup] 删除开关文件", SWITCH.name)


def verify() -> None:
    ok = True
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    sp_sha = sha(SP)
    if sp_sha != rec["server_properties_sha256"]:
        print("[verify] ✗ server.properties SHA 不一致：%s != %s" % (sp_sha, rec["server_properties_sha256"]))
        ok = False
    else:
        print("[verify] ✓ server.properties 逐字节复原", sp_sha)
    now = saves_digest()
    if now != rec["saves"]:
        print("[verify] ✗ run/saves 清单变了：%s -> %s" % (rec["saves"], now))
        ok = False
    else:
        print("[verify] ✓ run/saves 清单一致", json.dumps(now, ensure_ascii=False))
    hits = []
    for p in SRC.rglob("*.java"):
        t = p.read_text(encoding="utf-8")
        if "BgN10r9" in t or "BGN10R9" in t:
            hits.append(str(p.relative_to(REPO)))
    if hits:
        print("[verify] ✗ src 里仍有探针残留：", hits)
        ok = False
    else:
        print("[verify] ✓ src 里 BgN10r9 / BGN10R9 零命中")
    print("[verify] 结论：", "绿" if ok else "红")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"prep": prep, "install": install, "cleanup": cleanup, "verify": verify}.get(
        cmd, lambda: print("usage: prep|install|cleanup|verify"))()
