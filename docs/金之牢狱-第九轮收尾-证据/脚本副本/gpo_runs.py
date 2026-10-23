# -*- coding: utf-8 -*-
"""第十轮：两个种子的 A 级 runServer 驱动（串行；每条确认退出再起下一条）。

跑法（工作区自带 Python）：
  <dsh python> probe\\gpo\\gpo_runs.py

做的事：
  1) 备份 run\\server.properties -> .gpo.bak（字节复制；调用前必须已复原成基线）；
  2) compileJava；
  3) 种子 20261022（世界 gpoprobe_a）跑 runServer，归档 probe/gpo/report.json -> 02-A-种子20261022.json；
  4) 种子 7（世界 gpoprobe_b）再跑一次，归档 -> 03-B-种子7.json；
  5) 逐字节复原 server.properties 并打印 SHA256 对照。
⚠ 不删 run\\world / run\\saves；只删 run\\gpoprobe_*（本脚本跑前清）。
"""
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(ROOT, "run")
EVID = os.path.join(ROOT, "docs", "金之牢狱-第九轮收尾-证据")
GRADLE = os.path.join(ROOT, "gradlew.bat")
PY = sys.executable
REPORT = os.path.join(RUN, "probe", "gpo", "report.json")


def run(cmd, log):
    print(">>", " ".join(cmd), flush=True)
    with open(log, "wb") as out, open(log + ".err", "wb") as err:
        p = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=err)
    print("   exit =", p.returncode, flush=True)
    return p.returncode


def py(*args):
    return run([PY] + list(args), os.path.join(ROOT, "build", "gpo_driver.log"))


def main():
    ok = True
    ok &= py(os.path.join(HERE, "gpo_set_patch.py"), "save") == 0
    ok &= run([GRADLE, "compileJava", "--console=plain"], os.path.join(ROOT, "build", "gpo_compile_driver.log")) == 0
    if not ok:
        print("!! save/compile failed", flush=True)
        return 2

    plan = [
        ("gpoprobe_a", "20261022", "02-A-种子20261022.json", "build/gpo_run_a.log"),
        ("gpoprobe_b", "7", "03-B-种子7.json", "build/gpo_run_b.log"),
    ]
    for world, seed, archive, log in plan:
        py(os.path.join(HERE, "gpo_clean_world.py"), world)
        py(os.path.join(HERE, "gpo_set_patch.py"), "apply", world, seed)
        if os.path.exists(REPORT):
            os.remove(REPORT)
        rc = run([GRADLE, "runServer", "--console=plain"], os.path.join(ROOT, log))
        if os.path.exists(REPORT):
            shutil.copyfile(REPORT, os.path.join(EVID, archive))
            print("   archived ->", archive, os.path.getsize(REPORT), "B", flush=True)
        else:
            print("   !! no report at", REPORT, flush=True)
            ok = False
        print("   runServer exit =", rc, flush=True)
        if rc != 0:
            print("   !! runServer non-zero", flush=True)
            ok = False

    py(os.path.join(HERE, "gpo_set_patch.py"), "restore")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
