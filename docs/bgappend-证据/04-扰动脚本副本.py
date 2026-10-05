#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-append 追加轮 · 关卡扰动实测（会话标记 bgappend）

做法（照 mcmod_experience §3.4）：
  * 每条用例 = **对文件做一处真实的"改坏"** → 跑关卡 → 断言
    ① 退出码非 0、② 期望的稳定 ASCII id **确实出现**、③ 至少有一条 FAIL；
  * **基线**（不动）必须 exit 0；
  * **"只改注释必须仍绿"反向对照**：往源码里插一段注释 → 必须 exit 0；
  * 收尾：逐字节复原 + **SHA256 自证**（改前 == 改后）。

⚠ 兜底：`sys.stdout.reconfigure(errors="replace")` —— 断言消息里的非 GBK 字符
   会让 print 直接抛 UnicodeEncodeError，于是"关卡红了"变成"关卡崩了"（看起来像没命中）。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools" / "asset-generator"
BG3_ZH = REPO / "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/golden_knowledge.json"
BG3_EN = REPO / "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/en_us/entries/golden_knowledge.json"
LANG_ZH = REPO / "src/main/resources/assets/bettergold/lang/zh_cn.json"
LANG_EN = REPO / "src/main/resources/assets/bettergold/lang/en_us.json"
GEN = TOOLS / "generate_handbook_data.py"
MEV = REPO / "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java"
CLIENT = REPO / "src/main/java/com/hjmmd_8/bettergold/bettergoldClient.java"
ROSE = REPO / "src/main/resources/data/bettergold/recipe/golden_rose_bush.json"
ROSE_DYE = REPO / "src/main/resources/data/bettergold/recipe/yellow_dye_from_golden_rose_bush.json"
ADV = REPO / "src/main/resources/data/bettergold/advancement"
SPEC = REPO / "docs/1.6-规格.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------
# 用例定义： (编号, 目标文件, 期望 tag, 变更函数)
# 变更函数 = 传入原文，返回新文；只做**一处**改动。
# ---------------------------------------------------------------------------------


def _jl(v):
    return json.dumps(v, ensure_ascii=False)


def m_k3_no_title(txt: str) -> str:
    d = json.loads(txt)
    d["pages"][0].pop("title", None)
    return _jl(d)


def m_k3_ingot_dropped(txt: str) -> str:
    d = json.loads(txt)
    d["pages"][0]["item"] = d["pages"][0]["item"][:-1]   # 少一族锭
    return _jl(d)


def m_k3_summary_key_gone(txt: str) -> str:
    d = json.loads(txt)
    d["pages"][0]["text"] = "bettergold.handbook.page.knowledge_2_left"
    return _jl(d)


def m_k3_right_has_text(txt: str) -> str:
    d = json.loads(txt)
    d["pages"][1]["text"] = "bettergold.handbook.page.knowledge_1_summary"
    return _jl(d)


def m_k3_template_title(txt: str) -> str:
    d = json.loads(txt)
    d["pages"][1]["title"] = "旧标题"
    return _jl(d)


def m_k3_page_dropped(txt: str) -> str:
    d = json.loads(txt)
    d["pages"] = d["pages"][:8]
    return _jl(d)


def m_gen_order_shuffled(txt: str) -> str:
    return txt.replace('"_block", "_bricks", "_pillar"', '"_bricks", "_block", "_pillar"')


CASES = [
    ("01", BG3_ZH, "bgappend-book-k3-p1-ingot-title", m_k3_no_title),
    ("02", BG3_ZH, "bgappend-book-k3-p1-ingots", m_k3_ingot_dropped),
    ("03", BG3_ZH, "bgappend-book-k3-p1-summary", m_k3_summary_key_gone),
    ("04", BG3_ZH, "bgappend-book-k3-p1-summary", m_k3_right_has_text),
    ("05", BG3_ZH, "bgappend-book-k3-p1-template-title", m_k3_template_title),
    ("06", BG3_ZH, "bgappend-book-k3-pages", m_k3_page_dropped),
    ("07", GEN, "bgappend-book-block-order", m_gen_order_shuffled),
]

# 语言文件类的用例（只动一处、且**逐字节**复原）
LANG_CASES = [
    ("08", LANG_ZH, "bgappend-book-building-blocks",
     lambda t: t.replace("使用烈燃金制成的建筑方块", "使用烈燃金作为的建筑方块", 1)),
    ("09", LANG_ZH, "bgappend-book-no-pacify-text",
     lambda t: t.replace("1级6秒的生命恢复状态。",
                         "1级6秒的生命恢复状态，并对玩家发起敌意状态的中立生物在踩踏与贴近时瞬间变为被动形态。", 1)),
    ("10", LANG_ZH, "bgappend-config-i18n",
     lambda t: t.replace('"bettergold.configuration.echogoldWeaponBuffChance": "幽咆金 · 武器工具触发 Buff（音咆）概率",\n', "", 1)),
    ("11", LANG_EN, "bgappend-config-i18n-en",
     lambda t: t.replace('"bettergold.configuration.echogoldWeaponBuffChance": "Echogold - Weapon/Tool Buff (Sonic Roar) Chance"',
                         '"bettergold.configuration.echogoldWeaponBuffChance": "幽咆金 · 武器工具触发 Buff 概率"', 1)),
    ("12", LANG_ZH, "bgappend-config-i18n-zh",
     lambda t: t.replace('"bettergold.configuration.echogoldWeaponBuffChance": "幽咆金 · 武器工具触发 Buff（音咆）概率"',
                         '"bettergold.configuration.echogoldWeaponBuffChance": "echogoldWeaponBuffChance"', 1)),
]

CODE_CASES = [
    # ⚠ 这几份源码是 **CRLF** —— 多行字面量匹配会静默不中（这里用"只换一行"的写法绕开）。
    # ⚠ 另一条同样重要的教训：`if (hitAny)` 改成 `if (false)` **测不出东西** ——
    #   断言看的是 `playSonicBoomSound(` 这个**调用点**还在不在，不是条件真假。
    #   要真的"删掉那一处调用"，必须替换**调用本身**（这里连行一起换成注释）。
    ("13", MEV, "bgappend-sonic-sound-sites",
     lambda t: t.replace("playSonicBoomSound(serverLevel, pos);", "// sound removed", 1)),
    ("13b", MEV, "bgappend-sonic-sound-throttled",
     lambda t: t.replace("if (hitAny) {", "if (false) {", 1)),
    ("14", CLIENT, "bgappend-rose-render-layer",
     lambda t: t.replace("ItemBlockRenderTypes.setRenderLayer(AllBlocks.GOLDEN_ROSE_BUSH.get(), cutout);",
                         "// removed", 1)),
    ("15", ROSE, "bgappend-rose-recipe",
     lambda t: t.replace('"R": {\n      "item": "minecraft:rose_bush"\n    }',
                         '"R": {\n      "item": "minecraft:poppy"\n    }', 1)),
    ("16", ROSE_DYE, "bgappend-rose-dye",
     lambda t: t.replace('"count": 2', '"count": 5', 1)),
]

ADV_CASES = [
    # 把某一类"获得"判据改回"制作"（**完整合法**的 recipe_crafted，别把 JSON 改成解析不了的形状
    # ——那样关卡会以 exit 2 崩掉，反而看不出"命中期望 id"）
    ("17", ADV / "treasure/blazing_rod.json", "bgach-craft-to-have",
     lambda t: t.replace(
         '"have": {\n      "trigger": "minecraft:inventory_changed",\n      "conditions": {\n'
         '        "items": [\n          {\n            "items": "bettergold:blazing_rod"\n          }\n'
         '        ]\n      }\n    }',
         '"have": {\n      "trigger": "minecraft:recipe_crafted",\n      "conditions": {\n'
         '        "recipe_id": "bettergold:blazing_rod"\n      }\n    }', 1)),
    ("18", ADV / "merchant/gift_box.json", "bgach-craft-to-have-exception",
     lambda t: t.replace('"trigger": "minecraft:villager_trade"', '"trigger": "minecraft:inventory_changed"', 1)),
    # §七.6：把刀塞回"获得武器工具"那条的 items 列表
    ("19", ADV / "metal/flamegold/weapon.json", "bgach-no-knife-in-gear",
     lambda t: t.replace('              "bettergold:flamegold_shield"\n',
                         '              "bettergold:flamegold_shield",\n'
                         '              "bettergold:flamegold_knife"\n', 1)),
]

SPEC_CASES = [
    # 把"冻结快照"这个词整体抹掉（不是加个后缀 —— 那样断言里的 needle 仍然命中，测不出东西）
    ("20", SPEC, "bgappend-doc-snapshot", lambda t: t.replace("冻结快照", "外部需求文档", 3)),
    ("21", SPEC, "bgappend-doc-spotlight", lambda t: t.replace("PageSpotlight", "SpotlightPage", 3)),
]

# 反向对照：**只改注释/加一个不影响判据的字段** ⇒ 必须仍然 exit 0
CONTROLS = [
    ("C1", BG3_ZH, lambda t: t.replace('"category": "bettergold:alchemy_start"',
                                       '"comment_for_control": "只加一个字段，判据不看它",\n  "category": "bettergold:alchemy_start"', 1)),
    ("C2", MEV, lambda t: t.replace("    private static void playSonicBoomSound(",
                                    "    // 只改注释：这一行不该影响任何断言\n    private static void playSonicBoomSound(", 1)),
]


def run(tool: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "-X", "utf8", str(TOOLS / tool)],
                       capture_output=True, cwd=str(REPO))
    out = p.stdout.decode("utf-8", errors="replace") + p.stderr.decode("utf-8", errors="replace")
    return p.returncode, out


def expected_tool(target: Path) -> str:
    return "validate_advancements.py" if "advancement" in str(target) else "validate_metal_data.py"


def main() -> int:
    all_cases = []
    for cid, target, tag, fn in CASES + LANG_CASES + CODE_CASES + ADV_CASES + SPEC_CASES:
        all_cases.append((cid, target, tag, fn, expected_tool(target)))

    originals: dict[Path, bytes] = {}
    for _, target, _, _, _ in all_cases + [(c[0], c[1], "", c[2], "") for c in CONTROLS]:
        originals.setdefault(target, target.read_bytes())
    before = {p: sha(p) for p in originals}

    tool_before = {t: run(t) for t in ("validate_metal_data.py", "validate_advancements.py")}
    print("=== 基线（未改动）===")
    for t, (rc, out) in tool_before.items():
        print("  %-28s exit=%d" % (t, rc))
    if any(rc != 0 for rc, _ in tool_before.values()):
        print("!! 基线就是红的，扰动没有意义 —— 先修基线")
        return 1

    mismatches = []
    for cid, target, tag, fn, tool in all_cases:
        orig = originals[target]
        text = orig.decode("utf-8")
        new = fn(text)
        if new == text:
            mismatches.append((cid, tag, "变更函数没有真正改到内容（用例本身失效）"))
            print("  [%s] !! 变更未生效" % cid)
            continue
        target.write_bytes(new.encode("utf-8"))
        rc, out = run(tool)
        hit = ("[%s]" % tag) in out
        ok = rc != 0 and hit
        print("  [%s] %-22s target=%-52s exit=%d hit_expected=%s %s"
              % (cid, tag, target.name, rc, hit, "OK" if ok else "MISMATCH"))
        if not ok:
            reasons = []
            if rc == 0:
                reasons.append("关卡没红（exit 0）")
            if not hit:
                reasons.append("没有命中期望 id %s" % tag)
            tail = "\n".join(l for l in out.splitlines() if "bgappend" in l or "bgach" in l)[:400]
            mismatches.append((cid, tag, "; ".join(reasons) + (" | " + tail if tail else "")))
        target.write_bytes(orig)

    print("=== 反向对照：只改注释/加无关键字段 ⇒ 必须仍绿 ===")
    for cid, target, fn in CONTROLS:
        orig = originals[target]
        new = fn(orig.decode("utf-8"))
        if new == orig.decode("utf-8"):
            mismatches.append((cid, "control", "对照变更没有生效"))
            print("  [%s] !! 变更未生效" % cid)
            continue
        target.write_bytes(new.encode("utf-8"))
        rc, out = run(expected_tool(target) if cid != "C2" else "validate_metal_data.py")
        ok = rc == 0
        print("  [%s] %-24s exit=%d %s" % (cid, target.name, rc, "OK" if ok else "MISMATCH"))
        if not ok:
            tail = "\n".join(out.strip().splitlines()[-4:])
            mismatches.append((cid, "control", "只改注释却变红：\n%s" % tail))
        target.write_bytes(orig)

    after = {p: sha(p) for p in originals}
    print("=== 字节级复原自证（SHA256）===")
    bad = []
    for p in sorted(originals, key=str):
        same = before[p] == after[p]
        if not same:
            bad.append(p)
        print("  %s  %s" % ("OK " if same else "!! ", str(p.relative_to(REPO))))
        print("      %s" % before[p])
    if bad:
        mismatches.append(("RESTORE", "sha256", "这些文件没有逐字节复原：%s" % bad))

    print()
    print("用例数 = %d（扰动）+ %d（反向对照）  mismatches = %d" % (len(all_cases), len(CONTROLS), len(mismatches)))
    for m in mismatches:
        print("  MISMATCH %s [%s] %s" % m)
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
