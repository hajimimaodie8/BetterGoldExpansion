#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10hv_evidence.py —— 把本轮读数落成证据文件（00 探针原始行 / 02 saves 对比 / 03 日志扫描）。

用法： py -3 bgn10hv_evidence.py [日志]   默认 run/logs/latest.log（UTF-8，中文内容正确；
      build/bgn10hv/client3.out 是 PowerShell 重定向的 UTF-16 副本，中文会被转码，**只当备份**）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVID = REPO / "docs" / "bgn10hv-证据"
LOG = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "run" / "logs" / "latest.log"
LOG = LOG if LOG.is_absolute() else REPO / LOG
RECORD = EVID / "04-跑前留档.json"


def sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def saves_listing() -> dict:
    import hashlib
    out = {}
    saves = REPO / "run" / "saves"
    if saves.is_dir():
        for d in sorted(p for p in saves.iterdir() if p.is_dir()):
            files = sorted(q for q in d.rglob("*") if q.is_file())
            h = hashlib.sha256()
            mtimes = []
            for q in files:
                h.update(str(q.relative_to(d)).encode("utf-8"))
                h.update(b"\0")
                h.update(hashlib.sha256(q.read_bytes()).digest())
                mtimes.append(int(q.stat().st_mtime))
            out[d.name] = {"files": len(files), "max_mtime": max(mtimes) if mtimes else 0,
                           "digest": h.hexdigest().upper()}
    return out


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    log = LOG.read_text(encoding="utf-8", errors="replace").splitlines()

    # ---------- 00 探针原始行 ----------
    rows = [l for l in log if "BGN10HV" in l]
    (EVID / "00-探针原始行.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")

    # ---------- 02 run/saves 跑前/跑后 ----------
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    before, now = rec["saves"], saves_listing()
    out = ["run/saves 跑前 / 跑后 清单对比（名字 + 文件数 + max_mtime + 内容摘要 SHA256）", ""]
    for k in sorted(set(before) | set(now)):
        b, n = before.get(k), now.get(k)
        out.append("%-12s 跑前: %s" % (k, b))
        out.append("%-12s 跑后: %s" % ("", n))
        verdict = "一致（一字节未动）" if b == n else ("**本轮新增的探针世界（收尾删除）**" if b is None else "**变了**")
        out.append("%-12s 结论: %s" % ("", verdict))
        out.append("")
    out.append("跑前 server.properties SHA256 = %s" % rec["server_properties_sha256"])
    out.append("跑前 build.gradle       SHA256 = %s" % rec["build_gradle_sha256"])
    (EVID / "02-saves清单对比.txt").write_text("\n".join(out) + "\n", encoding="utf-8")

    # ---------- 03 日志扫描 ----------
    errs = [l for l in log if "/ERROR" in l]
    unable = [l for l in log if "Unable to " in l]
    notfound = [l for l in log if "not found" in l and "patchouli" in l.lower()]
    warns = [l for l in log if "/WARN" in l]
    scan = ["客户端日志扫描（整份 %s，共 %d 行）" % (LOG.relative_to(REPO), len(log)), ""]
    scan.append("① 含 '/ERROR' 的行数 = %d" % len(errs))
    scan.extend(["   ! " + l for l in errs[:10]])
    scan.append("② 含 'Unable to ' 的行数 = %d" % len(unable))
    scan.extend(["   ! " + l for l in unable[:10]])
    scan.append("③ Patchouli 'Recipe ... not found' 警告行数 = %d（配方页解析失败的唯一静默信号）" % len(notfound))
    scan.extend(["   ! " + l for l in notfound[:10]])
    scan.append("④ 全部 WARN 行（%d 条；逐条列出证明没有本模组/手册相关的）" % len(warns))
    scan.extend(["   " + l[:250] for l in warns])
    (EVID / "03-日志扫描.txt").write_text("\n".join(scan) + "\n", encoding="utf-8")

    print("[evidence] 00/02/03 已写；探针行=%d ERROR=%d Unable=%d RecipeNotFound=%d WARN=%d"
          % (len(rows), len(errs), len(unable), len(notfound), len(warns)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
