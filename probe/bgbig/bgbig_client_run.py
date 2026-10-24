# -*- coding: utf-8 -*-
"""bgbig B 段：跑一次**客户端**探针（真加载 Patchouli BookContents）。

跑法（工作区自带 Python）：
    <dsh python> probe\\bgbig\\bgbig_client_run.py

做的事（任一步失败就非 0 退出）：
  1) 独占检查：java.exe 里有 runServer / runClient / devlaunch ⇒ 拒绝（从不杀别人的进程）；
  2) 造一个 ASCII 探针世界 `run/saves/bgbigprobe`：**复制 `run/world`**（服务端世界，
     LevelName = world），删掉 session.lock；**绝不打开作者的 `run/saves/新的世界`**；
  3) 写 `run/logs/quickplay/bgbig.json`（quickPlayPath 用）；
  4) 字节备份 `build.gradle` → 在 client 块里临时加
     `programArguments.addAll '--quickPlayPath', …, '--quickPlaySingleplayer', 'bgbigprobe'`
     （⚠ 不贴 `build/moddev/clientRunProgramArgs.txt`：那个每次 runClient 都会被 Gradle 重写）；
  5) 放开关 `run/bgbig-client-probe.enabled`；把 `probe/bgbig/ClientProbe.java.txt` 拷进 src；
  6) `gradlew runClient`（探针读完 `mc.stop()` 自行退出）；
  7) 抽 `run/logs/latest.log` 里 `[bgbig-c]` 行 → `docs/bgbig-证据/10-客户端-BookContents.txt`；
  8) 逐字节复原 `build.gradle` 并复核 SHA256；删开关与 src 里的探针副本。
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(ROOT, "run")
EVID = os.path.join(ROOT, "docs", "bgbig-证据")
SRC = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "bgbig")
MASTER = os.path.join(HERE, "ClientProbe.java.txt")
GRADLE = os.path.join(ROOT, "gradlew.bat")
BUILD = os.path.join(ROOT, "build.gradle")
BAK = os.path.join(ROOT, "build", "build.gradle.bgbig.bak")
SWITCH = os.path.join(RUN, "bgbig-client-probe.enabled")
WORLD = os.path.join(RUN, "world")
SAVE = os.path.join(RUN, "saves", "bgbigprobe")
QP_DIR = os.path.join(RUN, "logs", "quickplay")
QP = os.path.join(QP_DIR, "bgbig.json")
LOG = os.path.join(RUN, "logs", "latest.log")


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


def prepare_world():
    if not os.path.isdir(WORLD):
        raise SystemExit("run/world 不存在（先跑一次 runServer 或手工准备）")
    if os.path.isdir(SAVE):
        shutil.rmtree(SAVE)
    shutil.copytree(WORLD, SAVE)
    lock = os.path.join(SAVE, "session.lock")
    if os.path.exists(lock):
        os.remove(lock)
    files = sum(len(fs) for _, _, fs in os.walk(SAVE))
    print("probe world copied ->", os.path.relpath(SAVE, ROOT), "files =", files, flush=True)


def write_quickplay():
    os.makedirs(QP_DIR, exist_ok=True)
    data = [{"type": "singleplayer", "id": "bgbigprobe", "name": "world",
             "lastPlayedTime": "2026-10-24T13:00:00.000000000Z", "gamemode": "survival"}]
    with io.open(QP, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("quickplay json ->", os.path.relpath(QP, ROOT), flush=True)


def patch_build_gradle():
    raw = open(BUILD, "rb").read()
    text = raw.decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    anchor = "        client {" + nl + "            client()" + nl
    if text.count(anchor) != 1:
        raise SystemExit("build.gradle 的 client() 锚点命中 %d 次" % text.count(anchor))
    insert = (anchor
              + "            programArguments.addAll '--quickPlayPath', file('run/logs/quickplay/bgbig.json').getAbsolutePath(), '--quickPlaySingleplayer', 'bgbigprobe'"
              + nl)
    open(BUILD, "wb").write(text.replace(anchor, insert, 1).encode("utf-8"))
    print("build.gradle patched; SHA before/after =", sha(BAK), "/", sha(BUILD), flush=True)


def main():
    hits = java_runs()
    print("java 里在跑的 runServer/runClient/devlaunch =", len(hits), hits[:3], flush=True)
    if hits:
        print("!! run\\ 不独占 ⇒ 拒绝执行", flush=True)
        return 2

    os.makedirs(EVID, exist_ok=True)
    base = sha(BUILD)
    shutil.copyfile(BUILD, BAK)
    if sha(BAK) != base:
        print("!! build.gradle 备份不一致", flush=True)
        return 2

    prepare_world()
    write_quickplay()
    patch_build_gradle()

    os.makedirs(SRC, exist_ok=True)
    probe_src = os.path.join(SRC, "ClientProbe.java")
    shutil.copyfile(MASTER, probe_src)
    print("probe copied ->", os.path.relpath(probe_src, ROOT), sha(probe_src), flush=True)
    with open(SWITCH, "wb") as f:
        f.write(b"1\n")

    log = os.path.join(ROOT, "build", "bgbig_client.log")
    rc = run([GRADLE, "runClient", "--console=plain"], log)
    print("runClient exit =", rc, "log =", os.path.relpath(log, ROOT), flush=True)

    # ⚠ 探针用 System.out.println ⇒ 落点是 **Gradle 的 stdout**（`build/bgbig_client.log`），
    #   不是 log4j 直写的 latest.log（那两个都收一遍，谁有就用谁）。
    lines = []
    for src in (log, LOG):
        if not os.path.exists(src):
            continue
        with io.open(src, encoding="utf-8", errors="replace") as f:
            got = [l.rstrip("\n") for l in f if "[bgbig-c]" in l]
        if len(got) > len(lines):
            lines = got
    out = os.path.join(EVID, "10-客户端-BookContents.txt")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("client probe lines ->", os.path.relpath(out, ROOT), len(lines), flush=True)

    # 复原
    shutil.copyfile(BAK, BUILD)
    now = sha(BUILD)
    print("build.gradle restored SHA =", now, "== base?", now == base, flush=True)
    if now != base:
        print("!! build.gradle 没复原", flush=True)
        return 1
    for p in (SWITCH, probe_src):
        if os.path.exists(p):
            os.remove(p)
    print("switch + src probe removed", flush=True)

    return 0 if (rc == 0 and len(lines) > 0) else 1


if __name__ == "__main__":
    sys.exit(main())
