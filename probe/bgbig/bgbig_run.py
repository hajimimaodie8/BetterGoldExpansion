# -*- coding: utf-8 -*-
"""bgbig A3：跑一次临时服务端探针（巫毒爆发伤害类型 / 护甲对照）。

跑法（工作区自带 Python；不用 py -3）：
    <dsh python> probe\\bgbig\\bgbig_run.py

做的事（任一步失败就非 0 退出）：
  1) 独占检查：java.exe 命令行里若有 runServer / runClient / devlaunch ⇒ 拒绝执行（绝不杀别人的进程）；
  2) 字节备份 run\\server.properties -> run\\server.properties.bgbig.bak（记录 SHA256）；
  3) 把 probe/bgbig/VoodooProbe.java.txt 拷进 src（唯一真源在 probe/bgbig/，src 是副本，收尾整块删）；
  4) 放开关文件 run\\bgbig-probe.enabled；
  5) gradlew compileJava 然后 runServer（串行，各自等退出码）；
  6) 归档 run\\probe\\bgbig\\report.json -> docs\\bgbig-证据\\01-A3-report.json；
     并把 run/logs/latest.log 里 `[bgbig-a3]` 行抽成 docs\\bgbig-证据\\00-探针原始行.txt（UTF-8）；
  7) 逐字节复原 server.properties 并复核 SHA256。
⚠ 不删 run\\world / run\\saves；不碰别的进程；不 commit / 不 push。
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
                         "VoodooProbe.java")
MASTER = os.path.join(HERE, "VoodooProbe.java.txt")
PROPS = os.path.join(RUN, "server.properties")
BAK = os.path.join(RUN, "server.properties.bgbig.bak")
SWITCH = os.path.join(RUN, "bgbig-probe.enabled")
REPORT = os.path.join(RUN, "probe", "bgbig", "report.json")
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
        print("!! run\\ 不独占（有别的 run 进程）⇒ 拒绝执行", flush=True)
        return 2

    os.makedirs(EVID, exist_ok=True)
    base = sha(PROPS)
    shutil.copyfile(PROPS, BAK)
    print("server.properties SHA256 =", base, "字节备份 ->", os.path.basename(BAK), flush=True)
    if sha(BAK) != base:
        print("!! 备份与源不一致", flush=True)
        return 2

    os.makedirs(os.path.dirname(SRC_PROBE), exist_ok=True)
    shutil.copyfile(MASTER, SRC_PROBE)
    print("probe copied ->", os.path.relpath(SRC_PROBE, ROOT), sha(SRC_PROBE), flush=True)

    with open(SWITCH, "wb") as f:
        f.write(b"1\n")
    if os.path.exists(REPORT):
        os.remove(REPORT)

    logs = os.path.join(ROOT, "build", "bgbig_compile.log")
    rc = run([GRADLE, "compileJava", "--console=plain"], logs)
    if rc != 0:
        print("!! compileJava 失败，见", logs, flush=True)
        return 1
    log = os.path.join(ROOT, "build", "bgbig_run.log")
    rc = run([GRADLE, "runServer", "--console=plain"], log)
    print("runServer exit =", rc, "log =", os.path.relpath(log, ROOT), flush=True)

    if os.path.exists(REPORT):
        shutil.copyfile(REPORT, os.path.join(EVID, "01-A3-report.json"))
        print("report archived ->", os.path.relpath(os.path.join(EVID, "01-A3-report.json"), ROOT),
              os.path.getsize(REPORT), "B", flush=True)
    else:
        print("!! no report at", REPORT, flush=True)

    if os.path.exists(LOG):
        with io.open(LOG, encoding="utf-8", errors="replace") as f:
            lines = [l.rstrip("\n") for l in f if "[bgbig-a3]" in l]
        with io.open(os.path.join(EVID, "00-探针原始行.txt"), "w", encoding="utf-8",
                     newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print("probe log lines =", len(lines), flush=True)

    shutil.copyfile(BAK, PROPS)
    now = sha(PROPS)
    print("server.properties 复原 SHA256 =", now, "== 基线?", now == base, flush=True)
    if now != base:
        print("!! server.properties 没复原", flush=True)
        return 1
    return 0 if (rc == 0 and os.path.exists(REPORT)) else 1


if __name__ == "__main__":
    sys.exit(main())
