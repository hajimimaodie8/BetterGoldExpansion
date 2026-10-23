# -*- coding: utf-8 -*-
"""第九轮收尾·改后：由 gpm 驱动脚本生成 gpn 版本（probe/gpn、gpnprobe_* 世界）。

跑法：<dsh python> gpn_make_scripts.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))


def conv(name):
    t = open(os.path.join(HERE, name), encoding="utf-8").read()
    t = t.replace("gpmprobe_", "gpnprobe_")
    t = t.replace("probe\", \"gpm\"", "probe\", \"gpn\"")
    t = t.replace('"probe", "gpm"', '"probe", "gpn"')
    t = t.replace("probe/gpm", "probe/gpn")
    t = t.replace("gpm_", "gpn_")
    t = t.replace(".gpm.bak", ".gpn.bak")
    t = t.replace("GPM", "GPN")
    t = t.replace("gpm", "gpn")
    return t


for src, dst in [("gpm_set_patch.py", "gpn_set_patch.py"),
                 ("gpm_clean_world.py", "gpn_clean_world.py"),
                 ("gpm_runs.py", "gpn_runs.py")]:
    t = conv(src)
    assert "gpm" not in t.lower().replace("gpn", ""), (dst, "still has gpm?")
    open(os.path.join(HERE, dst), "w", encoding="utf-8", newline="\n").write(t)
    print("wrote", dst, len(t))
