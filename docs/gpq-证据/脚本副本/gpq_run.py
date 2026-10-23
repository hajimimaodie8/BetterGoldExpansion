# -*- coding: utf-8 -*-
"""gpq：把一个临时服务端探针跑一遍（改前 / 改后各一次，同一份探针、同一份读数格式）。

跑法（工作区自带 Python；禁用 py -3）：
    <dsh python> probe\\gpq\\gpq_run.py before
    <dsh python> probe\\gpq\\gpq_run.py after

做的事（全部按顺序，任一步失败就非 0 退出）：
  1) 独占检查：列出 java.exe 的命令行，若有 runServer / runClient / devlaunch 在跑 ⇒ 拒绝执行；
  2) 字节备份 run\\server.properties -> run\\server.properties.gpq.bak（记录 SHA256）；
  3) 把 probe/gpq/GpqProbe.java.txt 拷进 src（探针源码的唯一真源在 probe/gpq/）；
  4) 放开关文件 run\\gpq-probe.enabled；
  5) gradlew compileJava 然后 runServer（两条都等退出码，串行）；
  6) 归档 run\\probe\\gpq\\report.json -> docs\\gpq-证据\\0X-A级-<phase>.json；
  7) 逐字节复原 server.properties 并复核 SHA256（与备份一致才打印 OK）。
⚠ 不删 run\\world / run\\saves；不碰别的进程。
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
EVID = os.path.join(ROOT, "docs", "gpq-证据")
SRC_PROBE = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe",
                         "GpqProbe.java")
MASTER = os.path.join(HERE, "GpqProbe.java.txt")
PROPS = os.path.join(RUN, "server.properties")
BAK = os.path.join(RUN, "server.properties.gpq.bak")
SWITCH = os.path.join(RUN, "gpq-probe.enabled")
REPORT = os.path.join(RUN, "probe", "gpq", "report.json")
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
    phase = sys.argv[1] if len(sys.argv) > 1 else "before"
    assert phase in ("before", "after"), phase

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

    # 探针源码：唯一真源在 probe/gpq/，src 是副本（收尾整块删）
    os.makedirs(os.path.dirname(SRC_PROBE), exist_ok=True)
    shutil.copyfile(MASTER, SRC_PROBE)
    print("probe copied ->", os.path.relpath(SRC_PROBE, ROOT), sha(SRC_PROBE), flush=True)

    with open(SWITCH, "wb") as f:
        f.write(b"1\n")
    if os.path.exists(REPORT):
        os.remove(REPORT)

    logs = os.path.join(ROOT, "build", "gpq_compile_%s.log" % phase)
    rc = run([GRADLE, "compileJava", "--console=plain"], logs)
    if rc != 0:
        print("!! compileJava 失败，见", logs, flush=True)
        return 1
    log = os.path.join(ROOT, "build", "gpq_run_%s.log" % phase)
    rc = run([GRADLE, "runServer", "--console=plain"], log)
    print("runServer exit =", rc, "log =", os.path.relpath(log, ROOT), flush=True)

    archive = os.path.join(EVID, "0%s-A级-%s.json" % ("1" if phase == "before" else "2", phase))
    if os.path.exists(REPORT):
        shutil.copyfile(REPORT, archive)
        print("report archived ->", os.path.relpath(archive, ROOT), os.path.getsize(REPORT), "B", flush=True)
    else:
        print("!! no report at", REPORT, flush=True)

    # 复原 server.properties（逐字节）
    shutil.copyfile(BAK, PROPS)
    now = sha(PROPS)
    print("server.properties 复原 SHA256 =", now, "== 基线?", now == base, flush=True)
    if now != base:
        print("!! server.properties 没复原", flush=True)
        return 1
    if not os.path.exists(REPORT):
        return 1
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
