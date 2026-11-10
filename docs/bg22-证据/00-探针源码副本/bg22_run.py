# -*- coding: utf-8 -*-
"""bg22 A 级：真 ServerPlayer + 真甜浆果丛，跑一次 runServer 读「耐久变不变」。

跑法（工作区自带 Python；禁用 py -3）：
    <dsh python> probe\\bg22\\bg22_run.py

顺序：独占检查 -> 字节备份 server.properties -> 探针源码拷进 src -> 开关文件 ->
compileJava -> runServer -> 归档读数 -> 逐字节复原 server.properties + SHA 复核。
⚠ 不删 run\\world / run\\saves；不碰别的进程；不杀任何人。
"""
import hashlib
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(ROOT, "run")
EVID = os.path.join(ROOT, "docs", "bg22-证据")
SRC_DIR = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "bg22")
SRC_PROBE = os.path.join(SRC_DIR, "Bg22Probe.java")
MASTER = os.path.join(HERE, "Bg22Probe.java.txt")
PROPS = os.path.join(RUN, "server.properties")
BAK = os.path.join(RUN, "server.properties.bg22.bak")
SWITCH = os.path.join(RUN, "bg22-probe.enabled")
READINGS = os.path.join(RUN, "probe", "bg22", "readings.txt")
GRADLE = os.path.join(ROOT, "gradlew.bat")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def run(cmd, log):
    print(">>", " ".join(cmd), flush=True)
    with open(log, "wb") as out, open(log + ".err", "wb") as err:
        p = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=err)
    print("   exit =", p.returncode, flush=True)
    return p.returncode


def java_runs():
    """列出 java.exe 命令行里带 runServer/runClient/devlaunch 的 PID（Gradle daemon 不算）。"""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | "
          "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }")
    p = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    hits = []
    for line in (p.stdout or "").splitlines():
        low = line.lower()
        if any(k in low for k in ("runserver", "runclient", "devlaunch")):
            hits.append(line.strip())
    return hits


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "after"
    assert phase in ("after", "before"), phase
    hits = java_runs()
    print("java 里在跑的 runServer/runClient/devlaunch =", len(hits), hits[:3], flush=True)
    if hits:
        print("!! run\\ 不独占（有别的 run 进程）⇒ 拒绝执行（绝不杀别人）", flush=True)
        return 2

    os.makedirs(EVID, exist_ok=True)
    base = sha(PROPS)
    shutil.copyfile(PROPS, BAK)
    print("server.properties SHA256 =", base, "字节备份 ->", os.path.basename(BAK), flush=True)
    if sha(BAK) != base:
        print("!! 备份与源不一致", flush=True)
        return 2

    os.makedirs(SRC_DIR, exist_ok=True)
    shutil.copyfile(MASTER, SRC_PROBE)
    print("probe copied ->", os.path.relpath(SRC_PROBE, ROOT), sha(SRC_PROBE), flush=True)

    with open(SWITCH, "wb") as f:
        f.write(b"1\n")
    if os.path.exists(READINGS):
        os.remove(READINGS)

    logs = os.path.join(ROOT, "build", "bg22_compile.log")
    rc = run([GRADLE, "compileJava", "--console=plain"], logs)
    if rc != 0:
        print("!! compileJava 失败，见", logs, flush=True)
        return 1

    log = os.path.join(ROOT, "build", "bg22_runserver.log")
    rc = run([GRADLE, "runServer", "--console=plain"], log)
    print("runServer exit =", rc, "log =", os.path.relpath(log, ROOT), flush=True)

    ok = False
    if os.path.exists(READINGS):
        archive = os.path.join(EVID, "00-A级-改前.txt" if phase == "before" else "02-A级-改后.txt")
        shutil.copyfile(READINGS, archive)
        print("readings archived ->", os.path.relpath(archive, ROOT),
              os.path.getsize(READINGS), "B", flush=True)
        ok = True
    else:
        print("!! no readings at", READINGS, flush=True)

    # 复原 server.properties（逐字节）
    shutil.copyfile(BAK, PROPS)
    now = sha(PROPS)
    print("server.properties 复原 SHA256 =", now, "== 基线?", now == base, flush=True)
    if now != base:
        print("!! server.properties 没复原", flush=True)
        return 1
    if ok:
        text = open(READINGS, "rb").read().decode("utf-8", "replace")
        summary = [ln for ln in text.splitlines() if ln.startswith("SUMMARY")]
        print("SUMMARY:", summary, flush=True)
        faults = [ln for ln in text.splitlines() if ln.startswith("FAIL")]
        print("FAIL 行数 =", len(faults), faults[:4], flush=True)
        if phase == "after":
            ok = not faults
    return 0 if (rc == 0 and ok) else 1


if __name__ == "__main__":
    sys.exit(main())
