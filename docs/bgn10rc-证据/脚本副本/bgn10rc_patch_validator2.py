#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 关卡补丁 2：把三条 shaped 的"产物 id"断言升级成"产物 id + 数量 = 1"。

为什么补：第一版只查了 `result.id`，**把 `count` 从 1 改成 2 不会红** ——
扰动矩阵正好要试这一格（"换数量"），补上才是真逐格。

用法：py -3 bgn10rc_patch_validator2.py [--apply]
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
TARGET = REPO / "tools" / "asset-generator" / "validate_metal_data.py"

HELPER_ANCHOR = "def _rc_want_text(want) -> str:\n"

HELPER = '''def _rc_check_result(name: str, obj, want_id: str) -> None:
    """产物：id 必须对、**数量必须是 1**（"换数量"这一格也要能单独变红）。"""
    global _bgn10rc_checked
    _bgn10rc_checked += 1
    if obj is None:
        return
    res = obj.get("result") or {}
    if res.get("id") != want_id:
        _bgn10rc_bad("bgn10rc-result", name + " 的产物不是 " + want_id + "：" + repr(res))
    if res.get("count") != 1:
        _bgn10rc_bad("bgn10rc-result", name + " 的产物数量不是 1：" + repr(res))


def _rc_want_text(want) -> str:
'''

PATCHES = [
    ('''_obj = _rc_recipe("chaosalloy_upgrade_template")
_rc_check_grid("chaosalloy_upgrade_template", _obj, _RC_TEMPLATE)
if _obj is not None:
    _bgn10rc_checked += 1
    if (_obj.get("result") or {}).get("id") != _RC_NS + ":chaosalloy_upgrade_template":
        _bgn10rc_bad("bgn10rc-result", "chaosalloy_upgrade_template 的产物不是本族模板")
''',
     '''_obj = _rc_recipe("chaosalloy_upgrade_template")
_rc_check_grid("chaosalloy_upgrade_template", _obj, _RC_TEMPLATE)
_rc_check_result("chaosalloy_upgrade_template", _obj,
                 _RC_NS + ":chaosalloy_upgrade_template")
'''),
    ('''_obj = _rc_recipe("chaosgold_enchanting_book")
_rc_check_grid("chaosgold_enchanting_book", _obj, _RC_BOOK)
if _obj is not None:
    _bgn10rc_checked += 3
    if (_obj.get("result") or {}).get("id") != _RC_NS + ":chaosgold_enchanting_book":
        _bgn10rc_bad("bgn10rc-result", "chaosgold_enchanting_book 的产物不是混沌金附魔书")
''',
     '''_obj = _rc_recipe("chaosgold_enchanting_book")
_rc_check_grid("chaosgold_enchanting_book", _obj, _RC_BOOK)
_rc_check_result("chaosgold_enchanting_book", _obj,
                 _RC_NS + ":chaosgold_enchanting_book")
if _obj is not None:
    _bgn10rc_checked += 2
'''),
    ('''_obj = _rc_recipe("sturdygold_anvil")
_rc_check_grid("sturdygold_anvil", _obj, _RC_ANVIL)
if _obj is not None:
    _bgn10rc_checked += 1
    if (_obj.get("result") or {}).get("id") != _RC_NS + ":sturdygold_anvil":
        _bgn10rc_bad("bgn10rc-result", "sturdygold_anvil 的产物不是万坚金砧")
''',
     '''_obj = _rc_recipe("sturdygold_anvil")
_rc_check_grid("sturdygold_anvil", _obj, _RC_ANVIL)
_rc_check_result("sturdygold_anvil", _obj, _RC_NS + ":sturdygold_anvil")
'''),
]


def main() -> None:
    apply = "--apply" in sys.argv
    raw = TARGET.read_bytes()
    text = raw.decode("utf-8")
    print("改前: %d B  sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))
    if "_rc_check_result" in text:
        raise SystemExit("已经打过补丁 2 —— 不要重复打")
    if text.count(HELPER_ANCHOR) != 1:
        raise SystemExit("锚点（_rc_want_text）出现 %d 次（应为 1）" % text.count(HELPER_ANCHOR))
    out = text.replace(HELPER_ANCHOR, HELPER)
    for i, (old, new) in enumerate(PATCHES, 1):
        if out.count(old) != 1:
            raise SystemExit("锚点 %d 出现 %d 次（应为 1）" % (i, out.count(old)))
        out = out.replace(old, new)
    compile(out, str(TARGET), "exec")
    data = out.encode("utf-8")
    print("改后: %d B（+%d B）" % (len(data), len(data) - len(raw)))
    if apply:
        TARGET.write_bytes(data)
        print("写盘后 sha256=%s" % hashlib.sha256(TARGET.read_bytes()).hexdigest())
    else:
        print("（演练，未写盘）")


if __name__ == "__main__":
    main()
