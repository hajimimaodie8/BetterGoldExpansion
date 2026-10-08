#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgfix5 关卡扰动实测（进度树 8 条线次序真正固定 / 彩虹序 = 现行序 / 五处同序）。

契约（mcmod_experience ex/03 §3.4 / §3.11 / §3.16 / §3.17）：
  * 每条用例只匹配**稳定的 ASCII 断言 id**（`[bgfix5-*]`），不匹配中文消息；
  * 「改坏」之后必须自证「确实改了」（new == old ⇒ SETUP-FAIL，不算命中）；
  * 期望 exit=1 **且** 期望 id 出现在输出里（只看退出码会被"红在别的判据上"骗过）；
  * 只做**单文件**内存级改坏：写完立刻按原始字节复原，收尾逐文件核对 SHA256；
  * 反向对照「**只改注释必须仍绿**」专钉"正向/负向 needle 都要跑在**去注释**源码上"
    （§3.17：负向检查跑在含注释源码上会假红、正向检查会假绿 —— 本脚本 P12 就是正向那一半）。

用法（仓库根）：python build/bgfix5_perturb.py
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
MIXIN_JSON = REPO / "src" / "main" / "resources" / "bettergold.mixins.json"
ORDER_CLS = JAVA / "advancement" / "AdvancementTreeOrder.java"
MIXIN_CLS = JAVA / "mixin" / "AdvancementNodeChildrenOrderMixin.java"
SPEC = REPO / "docs" / "1.6-规格.md"

VM = "validate_metal_data"
VA = "validate_advancements"

ID_SRC = "bgfix5-tree-order-single-source"
ID_5 = "bgfix5-metal-order-five-places"
ID_DOC = "bgfix5-doc"

# (名字, 脚本, 文件, 旧文本, 新文本, 期望 id, 期望退出码)
CASES = [
    # ---------- ① 排序类：守卫 / 真源 / 唯一 id ----------
    ("P01-守卫改成命名空间前缀匹配", VM, ORDER_CLS,
     "        if (!isGuardedParent(parentId)) {",
     '        if (!parentId.toString().startsWith("bettergold:")) {',
     ID_SRC, 1),
    ("P02-排序类里加第二份族名列表", VM, ORDER_CLS,
     '    private static final String NS = "bettergold";',
     '    private static final String NS = "bettergold";\n'
     '    private static final java.util.List<String> FAMILIES = java.util.List.of("flamegold", "sturdygold");',
     ID_SRC, 1),
    ("P03-排序类里加第二个 bettergold: 字面量", VM, ORDER_CLS,
     '    private static final String NS = "bettergold";',
     '    private static final String NS = "bettergold";\n'
     '    private static final String OTHER = "bettergold:treasure/any_raw_metal";',
     ID_SRC, 1),
    ("P04-位次不再来自真源 METAL_ORDER", VM, ORDER_CLS,
     "CreativeSections.METAL_ORDER.indexOf(family)",
     "CreativeSections.allMetalIds().indexOf(family)",
     ID_SRC, 1),
    # ---------- ② mixin：三件事 ----------
    ("P05-mixin 的 require 不是 1", VM, MIXIN_CLS,
     "            require = 1,", "            require = 2,",
     ID_SRC, 1),
    ("P06-mixin 去掉完整描述符", VM, MIXIN_CLS,
     'method = "children()Ljava/lang/Iterable;",', 'method = "children",',
     ID_SRC, 1),
    ("P07-mixin 里加族名字面量", VM, MIXIN_CLS,
     "public abstract class AdvancementNodeChildrenOrderMixin {",
     'public abstract class AdvancementNodeChildrenOrderMixin {\n'
     '    private static final String F = "flamegold";',
     ID_SRC, 1),
    # ---------- ③ mixins.json：键名与列表（静默失效的形状） ----------
    ("P08-mixin 从 mixins 挪到 client 列表", VM, MIXIN_JSON,
     '  "mixins": [\n    "CrossbowChargeDurationMixin",\n    "AdvancementNodeChildrenOrderMixin"\n  ],\n'
     '  "client": [\n',
     '  "mixins": [\n    "CrossbowChargeDurationMixin"\n  ],\n'
     '  "client": [\n    "AdvancementNodeChildrenOrderMixin",\n',
     ID_SRC, 1),
    ("P09-双端列表键名改成 common（静默不加载）", VM, MIXIN_JSON,
     '  "mixins": [', '  "common": [',
     ID_SRC, 1),
    # ---------- ④ 数据侧：线起点与白名单父节点 ----------
    ("P10-一条线的起点改挂到别的父节点", VM, ADV / "treasure" / "amethyst_energy_dust.json",
     '"parent": "bettergold:treasure/any_core_material"',
     '"parent": "bettergold:treasure/blazing_rod"',
     ID_SRC, 1),
    ("P11-非族节点 any_raw_metal 改挂到别处", VM, ADV / "treasure" / "any_raw_metal.json",
     '"parent": "bettergold:treasure/any_core_material"',
     '"parent": "bettergold:treasure/blazing_rod"',
     ID_SRC, 1),
    ("P12-真源 METAL_ORDER 少一族（五处同序崩）", VM, JAVA / "material" / "CreativeSections.java",
     '"illusiongold");  // 幻惑金（1.5）', '"illusiongoldX");  // 幻惑金（1.5）',
     ID_5, 1),
    # ---------- ⑤ 正向 needle 必须跑在去注释源码上（§3.17 的对偶） ----------
    ("P13-require 只留在注释里（正向 needle 必须仍红）", VM, MIXIN_CLS,
     "            require = 1,", "            // require = 1,   <- 只留在注释里",
     ID_SRC, 1),
    # ---------- ⑥ 反向对照：**只改注释必须仍绿** ----------
    ("R01-排序类注释里写满族名/startsWith（必须仍绿）", VM, ORDER_CLS,
     '    private static final String NS = "bettergold";',
     '    // 反向对照："flamegold" "sturdygold" startsWith("bettergold:") 都只出现在注释里\n'
     '    private static final String NS = "bettergold";',
     None, 0),
    ("R02-mixin 注释里写 require = 1 / 族名（必须仍绿）", VM, MIXIN_CLS,
     "public abstract class AdvancementNodeChildrenOrderMixin {",
     "// 反向对照注释：require = 1 / \"flamegold\" / startsWith( 都只在这里\n"
     "public abstract class AdvancementNodeChildrenOrderMixin {",
     None, 0),
    # ---------- ⑦ 文档侧 need（整份替换：名字以 PA 开头） ----------
    ("PA14-规格里删掉「材料区位次」（bgfix5-doc 崩）", VM, SPEC,
     "材料区位次", "材料区顺序",
     ID_DOC, 1),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(script: str):
    proc = subprocess.run([sys.executable, str(REPO / "tools" / "asset-generator" / f"{script}.py")],
                          cwd=str(REPO), capture_output=True)
    out = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
    return proc.returncode, out


def main() -> int:
    touched = {}
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

    for name, script, path, old, new, want_id, want_exit in CASES:
        if not path.is_file():
            print(f"SETUP-FAIL {name}: 文件不存在 {path}", flush=True)
            results.append((name, None, None, want_id, False, ""))
            continue
        original = path.read_bytes()
        text = original.decode("utf-8")
        all_mode = name.startswith("PA")
        hit_count = text.count(old)
        if (hit_count < 1) if all_mode else (hit_count != 1):
            print(f"SETUP-FAIL {name}: 模式命中 {hit_count} 次", flush=True)
            results.append((name, None, None, want_id, False, ""))
            path.write_bytes(original)
            continue
        new_text = text.replace(old, new)
        changed = new_text != text
        path.write_bytes(new_text.encode("utf-8"))
        if not changed:
            print(f"SETUP-FAIL {name}: 变更未生效", flush=True)
            results.append((name, None, None, want_id, False, ""))

        code, out = run(script)
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
