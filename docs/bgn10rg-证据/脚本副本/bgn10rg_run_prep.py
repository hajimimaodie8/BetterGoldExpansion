#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跑测前后留档（bg-n10rg）：`run/saves` 清单 / `run/world` 清单 / `run/server.properties` 字节备份。

用法:
    python build/bgn10rg_run_prep.py before     # 跑前留档 + 备份 server.properties
    python build/bgn10rg_run_prep.py after      # 跑后复核（与 before 比）
    python build/bgn10rg_run_prep.py restore    # 用跑前的 .bak **逐字节**复原 server.properties

⚠ `run/saves/新的世界` 是**作者的存档**，只许只读比对；本脚本只做 stat，不打开任何区块文件。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time

sys.stdout.reconfigure(errors="replace")

RUN = "run"
SAVES = os.path.join(RUN, "saves")
WORLD = os.path.join(RUN, "world")
PROPS = os.path.join(RUN, "server.properties")
BAK = "build/bgn10rg-server.properties.bak"
SNAP_BEFORE = "build/bgn10rg-run-before.json"
SNAP_AFTER = "build/bgn10rg-run-after.json"
OUT = "build/bgn10rg-run-prep.txt"


def tree(path: str) -> dict:
    """目录清单：文件数 / 总字节 / 最大 mtime / 每个文件的 (相对路径, 字节, mtime)"""
    if not os.path.isdir(path):
        return {"exists": False}
    items = []
    for root, _dirs, files in os.walk(path):
        for f in files:
            p = os.path.join(root, f)
            st = os.stat(p)
            items.append([os.path.relpath(p, path).replace("\\", "/"), st.st_size, int(st.st_mtime)])
    items.sort()
    return {
        "exists": True,
        "files": len(items),
        "bytes": sum(i[1] for i in items),
        "max_mtime": max([i[2] for i in items], default=0),
        "detail": items,
    }


def sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest().upper()


def log(lines: list[str]) -> None:
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "before"
    os.makedirs("build", exist_ok=True)
    if mode == "before":
        snap = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "saves": tree(SAVES),
            "world": tree(WORLD),
            "server_properties_sha": sha(PROPS),
            "server_properties_bytes": os.path.getsize(PROPS),
        }
        with open(SNAP_BEFORE, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(snap, fh, ensure_ascii=False, indent=2)
        shutil.copyfile(PROPS, BAK)          # **字节**复制（不是文本复制）
        msg = [
            "[跑前留档] " + snap["time"],
            "  run/saves   : files={} bytes={} max_mtime={}".format(
                snap["saves"].get("files"), snap["saves"].get("bytes"), snap["saves"].get("max_mtime")),
            "  run/world   : files={} bytes={}".format(
                snap["world"].get("files"), snap["world"].get("bytes")),
            "  server.props: sha={} bytes={}".format(snap["server_properties_sha"][:16],
                                                     snap["server_properties_bytes"]),
            "  已备份 → {}（sha {}）".format(BAK, sha(BAK)[:16]),
        ]
        print("\n".join(msg))
        log(msg)
    elif mode == "after":
        before = json.load(open(SNAP_BEFORE, encoding="utf-8"))
        after = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "saves": tree(SAVES),
            "world": tree(WORLD),
            "server_properties_sha": sha(PROPS),
            "server_properties_bytes": os.path.getsize(PROPS),
        }
        with open(SNAP_AFTER, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(after, fh, ensure_ascii=False, indent=2)
        same_saves = (before["saves"] == after["saves"])
        msg = [
            "[跑后复核] " + after["time"],
            "  run/saves   : files {} → {} / bytes {} → {} / 逐文件全等={}".format(
                before["saves"].get("files"), after["saves"].get("files"),
                before["saves"].get("bytes"), after["saves"].get("bytes"), same_saves),
            "  run/world   : files {} → {} / bytes {} → {}".format(
                before["world"].get("files"), after["world"].get("files"),
                before["world"].get("bytes"), after["world"].get("bytes")),
            "  server.props: {} ({}) → {} ({})".format(
                before["server_properties_sha"][:16], before["server_properties_bytes"],
                after["server_properties_sha"][:16], after["server_properties_bytes"]),
            "  ⇒ 作者存档 run/saves 是否一个字节没动：{}".format("是" if same_saves else "**否**"),
        ]
        print("\n".join(msg))
        log(msg)
    elif mode == "restore":
        if not os.path.isfile(BAK):
            raise SystemExit("[失败] 没有跑前备份")
        want = sha(BAK)
        shutil.copyfile(BAK, PROPS)          # 字节复制 = 逐字节复原
        got = sha(PROPS)
        msg = [
            "[复原] server.properties 用跑前 .bak 字节复制回来",
            "  sha256 期望 {} / 实际 {} / 一致={}".format(want, got, want == got),
        ]
        print("\n".join(msg))
        log(msg)
        if want != got:
            raise SystemExit("[失败] 复原后 SHA 不一致")
    else:
        raise SystemExit("用法: before | after | restore")


if __name__ == "__main__":
    main()
