#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-fix3 关卡扰动实测（1 基线 + N 条改坏 + 2 条「只改注释必须仍绿」+ 收尾基线）。

契约（mcmod_experience ex/03 §3.4 / §3.11 / §3.13）：
  * 每条用例只匹配**稳定的 ASCII 断言 id**，不匹配中文消息；
  * 「改坏」之后必须自证「确实改了」（new == old ⇒ SETUP-FAIL，不算命中）；
  * 期望 exit=1 **且** 期望 id 出现在输出里 —— 只看退出码会被"红在别的判据上"骗过；
  * 只做**单文件**内存级改坏：写完立刻按原始字节复原，收尾逐文件核对 SHA256。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:  # noqa: BLE001
    pass

REPO = Path(__file__).resolve().parents[1]  # 本脚本放 build/ ⇒ parents[1] = 仓库根
ADV = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "advancement"
TAGS = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "tags" / "item"
BOOK = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "patchouli_books" / "alchemy_handbook" / "zh_cn" / "entries"
GEN_HANDBOOK = REPO / "tools" / "asset-generator" / "generate_handbook_data.py"
JAVA_HANDBOOK = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "patchouli" / "HandbookModule.java"

VA = "validate_advancements"
VM = "validate_metal_data"

# (名字, 脚本, 文件, 旧文本, 新文本, 期望 id, 期望退出码)
CASES = [
    # ---------- ③ 乐事小刀纳入「获得武器工具」 ----------
    ("P01-刀判据指向别族标签", VA, ADV / "metal/flamegold/weapon.json",
     '"#bettergold:flamegold_knives"', '"#bettergold:sturdygold_knives"',
     "bgfix3-knife-in-gear", 1),
    ("P02-刀判据从 OR 组里拿出来（组间 AND）", VA, ADV / "metal/flamegold/weapon.json",
     '  "requirements": [\n    [\n      "have",\n      "have_knife"\n    ]\n  ],',
     '  "requirements": [\n    [\n      "have"\n    ],\n    [\n      "have_knife"\n    ]\n  ],',
     "bgfix3-knife-in-gear", 1),
    ("P03-裁掉 have_knife 判据", VA, ADV / "metal/flamegold/weapon.json",
     '    "have_knife": {\n      "trigger": "minecraft:inventory_changed",\n      "conditions": {\n        "items": [\n          {\n            "items": "#bettergold:flamegold_knives"\n          }\n        ]\n      }\n    }\n',
     '', "bgfix3-knife-in-gear", 1),
    # ---------- 标签：required:false / 成员 ----------
    ("P04-标签条目改成 required:true", VA, TAGS / "flamegold_knives.json",
     '"required": false', '"required": true', "bgfix3-adv-tag-optional", 1),
    ("P05-标签成员写错物品", VA, TAGS / "flamegold_knives.json",
     '"bettergold:flamegold_knife"', '"bettergold:flamegold_sword"', "bgfix3-adv-tag-members", 1),
    ("P06-裁掉 handbook 标签文件", VA, TAGS / "handbook.json", None, "<DELETE>", "bgfix3-adv-tag-file", 1),
    # ---------- ⑤ 根成就改「获得」 ----------
    ("P07-root 判据改回 recipe_crafted（合法但语义相反）", VA, ADV / "root.json",
     '    "have_handbook": {\n      "trigger": "minecraft:inventory_changed",\n      "conditions": {\n'
     '        "items": [\n          {\n            "items": "#bettergold:handbook"\n          }\n'
     '        ]\n      }\n    }',
     '    "have_handbook": {\n      "trigger": "minecraft:recipe_crafted",\n      "conditions": {\n'
     '        "recipe_id": "bettergold:alchemy_student_handbook"\n      }\n    }',
     "bgfix3-recipe-crafted-none", 1),
    ("P08-root 的标签指错", VA, ADV / "root.json",
     '"#bettergold:handbook"', '"#bettergold:handbook_two"', "bgfix3-adv-tag-refs", 1),
    ("P09-别的成就混进 recipe_crafted（合法但语义相反）", VA, ADV / "metal/flamegold/ingot.json",
     '    "have": {\n      "trigger": "minecraft:inventory_changed",\n      "conditions": {\n'
     '        "items": [\n          {\n            "items": "bettergold:flamegold_ingot"\n          }\n'
     '        ]\n      }\n    }',
     '    "have": {\n      "trigger": "minecraft:recipe_crafted",\n      "conditions": {\n'
     '        "recipe_id": "bettergold:flamegold_ingot"\n      }\n    }',
     "bgfix3-recipe-crafted-none", 1),
    # ---------- ⑥ 排版：四级链 + 挑战 frame ----------
    ("P10-盔甲 frame 改回 task", VA, ADV / "metal/flamegold/armor.json",
     '"frame": "challenge"', '"frame": "task"', "bgach-frame-challenge", 1),
    ("P11-盔甲挂回锭下（链断）", VA, ADV / "metal/flamegold/armor.json",
     '"parent": "bettergold:metal/flamegold/weapon",', '"parent": "bettergold:metal/flamegold/ingot",',
     "bgfix3-metal-chain", 1),
    ("P12-炼制II 挂回 root（链式退成并列）", VA, ADV / "alchemy/alchemic_fuel.json",
     '"parent": "bettergold:alchemy/mixed_crystal_pile",', '"parent": "bettergold:root",',
     "bgfix3-root-chain", 1),
    # ---------- ④ 手册删两节 ----------
    ("P13-作废条目回到产物", VM, BOOK / "metal_tour.json", None, None,
     "bgfix3-old-skeleton-gone", 1),
    ("P14-生成器里删掉 entry_metal_tour 构造函数", VM, GEN_HANDBOOK,
     "def entry_metal_tour():", "def entry_metal_tour_retired():", "bgfix3-generator-retired", 1),
    ("P15-把 entry_metal_tour 塞回 ENTRIES", VM, GEN_HANDBOOK,
     "\nENTRIES = [\n", "\nENTRIES = [\n    entry_metal_tour,\n", "bgfix3-generator-retired", 1),
    # ---------- 标签机制与文档锚点（收口轮补的三条） ----------
    #   ⚠ 第一版把常量名改成 `OPTIONAL_ITEM_TAG_VALUES_RENAMED` —— 那是**它的前缀**，
    #     针（子串匹配）照样命中 ⇒ 关卡没红、用例却被记成 MISMATCH（mcmod_experience ex/03 §3.12 的陷阱）。
    #     ⇒ 替换串**必须不含原针**，并且要改**全部出现处**（all 模式）。
    ("P16-标签生成器删掉计划表常量（all 模式）", VM, REPO / "tools" / "asset-generator" / "generate_metal_tags.py",
     "OPTIONAL_ITEM_TAG_VALUES", "OPTIONAL_TAG_PLAN", "bgfix3-tag-generator", 1),
    ("P17-删掉一张刀标签文件", VM, TAGS / "flamegold_knives.json", None, "<DELETE>",
     "bgfix3-tag-generator", 1),
    ("P18-规格里抹掉『链式』口径（all 模式）", VM, REPO / "docs" / "1.6-规格.md",
     "链式", "并式（扰动占位）", "bgfix3-doc", 1),
    # ---------- 反向对照：只改注释必须仍绿 ----------
    ("R01-只往生成器 ENTRIES 加一句注释（必须仍绿）", VM, GEN_HANDBOOK,
     "\nENTRIES = [\n",
     "\nENTRIES = [\n    # bgfix3 反向对照：entry_metal_tour / entry_upgrade_templates 已作废（本行只是注释）\n",
     None, 0),
    ("R02-只往 HandbookModule 加一句注释提到 ITEM_PATH（必须仍绿）", VA, JAVA_HANDBOOK,
     "    public static final String ITEM_PATH =",
     '    // 反向对照注释：ITEM_PATH = "wrong_handbook_value"（真源解析必须先把注释剥掉）\n'
     "    public static final String ITEM_PATH =",
     None, 0),
]

STUB_METAL_TOUR = '{\n  "name": "bettergold.handbook.entry.metal_tour",\n  "category": "bettergold:alchemy_start",\n  "icon": "bettergold:raw_sturdygold",\n  "sortnum": 0,\n  "read_by_default": true,\n  "pages": []\n}\n'


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(script: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(REPO / "tools" / "asset-generator" / f"{script}.py")],
                          cwd=str(REPO), capture_output=True)
    out = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
    return proc.returncode, out


def main() -> int:
    touched: dict[Path, bytes] = {}
    for _, _, path, _, _, _, _ in CASES:
        if path is not None and path not in touched and path.is_file():
            touched[path] = path.read_bytes()
    manifest = {p: hashlib.sha256(b).hexdigest() for p, b in touched.items()}

    print("=== 基线 ===", flush=True)
    results = []
    for script in (VA, VM):
        code, out = run(script)
        print(f"BASELINE {script} exit={code}", flush=True)
        results.append((f"BASELINE-{script}", code, 0, None, code == 0, out))

    created_files = []
    for name, script, path, old, new, want_id, want_exit in CASES:
        existed = path.is_file()
        if not existed:
            created_files.append(path)
        original = path.read_bytes() if existed else None
        if old is None:
            if new == "<DELETE>":
                path.unlink(missing_ok=True)
                changed = existed
            else:
                # 造出"不该存在的文件"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(STUB_METAL_TOUR.encode("utf-8"))
                changed = True
        else:
            text = original.decode("utf-8")
            all_mode = name.startswith("P18") or name.startswith("P16")
            if (text.count(old) < 1) if all_mode else (text.count(old) != 1):
                print(f"SETUP-FAIL {name}: 模式命中 {text.count(old)} 次（要求恰好 1 次）", flush=True)
                results.append((name, None, None, want_id, False, ""))
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(original)
                continue
            new_text = text.replace(old, new) if all_mode else text.replace(old, new, 1)
            changed = new_text != text
            path.write_bytes(new_text.encode("utf-8"))
        if not changed:
            print(f"SETUP-FAIL {name}: 变更未生效", flush=True)
            results.append((name, None, None, want_id, False, ""))

        code, out = run(script)
        # 立刻按原始字节复原
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(original)
        hit = (want_id is None) or (want_id in out)
        ok = (code == want_exit) and hit
        print(f"{'OK   ' if ok else 'MISS '} {name}: exit={code} (期望 {want_exit}) "
              f"hit_expected={hit} [{want_id}]", flush=True)
        results.append((name, code, want_exit, want_id, ok, out))

    print("=== 收尾基线 ===", flush=True)
    for script in (VA, VM):
        code, out = run(script)
        print(f"BASELINE-END {script} exit={code}", flush=True)
        results.append((f"BASELINE-END-{script}", code, 0, None, code == 0, out))

    print("=== 逐字节复原核对（SHA256）===", flush=True)
    restore_ok = True
    for p, want in manifest.items():
        got = sha(p)
        same = got == want
        restore_ok &= same
        print(f"{'OK  ' if same else 'DIFF'} {p.relative_to(REPO)} {got[:16]}", flush=True)
    for p in touched:
        pass
    # 造出来的文件必须已消失
    for path in created_files:
        if path.is_file():
            print(f"DIFF {path.relative_to(REPO)} 还在（本该被删掉）", flush=True)
            restore_ok = False

    mismatches = [r for r in results if not r[4]]
    print(f"\nmismatches = {len(mismatches)} / 用例 {len(results)}")
    for m in mismatches:
        print("  MISMATCH:", m[0], "exit=", m[1], "期望", m[2], "期望 id", m[3])
    if mismatches or not restore_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
