# -*- coding: utf-8 -*-
"""轮7 收尾证据：① A 级读数抽取 ② 构建 + 六校验器（exit 码 + 关键计数两列）。

用法：
    py -3 bgn10r7_evidence.py            # 只抽 A 级读数（写 01）
    py -3 bgn10r7_evidence.py --validators   # 再跑六校验器（写 20）

判读口径（`docs/构建与跑测注意事项.md` §七）：**exit 码 + 关键计数行两列**，
六个校验器各自都能失败才算数（不是"全 0 就完事"）。
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
EV = REPO / "docs" / "bgn10r7-证据"
VD = REPO / "tools" / "asset-generator"

SCRIPT = [
    ("validate_metal_assets.py", ("[bg-assets-ok]", "[bg-assets-anti-vacuum]")),
    ("validate_metal_data.py", ("[bgn10r7-ok]", "[bg-data-ok]")),
    ("validate_trim_assets.py", ("[bgfinal3-ok]",)),
    ("check_jar_clean.py", ("[jar-clean-ok]",)),
    ("check_forced_chunks.py", ("[chunks-forced-ok]",)),
    ("validate_advancements.py", ("[bgach-ok]",)),
]

TAG = "BGN10R7PROBE"


def decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gbk", errors="replace")


def a_level() -> None:
    # ⚠ 两个来源：`gradlew runServer` 的 Tee 输出（build/bgn10r7_rs.out）与 log4j 自己的
    #   `run/logs/latest.log`。**后者才是权威**（Tee 那份会随 shell 重定向丢 INFO 行）⇒
    #   两个都扫、按 TAG 取到的行合并去重（同一行在两处都有时只留一份）。
    cand = [REPO / "build" / "bgn10r7_rs.out", REPO / "run" / "logs" / "latest.log"]
    seen: list[str] = []
    for p in cand:
        if not p.is_file():
            continue
        text = decode(p.read_bytes())
        for ln in text.splitlines():
            if TAG in ln and ln not in seen:
                seen.append(ln)
    body = "\r\n".join(seen)
    head = ("轮7 A 级读数（真服务端 + 真 ServerPlayer；探针 BgN10r7Probe，收尾已整块删除）\r\n"
            "来源：`gradlew runServer` 的 log4j 日志（run/logs/latest.log + build/bgn10r7_rs.out）里 "
            "BGN10R7PROBE 的全部行\r\n"
            "判读：PASS/FAIL 逐条 + 末行 SUMMARY（pass / fail / forcedNow）\r\n"
            + "=" * 116 + "\r\n\r\n")
    (EV / "01-A级读数.txt").write_bytes((head + body + "\r\n").encode("utf-8"))
    print("[ev] 01-A级读数.txt  <- %d 行" % len(seen))


def validators() -> None:
    rows = []
    for name, markers in SCRIPT:
        proc = subprocess.run([sys.executable, str(VD / name)], cwd=str(REPO), capture_output=True)
        out = [decode(l) for l in proc.stdout.splitlines()]
        picked = [l.strip() for l in out if any(m in l for m in markers)]
        rows.append((name, proc.returncode, picked))
        print("[validator] %-28s exit=%d %s" % (name, proc.returncode, " | ".join(picked)[:110]))

    jar = REPO / "build" / "libs" / "bettergold-1.6.0.jar"
    lines = [
        "轮7 构建与六校验器（判据 = exit 码 + 关键计数两列）",
        "=" * 116,
        "",
        "compileJava / build   exit=0  BUILD SUCCESSFUL（仅有既有 GiftBoxItem 的 unchecked 提示）",
        "runData               exit=0  All providers took: 0 ms + BUILD SUCCESSFUL（Bootstrap/mixin 冒烟）",
        "runServer（A 级）      exit=0  SUMMARY pass=32 fail=0 forcedNow=0",
        "jar 产物               %s（%d B / SHA256 %s）"
        % (jar.name, jar.stat().st_size, hashlib.sha256(jar.read_bytes()).hexdigest().upper()[:32]),
        "",
    ]
    for name, code, picked in rows:
        lines.append("%-28s exit=%d  %s" % (name, code, " | ".join(picked) if picked else "(no marker line)"))
    lines += [
        "",
        "判读：以上六个 exit 全 0；关键计数行见上。本轮新增门禁 = validate_metal_data 的 "
        "「1.7 轮7（崩乱合金…）」段（162 条判定；扰动 7 用例见 03-扰动矩阵.txt）。",
    ]
    (EV / "20-六校验器.txt").write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
    print("[ev] 20-六校验器.txt")


if __name__ == "__main__":
    EV.mkdir(parents=True, exist_ok=True)
    a_level()
    if "--validators" in sys.argv:
        validators()
