# -*- coding: utf-8 -*-
"""bgbig C 段：跑一次临时服务端探针（真 ServerPlayer 解锁新增成就）。

跑法（工作区自带 Python）：
    <dsh python> probe\\bgbig\\bgbig_c_run.py

与 `bgbig_run.py` 同构：独占检查 → 备份 server.properties → 拷探针 → 开关 → compileJava + runServer →
归档 report / 原始行 → 逐字节复原 server.properties。
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(ROOT, "run")
EVID = os.path.join(ROOT, "docs", "bgbig-证据")
SRC_PROBE = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe",
                         "CProbe.java")
MASTER = os.path.join(HERE, "CProbe.java.txt")
PROPS = os.path.join(RUN, "server.properties")
BAK = os.path.join(RUN, "server.properties.bgbigc.bak")
SWITCH = os.path.join(RUN, "bgbig-c-probe.enabled")
REPORT = os.path.join(RUN, "probe", "bgbig", "c-report.json")
LOG = os.path.join(RUN, "logs", "latest.log")
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
    hits = java_runs()
    print("java 里在跑的 runServer/runClient/devlaunch =", len(hits), hits[:3], flush=True)
    if hits:
        print("!! run\\ 不独占 ⇒ 拒绝执行", flush=True)
        return 2
    os.makedirs(EVID, exist_ok=True)
    base = sha(PROPS)
    shutil.copyfile(PROPS, BAK)
    if sha(BAK) != base:
        print("!! server.properties 备份不一致", flush=True)
        return 2
    os.makedirs(os.path.dirname(SRC_PROBE), exist_ok=True)
    shutil.copyfile(MASTER, SRC_PROBE)
    print("probe copied ->", os.path.relpath(SRC_PROBE, ROOT), sha(SRC_PROBE), flush=True)
    with open(SWITCH, "wb") as f:
        f.write(b"1\n")
    if os.path.exists(REPORT):
        os.remove(REPORT)

    logs = os.path.join(ROOT, "build", "bgbig_c_compile.log")
    rc = run([GRADLE, "compileJava", "--console=plain"], logs)
    if rc != 0:
        print("!! compileJava 失败，见", logs, flush=True)
        return 1
    log = os.path.join(ROOT, "build", "bgbig_c_run.log")
    rc = run([GRADLE, "runServer", "--console=plain"], log)
    print("runServer exit =", rc, "log =", os.path.relpath(log, ROOT), flush=True)

    if os.path.exists(REPORT):
        shutil.copyfile(REPORT, os.path.join(EVID, "11-C-A级-report.json"))
        print("report archived", flush=True)
    else:
        print("!! no report at", REPORT, flush=True)

    if os.path.exists(LOG):
        with io.open(LOG, encoding="utf-8", errors="replace") as f:
            lines = [l.rstrip("\n") for l in f if "[bgbig-c2]" in l]
        with io.open(os.path.join(EVID, "12-C-A级-原始行.txt"), "w", encoding="utf-8",
                     newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print("probe log lines =", len(lines), flush=True)

    shutil.copyfile(BAK, PROPS)
    now = sha(PROPS)
    print("server.properties 复原 SHA256 =", now, "== 基线?", now == base, flush=True)
    if now != base:
        return 1
    return 0 if (rc == 0 and os.path.exists(REPORT)) else 1


if __name__ == "__main__":
    sys.exit(main())
