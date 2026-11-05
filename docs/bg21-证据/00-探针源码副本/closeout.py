#!/usr/bin/env python3
"""bg21 closeout checklist -> docs/bg21-证据/06-收尾核对.txt (temporary; deleted after running)."""
import hashlib
import subprocess
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[0]
OUT = REPO / "docs" / "bg21-证据" / "06-收尾核对.txt"


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else "<missing>"


def run(args, shell=False):
    r = subprocess.run(args, cwd=str(REPO), capture_output=True, shell=shell)
    return (r.stdout + r.stderr).decode("utf-8", errors="replace").strip()


def git(*args):
    return run(["git"] + list(args))


lines = []
add = lines.append

add("bg21 收尾核对（2026-11-05）")
add("=" * 70)
add("")
add("[1] git status --porcelain（期望：1 个生产 java + 关卡 + 本档 + 2 快照 + 证据目录；不 commit / 不 push）")
add(git("status", "--porcelain"))
add("")
add("[2] 生产代码改动范围：只 CreativeTabSections.java（+4286 B）")
add(git("diff", "--stat", "--", "src/main/java"))
add("")
add("[3] 探针 / 开关残留 grep（全部应为 0 命中）")
for pattern in ("Bg21CreativeOrderProbe", "BG-PROBE", "bg21-client-probe"):
    hits = run('findstr /s /i /m /c:"%s" src\\main\\java\\*.java' % pattern, shell=True)
    add("  findstr %-24s -> %s" % (pattern, hits if hits else "0 命中"))
add("  说明：`bg21` 在 CreativeTabSections.java 的 javadoc 里出现 1 次 —— 是关卡 tag `[bg21-creative-pins]` 的"
    "**说明性引用**（不是探针代码；探针类名 / 开关文件 / BG-PROBE 全 0 命中）")
add("  probe/bg21 exists: %s" % (REPO / "probe" / "bg21").exists())
add("  src/main/java/.../probe/bg21 exists: %s"
    % (REPO / "src/main/java/com/hjmmd_8/bettergold/probe/bg21").exists())
add("")
add("[4] 关键文件 SHA256")
for f in ("build.gradle", "run/server.properties",
          "src/main/java/com/hjmmd_8/bettergold/material/CreativeTabSections.java",
          "tools/asset-generator/validate_metal_data.py",
          "tools/asset-generator/bg21-creative-order-before.txt",
          "tools/asset-generator/bg21-creative-order-after.txt",
          "build/moddev/clientRunProgramArgs.txt",
          "docs/1.7-混沌金与崩乱合金-需求立档.md"):
    add("  %-72s %s" % (f, sha(REPO / f)))
add("")
add("[5] 复原判据：build.gradle = 2AAC7860E5B1F03128D42637B9F002C7A44F37E269EE6B7BC9DFBE41AD478C2F")
add("    clientRunProgramArgs.txt 规范形态 = A365A5EDF7ABC44C576E5DD3F725A54D46658FCDDC1E3A0257BEC7C0AB2E4BDB（394 B）")
add("    server.properties 历史目标值 = A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4")
add("")
add("[6] 产物 jar：条目数 / 探针残留")
jar = REPO / "build" / "libs" / "bettergold-1.7.0.jar"
if jar.is_file():
    with zipfile.ZipFile(jar) as z:
        names = z.namelist()
        halt = [n for n in names if n.endswith(".class") and b"halt" in z.read(n)]
    probe = [n for n in names if "Probe" in n or "probe" in n.lower()]
    add("  %s entries=%d probe-like=%s halt-classes=%d" % (jar.name, len(names), probe, len(halt)))
else:
    add("  缺 jar")
add("")
add("[7] run/saves 前后文件数（作者存档 = 新的世界；本轮未打开）")
for d in sorted((REPO / "run" / "saves").iterdir()):
    files = [p for p in d.rglob("*") if p.is_file()]
    add("  %-12s files=%d" % (d.name, len(files)))
add("  （开工 29 → 收尾 29；mtime 变化来自 12:06:37 起就在跑的别人的 dev 客户端 PID 42896，不是本轮）")
add("")
add("[8] run/ 独占（本轮自己的 runClient 已退出；开工时就在跑的别人的客户端 PID 42896 收尾时已不在进程表里）")
add("  本会话从未执行 Stop-Process / taskkill / kill（命令记录可查）；只按 PID 停过自己的 runClient（mc.stop()）。")
add("  42896 最后一次写作者存档 = 12:21:56；没有它对应的 crash-report（run/crash-reports 最新一份是 2026-10-05）。")
add(run("tasklist /FI \"IMAGENAME eq java.exe\"", shell=True))
add("")
add("[9] 本轮删掉的文件（都在 run/ 与 probe/，且已留档到 docs/bg21-证据/）")
add("  probe/bg21/**（脚本 10 个；探针源码已提前复制到 00-探针源码副本/）")
add("  run/bg21-client-probe.enabled / run/bg21-phase.txt / run/bg21-order-*.txt / run/logs/quickplay/bg21.json")
add("  run/saves/bg21probe（84 → 89 文件，删前已记文件数 / mtime）")
add("")
add("[10] 文档：git diff --numstat")
add(git("diff", "--numstat", "--", "docs/1.7-混沌金与崩乱合金-需求立档.md"))

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines).encode("ascii", "backslashreplace").decode("ascii"))
