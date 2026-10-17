# -*- coding: utf-8 -*-
"""把两轮 runServer 日志里的探针行抽成 UTF-8 证据文件（PowerShell 的 `1>` 写出的是 UTF-16LE）。

同时：把探针源码与扰动备份复制进证据目录（**删之前先复制**），再报告 src 内的命中数。
"""
import codecs
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs" / "bgn10rc2-证据"
COPY = OUT / "脚本副本"
TAG = "BGN10RC2PROBE"


def decode(p: Path) -> str:
    raw = p.read_bytes()
    if raw[:2] == codecs.BOM_UTF16_LE or (len(raw) > 1 and raw[1:2] == b"\x00"):
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def extract(log: Path, dest: Path, title: str) -> tuple[int, int, int]:
    text = decode(log)
    lines = [l for l in text.splitlines() if TAG in l]
    body = ["# " + title, "# 来源 = run/logs 汇总（gradlew runServer 的 stdout）: " + log.name,
            "# 说明：日志本体是 UTF-16LE，本文件已转成 UTF-8、只保留探针行", ""]
    for l in lines:
        body.append(l[l.index(TAG):])
    dest.write_text("\n".join(body) + "\n", encoding="utf-8")
    passed = sum(1 for l in lines if " PASS " in l)
    failed = sum(1 for l in lines if " FAIL " in l)
    return len(lines), passed, failed


def main() -> None:
    COPY.mkdir(parents=True, exist_ok=True)
    a = extract(REPO / "build" / "bgn10rc2-runserver-1.log", OUT / "01-A级读数.txt",
                "bg-n10rc2 A 级读数（干净构建：4 件 + 双倍 + 只返 1 瓶 + chaosalloy + 燃油）")
    b = extract(REPO / "build" / "bgn10rc2-runserver-2-double.log", OUT / "02-双返负向读数.txt",
                "bg-n10rc2 双返负向（故意注入「第二格也塞瓶」）：期望 _bottle_total=2 ⇒ 红")
    print("01 lines=%d pass=%d fail=%d" % a)
    print("02 lines=%d pass=%d fail=%d" % b)

    src = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "probe" / "BgN10rc2Probe.java"
    if src.is_file():
        shutil.copyfile(src, COPY / "BgN10rc2Probe.java.txt")
        src.unlink()
        d = src.parent
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    for p in sorted((REPO / "probe" / "bgn10rc2").glob("*.orig")):
        shutil.copyfile(p, COPY / ("扰动备份-" + p.name))
    hits = 0
    for p in (REPO / "src").rglob("*"):
        if p.is_file() and p.suffix in (".java", ".json", ".toml", ".txt"):
            t = p.read_text(encoding="utf-8", errors="replace")
            if "BgN10rc2" in t or "BGN10RC2" in t or "bgn10rc2" in t:
                hits += 1
                print("HIT:", p.relative_to(REPO))
    print("src hits:", hits)


if __name__ == "__main__":
    main()
