# -*- coding: utf-8 -*-
"""[bgn10r7dur-summary] 里把 problems 前几条也打出来（否则扰动时 id 不出现在 stdout，P3 误判"没命中"）。"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
p = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")
raw = open(p, "rb").read()
t = raw.decode("utf-8")
old = '''print("[bgn10r7dur-summary] 崩乱合金盔甲耐久（按作者字面值钉死）：判定 "
      + str(_bgn10r7dur_checked) + " 条，问题 " + str(len(_bgn10r7dur_problems)) + " 条")
'''
new = '''print("[bgn10r7dur-summary] 崩乱合金盔甲耐久（按作者字面值钉死）：判定 "
      + str(_bgn10r7dur_checked) + " 条，问题 " + str(len(_bgn10r7dur_problems)) + " 条"
      + ("" if not _bgn10r7dur_problems else "：" + str(_bgn10r7dur_problems[:4])))
'''
assert t.count(old) == 1
t = t.replace(old, new)
data = t.encode("utf-8")
open(p, "wb").write(data)
print("patched  %d B -> %d B  SHA256 %s" % (len(raw), len(data), hashlib.sha256(data).hexdigest().upper()))
