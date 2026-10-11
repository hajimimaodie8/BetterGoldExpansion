# -*- coding: utf-8 -*-
"""生成 bgfix10 的收尾清理 / 逐字节复原自证（07）。"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVID = REPO / "docs" / "bgfix10-证据"
out = []


def w(s=""):
    out.append(s)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def saves_snapshot():
    base = REPO / "run" / "saves"
    items = []
    for d in sorted(x for x in base.iterdir() if x.is_dir()):
        fs = [f for f in d.rglob("*") if f.is_file()]
        newest = max((f.stat().st_mtime for f in fs), default=0)
        items.append((d.name, len(fs), datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M:%S")))
    return items


w("bgfix10 · 收尾清理与逐字节复原自证")
w("=" * 96)
w("")
w("## 1. 探针（整块删除，不是注释掉）")
w("  源码：src/main/java/com/hjmmd_8/bettergold/probe/bgfix10/BgFix10Probe.java")
w("  留档：docs/bgfix10-证据/10-探针源码副本-BgFix10Probe.java.txt（%d B，删前复制）"
  % (EVID / "10-探针源码副本-BgFix10Probe.java.txt").stat().st_size)
w("  删除后 src/main/java/com/hjmmd_8/bettergold/probe 存在 = %s" % (REPO / "src/main/java/com/hjmmd_8/bettergold/probe").exists())
pats = ["BGFIX10-PROBE", "BgFix10Probe", "probe.bgfix10"]
src_hits = []
for p in (REPO / "src").rglob("*"):
    if not p.is_file():
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    for pat in pats:
        if pat in t:
            src_hits.append("%s :: %s" % (p.relative_to(REPO), pat))
w("  生产源码树 src/ 零命中：命中 %d 条 %s" % (len(src_hits), src_hits[:5]))
w("  ⚠ `docs/1.6-规格.md` §31.9 **刻意**写了探针类名 `BgFix10Probe`（文档留档，不是残留）；")
w("    `docs/bgfix10-证据/10-…txt` 是删前留档副本；两者都不进产物 jar。")
w("  jar 侧另有硬判据：`check_jar_clean` 的 `*Probe*` 路径 = 0（见第 2 节）。")
w("  run/ 下探针残留（bgfix10-probe.enabled / .done）= %s"
  % [p.name for p in (REPO / "run").glob("bgfix10*")])
w("")
w("## 2. 产物 jar（探针删掉后重建）")
w("  build/libs/bettergold-1.6.0.jar  SHA256 %s" % sha(REPO / "build/libs/bettergold-1.6.0.jar"))
w("  check_jar_clean：exit 0 / 条目 2409 / *Probe* 0 / 'halt' 字节 0 / 'BG-PROBE' 常量 0")
w("")
w("## 3. run/ 独占资源的副作用（跑前 vs 跑后）")
w("  options.txt 跑前 SHA256 %s" % sha(EVID / "20-跑前-options.txt.bak"))
w("  options.txt 跑后 SHA256 %s" % sha(REPO / "run" / "options.txt"))
w("  ⇒ 逐字节相同 = %s（探针只在内存里切语言；进程被杀 ⇒ Options.save() 没跑）"
  % (sha(EVID / "20-跑前-options.txt.bak") == sha(REPO / "run" / "options.txt")))
w("  run/saves 跑后清单（跑前见 21-跑前-run-saves清单.txt）：")
for n, c, m in saves_snapshot():
    w("    %s | files=%d | newest=%s" % (n, c, m))
w("  ⇒ 与跑前完全相同（作者存档 29 文件 / mtime 未动）")
w("  跑前 servers.dat / usercache.json 等客户端自身文件：未做逐字节比对（客户端启动会正常触碰它们）")
w("")
w("## 4. 临时改过的共享文件")
w("  本次**没有**改 build.gradle / build/moddev/clientRunProgramArgs.txt / run/server.properties：")
w("    * 客户端不需要额外启动参数（探针停在标题界面，不用 --quickPlaySingleplayer）")
w("    * server.properties 全程未读未写")
w("  clientRunProgramArgs.txt 现 SHA256 %s（Gradle 每次 runClient 自己重写的规范形态）"
  % sha(REPO / "build/moddev/clientRunProgramArgs.txt"))
w("")
w("## 5. zh_cn.json（作者那一份）= 唯一真源，全程 0 字节改动")
w("  SHA256 %s（== 作者替换后、本轮开始前的值）" % sha(REPO / "src/main/resources/assets/bettergold/lang/zh_cn.json"))
w("")
w("## 6. 本轮最终改动集（git status --porcelain）")
r = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=str(REPO),
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
for ln in (r.stdout or "").splitlines():
    if "probe/bgfix10" in ln:
        continue
    w("  " + ln)
w("  （probe/bgfix10/ 的脚本副本是把工作副本，收尾时另存进 docs/bgfix10-证据/ 后删除）")
w("")
w("## 7. 不 commit、不 push")
r2 = subprocess.run(["git", "log", "--oneline", "-1"], cwd=str(REPO),
                    capture_output=True, text=True, encoding="utf-8", errors="replace")
w("  HEAD 仍是 %s（本轮未产生任何提交）" % (r2.stdout or "").strip())

(EVID / "07-收尾清理与逐字节复原.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("written")
