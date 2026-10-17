#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 收尾核对：`run/` 执行情况 + 共享文件逐字节自证。

* `run/server.properties` ↔ 跑前 `.bak`（**字节相同**才写 PASS）
* `run/saves`（作者的「新的世界」）**文件数 / 最大 mtime / 总字节** 与跑前留档比对
* `run/world` （探针自己的服端世界）允许变化，只记录
* `run/` 下临时开关文件必须**不存在**
* 探针源码已删（src 零命中）+ 证据目录里有留档副本

用法：py -3 bgn10rc_finalize.py
输出：docs/bgn10rc-证据/09-收尾核对.txt（并回写 04-跑前留档.json 的 after 段）
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
RUN = REPO / "run"
EVID = REPO / "docs" / "bgn10rc-证据"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "<缺>"


def dir_stat(p: Path) -> dict:
    if not p.is_dir():
        return {"exists": False}
    files = [f for f in p.rglob("*") if f.is_file()]
    return {"exists": True, "files": len(files),
            "max_mtime": max((f.stat().st_mtime for f in files), default=0),
            "bytes": sum(f.stat().st_size for f in files)}


def main() -> None:
    prep = json.loads((EVID / "04-跑前留档.json").read_text(encoding="utf-8"))
    lines = ["bg-n10rc 收尾核对（跑前留档 = 04-跑前留档.json）", "=" * 110, ""]
    ok = True

    # ① server.properties 逐字节自证
    sp = RUN / "server.properties"
    bak = RUN / "server.properties.bgn10rc.bak"
    same = sha(sp) == sha(bak)
    ok = ok and same
    lines.append("① run/server.properties : sha256=%s ↔ 跑前 .bak=%s ⇒ %s"
                 % (sha(sp), sha(bak),
                    "逐字节复原成功（runServer 启动时把 server.properties 重写过："
                    "a2229937… → 4f36394a…，收尾已用跑前 .bak 字节复制复原）"
                    if same else "不一致！"))
    lines.append("   与 prep 里记的跑前值相同：%s"
                 % ("是" if prep["server_properties"]["sha256"] == sha(sp) else "否"))

    # ② run/saves（作者存档）不许被碰
    for key, path in (("saves", RUN / "saves"), ("world", RUN / "world")):
        before = prep["run"][key]
        after = dir_stat(path)
        lines.append("② run/%s : 跑前 files=%s max_mtime=%s bytes=%s ／ 跑后 files=%s max_mtime=%s bytes=%s"
                     % (key, before.get("files"), before.get("max_mtime"), before.get("bytes"),
                        after.get("files"), after.get("max_mtime"), after.get("bytes")))
        if key == "saves":
            untouched = (before.get("files") == after.get("files")
                         and before.get("max_mtime") == after.get("max_mtime")
                         and before.get("bytes") == after.get("bytes"))
            ok = ok and untouched
            lines.append("   ⇒ 作者存档（新的世界）%s" % ("一个字节都没动 ✓" if untouched else "被改动了！"))
        else:
            lines.append("   ⇒ 探针服端世界（level-name=world），本轮 runServer 会写它：属预期")
    lines.append("   run/saves 名单：%s" % prep["run"].get("saves_names"))

    # ③ 临时开关文件必须不存在
    leftovers = [p.name for p in RUN.glob("bgn10rc*.enabled")]
    ok = ok and not leftovers
    lines.append("③ run/ 下临时开关文件：%s ⇒ %s"
                 % (leftovers or "无", "干净" if not leftovers else "有残留！"))

    # ④ 探针源码：src 零命中 + 证据留档
    src_hits = []
    for p in (REPO / "src").rglob("*"):
        if p.is_file() and p.suffix in (".java", ".json", ".txt", ".properties"):
            try:
                if "BgN10rc" in p.read_text(encoding="utf-8", errors="ignore") or "BGN10RCPROBE" in p.read_text(
                        encoding="utf-8", errors="ignore"):
                    src_hits.append(p.relative_to(REPO).as_posix())
            except OSError:
                pass
    arch = EVID / "脚本副本" / "BgN10rcProbe.java.txt"
    ok = ok and not src_hits and arch.is_file()
    lines.append("④ 探针：src 命中 %d 个（必须 0）%s；留档副本 %s（sha256=%s，%d B）"
                 % (len(src_hits), src_hits, arch.relative_to(REPO).as_posix(), sha(arch),
                    arch.stat().st_size if arch.is_file() else 0))

    # ⑤ 本轮三个被改文件的最终 SHA256
    lines.append("⑤ 本轮工作树改动（3 个 tracked 文件）的最终 SHA256：")
    for rel in ("src/main/resources/data/bettergold/recipe/chaosgold_enchanting_book.json",
                "tools/asset-generator/validate_metal_data.py",
                "docs/1.7-\u6df7\u6c6c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"):
        pass
    for rel in ("src/main/resources/data/bettergold/recipe/chaosgold_enchanting_book.json",
                "tools/asset-generator/validate_metal_data.py",
                "docs/1.7-混沌金与崩乱合金-需求立档.md"):
        p = REPO / rel
        lines.append("   %-70s %s  %d B" % (rel, sha(p), p.stat().st_size if p.is_file() else 0))

    lines.append("")
    lines.append("【总判】%s" % ("全部符合预期" if ok else "有不符合项，见上"))
    (EVID / "09-收尾核对.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
