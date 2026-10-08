# -*- coding: utf-8 -*-
"""收尾核对：产物 jar 名 / jar 内是否有 *Probe* 路径 / class 里是否含 halt 字节。

==================== 关卡退出码契约（bgfix6，2026-10-08）====================
  0 = 全绿：真的读到了 jar，且三个计数（*Probe* 路径 / 含 'halt' 字节的 class /
      含 'BG-PROBE' 常量的 class）**全部为 0**
  1 = 有「问题」：三个计数**任一 > 0**（探针残留进了产物）
  2 = 基线被破坏 / 前置缺失 / 脚本自身出错：jar 不存在、jar 读不开、jar 内 0 个条目
  ★ **任何未捕获异常都不许变成 0**：顶层 try/except 一律转成 2。
  ★ **反空转**：必须打印「实际检查了 N 项」并断言 N > 0（N = jar 内条目数）；
    **jar 不存在 ⇒ exit 2，绝不许当成「0 个探针 ⇒ 干净」**。
  依据：`docs/构建与跑测注意事项.md`「关卡的退出码契约」；
        `mod_experience\\ex\\03-验证与证据.md` §3.19。
==========================================================================

⚠⚠ bgfix6（2026-10-08）**就地标注**：本关卡原先**全篇没有 `sys.exit`**
（旧行为 = 只 print、退出码恒 0）⇒ 探针还在 jar 里时它照样报 "exit 0"，
收尾汇报里那句「六校验器全部 exit 0」在这一条上是**假绿**（`docs/1.6-规格.md` §26.9 记账、
§26.10 第 6 条「本轮不改它，超出范围」—— 本轮 bgfix6 §27 就是来修这一条的）。
**旧打印一字未删**（原文保留），只在后面补了 exit 2 前置、反空转与退出码结论行。
⚠ 判定口径**未动**：`b"halt" in data` / `"Probe" in n or "probe" in n.lower()` / `b"BG-PROBE" in data`
三条判据与原来逐字相同（不许放宽来减少红）。
"""
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
LIBS = REPO / "build" / "libs"


def main() -> int:
    jars = sorted(LIBS.glob("*.jar"))
    print("build/libs jars:")
    for j in jars:
        print(f"  {j.name}  ({j.stat().st_size} bytes)")

    # ⚠ bg-16（1.6）：**jar 名必须从 gradle.properties 的 mod_version 现算**，不许写死 ——
    #   写死 1.5.0 时，1.6.0 这一轮里这个关卡会去检查一个**过期的旧 jar**（而且照样全绿），
    #   于是"收尾核对"检查的根本不是这一轮的产物（旧 jar 里当然没有新探针）。
    _props = (REPO / "gradle.properties").read_text(encoding="utf-8")
    _m = re.search(r"^mod_version\s*=\s*(\S+)\s*$", _props, re.MULTILINE)
    _version = _m.group(1) if _m else "0.0.0"
    target = LIBS / f"bettergold-{_version}.jar"
    print(f"\n产物 bettergold-{_version}.jar（来自 gradle.properties 的 mod_version）存在 = {target.is_file()}")
    if len(jars) > 1:
        print(f"  ⚠ build/libs 里有 {len(jars)} 个 jar（旧版本的 jar 会留在这里）——"
              f"只核对上面这一个；跑 `gradlew clean` 可在干净树里复核")

    # ---------------- bgfix6：前置缺失 ⇒ exit 2（原来的 `if target.is_file():` 没有 else 分支）----------------
    if not target.is_file():
        print(f"FAIL [jar-clean-jar-missing] 产物 jar 不存在：{target}")
        print("      ⇒ 基线被破坏（前置缺失）。**不是**「0 个探针 ⇒ 干净」；本关卡 exit 2")
        return 2

    try:
        zf = zipfile.ZipFile(target)
    except Exception as exc:  # noqa: BLE001 —— 读不开 = 前置坏，绝不当成"干净"
        print(f"FAIL [jar-clean-jar-unreadable] jar 读不开：{exc!r}")
        print("      ⇒ 基线被破坏（前置缺失）；本关卡 exit 2")
        return 2

    with zf:
        names = zf.namelist()
        probe_paths = [n for n in names if "Probe" in n or "probe" in n.lower()]
        print(f"jar 内 *Probe* 路径 = {len(probe_paths)} {probe_paths[:5]}")
        halt_classes = []
        for n in names:
            if n.endswith(".class"):
                data = zf.read(n)
                # 常量池里的 "halt" 会以 UTF8 常量出现；直接找字节序列
                if b"halt" in data:
                    halt_classes.append(n)
        print(f"jar 内含 'halt' 字节的 class = {len(halt_classes)} {halt_classes[:5]}")
        probe_str = [n for n in names if n.endswith(".class") and b"BG-PROBE" in zf.read(n)]
        print(f"jar 内含 'BG-PROBE' 常量的 class = {len(probe_str)} {probe_str[:5]}")
        print(f"jar 内文件总数 = {len(names)}")

    # ---------------- bgfix6：反空转（真的读到了 jar）----------------
    print(f"[jar-clean-anti-vacuum] 实际检查了 {len(names)} 项（jar 内条目数；必须 > 0）")
    if len(names) <= 0:
        print("FAIL [jar-clean-anti-vacuum] jar 内 0 个条目 ⇒ 基线坏了（读到的不是产物）⇒ 本关卡 exit 2")
        return 2

    # ---------------- bgfix6：结论 + 退出码（三个计数任一 > 0 ⇒ 1）----------------
    problems = []
    if probe_paths:
        problems.append(f"[jar-clean-probe-residue] jar 内有 *Probe* 路径 {len(probe_paths)} 条：{probe_paths[:5]}")
    if halt_classes:
        problems.append(f"[jar-clean-halt-byte] jar 内有 {len(halt_classes)} 个 class 含 'halt' 字节：{halt_classes[:5]}")
    if probe_str:
        problems.append(f"[jar-clean-bg-probe-const] jar 内有 {len(probe_str)} 个 class 含 'BG-PROBE' 常量：{probe_str[:5]}")
    if problems:
        for _p in problems:
            print(f"FAIL {_p}")
        print(f"[jar-clean-fail] 产物 jar 不干净：问题 {len(problems)} 条 ⇒ 本关卡 exit 1")
        return 1
    print(f"[jar-clean-ok] 产物 jar 干净（条目 {len(names)}；*Probe* 0 / 'halt' 字节 0 / 'BG-PROBE' 0）")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"关卡自身出错（exit 2）：{exc!r}")
        raise SystemExit(2)
