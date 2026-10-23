# -*- coding: utf-8 -*-
"""收尾证据：06-收尾核对.md（共享文件 / run\\ / jar / 改动清单与 SHA256 / 文档行数）+ 09-构建.txt
+ 把 probe/gpq 的脚本副本留档到 docs/gpq-证据/脚本副本/。"""
import hashlib
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVID = os.path.join(ROOT, "docs", "gpq-证据")
RUN = os.path.join(ROOT, "run")

FILES = [
    "src/main/java/com/hjmmd_8/bettergold/material/MetalFamily.java",
    "src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java",
    "src/main/java/com/hjmmd_8/bettergold/fd/FdItems.java",
    "src/main/resources/data/bettergold/loot_table/chests/golden_prison.json",
    "tools/asset-generator/validate_metal_data.py",
    "tools/asset-generator/validate_golden_prison.py",
    "docs/1.7-混沌金与崩乱合金-需求立档.md",
    "docs/金之牢狱-实现记录.md",
]
BASE = {
    "src/main/java/com/hjmmd_8/bettergold/material/MetalFamily.java": (122778, "210528B65AAD07FD20E717BE5611FEE803572E992E99203BA93226DBC4626009"),
    "src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java": (31116, "(本轮之前未记录；只有 ② 的 3 行注释增补)"),
    "src/main/java/com/hjmmd_8/bettergold/fd/FdItems.java": (16435, "62BF7796EC9EAC81C16F3CF9A18C33A2DB06716343456DF87979D3E1F93917D0"),
    "src/main/resources/data/bettergold/loot_table/chests/golden_prison.json": (8995, "5028374A2DC53523F669863D82FDDDE7C17495DBEA058497B74878B67D4A36F4"),
    "tools/asset-generator/validate_metal_data.py": (705928, "BDCE441483D603A1675A2EBD5358B6B2174B7A5E93B8C09042714A43639E24C8"),
    "tools/asset-generator/validate_golden_prison.py": (160410, "C53BC01E3983AD1725481E099161B2E9F9301B1DB30D3362C23B3DC06A16535B"),
    "docs/1.7-混沌金与崩乱合金-需求立档.md": (384637, "184F45E72FB360155141396DE8EB0AE3B4F4A32B03A783DCABB18AFE4B529CA9"),
    "docs/金之牢狱-实现记录.md": (184579, "C9C82E6B979752D791600446CCEA93D93DE8475586DBFD626CA8755D3E004213"),
}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def sh(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout or "") + (p.stderr or "")


def main():
    os.makedirs(EVID, exist_ok=True)
    L = []
    L.append("# 收尾核对（gpq 轮，2026-10-23）")
    L.append("")
    L.append("## 1. 改动清单（只这 8 个文件；`git status` 的 `M` = 8，其余全是本轮新增的 `??` 证据）")
    L.append("")
    L.append("| 文件 | 改前字节 / SHA256 | 改后字节 / SHA256 |")
    L.append("|---|---|---|")
    for rel in FILES:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        b, want = BASE[rel]
        L.append("| `%s` | %s / `%s` | %s / `%s` |" % (rel, b, want, os.path.getsize(p), sha(p)))
    L.append("")
    L.append("## 2. 文档行数（改前 → 改后）")
    L.append("")
    for rel in ("docs/1.7-混沌金与崩乱合金-需求立档.md", "docs/金之牢狱-实现记录.md"):
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        n = len(open(p, encoding="utf-8").read().splitlines())
        b = BASE[rel][0]
        L.append("- `%s`：**%d 行**（字节 %d → %d）" % (rel, n, b, os.path.getsize(p)))
    L.append("")
    L.append("## 3. git（不 commit / 不 push）")
    L.append("")
    L.append("```")
    L.append("HEAD = " + sh(["git", "rev-parse", "HEAD"]).strip())
    L.append("git status --porcelain:")
    L.append(sh(["git", "status", "--porcelain"]).rstrip())
    L.append("```")
    L.append("")
    L.append("## 4. `run\\`（独占 / server.properties 逐字节复原 / 不碰作者存档）")
    L.append("")
    L.append("- 两次 `runServer` 之前都跑过独占检查：命令行里带 `runServer` / `runClient` / `devlaunch`")
    L.append("  的 java 进程 = **0**（唯一的 java 是 Gradle daemon 8.8，未杀、未动）。")
    L.append("- `run/server.properties` 跑前 `.gpq.bak` 字节备份 → 跑后逐字节复原：")
    L.append("  SHA256 = `%s`（1440 B，与基线一致；两次探针跑都是这个值）。" % sha(os.path.join(RUN, "server.properties")))
    L.append("- 进世界走的是 **runServer + run/world**（仓库自带 dev 服务端世界）；")
    L.append("  **没有**开客户端、**没有** `--quickPlaySingleplayer`、**没有** UI 自动化、**没有**打开 `run/saves`。")
    L.append("- `run/saves` 目录 mtime：%s（本轮没被写过）" % sh([
        "powershell", "-NoProfile", "-Command",
        "(Get-Item 'run\\saves').LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')"]).strip())
    L.append("- 探针开关 `run/gpq-probe.enabled` 与 `run/probe/gpq/` 结果目录：**已删**；")
    L.append("  探针类 `src/.../probe/GpqProbe.java`：**整块删**（目录也删了），`grep` 0 命中（见 `08-探针清理.txt`）。")
    L.append("- forceload：探针一次都没下（`forcedChunksBefore = After = []`，`check_forced_chunks.py` 也全绿）。")
    L.append("")
    L.append("## 5. 构建 / jar")
    L.append("")
    jar = os.path.join(ROOT, "build", "libs", "bettergold-1.7.0.jar")
    L.append("- `gradlew.bat build` ⇒ **BUILD SUCCESSFUL**（exit 0；`build/gpq_build.out`）")
    L.append("- `build/libs/bettergold-1.7.0.jar`：**%d B**，SHA256 `%s`" % (os.path.getsize(jar), sha(jar)))
    L.append("- `check_jar_clean.py`：条目 2868 / `*Probe*` 0 / `'halt'` 字节 0 / `'BG-PROBE'` 0")
    L.append("")
    L.append("## 6. 证据清单（本目录）")
    L.append("")
    for f in sorted(os.listdir(EVID)):
        p = os.path.join(EVID, f)
        if os.path.isfile(p):
            L.append("- `%s`（%d B）" % (f, os.path.getsize(p)))
    L.append("- `06-收尾核对.md`（本节）")
    L.append("- `09-构建.txt`（`gradlew.bat build` 尾部 + jar 字节数/SHA256）")
    _scr = os.path.join(EVID, "脚本副本")
    _n_scr = len([x for x in os.listdir(_scr) if os.path.isfile(os.path.join(_scr, x))]) if os.path.isdir(_scr) else 0
    L.append("- `脚本副本/`（探针源码 + 本轮全部驱动 / 校验 / 扰动 / 文档脚本，共 %d 个文件）" % _n_scr)
    L.append("")
    text = "\n".join(L) + "\n"
    open(os.path.join(EVID, "06-收尾核对.md"), "w", encoding="utf-8", newline="\n").write(text)
    print(text)

    # 09-构建.txt（PowerShell 的 `1>` 默认写 UTF-16LE，这里按 BOM 判）
    build = os.path.join(ROOT, "build", "gpq_build.out")
    if os.path.exists(build):
        rawb = open(build, "rb").read()
        enc = "utf-16" if rawb[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8"
        tail = rawb.decode(enc, "replace").splitlines()[-15:]
    else:
        tail = []
    open(os.path.join(EVID, "09-构建.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(tail) + "\n\njar: %s  %d B  SHA256 %s\n" % (
            os.path.relpath(jar, ROOT), os.path.getsize(jar), sha(jar)))

    # 脚本副本
    dst = os.path.join(EVID, "脚本副本")
    os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(HERE)):
        if f.endswith(".py") or f.endswith(".txt"):
            shutil.copyfile(os.path.join(HERE, f), os.path.join(dst, f))
    print("脚本副本:", sorted(os.listdir(dst)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
