# -*- coding: utf-8 -*-
"""从 run/logs 的轮转日志里把两段探针输出抽成证据文件（只读）。"""
import gzip
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "run" / "logs"
EV = ROOT / "docs" / "bgn10err-证据"
files = sorted([p for p in LOGS.glob("2026-10-18-*.log.gz")] + [LOGS / "latest.log"],
               key=lambda p: p.stat().st_mtime)


def lines_of(p):
    if p.suffix == ".gz":
        return gzip.open(p, "rt", encoding="utf-8", errors="replace").read().splitlines()
    return p.read_text(encoding="utf-8", errors="replace").splitlines()


def collect(tag):
    hits = []
    src = []
    for p in files:
        for ln in lines_of(p):
            if tag in ln:
                hits.append(ln)
                src.append(p.name)
    return hits, sorted(set(src))


NOTE = {
    "BGN10ERRCLIENT": [
        "⚠ 这个 tag 有两轮：21:46:21 那轮 3 条 FAIL 是**探针自己的期望值写错了**（NativeImage#getPixelRGBA",
        "   的原生字节序是 ABGR 打包进 int，我把 #D89106 写成了 ffd89106、实际读出 ff0691d8；像素本身是对的），",
        "   改成 ABGR 之后 21:46:50 那轮 13 PASS / 0 FAIL。以 SUMMARY pass=13 fail=0 那行为准。",
        "",
    ],
    "BGN10ERRSERVER": ["（一次跑到 SUMMARY pass=17 fail=0；forcedNow=0）", ""],
}

for tag, out in (("BGN10ERRSERVER", EV / "02-服务端探针.txt"),
                 ("BGN10ERRCLIENT", EV / "03-客户端启动探针.txt")):
    hits, src = collect(tag)
    body = []
    body.append("%s —— 从 run/logs 轮转日志抽出的原始行（只读抽取，未改日志）" % tag)
    body.append("来源日志: %s" % ", ".join(src))
    body.append("匹配行数: %d" % len(hits))
    body.append("")
    body.extend(NOTE.get(tag, []))
    body.extend(hits)
    out.write_text("\n".join(body) + "\n", encoding="utf-8")
    print("%s -> %s（%d 行，来源 %s）" % (tag, out.name, len(hits), ",".join(src)))
