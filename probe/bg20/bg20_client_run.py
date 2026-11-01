# -*- coding: utf-8 -*-
"""bg20 B 段：跑一次**客户端**探针（真加载 Patchouli BookContents，验证 P4 的页序 / 自定义页型）。

跑法（工作区自带 Python）：
    <dsh python> probe\\bg20\\bg20_client_run.py

任一步失败就非 0 退出。做的事：
  1) 独占检查：java.exe 里有 runServer / runClient / devlaunch ⇒ 拒绝（从不杀别人的进程）；
  2) **留档** `run/saves` 的目录清单（名字 + 文件数 + mtime）——**绝不打开作者存档**；
  3) 造 ASCII 探针世界 `run/saves/bg20probe`：**复制 `run/world`**（服务端世界，LevelName = world），
     只删**副本里**的 session.lock；
  4) 写 `run/logs/quickplay/bg20.json`（quickPlayPath 用）；
  5) 字节备份 `build.gradle` → 在 client 块里临时加
     `--quickPlayPath <json> --quickPlaySingleplayer bg20probe`（**两个都带**）；
  6) 放开关 `run/bg20-client-probe.enabled`；把 `probe/bg20/ClientProbe.java.txt` 拷进 src；
  7) `gradlew runClient`（探针读完 `mc.stop()` 自行退出）；
  8) 抽日志里 `[bg20-c]` 行 → `docs/bg20-证据/10-客户端-BookContents.txt`；
  9) 逐字节复原 `build.gradle` 并复核 SHA256；删开关与 src 里的探针副本；复核 `run/saves` 清单。
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
EVID = os.path.join(ROOT, "docs", "bg20-证据")
SRC = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "bg20")
MASTER = os.path.join(HERE, "ClientProbe.java.txt")
GRADLE = os.path.join(ROOT, "gradlew.bat")
BUILD = os.path.join(ROOT, "build.gradle")
BAK = os.path.join(ROOT, "build", "build.gradle.bg20.bak")
SWITCH = os.path.join(RUN, "bg20-client-probe.enabled")
WORLD = os.path.join(RUN, "world")
SAVE = os.path.join(RUN, "saves", "bg20probe")
QP_DIR = os.path.join(RUN, "logs", "quickplay")
QP = os.path.join(QP_DIR, "bg20.json")
LOG = os.path.join(RUN, "logs", "latest.log")
AUTHOR_SAVE = os.path.join(RUN, "saves", "\u65b0\u7684\u4e16\u754c")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def listing(root):
    """目录清单：名字 + 文件数 + 最新 mtime（**只 stat，不打开**）。"""
    out = []
    if not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        files = 0
        newest = 0.0
        for base, _dirs, fs in os.walk(p):
            for f in fs:
                files += 1
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(base, f)))
                except OSError:
                    pass
        out.append("%s files=%d newest=%.0f" % (name, files, newest))
    return out


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
    data = [{"type": "singleplayer", "id": "bg20probe", "name": "world",
             "lastPlayedTime": "2026-10-26T13:00:00.000000000Z", "gamemode": "survival"}]
    with io.open(QP, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("quickplay json ->", os.path.relpath(QP, ROOT), flush=True)


def patch_build_gradle():
    text = open(BUILD, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    anchor = "        client {" + nl + "            client()" + nl
    if text.count(anchor) != 1:
        raise SystemExit("build.gradle 的 client() 锚点命中 %d 次" % text.count(anchor))
    insert = (anchor
              + "            programArguments.addAll '--quickPlayPath', file('run/logs/quickplay/bg20.json').getAbsolutePath(), '--quickPlaySingleplayer', 'bg20probe'"
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
    saves_before = listing(os.path.join(RUN, "saves"))
    print("run/saves BEFORE:", saves_before, flush=True)

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

    log = os.path.join(ROOT, "build", "bg20_client.log")
    rc = run([GRADLE, "runClient", "--console=plain"], log)
    print("runClient exit =", rc, "log =", os.path.relpath(log, ROOT), flush=True)

    # ⚠ 探针用 System.out.println ⇒ 落点是 **Gradle 的 stdout**（`build/bg20_client.log`），
    #   不是 log4j 直写的 latest.log（两个都收一遍，谁有就用谁）。
    lines = []
    for src in (log, LOG):
        if not os.path.exists(src):
            continue
        with io.open(src, encoding="utf-8", errors="replace") as f:
            got = [l.rstrip("\n") for l in f if "[bg20-c]" in l]
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
    ok = True
    if now != base:
        print("!! build.gradle 没复原", flush=True)
        ok = False
    for p in (SWITCH, probe_src):
        if os.path.exists(p):
            os.remove(p)
    print("switch + src probe removed", flush=True)

    saves_after = listing(os.path.join(RUN, "saves"))
    print("run/saves AFTER :", saves_after, flush=True)
    # ⚠ 修好的比对：按**名字**配对，不按位置 zip（否则"跑前 1 项 / 跑后 2 项"会拿
    #   作者存档去比探针存档，误报一次"作者存档清单变了"——本轮第一次跑就踩了这一下，见 §33.8）。
    before_map = {}
    for line in saves_before:
        before_map[line.split(" ", 1)[0]] = line
    if os.path.isdir(AUTHOR_SAVE):
        name = "\u65b0\u7684\u4e16\u754c"
        if name not in before_map:
            print("!! 跑前清单里没有作者存档目录（异常）", flush=True)
            ok = False
        else:
            after_line = ""
            for line in saves_after:
                if line.startswith(name + " "):
                    after_line = line
            if after_line != before_map[name]:
                print("!! 作者存档清单变了（绝不能碰）:", before_map[name], "->", after_line, flush=True)
                ok = False
            else:
                print("作者存档清单未变（0 触碰）:", before_map[name], flush=True)
    else:
        print("（run/saves 里没有作者存档目录）", flush=True)

    return 0 if (rc == 0 and len(lines) > 0 and ok) else 1


if __name__ == "__main__":
    sys.exit(main())
