#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10hv_prep.py —— 1.7 手册渲染验证轮（bgn10hv）的 prep / install / cleanup / verify。

用法：
  py -3 bgn10hv_prep.py prep      # 跑前留档 + server.properties 字节备份 + level-name -> bgn10hvgen
  py -3 bgn10hv_prep.py install   # 探针源码拷进 src/probe + bettergold.java 注入 grep 锚点 + 开关文件
  py -3 bgn10hv_prep.py patchbd   # build.gradle 的 runs.client 临时加 quickPlay 两个参数（字节改）
  py -3 bgn10hv_prep.py cleanup   # 探针/注入/build.gradle/server.properties 全部逐字节复原 + 删开关
  py -3 bgn10hv_prep.py verify    # 复核 SHA + saves 清单 + src grep 零命中

纪律（全仓红线）：
  * 一律走 bytes（PowerShell 5.1 的 Get-Content/Set-Content 会把中文注释双重编码写坏）；
  * 绝不打开 / 绝不改动作者的 `run/saves/新的世界`；
  * `server.properties` 与 `build.gradle` **改前 .bak 字节复制**，复原后核对 SHA256。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SRC = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
TARGET = SRC / "bettergold.java"
DST_DIR = SRC / "probe"
PROBE_FILES = ("Bgn10hvGenProbe.java", "Bgn10hvClientProbe.java")
BAK_JAVA = REPO / "build" / "bgn10hv_bettergold.java.bak"
BD = REPO / "build.gradle"
BAK_BD = REPO / "build" / "bgn10hv_build.gradle.bak"
SP = REPO / "run" / "server.properties"
SP_BAK = REPO / "run" / "server.properties.bgn10hv.bak"
SWITCH_GEN = REPO / "run" / "bgn10hv-gen.enabled"
SWITCH_CLIENT = REPO / "run" / "bgn10hv-probe.enabled"
SAVES = REPO / "run" / "saves"
EVID = REPO / "docs" / "bgn10hv-证据"
RECORD = EVID / "04-跑前留档.json"

LEVEL_NAME_OLD = b"level-name=world\r\n"
LEVEL_NAME_NEW = b"level-name=bgn10hvgen\r\n"

BD_OLD = (b"            systemProperty 'neoforge.enabledGameTestNamespaces', project.mod_id\n"
          b"        }\n\n        server {")
BD_NEW = (b"            systemProperty 'neoforge.enabledGameTestNamespaces', project.mod_id\n"
          b"\n            // TEMP PROBE (bgn10hv \xe9\xaa\x8c\xe8\xaf\x81\xe8\xbd\xae) \xe2\x80\x94\xe2\x80\x94 "
          b"\xe6\x94\xb6\xe5\xb0\xbe\xe9\x80\x90\xe5\xad\x97\xe8\x8a\x82\xe5\xa4\x8d\xe5\x8e\x9f\n"
          b"            programArguments.addAll '--quickPlayPath', 'logs/quickplay/bgn10hv.json', "
          b"'--quickPlaySingleplayer', 'bgn10hvcw'\n"
          b"        }\n\n        server {")

ANCHOR = b"        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.material.ImbalanceEffects.class);\n"
INJECT = ANCHOR + (b"        // TEMP PROBE (bgn10hv) \xe2\x80\x94\xe2\x80\x94 \xe6\x94\xb6\xe5\xb0\xbe\xe6\x95\xb4\xe5\x9d\x97\xe5\x88\xa0\xe9\x99\xa4\n"
                   b"        com.hjmmd_8.bettergold.probe.Bgn10hvGenProbe.install();\n")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def saves_listing() -> dict:
    out = {}
    if SAVES.is_dir():
        for d in sorted(p for p in SAVES.iterdir() if p.is_dir()):
            files = sorted(q for q in d.rglob("*") if q.is_file())
            h = hashlib.sha256()
            mtimes = []
            for q in files:
                h.update(str(q.relative_to(d)).encode("utf-8"))
                h.update(b"\0")
                h.update(hashlib.sha256(q.read_bytes()).digest())
                mtimes.append(int(q.stat().st_mtime))
            out[d.name] = {
                "files": len(files),
                "max_mtime": max(mtimes) if mtimes else 0,
                "digest": h.hexdigest().upper(),
            }
    return out


def prep() -> None:
    if not SP_BAK.exists():
        shutil.copyfile(SP, SP_BAK)
        print("[prep] server.properties 字节备份 ->", SP_BAK.name, sha(SP_BAK))
    EVID.mkdir(parents=True, exist_ok=True)
    rec = {
        "head": (__import__("subprocess").run(["git", "log", "--oneline", "-1"], cwd=REPO,
                                              capture_output=True, text=True, encoding="utf-8",
                                              errors="replace").stdout or "").strip(),
        "server_properties_sha256": sha(SP),
        "server_properties_bytes": SP.stat().st_size,
        "build_gradle_sha256": sha(BD),
        "moddev_runargs": {p.name: sha(p) for p in sorted((REPO / "build" / "moddev").glob("*.txt"))},
        "saves": saves_listing(),
        "level_name_before": "world",
    }
    RECORD.write_bytes((json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print("[prep] 留档 ->", RECORD.relative_to(REPO))
    print("[prep] server.properties SHA256 =", rec["server_properties_sha256"])
    print("[prep] build.gradle SHA256 =", rec["build_gradle_sha256"])
    for k, v in rec["saves"].items():
        print("[prep] saves/%s files=%d max_mtime=%d digest=%s" % (k, v["files"], v["max_mtime"], v["digest"]))

    data = SP.read_bytes()
    if LEVEL_NAME_NEW in data:
        print("[prep] level-name 已是 bgn10hvgen（幂等）")
    elif LEVEL_NAME_OLD in data:
        SP.write_bytes(data.replace(LEVEL_NAME_OLD, LEVEL_NAME_NEW, 1))
        print("[prep] level-name world -> bgn10hvgen；新 SHA256 =", sha(SP))
    else:
        raise SystemExit("[prep] 找不到 level-name=world，拒绝乱改")


def install() -> None:
    if not BAK_JAVA.exists():
        shutil.copyfile(TARGET, BAK_JAVA)
    print("[install] bettergold.java 备份 sha256 =", sha(BAK_JAVA))
    DST_DIR.mkdir(parents=True, exist_ok=True)
    for name in PROBE_FILES:
        shutil.copyfile(HERE / name, DST_DIR / name)
        print("[install] probe ->", (DST_DIR / name).relative_to(REPO), sha(DST_DIR / name))
    text = TARGET.read_bytes()
    if INJECT in text:
        print("[install] bettergold.java 已注入（幂等）")
    elif ANCHOR in text:
        TARGET.write_bytes(text.replace(ANCHOR, INJECT, 1))
        print("[install] bettergold.java 已注入；新 sha256 =", sha(TARGET))
    else:
        raise SystemExit("[install] 注入锚点没找到")
    SWITCH_GEN.write_bytes(b"")
    SWITCH_CLIENT.write_bytes(b"")
    print("[install] 开关文件 ->", SWITCH_GEN.name, SWITCH_CLIENT.name)


def patchbd() -> None:
    if not BAK_BD.exists():
        shutil.copyfile(BD, BAK_BD)
        print("[patchbd] build.gradle 字节备份 sha256 =", sha(BAK_BD))
    data = BD.read_bytes()
    if BD_NEW in data:
        print("[patchbd] build.gradle 已打补丁（幂等）")
    elif BD_OLD in data:
        BD.write_bytes(data.replace(BD_OLD, BD_NEW, 1))
        print("[patchbd] build.gradle 已打补丁；新 sha256 =", sha(BD))
    else:
        raise SystemExit("[patchbd] 锚点没找到，拒绝乱改")


def cleanup() -> None:
    for name in PROBE_FILES:
        p = DST_DIR / name
        if p.exists():
            p.unlink()
            print("[cleanup] 删除探针源", p.relative_to(REPO))
    if DST_DIR.is_dir() and not any(DST_DIR.iterdir()):
        DST_DIR.rmdir()
        print("[cleanup] 删除空目录", DST_DIR.relative_to(REPO))
    if BAK_JAVA.exists():
        shutil.copyfile(BAK_JAVA, TARGET)
        print("[cleanup] bettergold.java 逐字节复原 sha256 =", sha(TARGET))
    if BAK_BD.exists():
        shutil.copyfile(BAK_BD, BD)
        print("[cleanup] build.gradle 逐字节复原 sha256 =", sha(BD))
    if SP_BAK.exists():
        shutil.copyfile(SP_BAK, SP)
        print("[cleanup] server.properties 逐字节复原 sha256 =", sha(SP))
    for sw in (SWITCH_GEN, SWITCH_CLIENT):
        if sw.exists():
            sw.unlink()
            print("[cleanup] 删除开关文件", sw.name)


def verify() -> None:
    ok = True
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    for label, path, key in (("server.properties", SP, "server_properties_sha256"),
                             ("build.gradle", BD, "build_gradle_sha256")):
        cur = sha(path)
        if cur != rec[key]:
            print("[verify] x %s SHA 不一致：%s != %s" % (label, cur, rec[key]))
            ok = False
        else:
            print("[verify] v %s 逐字节复原 %s" % (label, cur))
    now = saves_listing()
    if now != rec["saves"]:
        print("[verify] x run/saves 清单变了：%s -> %s" % (rec["saves"], now))
        ok = False
    else:
        print("[verify] v run/saves 清单一致 %s" % json.dumps(now, ensure_ascii=False))
    runargs = {p.name: sha(p) for p in sorted((REPO / "build" / "moddev").glob("*.txt"))}
    if runargs != rec["moddev_runargs"]:
        diff = {k: (rec["moddev_runargs"].get(k), runargs[k]) for k in runargs
                if rec["moddev_runargs"].get(k) != runargs[k]}
        print("[verify] ! build/moddev/*.txt 与跑前不同（Gradle 可能自己写回）：%s" % diff)
    else:
        print("[verify] v build/moddev/*RunProgramArgs.txt 未变（clientRunProgramArgs.txt 没被手改）")
    hits = []
    for p in SRC.rglob("*.java"):
        t = p.read_text(encoding="utf-8")
        if "Bgn10hv" in t or "BGN10HV" in t or "TEMP PROBE" in t:
            hits.append(str(p.relative_to(REPO)))
    if hits:
        print("[verify] x src 里仍有探针残留：", hits)
        ok = False
    else:
        print("[verify] v src 里 Bgn10hv / BGN10HV / TEMP PROBE 零命中")
    print("[verify] 结论：", "绿" if ok else "红")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"prep": prep, "install": install, "patchbd": patchbd,
     "cleanup": cleanup, "verify": verify}.get(cmd, lambda: print("usage: prep|install|patchbd|cleanup|verify"))()
