#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_evidence.py —— 从跑测日志里**原样摘录**轮9 的 A 级读数（不手写、不改字）。

输入（本会话的原始日志，收尾后仍在 build/ 里）：
  build/r9_rs3.out / r9_rs4.out / r9_rs5.out   —— 同一构建连跑 3 次 runServer（探针 BgN10r9Probe）
  build/r9_rc4.out                             —— runClient（探针 BgN10r9ClientProbe，quickPlay 进探针世界）
输出：
  docs/bgn10r9-证据/00-探针原始行.txt
  docs/bgn10r9-证据/01-A级读数.txt
  docs/bgn10r9-证据/02-客户端读数.txt
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"
EVID = REPO / "docs" / "bgn10r9-证据"

SERVERS = ["r9_rs3.out", "r9_rs4.out", "r9_rs5.out"]
CLIENT = "r9_rc4.out"


def lines(path: Path, tag: str) -> list:
    if not path.is_file():
        return []
    raw = path.read_bytes()
    # ⚠ PowerShell 的 `>` 重定向写的是 **UTF-16LE + BOM**（本轮实测：按 utf-8 读会一条都扫不到）
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8"
    out = []
    for line in raw.decode(enc, errors="replace").splitlines():
        if tag in line:
            out.append(line.rstrip())
    return out


def strip_ts(line: str) -> str:
    return re.sub(r"^\[\d\d:\d\d:\d\d\] \[[^\]]*\] \[[^\]]*\]: ", "", line)


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    raw = ["轮9 探针原始行（从 build/ 的跑测日志原样摘录；探针源码副本见 脚本副本/）", "=" * 110, ""]
    for name in SERVERS:
        raw.append("### runServer %s" % name)
        raw.extend(strip_ts(x) for x in lines(BUILD / name, "BGN10R9PROBE"))
        raw.append("")
    raw.append("### runClient %s" % CLIENT)
    raw.extend(strip_ts(x) for x in lines(BUILD / CLIENT, "BGN10R9CPROBE"))
    raw.append("")
    (EVID / "00-探针原始行.txt").write_bytes(("\n".join(raw) + "\n").encode("utf-8"))

    srv = ["轮9 A 级读数（真专用服务端 + 真 ServerPlayer；探针 BgN10r9Probe，收尾已整块删除）",
           "来源：build/r9_rs3.out / r9_rs4.out / r9_rs5.out（**同一构建连跑 3 次**）",
           "判读：PASS/FAIL 逐条 + 末行 SUMMARY；forceload 双向归零",
           "=" * 110, ""]
    for name in SERVERS:
        ls = lines(BUILD / name, "BGN10R9PROBE")
        p = sum(1 for x in ls if " PASS " in x)
        f = sum(1 for x in ls if " FAIL " in x)
        order = [strip_ts(x) for x in ls if "INFO tree_order ::" in x]
        summ = [strip_ts(x) for x in ls if "SUMMARY" in x]
        srv.append("### %s：PASS=%d FAIL=%d" % (name, p, f))
        srv.append("  " + (summ[0] if summ else "<无 SUMMARY>"))
        srv.append("  " + (order[0] if order else "<无 tree_order>"))
        srv.append("")
    # 三次 tree_order 是否逐字相同
    orders = []
    for name in SERVERS:
        for x in lines(BUILD / name, "INFO tree_order ::"):
            orders.append(strip_ts(x))
    srv.append("三次 runServer 的 tree_order 逐字相同：%s" % (len(set(orders)) == 1 and len(orders) == 3))
    srv.append("")
    srv.append("### 逐条读数（第 3 次 runServer，r9_rs5.out）")
    srv.extend("  " + strip_ts(x) for x in lines(BUILD / "r9_rs5.out", "BGN10R9PROBE")
               if " PASS " in x or " FAIL " in x)
    (EVID / "01-A级读数.txt").write_bytes(("\n".join(srv) + "\n").encode("utf-8"))

    cl = ["轮9 客户端读数（真 runClient + quickPlay 进**探针世界副本**；探针 BgN10r9ClientProbe，收尾已整块删除）",
          "来源：build/r9_rc4.out；世界名 A 级断言 = world（不是作者的「新的世界」）",
          "为什么必须进世界：Patchouli 的 BookContents 在无 Level 时是**空壳**（标题界面 entries=0、不报错）",
          "=" * 110, ""]
    cls = lines(BUILD / CLIENT, "BGN10R9CPROBE")
    cl.extend("  " + strip_ts(x) for x in cls)
    (EVID / "02-客户端读数.txt").write_bytes(("\n".join(cl) + "\n").encode("utf-8"))
    print("wrote 00 / 01 / 02 到", EVID)
    print("server runs:", [(n, sum(1 for x in lines(BUILD / n, 'BGN10R9PROBE') if ' PASS ' in x),
                            sum(1 for x in lines(BUILD / n, 'BGN10R9PROBE') if ' FAIL ' in x))
                           for n in SERVERS])
    print("client:", sum(1 for x in cls if " PASS " in x), "PASS /",
          sum(1 for x in cls if " FAIL " in x), "FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
