# -*- coding: utf-8 -*-
"""独立复核：语言键注入**没有覆盖任何既有键的值**（比对注入前的副本）。"""
import io
import json
import sys

sys.stdout.reconfigure(errors="replace")
LANGDIR = r"E:\mc\mcmod\bettergold-template-1.21.1\src\main\resources\assets\bettergold\lang"
CAT = "bettergold.handbook.category.gear_upgrade.name"

for name, before_path in (("zh_cn.json", r"E:\mc\mcmod\bettergold-template-1.21.1\build\zh_cn.before.json"),
                          ("en_us.json", r"E:\mc\mcmod\bettergold-template-1.21.1\build\en_us.before.json")):
    before = json.loads(io.open(before_path, encoding="utf-8").read())
    after = json.loads(io.open(LANGDIR + "\\" + name, encoding="utf-8").read())
    changed = sorted(k for k, v in before.items() if after.get(k) != v)
    removed = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    print("%s: before=%d after=%d added=%d removed=%d changed=%s"
          % (name, len(before), len(after), len(added), len(removed), changed))
    print("   added sample:", added[:2], "| category now:", after.get(CAT))
    if changed != [CAT] or removed:
        raise SystemExit("FAIL: 既有内容被动过")
print("OK: 只有类别名一处是值级更正，其余全是追加")
