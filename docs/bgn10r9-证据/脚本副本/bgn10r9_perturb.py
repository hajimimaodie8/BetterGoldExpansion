#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10r9_perturb.py —— 轮9 关卡的**扰动实测**（每个用例逐字节复原 + SHA256 自证）。

7 个用例（6 红 + 1 绿）：
  P01 手册某页的配方引用改成不存在的 id            ⇒ validate_metal_data 必须红
  P02 手册 chaos_feast 删掉第 3 页（spotlight）    ⇒ validate_metal_data 必须红（页型序列）
  P03 崩乱合金「块或模板」的 requirements 改成两组 ⇒ validate_advancements 必须红（组内 OR 变 AND）
  P04 混沌金武器成就的 have_knife 换成裸 id        ⇒ validate_advancements 必须红（安全范式）
  P05 一条新 en 值改成与 zh 逐字相同               ⇒ validate_metal_data 必须红（没翻译）
  P06 只在 validate_metal_data.py 里加一行注释/空白 ⇒ **必须仍绿**（反空转）
  P07 两族 8 条成就删掉一条（treasure/chaos_coin） ⇒ validate_advancements 必须红

用法：``py -3 docs/bgn10r9-证据/脚本副本/bgn10r9_perturb.py``（结果打印 + 落 docs/bgn10r9-证据/03-扰动矩阵.txt）
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[3]
GEN = REPO / "tools" / "asset-generator"
VDATA = GEN / "validate_metal_data.py"
VADV = GEN / "validate_advancements.py"
BOOK = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "patchouli_books" / \
    "alchemy_handbook" / "zh_cn" / "entries"
ADV = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "advancement"
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"
OUT = REPO / "docs" / "bgn10r9-证据" / "03-扰动矩阵.txt"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def run(v: Path) -> tuple:
    r = subprocess.run([sys.executable, str(v)], capture_output=True)
    out = (r.stdout + r.stderr).decode("utf-8", "replace")
    hits = []
    for line in out.splitlines():
        if "FAIL" in line or "[bg-data-fail]" in line or "问题合计" in line:
            hits.append(line.strip()[:200])
    return r.returncode, hits


CASES = []


def case(name: str, target: Path, mutate, validator: Path, want_red: bool, tag: str) -> None:
    CASES.append((name, target, mutate, validator, want_red, tag))


# ---------- P01 手册配方引用改成不存在的 id ----------
def _p01(raw: bytes) -> bytes:
    j = json.loads(raw.decode("utf-8"))
    for pg in j["pages"]:
        if "recipe" in pg:
            pg["recipe"] = "bettergold:__no_such_recipe__"
            break
    return (json.dumps(j, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


case("P01 手册配方引用改成不存在的 id", BOOK / "chaos_materials.json", _p01, VDATA, True,
     "bgbook-recipe-refs / bgn10r9-book")


# ---------- P02 chaos_feast 删掉第 3 页 ----------
def _p02(raw: bytes) -> bytes:
    j = json.loads(raw.decode("utf-8"))
    del j["pages"][2]
    return (json.dumps(j, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


case("P02 chaos_feast 删掉第 3 页（spotlight）", BOOK / "chaos_feast.json", _p02, VDATA, True,
     "bgn10r9-book")


# ---------- P03 supply 的 requirements 改成两组（OR 变 AND）----------
def _p03(raw: bytes) -> bytes:
    j = json.loads(raw.decode("utf-8"))
    j["requirements"] = [["have_block"], ["have_template"]]
    return (json.dumps(j, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


case("P03 supply 的 requirements 改成两组（OR→AND）", ADV / "metal" / "chaosalloy" / "supply.json",
     _p03, VADV, True, "bgn10r9-adv-chaos-chain")


# ---------- P04 have_knife 换成裸 id ----------
def _p04(raw: bytes) -> bytes:
    j = json.loads(raw.decode("utf-8"))
    j["criteria"]["have_knife"]["conditions"]["items"] = [{"items": "bettergold:chaosgold_knife"}]
    return (json.dumps(j, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


case("P04 混沌金武器 have_knife 换成裸 id", ADV / "metal" / "chaosgold" / "weapon.json", _p04,
     VADV, True, "bgfix3-knife-in-gear")


# ---------- P05 一条新 en 值改成与 zh 逐字相同 ----------
def _p05(raw: bytes) -> bytes:
    j = json.loads(raw.decode("utf-8"))
    zh = json.loads((LANG / "zh_cn.json").read_text(encoding="utf-8"))
    j["bettergold.handbook.entry.gear_chaosgold"] = zh["bettergold.handbook.entry.gear_chaosgold"]
    return (json.dumps(j, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


case("P05 新 en 值改成与 zh 逐字相同", LANG / "en_us.json", _p05, VDATA, True, "bgn10r9-lang")


# ---------- P06 只改注释 / 加空白 ⇒ 必须仍绿 ----------
def _p06(raw: bytes) -> bytes:
    return ("\n# bgn10r9 perturbation: 只加一行注释，不应改变任何判定\n" + raw.decode("utf-8")) \
        .encode("utf-8") if not raw.startswith(b"\xef\xbb\xbf") else raw


case("P06 只加一行注释（必须仍绿）", VDATA, _p06, VDATA, False, "（无，期望 0 问题）")


# ---------- P07 删掉 treasure/chaos_coin 成就 ----------
case("P07 删掉 treasure/chaos_coin（treasure 只剩 10 个孩子）", ADV / "treasure" / "chaos_coin.json",
     lambda raw: b"", VADV, True, "bgach-shape-treasure-children")


def main() -> int:
    lines = ["轮9 扰动矩阵（bg-n10r9）—— 每个用例：改字节 → 跑关卡 → 判读 → 逐字节复原 → SHA256 自证",
             "=" * 110, ""]
    ok_all = True
    for i, (name, target, mutate, validator, want_red, tag) in enumerate(CASES, 1):
        if not target.is_file():
            lines.append("%02d %-46s SKIP（目标不存在：%s）" % (i, name, target.name))
            ok_all = False
            continue
        before = target.read_bytes()
        sha_before = sha(target)
        try:
            target.write_bytes(mutate(before))
            code, hits = run(validator)
            red = code != 0
            judge = "红" if red else "绿"
            passed = (red == want_red)
            ok_all = ok_all and passed
            hit_tag = tag if red else "-"
            lines.append("%02d %-46s 关卡 exit=%d（判 %s）期望 %s ⇒ %s  [%s]"
                         % (i, name, code, judge, "红" if want_red else "绿",
                            "PASS" if passed else "FAIL", hit_tag))
            for h in hits[:3]:
                lines.append("      · " + h)
        finally:
            target.write_bytes(before)
        sha_after = sha(target)
        restored = sha_after == sha_before
        ok_all = ok_all and restored
        lines.append("      复原：sha256 %s %s" % ("一致" if restored else "不一致!!", sha_after[:32]))
        lines.append("")
    lines.append("结论：%s（%d 个用例）" % ("全过" if ok_all else "有失败", len(CASES)))
    text = "\n".join(lines) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    print(text)
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
