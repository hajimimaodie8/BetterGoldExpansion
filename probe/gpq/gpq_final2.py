# -*- coding: utf-8 -*-
"""重算 06-收尾核对.md（文档又改了两处 ⇒ SHA256 / 字节数要重算；文件清单已含 06/09，去掉重复行）。"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
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
    "src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java": (31116, "本轮前未记录（本轮只 +② 的注释，数值未动）"),
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
    L = []
    L.append("# 收尾核对（gpq 轮，2026-10-23）")
    L.append("")
    L.append("## 1. 改动清单（8 个文件；`git status` 的 `M` = 8，其余是本轮新增的 `??` 证据目录）")
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
        L.append("- `%s`：**%d 行**（字节 %d → %d）" % (rel, n, BASE[rel][0], os.path.getsize(p)))
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
    L.append("- 两次 `runServer` 之前都做了独占检查：命令行里带 `runServer` / `runClient` / `devlaunch`")
    L.append("  的 java 进程 = **0**（唯一 java 是 Gradle daemon 8.8，未杀未动）。")
    L.append("- `run/server.properties` 跑前 `.gpq.bak` 字节备份、跑后逐字节复原：")
    L.append("  SHA256 = `%s`（1440 B，与基线一致；两次探针跑都是这个值）。" % sha(os.path.join(RUN, "server.properties")))
    L.append("- 进世界 = **runServer + run/world**（仓库自带 dev 服务端世界）；**没有**开客户端、")
    L.append("  **没有** `--quickPlaySingleplayer`、**没有** UI 自动化、**没有**打开 `run/saves`。")
    L.append("- `run/saves` mtime：%s（本轮没被写过）" % sh([
        "powershell", "-NoProfile", "-Command",
        "(Get-Item 'run\\saves').LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')"]).strip())
    L.append("- 探针：`run/gpq-probe.enabled` / `run/probe/gpq/` / `src/.../probe/GpqProbe.java` 全删；")
    L.append("  `grep` 0 命中（见 `08-探针清理.txt`），`check_jar_clean.py` 也全绿（`*Probe*` 0）。")
    L.append("- forceload：一次都没下（`forcedChunksBefore = After = []`）。")
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
    scr = os.path.join(EVID, "脚本副本")
    n = len([x for x in os.listdir(scr) if os.path.isfile(os.path.join(scr, x))]) if os.path.isdir(scr) else 0
    L.append("- `脚本副本/`（探针源码 + 全部驱动 / 校验 / 扰动 / 文档脚本，共 %d 个文件）" % n)
    L.append("")
    text = "\n".join(L) + "\n"
    open(os.path.join(EVID, "06-收尾核对.md"), "w", encoding="utf-8", newline="\n").write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
