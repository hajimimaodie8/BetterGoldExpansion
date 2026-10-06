# -*- coding: utf-8 -*-
"""bg-book §九：补齐最终证据文件（收尾后跑一次）。

Run: python build\\bgbook9-evidence.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
EVID = os.path.join(REPO, "docs", "bgbook9-证据")
BUILD = os.path.join(REPO, "build")


def cp(src, dst, desc=""):
    sp = os.path.join(BUILD, src)
    if not os.path.isfile(sp):
        print("MISSING", src, desc)
        return
    shutil.copyfile(sp, os.path.join(EVID, dst))
    print("copied %-42s -> %s" % (src, dst))


def write(name, text):
    io.open(os.path.join(EVID, name), "w", encoding="utf-8", newline="\n").write(text)
    print("wrote ", name)


def main():
    os.makedirs(EVID, exist_ok=True)
    cp("bgbook9-perturb-result.txt", "01-关卡扰动实测.txt")
    cp("bgbook9-b-level.txt", "02-B级构建与六校验器.txt")
    cp("bgbook9-run1-bg9p.txt", "03-A级-runServer-不就地转换与礼物盒抽样.txt")
    cp("bgbook9-run3-bg9c.txt", "04-A级-runClient-手册内容树.txt")
    cp("bgbook9-run2-bg9c.txt", "04b-A级-runClient-第一轮用例错留档.txt")
    cp("bgbook9-restore-props.py", "17-server.properties头部复原脚本.py")
    cp("bgbook9-teardown.py", "18-收尾脚本副本.py")
    cp("bgbook9-evidence.py", "19-证据收集脚本副本.py")

    # 12 行尾与哈希实测（重跑一次 le 脚本，输出落到证据目录）
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(BUILD, "bgbook9-le.py")],
                       cwd=REPO, capture_output=True)
    write("12-行尾与哈希实测.txt", r.stdout.decode("utf-8", "replace"))

    # 14 作者存档改前清单 = 跑前 manifest 里的 run/saves 段
    pre = io.open(os.path.join(BUILD, "bgbook9-pre-manifest.txt"), encoding="utf-8").read().split("\n")
    i = pre.index("== dir run/saves ==")
    out = [pre[i]]
    for ln in pre[i + 1:]:
        if ln.startswith("== "):
            break
        out.append(ln)
    write("14-作者存档改前清单.txt", "\n".join(out) + "\n")


if __name__ == "__main__":
    main()
