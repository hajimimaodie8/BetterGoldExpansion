# -*- coding: utf-8 -*-
"""bg22 收尾：归档证据 + 探针残留 / 共享文件 / run\\ / 存档核对。"""
import hashlib
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EVID = os.path.join(ROOT, "docs", "bg22-证据")
BUILD = os.path.join(ROOT, "build")


def sha(path):
    path = os.path.join(ROOT, path)
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper() if os.path.isfile(path) else "<missing>"


def run(args, shell=False):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, shell=shell)
    return (p.stdout + p.stderr).decode("utf-8", "replace").strip()


def git(*args):
    return run(["git"] + list(args))


def main():
    os.makedirs(EVID, exist_ok=True)

    # ① 八关卡原件 / 构建原件
    shutil.copyfile(os.path.join(BUILD, "bg22-gates.txt"), os.path.join(EVID, "04-八关卡.txt"))
    bl = open(os.path.join(BUILD, "bg22_build.log"), "rb").read()
    be = open(os.path.join(BUILD, "bg22_build.err"), "rb").read() if os.path.exists(
        os.path.join(BUILD, "bg22_build.err")) else b""
    with open(os.path.join(EVID, "05-构建.txt"), "wb") as f:
        f.write(b"$ .\\gradlew.bat build\n")
        f.write(bl)
        f.write(b"\n--- stderr ---\n")
        f.write(be)

    # ② runserver 日志摘录（最后一次 = 改前 A 级那一次；改后读数见 02）
    log = os.path.join(ROOT, "run", "logs", "latest.log")
    if os.path.isfile(log):
        text = open(log, "rb").read().decode("utf-8", "replace")
        hits = [ln for ln in text.splitlines() if "[bg22-s]" in ln or "Bg22Probe" in ln]
        with open(os.path.join(EVID, "06-服务端日志摘录.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(hits) + "\n")

    # ③ 收尾核对
    lines = []
    add = lines.append
    add("bg22 收尾核对（2026-11-10）")
    add("=" * 72)
    add("")
    add("[1] git status --porcelain（不 commit / 不 push）")
    add(git("status", "--porcelain"))
    add("")
    add("[2] git diff --stat")
    add(git("diff", "--stat"))
    add("")
    add("[3] 文档：插入/删除行（删除必须 = 0）")
    add(git("diff", "--numstat", "--", "docs/1.7-混沌金与崩乱合金-需求立档.md"))
    add("")
    add("[4] 关键文件 SHA256")
    for f in ("build.gradle", "run/server.properties",
              "src/main/resources/bettergold.mixins.json",
              "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java",
              "tools/asset-generator/validate_metal_data.py",
              "docs/1.7-混沌金与崩乱合金-需求立档.md",
              "build/libs/bettergold-1.7.0.jar"):
        add("  %-74s %s" % (f, sha(f)))
    add("")
    add("[5] 复原判据（开工基线）")
    add("  build.gradle                         期望 2AAC7860E5B1F03128D42637B9F002C7A44F37E269EE6B7BC9DFBE41AD478C2F")
    add("  run/server.properties                期望 A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4 (1440 B)")
    add("  bettergold.mixins.json               期望 FB89F4CA7FA21745BEED8F73DA3259ED8FDC58B5733FDAAAE063D2165A4C26BD (354 B)")
    add("")
    add("[6] 探针残留 grep（src / run / 产物）")
    for pat in ("Bg22Probe", "bg22-probe", "probe.bg22", "BG-PROBE"):
        hits = run('findstr /s /i /m /c:"%s" src\\main\\java\\*.java src\\main\\resources\\*.*' % pat,
                   shell=True)
        add("  findstr %-14s -> %s" % (pat, hits if hits else "0 命中"))
    add("  probe/bg22 exists: %s" % os.path.isdir(os.path.join(ROOT, "probe", "bg22")))
    add("  src/.../probe/bg22 exists: %s" % os.path.isdir(
        os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "bg22")))
    add("  run/bg22-probe.enabled exists: %s" % os.path.exists(os.path.join(ROOT, "run", "bg22-probe.enabled")))
    add("")
    add("[7] run/ 独占：本轮从来没有别人的 run 进程；本会话从未 Stop-Process / taskkill")
    add(run('tasklist /FI "IMAGENAME eq java.exe"', shell=True) or "  （无 java.exe）")
    add("")
    add("[8] 作者存档 run/saves/新的世界 文件数（开工 29 / 收尾应仍 29；本轮从未打开）")
    saves = os.path.join(ROOT, "run", "saves")
    for d in sorted(os.listdir(saves)):
        p = os.path.join(saves, d)
        n = sum(len(fs) for _, _, fs in os.walk(p)) if os.path.isdir(p) else 0
        add("  %-14s files=%d" % (d, n))
    add("")
    add("[9] run/world forceload（关卡 check_forced_chunks.py 已判过；这里再看一眼）")
    add("  " + run("findstr /s /i /c:\"Forced\" run\\world\\data\\*.dat", shell=True)[:200]
        if os.path.isdir(os.path.join(ROOT, "run", "world")) else "  （无 run/world）")
    add("")
    add("[10] 证据目录")
    for f in sorted(os.listdir(EVID)):
        p = os.path.join(EVID, f)
        if os.path.isfile(p):
            add("  %-40s %d B" % (f, os.path.getsize(p)))
        else:
            add("  %-40s <dir>" % f)

    out = os.path.join(EVID, "07-收尾核对.txt")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
