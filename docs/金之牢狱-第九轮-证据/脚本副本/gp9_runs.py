# -*- coding: utf-8 -*-
"""第九轮：两个种子的 A 级 runServer 驱动（串行；每条确认退出再起下一条）。

跑法：py -3 gp9_runs.py
做的事：
  1) 干净重建 + 跑 runServer（世界 gp9probe_a / 种子 20261022），把 probe/gpk/report.json 归档；
  2) 换 server.properties 到（gp9probe_b / 种子 7）再跑一次，同样归档；
  3) **逐字节复原** server.properties 并打印 SHA256 对照。
⚠ 本脚本不删 run\\world / run\\saves；只删 run\\gp9probe_*（见 gp9_clean_world.py）。
"""
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUN = os.path.join(ROOT, "run")
EVID = os.path.abspath(os.path.join(HERE, ".."))
GRADLE = os.path.join(ROOT, "gradlew.bat")


def run(cmd, log):
    print(">>", " ".join(cmd))
    with open(log, "wb") as out, open(log + ".err", "wb") as err:
        p = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=err)
    print("   exit =", p.returncode)
    return p.returncode


def py(*args):
    return run([sys.executable] + list(args), os.path.join(ROOT, "build", "gp9_driver.log"))


def main():
    ok = True
    ok &= py(os.path.join(HERE, "gp9_set_patch.py"), "save") == 0
    ok &= run([GRADLE, "compileJava", "--console=plain"], os.path.join(ROOT, "build", "gp9_compile.log")) == 0
    if not ok:
        print("!! compile/save failed")
        return 2

    plan = [
        ("gp9probe_a", "20261022", "02-A-种子20261022.json", "build/gp9_run_a.log"),
        ("gp9probe_b", "7", "03-B-种子7.json", "build/gp9_run_b.log"),
    ]
    for world, seed, archive, log in plan:
        py(os.path.join(HERE, "gp9_clean_world.py"), world)
        py(os.path.join(HERE, "gp9_set_patch.py"), "apply", world, seed)
        rc = run([GRADLE, "runServer", "--console=plain"], os.path.join(ROOT, log))
        report = os.path.join(RUN, "probe", "gpk", "report.json")
        if os.path.exists(report):
            shutil.copyfile(report, os.path.join(EVID, archive))
            print("   archived ->", archive, os.path.getsize(report), "B")
        else:
            print("   !! no report at", report)
            ok = False
        print("   runServer exit =", rc)

    py(os.path.join(HERE, "gp9_set_patch.py"), "restore")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
