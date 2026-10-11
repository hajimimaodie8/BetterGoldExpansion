#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgfix9：run\\ 跑测的准备与复原（**逐字节**，不经过 PowerShell 文本转码）。

用法：
    python docs/bgfix9-证据/run_setup.py prepare     # 备份 server.properties + 记 run/saves 清单 + 改 level-name + 建开关
    python docs/bgfix9-证据/run_setup.py restore     # 逐字节复原 + 复核 SHA256 + 删开关 + 删本轮探针世界

口径（`docs\\构建与跑测注意事项.md` / `ex/05`）：
  * `run\\server.properties` 的临时改动**一律用跑前 `.bak` 字节复制复原**（文本往返会加 BOM /
    服务端自己重写头部时间戳行）；复原后必须核对 **SHA256**。
  * 探针世界名 = **ASCII** 且**不是作者存档名**（`新的世界`）；作者的存档在 `run/saves/` 下，
    本脚本只**记录**它的名字/文件数/mtime，**绝不打开、绝不写入**。
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RUN = REPO / "run"
PROPS = RUN / "server.properties"
BAK = HERE / "00-改前-server.properties.bak"
SAVES_LIST = HERE / "00-跑前-run-saves清单.txt"
PROBE_WORLD = "bgfix9probe"
FLAG = RUN / "bgfix9s-probe.enabled"
PROBE_WORLD_DIR = RUN / PROBE_WORLD


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def saves_manifest(tag: str) -> str:
    lines = [f"# {tag}：run/saves 清单（只读记录；本脚本不写入该目录）"]
    saves = RUN / "saves"
    if not saves.is_dir():
        lines.append("(run/saves 不存在)")
        return "\n".join(lines) + "\n"
    for d in sorted(x for x in saves.iterdir()):
        if d.is_dir():
            files = [f for f in d.rglob("*") if f.is_file()]
            mtimes = [f.stat().st_mtime for f in files] or [0]
            lines.append(f"{d.name}\t文件数={len(files)}\tmtime_max={max(mtimes):.0f}"
                         f"\tmtime_min={min(mtimes):.0f}")
        else:
            lines.append(f"{d.name}\t<file>\tsize={d.stat().st_size}")
    return "\n".join(lines) + "\n"


def prepare() -> int:
    if not PROPS.is_file():
        print("前置缺失：run/server.properties 不存在")
        return 2
    orig = PROPS.read_bytes()
    if BAK.is_file():
        print(f"[prepare] 已存在跑前备份（不覆盖）：{BAK.name} sha256={sha(BAK.read_bytes())[:16]}")
    else:
        BAK.write_bytes(orig)
        print(f"[prepare] 备份 server.properties -> {BAK.name} sha256={sha(orig)[:16]}…"
              f"（{len(orig)} B）")
    SAVES_LIST.write_text(saves_manifest("跑前"), encoding="utf-8", newline="\n")
    print(f"[prepare] run/saves 清单 -> {SAVES_LIST.name}")
    # 用**字节**替换 level-name 那一行
    old = b"level-name=world"
    new = f"level-name={PROBE_WORLD}".encode()
    if old not in orig:
        have = [ln for ln in orig.split(b"\n") if ln.startswith(b"level-name=")]
        print(f"[prepare] 当前 {have} ⇒ 直接按现有那一行替换")
        if not have:
            print("[prepare] 找不到 level-name 行 ⇒ exit 2")
            return 2
        old = have[0]
    PROPS.write_bytes(orig.replace(old, new, 1))
    print(f"[prepare] level-name: {old.decode()} -> {new.decode()}"
          f"（改后 sha256={sha(PROPS.read_bytes())[:16]}…）")
    FLAG.write_text("bgfix9s\n", encoding="utf-8")
    print(f"[prepare] 开关文件已建：{FLAG}")
    return 0


def restore() -> int:
    if not BAK.is_file():
        print("前置缺失：没有跑前 .bak ⇒ 不敢改（exit 2）")
        return 2
    target = BAK.read_bytes()
    cur = PROPS.read_bytes() if PROPS.is_file() else b""
    print(f"[restore] 当前 sha256={sha(cur)[:16]}… / 目标 sha256={sha(target)[:16]}…")
    shutil.copyfile(BAK, PROPS)          # **字节复制**（不是 git checkout / 文本往返）
    after = PROPS.read_bytes()
    ok = sha(after) == sha(target)
    print(f"[restore] 复原后 sha256={sha(after)[:16]}… 一致={ok}（{len(after)} B）")
    if FLAG.exists():
        FLAG.unlink()
        print(f"[restore] 开关文件已删：{FLAG.name}")
    else:
        print("[restore] 开关文件本来就不在")
    if PROBE_WORLD_DIR.exists():
        shutil.rmtree(PROBE_WORLD_DIR)
        print(f"[restore] 本轮探针世界已删：run/{PROBE_WORLD}/")
    else:
        print(f"[restore] 本轮探针世界本来就不在：run/{PROBE_WORLD}/")
    SAVES_LIST.write_text(saves_manifest("跑后") + "\n--- 跑前 ---\n"
                          + (SAVES_LIST.read_text(encoding="utf-8")
                             if SAVES_LIST.is_file() else ""),
                          encoding="utf-8", newline="\n")
    print(f"[restore] run/saves 跑后清单已写进 {SAVES_LIST.name}（与跑前逐行对照）")
    return 0 if ok else 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prepare":
        raise SystemExit(prepare())
    if cmd == "restore":
        raise SystemExit(restore())
    print(__doc__)
    raise SystemExit(2)
