# -*- coding: utf-8 -*-
"""bgfix8：从**游戏自己写的** `run/logs/*.log(.gz)` 抽探针行（UTF-8 正确），生成证据文件。

⚠ 教训（本轮实测）：`gradlew ... | Out-File -Encoding utf8` 抓下来的日志里**中文是乱码**
（PowerShell 按本机代码页解码子进程的 UTF-8 输出，写进文件的是二次编码的坏字节，
  `�` 处**不可逆**）。**正确做法 = 直接读 `run/logs/latest.log` 或轮转归档 `run/logs/*.log.gz`。**
"""
import gzip
import os
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
LOGS = os.path.join(REPO, "run", "logs")
OUT = os.path.join(REPO, "docs", "bgfix8-\u8bc1\u636e")
os.makedirs(OUT, exist_ok=True)


def read_log(name):
    p = os.path.join(LOGS, name)
    if name.endswith(".gz"):
        with gzip.open(p, "rb") as fh:
            return fh.read().decode("utf-8", errors="replace")
    with open(p, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace")


def extract(src, tag, dst, extra=()):
    text = read_log(src)
    lines = [ln.rstrip() for ln in text.splitlines()
             if tag in ln or any(e in ln for e in extra)]
    with open(os.path.join(OUT, dst), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 来源：run/logs/%s（**游戏自己写的 UTF-8**；探针行原样抽取）\n" % src)
        fh.write("\n".join(lines) + "\n")
    print("%-52s 行数=%d  （来源 %s）" % (dst, len(lines), src))


extract("2026-10-09-4.log.gz", "BGFIX8S-PROBE", "05-A级-runServer-探针读数.txt",
        extra=("Done (", "Stopping server"))
extract("latest.log", "BGFIX8C-PROBE", "06-A级-runClient-探针读数.txt")
extract("2026-10-09-3.log.gz", "BGFIX8C-PROBE", "06b-A级-runClient-首轮用例错留档.txt")
