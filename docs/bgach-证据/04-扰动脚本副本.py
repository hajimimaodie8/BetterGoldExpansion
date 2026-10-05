# -*- coding: utf-8 -*-
"""bg-ach 扰动实测：把关卡（validate_advancements.py）的每条断言真的"改坏 ⇒ 必须红"证明一遍。

纪律（mcmod_experience §3.4 / §5）：
  * 备份-扰动-复原一律**逐字节**（绝不用文本模式读写，避免 CRLF→LF 静默漂移）；
  * 每条用例自证"确实改了文本"（改前 != 改后）；命中期望的 ASCII 断言 id 才算 PASS；
  * 留一条**只改注释必须仍绿**的反向对照（证明判据跑在去注释的源码上）；
  * 全部复原后逐文件核对 SHA256，再跑一次收尾基线。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "tools" / "asset-generator" / "validate_advancements.py"
ADV = "src/main/resources/data/bettergold/advancement/"
LANGD = "src/main/resources/assets/bettergold/lang/"
JAVAD = "src/main/java/com/hjmmd_8/bettergold/"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True, cwd=str(REPO))
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


class Case:
    def __init__(self, name, rel, mutate, tag, red=True, kind="value", delete=False):
        self.name, self.path, self.mutate = name, REPO / rel, mutate
        self.tag, self.red, self.kind, self.delete = tag, red, kind, delete


CASES: list[Case] = []


def add(name, rel, mutate, tag, red=True, kind="value", delete=False):
    CASES.append(Case(name, rel, mutate, tag, red, kind, delete))


def jsonmut(fn):
    def inner(t: bytes) -> bytes:
        obj = json.loads(t.decode("utf-8"))
        fn(obj)
        return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return inner


# ---------------- 值级 ----------------
add("icon-not-exists", ADV + "root.json",
    lambda t: t.replace(b'"id": "minecraft:gold_ingot"', b'"id": "bettergold:nope_ingot"'),
    "[bgach-item-exists]")
add("trigger-not-whitelisted", ADV + "metal/flamegold/ingot.json",
    lambda t: t.replace(b'"minecraft:inventory_changed"', b'"minecraft:tick"'),
    "[bgach-trigger-whitelist]")
add("recipe-id-drift", ADV + "alchemy/mixed_crystal_pile.json",
    lambda t: t.replace(b'"bettergold:mixed_crystal_pile"', b'"bettergold:mixed_crystal_pile_x"'),
    "[bgach-recipe-exists]")
add("food-list-drift", ADV + "agriculture/midas_feast_1.json",
    lambda t: t.replace(b'"minecraft:golden_apple"', b'"minecraft:golden_apple_pie"'),
    "[bgach-food-list]")
add("display-lang-key-drift", ADV + "merchant/gift_box.json",
    lambda t: t.replace(b'"advancements.bettergold.gift_box.title"',
                        b'"advancements.bettergold.gift_box.titel"'),
    "[bgach-display-lang]")
add("frame-challenge-extra", ADV + "metal/flamegold/armor.json",
    lambda t: t.replace(b'"icon": {', b'"frame": "challenge",\n    "icon": {', 1),
    "[bgach-frame-challenge]")
add("hidden-true", ADV + "agriculture/midas_feast_1.json",
    lambda t: t.replace(b'"description": {', b'"hidden": true,\n    "description": {', 1),
    "[bgach-no-hidden]")

# ---------------- 负向断言 ----------------
add("fd-condition-removed", ADV + "agriculture/midas_feast_2.json",
    jsonmut(lambda o: o.pop("neoforge:conditions")),
    "[bgach-fd-condition]")
add("fd-condition-wrong-body", ADV + "agriculture/alchemical_meat.json",
    lambda t: t.replace(b'"modid": "farmersdelight"', b'"modid": "farmersdelight2"'),
    "[bgach-fd-condition-body]")
add("fd-condition-on-non-fd", ADV + "agriculture/midas_feast_1.json",
    lambda t: t.replace(
        b'  "criteria": {',
        b'  "neoforge:conditions": [\n    {\n      "type": "neoforge:mod_loaded",\n'
        b'      "modid": "farmersdelight"\n    }\n  ],\n  "criteria": {', 1),
    "[bgach-fd-condition]")

# ---------------- 结构级 ----------------
add("reparent-to-root", ADV + "metal/thornsgold/armor.json",
    lambda t: t.replace(b'  "parent": "bettergold:metal/thornsgold/ingot",\n', b''),
    "[bgach-root]", kind="structure")
add("cycle-root-parent", ADV + "root.json",
    lambda t: t.replace(b'{\n  "display"',
                        b'{\n  "parent": "bettergold:agriculture/golden_egg",\n  "display"'),
    "[bgach-root]", kind="structure")
add("gold-split-broken", ADV + "metal/sturdygold/armor.json",
    lambda t: t.replace(b'"parent": "bettergold:metal/sturdygold/weapon"',
                        b'"parent": "bettergold:metal/sturdygold/ingot"'),
    "[bgach-shape-gold-split]", kind="structure")
add("treasure-children-broken", ADV + "treasure/any_raw_metal.json",
    lambda t: t.replace(b'"parent": "bettergold:treasure/any_core_material"',
                        b'"parent": "bettergold:root"'),
    "[bgach-shape-treasure-children]", kind="structure")
add("requirements-mismatch", ADV + "merchant/antique_tool.json",
    jsonmut(lambda o: o.__setitem__("requirements", [["have_x"]])),
    "[bgach-requirements]", kind="structure")
add("requirements-or-vs-and", ADV + "metal/flamegold/armor.json",
    jsonmut(lambda o: o.__setitem__("requirements",
                                    [[c for g in o["requirements"] for c in g]])),
    "[bgach-requirements-semantics]", kind="structure")
add("feast-or-vs-and", ADV + "agriculture/midas_feast_1.json",
    jsonmut(lambda o: o.__setitem__("requirements",
                                    [[c for g in o["requirements"] for c in g]])),
    "[bgach-requirements-semantics]", kind="structure")
add("delete-file", ADV + "agriculture/golden_egg.json", None,
    "[bgach-count]", kind="structure", delete=True)

# ---------------- 语言键（共享文件，逐行定点替换）----------------
add("lang-verbatim-drift", LANGD + "zh_cn.json",
    lambda t: t.replace("旧时代炼金术的继承者".encode("utf-8"),
                        "旧时代炼金术的继承者X".encode("utf-8")),
    "[bgach-lang-verbatim]")
add("lang-key-missing", LANGD + "en_us.json",
    lambda t: t.replace(b'"advancements.bettergold.gift_box.description"',
                        b'"advancements.bettergold.gift_box.description2"'),
    "[bgach-lang-missing]")
add("lang-empty-value", LANGD + "zh_cn.json",
    lambda t: t.replace("旧时代炼金术的继承者".encode("utf-8"), b""),
    "[bgach-lang-empty]")

# ---------------- 真源级（Java）：注册表解析 ----------------
add("registry-source-drift", JAVAD + "registry/AllItems.java",
    lambda t: t.replace(b'registerSimpleItem("mixed_crystal_pile")',
                        b'registerSimpleItem("mixed_crystal_pile_x")'),
    "[bgach-item-exists]", kind="source")

# ---------------- 只改注释：必须仍绿（反向对照）----------------
add("comment-only-control", JAVAD + "registry/AllItems.java",
    lambda t: t.replace(
        b'    /** \xe9\x87\x91\xe9\x92\xa5\xe5\x8c\x99\xef\xbc\x9a',
        b'    // \xe8\xbf\x99\xe9\x87\x8c"\xe4\xb8\x8d\xe7\x94\xa8" .food( '
        b'\xe4\xb9\x9f\xe4\xb8\x8d\xe7\x94\xa8 registerSimpleItem("zzz_fake")\n'
        b'    /** \xe9\x87\x91\xe9\x92\xa5\xe5\x8c\x99\xef\xbc\x9a', 1),
    "", red=False, kind="control")


def main() -> int:
    mismatches: list[str] = []
    rows: list[tuple[str, int, str, bool]] = []

    code, out = run_gate()
    rows.append(("baseline-before", code, "-", True))
    if code != 0:
        mismatches.append("baseline-before 不是 exit 0")

    for c in CASES:
        if not c.path.is_file():
            mismatches.append(f"{c.name}: 目标文件不存在 {c.path}")
            continue
        original = c.path.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        if c.delete:
            mutated = None
        else:
            mutated = c.mutate(original)
            if mutated == original:
                mismatches.append(f"{c.name}: 扰动没生效（改前 == 改后）")
                continue
        try:
            if c.delete:
                c.path.unlink()
            else:
                c.path.write_bytes(mutated)
            code, out = run_gate()
        finally:
            c.path.write_bytes(original)
        if sha(c.path) != before:
            mismatches.append(f"{c.name}: 复原后 SHA256 不一致")
        if c.red:
            ok = (code == 1 and c.tag in out)
        else:
            ok = (code == 0 and "FAIL" not in out)
        rows.append((c.name, code, c.tag if c.red else "(green)", ok))
        if not ok:
            fails = [l for l in out.splitlines() if l.startswith("FAIL")][:3]
            mismatches.append(f"{c.name}: exit={code} 期望={'红/' + c.tag if c.red else '绿'}；"
                              f"实际 FAIL={fails}")

    code, out = run_gate()
    rows.append(("baseline-after", code, "-", code == 0))
    if code != 0:
        mismatches.append("baseline-after 不是 exit 0（有东西没复原干净）")

    for name, code, tag, ok in rows:
        print(f"{'PASS' if ok else 'FAIL'} {name:28s} exit={code} expect={tag}")
    print(f"用例数={len(rows)} mismatches={len(mismatches)}")
    for m in mismatches:
        print(f"MISMATCH {m}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
