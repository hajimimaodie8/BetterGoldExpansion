# -*- coding: utf-8 -*-
"""第九轮收尾：两个种子的 A 级 runServer 驱动（串行；每条确认退出再起下一条）。

跑法（工作区自带 Python）：
  <dsh python> gpn_runs.py

做的事：
  1) 备份 run\\server.properties -> .gpn.bak（字节复制）；
  2) compileJava；
  3) 种子 20261022（世界 gpnprobe_a）跑 runServer，归档 probe/gpn/report.json；
  4) 种子 7（世界 gpnprobe_b）再跑一次，同样归档；
  5) 逐字节复原 server.properties 并打印 SHA256 对照。
⚠ 不删 run\\world / run\\saves；只删 run\\gpnprobe_*（本脚本跑前清、收尾脚本再删）。
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
PY = sys.executable


def run(cmd, log):
    print(">>", " ".join(cmd), flush=True)
    with open(log, "wb") as out, open(log + ".err", "wb") as err:
        p = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=err)
    print("   exit =", p.returncode, flush=True)
    return p.returncode


def py(*args):
    return run([PY] + list(args), os.path.join(ROOT, "build", "gpn_driver.log"))


def main():
    ok = True
    ok &= py(os.path.join(HERE, "gpn_set_patch.py"), "save") == 0
    ok &= run([GRADLE, "compileJava", "--console=plain"], os.path.join(ROOT, "build", "gpn_compile_driver.log")) == 0
    if not ok:
        print("!! save/compile failed", flush=True)
        return 2

    plan = [
        ("gpnprobe_a", "20261022", "02-A-种子20261022.json", "build/gpn_run_a.log"),
        ("gpnprobe_b", "7", "03-B-种子7.json", "build/gpn_run_b.log"),
    ]
    for world, seed, archive, log in plan:
        py(os.path.join(HERE, "gpn_clean_world.py"), world)
        py(os.path.join(HERE, "gpn_set_patch.py"), "apply", world, seed)
        rc = run([GRADLE, "runServer", "--console=plain"], os.path.join(ROOT, log))
        report = os.path.join(RUN, "probe", "gpn", "report.json")
        if os.path.exists(report):
            shutil.copyfile(report, os.path.join(EVID, archive))
            print("   archived ->", archive, os.path.getsize(report), "B", flush=True)
        else:
            print("   !! no report at", report, flush=True)
            ok = False
        print("   runServer exit =", rc, flush=True)
        if rc != 0:
            print("   !! runServer non-zero", flush=True)
            ok = False

    py(os.path.join(HERE, "gpn_set_patch.py"), "restore")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
