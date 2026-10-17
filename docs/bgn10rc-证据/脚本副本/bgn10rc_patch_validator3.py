#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-n10rc 关卡补丁 3：加载生成器时**不许留 `__pycache__`**。

现象：校验器用 `importlib` 加载 `generate_chaosalloy_recipes.py` 之后，工作树里冒出一个
`tools/asset-generator/__pycache__/*.pyc`（本轮实测）⇒ 违反"跑测不留垃圾"。
修法：加载前后夹 `sys.dont_write_bytecode = True`（`finally` 里复原）。

用法：py -3 bgn10rc_patch_validator3.py [--apply]
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
TARGET = REPO / "tools" / "asset-generator" / "validate_metal_data.py"

OLD = '''    try:
        import importlib.util
        _spec = importlib.util.spec_from_file_location("_bgn10rc_gen", _rc_gen)
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)          # 模块名不是 __main__ ⇒ 不会写盘
'''

NEW = '''    try:
        import importlib.util
        # ⚠ 加载**别人家的生成器**会写 `__pycache__/*.pyc`（本轮实测在 tools/asset-generator/ 里冒出来）
        #   ⇒ 这里临时关掉字节码缓存，加载完在 finally 复原（跑测不许在工作树留垃圾）。
        _dwb = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            _spec = importlib.util.spec_from_file_location("_bgn10rc_gen", _rc_gen)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)      # 模块名不是 __main__ ⇒ 不会写盘
        finally:
            sys.dont_write_bytecode = _dwb
'''


def main() -> None:
    apply = "--apply" in sys.argv
    raw = TARGET.read_bytes()
    text = raw.decode("utf-8")
    print("改前: %d B  sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))
    if "sys.dont_write_bytecode" in text:
        raise SystemExit("已经打过补丁 3 —— 不要重复打")
    if text.count(OLD) != 1:
        raise SystemExit("锚点出现 %d 次（应为 1）" % text.count(OLD))
    out = text.replace(OLD, NEW)
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
