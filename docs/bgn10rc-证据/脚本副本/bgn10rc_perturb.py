#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 扰动矩阵（8 用例）：把某一格换物品 / 换数量 / 换位置 / 只改注释。

判据：
* 每个"真扰动"必须 **exit 1**，且**点名**到对应的 tag（不是靠别的段红）；
* "只改注释"必须 **exit 0**（关卡不许被注释骗过）；
* 每个用例跑完**逐字节复原** + SHA256 自证（与改前逐一相等）；
* 全部跑完再确认整体回到 exit 0。

用法：py -3 bgn10rc_perturb.py
输出：docs/bgn10rc-证据/03-扰动矩阵.txt
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
EVID = REPO / "docs" / "bgn10rc-证据"
RECIPE = REPO / "src/main/resources/data/bettergold/recipe"
VALIDATOR = REPO / "tools/asset-generator/validate_metal_data.py"
GEN = REPO / "tools/asset-generator/generate_chaosalloy_recipes.py"

BOOK = RECIPE / "chaosgold_enchanting_book.json"
TEMPLATE = RECIPE / "chaosalloy_upgrade_template.json"
ANVIL = RECIPE / "sturdygold_anvil.json"
COPPER = RECIPE / "copper_block_with_chaos_coin.json"

CASES = [
    # (id, 目标, [(old, new), ...], 期望 exit, 期望命中的 tag)
    ("book-diag-swap（把两条对角线换回去 = 旧口径）", BOOK,
     [('"LIS"', '"LIL"'), ('"SIL"', '"SIS"')], 1,
     ["bgn10r4-enchanting-book", "bgn10rc-cell"]),
    ("book-count-2（产物数量 1 → 2）", BOOK,
     [('"count": 1', '"count": 2')], 1, ["bgn10rc-result"]),
    ("book-coin（混沌金币串 → 混沌金币）", BOOK,
     [('"item": "bettergold:chaos_coin_string"', '"item": "bettergold:chaos_coin"')], 1,
     ["bgn10rc-cell", "bgn10rc-book-coin"]),
    ("template-cell（中上 混沌金锭 → 混沌金块）", TEMPLATE,
     [('"GIG"', '"GIC"')], 1, ["bgn10rc-cell"]),
    ("anvil-cell（右下 金锭 → 万坚金锭）", ANVIL,
     [('"ISI"', '"ISS"')], 1, ["bgn10rc-cell"]),
    ("filler-count（铜 4 → 3）", COPPER,
     [('\n    { "item": "minecraft:copper_ingot" },', '')], 1, ["bgn10rc-filler"]),
    ("generator-pattern（真源模板排布 GCG → GIG）", GEN,
     [('"GCG"', '"GIG"')], 1, ["bgn10rc-generator"]),
    ("comment-only（只在关卡里加一条注释，注释里逐字含错的排布）", VALIDATOR,
     [("_EXIT_PROBLEM_LISTS = (missing_zh,",
       "# 扰动占位注释：LIL/IBI/SIS / GIG/GAG/GIG / 9 格全错（本行不得影响任何判定）\n"
       "_EXIT_PROBLEM_LISTS = (missing_zh,")], 0, []),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_validator() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(VALIDATOR)], cwd=REPO, capture_output=True)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", errors="replace")


def main() -> None:
    original = {c[1]: c[1].read_bytes() for c in CASES}
    lines: list[str] = [
        "bg-n10rc 扰动矩阵（判据：真扰动 exit 1 + 点名 tag；只改注释 exit 0；每例逐字节复原）",
        "=" * 110,
        "",
    ]

    base_exit, _ = run_validator()
    lines.append("【基线】validate_metal_data.py exit=%d 【%s】"
                 % (base_exit, "绿" if base_exit == 0 else "红"))
    assert base_exit == 0, "基线就不绿，先修好再做扰动"

    ok_all = True
    for name, path, subs, want_exit, want_tags in CASES:
        before_sha = sha(path)
        raw = original[path]
        for old, new in subs:
            old_b = old.encode("utf-8") if isinstance(old, str) else old
            new_b = new.encode("utf-8") if isinstance(new, str) else new
            if raw.count(old_b) < 1:
                raise SystemExit("扰动 %s：锚点 %r 在 %s 里 0 次" % (name, old, path.name))
            raw = raw.replace(old_b, new_b, 1)
        path.write_bytes(raw)
        after_sha = sha(path)
        perturbed_len = path.stat().st_size
        code, out = run_validator()
        path.write_bytes(original[path])                 # ← 逐字节复原
        restored_sha = sha(path)
        hit = [t for t in want_tags if t in out]
        tags_ok = len(hit) == len(want_tags)
        exit_ok = code == want_exit
        restore_ok = restored_sha == before_sha
        ok_all = ok_all and tags_ok and exit_ok and restore_ok
        lines.append("### %s" % name)
        lines.append("  文件      : %s" % path.relative_to(REPO).as_posix())
        lines.append("  改后      : sha256=%s（%d B）" % (after_sha, perturbed_len))
        lines.append("  exit      : %d（期望 %d）%s" % (code, want_exit, "PASS" if exit_ok else "FAIL"))
        lines.append("  命中 tag  : %s（期望 %s）%s" % (hit, want_tags, "PASS" if tags_ok else "FAIL"))
        lines.append("  复原      : sha256=%s ↔ 改前 %s %s"
                     % (restored_sha, before_sha, "一致" if restore_ok else "不一致"))
        for ln in out.splitlines():
            if "问题合计" in ln:
                lines.append("  ★ 读数    : %s" % ln.strip())
                break
        for ln in out.splitlines():
            if "[bgn10rc" in ln or "[bgn10r4-enchanting-book]" in ln:
                lines.append("  → 点名    : %s" % ln.strip()[:200])
        lines.append("")
        print("[%s] exit=%d tags=%s restore=%s" % (name, code, hit, restore_ok))

    fin_exit, _ = run_validator()
    lines.append("【收尾】复原后 validate_metal_data.py exit=%d 【%s】"
                 % (fin_exit, "绿" if fin_exit == 0 else "红"))
    lines.append("【总判】%s" % ("全部符合预期" if (ok_all and fin_exit == 0) else "有用例不符"))
    (EVID / "03-扰动矩阵.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines[-4:]))
    raise SystemExit(0 if (ok_all and fin_exit == 0) else 1)


if __name__ == "__main__":
    main()
