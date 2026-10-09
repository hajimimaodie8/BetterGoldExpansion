# -*- coding: utf-8 -*-
"""bgfix8：把四轮 runClient / runServer 日志里的探针行抽成 UTF-8 证据文件。"""
import os
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
OUT = os.path.join(REPO, "docs", "bgfix8-\u8bc1\u636e")
os.makedirs(OUT, exist_ok=True)
SRC = os.path.join(REPO, "build")


def extract(log, tags, dst, keep_all=False):
    path = os.path.join(SRC, log)
    lines = []
    with open(path, "rb") as fh:
        for raw in fh:
            s = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if any(t in s for t in tags):
                lines.append(s)
            elif keep_all and ("Stopping server" in s or "Done (" in s):
                lines.append(s)
    with open(os.path.join(OUT, dst), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 来源：build/%s（探针行原样抽取，UTF-8 / LF）\n" % log)
        fh.write("\n".join(lines) + "\n")
    print("%-52s 行数=%d" % (dst, len(lines)))


extract("bgfix8-server.log", ["BGFIX8S-PROBE"], "05-A级-runServer-探针读数.txt", keep_all=True)
extract("bgfix8-client4.log", ["BGFIX8C-PROBE"], "06-A级-runClient-探针读数.txt")
extract("bgfix8-client.log", ["BGFIX8C-PROBE"], "06b-A级-runClient-首轮用例错留档.txt")
