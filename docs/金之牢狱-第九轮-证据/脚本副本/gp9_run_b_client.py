# -*- coding: utf-8 -*-
"""第九轮尾段：① 种子 B 的 runServer（A 级 ≥2 种子）；② 客户端 SoundManager 探针（标题界面，不建世界）。

跑法：py -3 gp9_run_b_client.py
纪律：server.properties 改前 .bak、跑后**逐字节复原**；开关文件收尾删除；不 quickPlay、不进任何存档。
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
SWITCH = os.path.join(RUN, "gp9_client_probe.on")


def py(*args):
    print(">> py", args[0].split(os.sep)[-1], args[1:])
    p = subprocess.run([sys.executable] + list(args), cwd=ROOT, capture_output=True)
    print("   exit =", p.returncode)
    return p.returncode


def gradle(*args, log="build/gp9_driver.log"):
    print(">>", " ".join(args))
    with open(os.path.join(ROOT, log), "wb") as out, open(os.path.join(ROOT, log + ".err"), "wb") as err:
        p = subprocess.run([GRADLE] + list(args), cwd=ROOT, stdout=out, stderr=err)
    print("   exit =", p.returncode)
    return p.returncode


def main():
    py(os.path.join(HERE, "gp9_set_patch.py"), "save")
    rc = 0
    # ---- ① 种子 B
    py(os.path.join(HERE, "gp9_clean_world.py"), "gp9probe_b")
    py(os.path.join(HERE, "gp9_set_patch.py"), "apply", "gp9probe_b", "7")
    gradle("runServer", "--console=plain", log="build/gp9_run_b.log")
    report = os.path.join(RUN, "probe", "gpk", "report.json")
    if os.path.exists(report):
        dst = os.path.join(EVID, "03-B-种子7.json")
        shutil.copyfile(report, dst)
        print("   archived ->", os.path.basename(dst), os.path.getsize(dst), "B")
    else:
        print("   !! missing report B")
        rc = 1
    py(os.path.join(HERE, "gp9_set_patch.py"), "restore")
    py(os.path.join(HERE, "gp9_clean_world.py"), "gp9probe_b")

    # ---- ② 客户端 SoundManager 探针（标题界面；不 quickPlay）
    open(SWITCH, "w", encoding="utf-8").write("1\n")
    try:
        gradle("runClient", "--console=plain", log="build/gp9_run_client.log")
    finally:
        if os.path.exists(SWITCH):
            os.remove(SWITCH)
            print("   switch removed")
    cs = os.path.join(RUN, "probe", "gpk", "client_sound.json")
    if os.path.exists(cs):
        dst = os.path.join(EVID, "04-客户端音效-标题界面.json")
        shutil.copyfile(cs, dst)
        print("   archived ->", os.path.basename(dst), os.path.getsize(dst), "B")
    else:
        print("   !! missing client_sound.json")
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
