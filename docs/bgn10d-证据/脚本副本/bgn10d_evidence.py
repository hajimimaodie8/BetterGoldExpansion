# -*- coding: utf-8 -*-
"""把两条 A 级探针的读数从 run/logs 抽成证据文件（轮转的 .log.gz 里也有）。

产出：
  docs/bgn10d-证据/01-A级读数.txt     —— 服务端探针（#13 标签）
  docs/bgn10d-证据/02-客户端读数.txt  —— 客户端探针（#12 tremble 图集）
"""
import glob
import gzip
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOGS = os.path.join(ROOT, "run", "logs")
EVID = os.path.join(ROOT, "docs", "bgn10d-证据")

STRIP = re.compile(r"^\[[^\]]+\]\s*\[[^\]]+\]\s*\[[^\]]+\]:\s*")


def lines_of(path):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    with io.open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def collect(tag):
    """取**最后一份**含该 TAG 的日志（时间序：文件名排序 ≈ 轮转顺序，latest.log 最末）。"""
    best = None
    best_name = None
    files = sorted(glob.glob(os.path.join(LOGS, "*.log.gz")))
    files.append(os.path.join(LOGS, "latest.log"))
    for f in files:
        try:
            ls = lines_of(f)
        except Exception:
            continue
        if any(tag in l for l in ls):
            best, best_name = ls, os.path.basename(f)
    return best or [], best_name


def dump(tag, title, out):
    ls, src = collect(tag)
    rows = [STRIP.sub("", l) for l in ls if tag in l]
    with io.open(os.path.join(EVID, out), "w", encoding="utf-8", newline="\n") as f:
        f.write(title + "\n")
        f.write("来源日志：run/logs/" + str(src) + "\n")
        f.write("探针开关文件：run/bgn10d-probe.enabled（跑完已删除）\n")
        f.write("行数：%d（PASS %d / FAIL %d）\n\n"
                % (len(rows), sum(1 for r in rows if " PASS " in r),
                   sum(1 for r in rows if " FAIL " in r)))
        f.write("\n".join(rows) + "\n")
    print(out, "from", src, "rows", len(rows))


def main():
    dump("BGN10DPROBE", "bg-n10d A 级 · 服务端探针（#13 四条原版种子标签 · stack.is(tag) 逐条）",
         "01-A级读数.txt")
    dump("BGN10DCPROBE", "bg-n10d A 级 · 客户端启动探针（#12 tremble 图标被 mob_effects 图集解析）",
         "02-客户端读数.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
