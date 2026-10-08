#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-fix4（bg-fix3 追加轮 + 第四批）关卡扰动实测。

契约（mcmod_experience ex/03 §3.4 / §3.11 / §3.13 / §3.16 / §3.17）：
  * 每条用例只匹配**稳定的 ASCII 断言 id**，不匹配中文消息；
  * 「改坏」之后必须自证「确实改了」（new == old ⇒ SETUP-FAIL，不算命中）；
  * 期望 exit=1 **且** 期望 id 出现在输出里（只看退出码会被"红在别的判据上"骗过）；
  * 只做**单文件**内存级改坏：写完立刻按原始字节复原，收尾逐文件核对 SHA256；
  * 反向对照「只改注释必须仍绿」专钉"正向/负向 needle 都要跑在**去注释**源码上"。

用法：python build/bgfix4_perturb.py
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:  # noqa: BLE001
    pass

REPO = Path(__file__).resolve().parents[1]
JAVA = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
ADV = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "advancement"
TAGS = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "tags" / "item"
BOOK_ZH = (REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "patchouli_books"
           / "alchemy_handbook" / "zh_cn" / "entries" / "golden_knowledge.json")
LANG_ZH = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang" / "zh_cn.json"
LANG_EN = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang" / "en_us.json"
GLM = JAVA / "registry" / "AllLootModifiers.java"
CREATIVE = JAVA / "material" / "CreativeSections.java"
CONFIG = JAVA / "config" / "Config.java"
GEN_ADV = REPO / "tools" / "asset-generator" / "generate_advancements.py"
GEN_BOOK = REPO / "tools" / "asset-generator" / "generate_handbook_data.py"
SPEC = REPO / "docs" / "1.6-规格.md"

VA = "validate_advancements"
VM = "validate_metal_data"

# (名字, 脚本, 文件, 旧文本, 新文本, 期望 id, 期望退出码)
CASES = [
    # ---------- bg-fix3 追加轮：藤条去掉万坚金豁免 ----------
    ("P01-isOurTool 加回 isSpecialMetal 豁免", VM, GLM,
     '            return family != null\n'
     '                    && (family.isTool(tool.getItem()) || family.isWeapon(tool.getItem()));',
     '            return family != null && family.isSpecialMetal()\n'
     '                    && (family.isTool(tool.getItem()) || family.isWeapon(tool.getItem()));',
     "bgfix4-vine-all-metals", 1),
    ("P02-isOurTool 丢掉器具那一半", VM, GLM,
     '            return family != null\n'
     '                    && (family.isTool(tool.getItem()) || family.isWeapon(tool.getItem()));',
     '            return family != null\n'
     '                    && (family.isTol(tool.getItem()) || family.isWeapon(tool.getItem()));',
     "bgfix4-vine-all-metals", 1),
    ("P03-藤条基础概率被改", VM, GLM,
     "public static final float BASE_CHANCE = 0.06F;",
     "public static final float BASE_CHANCE = 0.07F;",
     "bgfix2-vine-chance", 1),
    # ---------- ② 顺序真源 / 两处同序 ----------
    ("P04-顺序真源（METAL_ORDER）改一位", VM, CREATIVE,
     '"sturdygold",     // 万坚金', '"sturdygoldz",    // 万坚金',
     "bgfix4-metal-order-single-source", 1),
    ("P05-成就生成器的 METALS 换序", VM, GEN_ADV,
     'METALS = ["flamegold", "sturdygold"', 'METALS = ["sturdygold", "flamegold"',
     "bgfix4-metal-order-single-source", 1),
    ("P06-手册生成器的 METALS 换序", VM, GEN_BOOK,
     '    ("flamegold", "blazing_rod"),\n    ("sturdygold", "golden_cowrie"),',
     '    ("sturdygold", "golden_cowrie"),\n    ("flamegold", "blazing_rod"),',
     "bgfix4-metal-order-single-source", 1),
    # ---------- ④ 建筑方块 11 项的顺序真源 ----------
    ("P07-生成器回到旧建筑顺序（栏杆在门之前）", VM, GEN_BOOK,
     '    "_bricks_wall", "_door", "_trapdoor", "_bars", "_chain", "_lantern",',
     '    "_bricks_wall", "_bars", "_door", "_trapdoor", "_chain", "_lantern",',
     "bgfix4-building-order-single-source", 1),
    ("P08-生成器少一种建材形态", VM, GEN_BOOK,
     '    "_bricks_wall", "_door", "_trapdoor", "_bars", "_chain", "_lantern",',
     '    "_bricks_wall", "_door", "_trapdoor", "_bars", "_chain",',
     "bgappend-book-block-order", 1),
    # ---------- ④ 字幕（语言值必须逐字来自冻结快照） ----------
    ("P09-字幕中文值被改", VM, LANG_ZH,
     '"bettergold.handbook.page.knowledge_2_left_title": "烈燃金建筑方块"',
     '"bettergold.handbook.page.knowledge_2_left_title": "烈燃金砖块"',
     "bgfix4-build-title-verbatim", 1),
    ("P10-字幕英文值被改成与中文相同", VM, LANG_EN,
     '"bettergold.handbook.page.knowledge_3_left_title": "Thornsgold Building Blocks"',
     '"bettergold.handbook.page.knowledge_3_left_title": "树棘金建筑方块"',
     "bgfix4-build-title-verbatim", 1),
    ("P11-建材页展示栏少一件（产物）", VM, BOOK_ZH,
     '        "bettergold:flamegold_chain",\n', '',
     "bgfix4-build-title-verbatim", 1),
    ("P12-复原页的锭表换一件", VM, BOOK_ZH,
     '        "bettergold:illusiongold_ingot"', '        "bettergold:illusiongold_ingot_x"',
     "bgfix4-k3p1-restored", 1),
    ("P13-建材页 title 指错键", VM, BOOK_ZH,
     '"title": "bettergold.handbook.page.knowledge_5_right_title"',
     '"title": "bettergold.handbook.page.knowledge_9_right_title"',
     "bgfix4-build-title-verbatim", 1),
    # ---------- ① 两条古董成就 ----------
    ("P14-古董屠刀那条从 OR 组里被拿掉", VA, ADV / "merchant" / "antique_tool.json",
     '  "requirements": [\n    [\n      "have",\n      "have_knife"\n    ]\n  ],',
     '  "requirements": [\n    [\n      "have"\n    ]\n  ],',
     "bgfix4-antique-knife-in-gear", 1),
    ("P15-幽冥断骸刀那条改成组间 AND", VA, ADV / "merchant" / "netherite_antique_tool.json",
     '  "requirements": [\n    [\n      "have",\n      "have_knife"\n    ]\n  ],',
     '  "requirements": [\n    [\n      "have"\n    ],\n    [\n      "have_knife"\n    ]\n  ],',
     "bgfix4-antique-knife-in-gear", 1),
    ("P16-古董刀的判据指向不存在的标签", VA, ADV / "merchant" / "antique_tool.json",
     '"items": "#bettergold:antique_knives"', '"items": "#bettergold:antique_knives_x"',
     "bgfix4-antique-knife-in-gear", 1),
    # ---------- 标签机制（11 张） ----------
    ("P17-删掉一张古董刀标签文件", VM, TAGS / "antique_knives.json", None, "<DELETE>",
     "bgfix3-tag-generator", 1),
    ("P18-标签条目改成 required:true", VA, TAGS / "antique_knives.json",
     '"required": false', '"required": true',
     "bgfix3-adv-tag-optional", 1),
    # ---------- 文档锚点 ----------
    ("P19-规格里抹掉『建筑方块』（all 模式）", VM, SPEC,
     "建筑方块", "构筑方块", "bgfix4-doc", 1),
    ("P20-规格里抹掉门禁项的关键词 ReferenceOpenHashSet", VM, SPEC,
     "ReferenceOpenHashSet", "引用哈希集合", "bgfix4-doc", 1),
    # ---------- 反向对照：只改注释必须仍绿（ex/03 §3.17） ----------
    ("R01-在 isOurTool 里加注释逐字提到 isSpecialMetal()（必须仍绿）", VM, GLM,
     "        private static boolean isOurTool(ItemStack tool) {",
     "        private static boolean isOurTool(ItemStack tool) {\n"
     "            // 反向对照：这里提到 family.isSpecialMetal() 只是注释（判据必须跑在去注释源码上）",
     None, 0),
    ("R02-在生成器常量上方加注释写出旧建筑顺序（必须仍绿）", VM, GEN_BOOK,
     "METAL_BLOCK_SUFFIX_ORDER = [",
     "# 反向对照注释：旧顺序是 _bars 在 _door 之前（本行只是注释）\nMETAL_BLOCK_SUFFIX_ORDER = [",
     None, 0),
    ("R03-在 Config.java 加注释写出错的金属顺序（必须仍绿）", VM, CONFIG,
     "    // ==================== bg-fix4 §二：16 条的**声明顺序** ====================",
     "    // 反向对照注释（是错的顺序，只是注释）：sturdygold → illusiongold → flamegold\n"
     "    // ==================== bg-fix4 §二：16 条的**声明顺序** ====================",
     None, 0),
]


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
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"{}\n")
                changed = True
        else:
            text = original.decode("utf-8")
            all_mode = name.startswith("P19") or name.startswith("P20")
            hit_count = text.count(old)
            if (hit_count < 1) if all_mode else (hit_count != 1):
                print(f"SETUP-FAIL {name}: 模式命中 {hit_count} 次", flush=True)
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
    for path in created_files:
        if path.is_file():
            print(f"DIFF {path.relative_to(REPO)} 还在（本该被删掉）", flush=True)
            restore_ok = False

    mismatches = [r for r in results if not r[4]]
    print(f"\nmismatches = {len(mismatches)} / 用例 {len(results)}")
    for m in mismatches:
        print("  MISMATCH:", m[0], "exit=", m[1], "期望", m[2], "期望 id", m[3])
        if m[1] is not None and m[1] == 2:
            print("    （exit 2 = 用例自己坏了；输出尾部）", m[5][-400:].replace("\n", " | "))
    if mismatches or not restore_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
