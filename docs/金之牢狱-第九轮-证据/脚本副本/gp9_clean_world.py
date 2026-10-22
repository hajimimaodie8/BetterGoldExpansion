# -*- coding: utf-8 -*-
"""第九轮：删除探针世界（只删 run\\gp9probe_* 与 run\\probe\\gpk，绝不碰 run\\world / run\\saves）。

用法：gp9_clean_world.py <worldName> [<worldName> ...]   （worldName 形如 gp9probe_a）
"""
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
RUN = os.path.join(ROOT, "run")

for name in sys.argv[1:]:
    if not name.startswith("gp9probe_"):
        raise SystemExit("refuse to delete non-probe world: %r" % name)
    target = os.path.abspath(os.path.join(RUN, name))
    if not target.startswith(os.path.abspath(RUN) + os.sep):
        raise SystemExit("refuse outside run/: %r" % target)
    print("target:", target, "exists:", os.path.isdir(target))
    if os.path.isdir(target):
        shutil.rmtree(target)
        print("  removed")

probe = os.path.join(RUN, "probe")
print("probe dir:", probe, "exists:", os.path.isdir(probe))
# probe/gpk 是 A 级输出：**删前留档**（调用方先复制），这里只清空重跑
if os.path.isdir(os.path.join(probe, "gpk")):
    shutil.rmtree(os.path.join(probe, "gpk"))
    print("  removed probe/gpk")
