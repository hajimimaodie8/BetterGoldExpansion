# -*- coding: utf-8 -*-
"""bg-n10rc2 跑测前置：server.properties 字节备份 + run/saves 快照 + 开关文件。

纪律：修改/恢复一律走 bytes（PowerShell 的 Get-Content/Set-Content 会按 ANSI 解码再按 UTF-8
写出，把中文注释写坏 —— 本仓踩过）。
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
RUN = REPO / "run"
OUT = REPO / "docs" / "bgn10rc2-证据"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def snapshot(tag: str) -> dict:
    saves = RUN / "saves"
    files = []
    total = 0
    if saves.is_dir():
        for p in sorted(saves.rglob("*")):
            if p.is_file():
                files.append({"path": p.relative_to(RUN).as_posix(),
                              "size": p.stat().st_size,
                              "mtime": p.stat().st_mtime_ns})
                total += p.stat().st_size
    world = RUN / "world"
    wfiles = 0
    wtotal = 0
    if world.is_dir():
        for p in world.rglob("*"):
            if p.is_file():
                wfiles += 1
                wtotal += p.stat().st_size
    data = {
        "tag": tag,
        "server_properties_sha256": sha(RUN / "server.properties"),
        "saves_dirs": sorted([d.name for d in saves.iterdir() if d.is_dir()]) if saves.is_dir() else [],
        "saves_file_count": len(files),
        "saves_total_bytes": total,
        "saves_files": files,
        "world_file_count": wfiles,
        "world_total_bytes": wtotal,
    }
    return data


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "before"
    OUT.mkdir(parents=True, exist_ok=True)
    props = RUN / "server.properties"
    bak = RUN / "server.properties.bgn10rc2.bak"
    if mode == "before":
        if not bak.exists():
            shutil.copyfile(props, bak)          # 逐字节复制
        data = snapshot("before")
        (OUT / "04-跑前留档.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (RUN / "bgn10rc2-probe.enabled").write_bytes(b"1\n")
        print("before: props sha=%s (bak sha=%s) saves=%d files/%d B world=%d files/%d B"
              % (data["server_properties_sha256"][:16], sha(bak)[:16],
                 data["saves_file_count"], data["saves_total_bytes"],
                 data["world_file_count"], data["world_total_bytes"]))
    else:
        data = snapshot("after")
        (OUT / "05-跑后复核.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # 逐字节复原 server.properties（跑前那份 .bak 的字节）
        shutil.copyfile(bak, props)
        sw = RUN / "bgn10rc2-probe.enabled"
        if sw.exists():
            sw.unlink()
        print("after : props sha=%s restored sha=%s bak=%s saves=%d files/%d B world=%d files/%d B"
              % (data["server_properties_sha256"][:16], sha(props)[:16], sha(bak)[:16],
                 data["saves_file_count"], data["saves_total_bytes"],
                 data["world_file_count"], data["world_total_bytes"]))


if __name__ == "__main__":
    main()
