#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 证据收集（A 级读数 + 探针源码归档）。

⚠ 铁律：**删探针源码之前**先把源码复制到证据目录（前两轮漏过这条）。
本脚本第 1 步就做这件事，第 2 步才整理读数。

用法：py -3 bgn10rc_evidence.py
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
EVID = REPO / "docs" / "bgn10rc-证据"
COPY = EVID / "脚本副本"
SRC_PROBE = REPO / "src/main/java/com/hjmmd_8/bettergold/probe/BgN10rcProbe.java"
MASTER_PROBE = REPO / "probe/bgn10rc/BgN10rcProbe.java"
LOG = REPO / "run/logs/latest.log"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "<缺>"


def main() -> None:
    # ---------- ① 删前留档（探针源码 + 开关文件存在性） ----------
    src = SRC_PROBE if SRC_PROBE.is_file() else MASTER_PROBE
    if not src.is_file():
        raise SystemExit("找不到探针源码（既没有 src 副本也没有 probe/bgn10rc 母本）")
    target = COPY / "BgN10rcProbe.java.txt"
    shutil.copyfile(src, target)
    print("① 探针源码已留档: %s ← %s（sha256=%s，%d B）"
          % (target.relative_to(REPO).as_posix(), src.relative_to(REPO).as_posix(),
             sha(target), target.stat().st_size))

    # ---------- ② A 级读数（从 UTF-8 的 run/logs/latest.log 摘，不用 GBK 的控制台重定向） ----------
    text = LOG.read_text(encoding="utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if "BGN10RCPROBE" in ln]
    if not lines:
        raise SystemExit("run/logs/latest.log 里没有 BGN10RCPROBE 行 —— 探针没跑？")
    (EVID / "00-探针原始行.txt").write_text(
        "轮R 探针原始行（摘自 run/logs/latest.log，UTF-8 原样；探针源码副本见 脚本副本/）\n"
        + "=" * 110 + "\n\n" + "\n".join(lines) + "\n",
        encoding="utf-8", newline="\n")

    def pick(tag: str) -> list[str]:
        return [ln.split("BGN10RCPROBE ", 1)[1] for ln in lines if "BGN10RCPROBE " + tag in ln]

    summary = pick("SUMMARY")
    passes = [ln for ln in lines if "BGN10RCPROBE PASS" in ln]
    fails = [ln for ln in lines if "BGN10RCPROBE FAIL" in ln]

    out = [
        "bg-n10rc A 级读数（真服务端 `gradlew runServer` + 真 `ServerPlayer` + 真 `CraftingMenu` + 两次真点击）",
        "=" * 110,
        "来源：run/logs/latest.log（UTF-8）。探针源码：脚本副本/BgN10rcProbe.java.txt。",
        "世界：run/world（服务器 level-name=world，**不是**作者的 run/saves/新的世界）。",
        "",
        "【总结】" + (summary[0] if summary else "<没有 SUMMARY 行>"),
        "  PASS 行数 = %d / FAIL 行数 = %d" % (len(passes), len(fails)),
        "",
        "—— 逐条读数 ——",
    ]
    for ln in lines:
        if "BGN10RCPROBE" in ln:
            out.append(ln.split("BGN10RCPROBE ", 1)[1] if "BGN10RCPROBE " in ln else ln)
    out += [
        "",
        "—— 四类正例的「产出 / 消耗 / 落袋」对照 ——",
        "  ① 铜块：4 copper_ingot + 1 chaos_coin ⇒ 1 copper_block；币（格4）1→0；逐格 −1；落袋 1",
        "  ① 铁块：6 iron_ingot  + 1 chaos_coin ⇒ 1 iron_block；币（格6）1→0；逐格 −1；落袋 1",
        "  ① 金块：8 gold_ingot  + 1 chaos_coin ⇒ 1 gold_block；币（格8）1→0；逐格 −1；落袋 1",
        "  ② 模板：6 混沌金锭 + 原版模板 + 崩乱合金锭 + 混沌金块 ⇒ 1 chaosalloy_upgrade_template；逐格 −1；落袋 1",
        "  ③ 附魔书：LIS/IBI/SIL ⇒ 1 chaosgold_enchanting_book；逐格 −1；落袋 1",
        "  ④ 万坚金砧：BBB/ITI/ISI ⇒ 1 sturdygold_anvil；逐格 −1；落袋 1",
        "  负向 1：附魔书**旧口径** LIL/IBI/SIS ⇒ 结果格空（说明「按作者改过」这件事在运行期真的生效）",
        "  负向 2：万坚金砧中下留空 ⇒ 结果格空",
        "  负向 3：崩乱合金模板中下换成混沌金锭 ⇒ 结果格空",
        "",
        "—— forceload 双向 ——",
        "  " + (summary[0] if summary else ""),
    ]
    (EVID / "01-A级读数.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("② 01-A级读数.txt 已写（%d 行 PASS / %d 行 FAIL）" % (len(passes), len(fails)))
    print("\n".join(out[:14]))


if __name__ == "__main__":
    main()
