# -*- coding: utf-8 -*-
"""第九轮收尾：删除探针世界（只删 run\\gpmprobe_*），绝不碰 run\\world / run\\saves / 作者存档。

用法：gpm_clean_world.py <worldName> [<worldName> ...]
"""
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
RUN = os.path.join(ROOT, "run")

for name in sys.argv[1:]:
    if not name.startswith("gpmprobe_"):
        raise SystemExit("refuse to delete non-probe world: %r" % name)
    target = os.path.abspath(os.path.join(RUN, name))
    if not target.startswith(os.path.abspath(RUN) + os.sep):
        raise SystemExit("refuse outside run/: %r" % target)
    print("target:", target, "exists:", os.path.isdir(target))
    if os.path.isdir(target):
        shutil.rmtree(target)
        print("  removed")
