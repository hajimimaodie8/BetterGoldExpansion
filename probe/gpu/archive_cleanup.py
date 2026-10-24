# -*- coding: utf-8 -*-
"""第十四轮证据归档 + 探针清理（删前留档）。

顺序：① 归档（报告 / 读数 / 关卡 / 扰动 / 构建 / 日志 / 探针源码 / 脚本）→
      ② 删除 src 里的临时探针 + run 里的开关文件 → ③ 复原 run/server.properties（逐字节）。
跑法：<python> probe\\gpu\\archive_cleanup.py
"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
E14 = os.path.join(ROOT, "docs", "金之牢狱-第十四轮-证据")
SCRIPTS = os.path.join(E14, "脚本副本")
PROBE_SRC = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe",
                         "GprProbe.java")
PROBE_DIR = os.path.dirname(PROBE_SRC)
SWITCH = os.path.join(ROOT, "run", "gp14-probe.enabled")
PROPS = os.path.join(ROOT, "run", "server.properties")
PROPS_BAK = os.path.join(ROOT, "run", "server.properties.gp14.bak")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    return os.path.relpath(dst, ROOT), os.path.getsize(dst), sha(dst)


def main():
    rows = []
    # ① 归档
    pairs = [
        (os.path.join(ROOT, "run", "probe", "gp14", "report.json"), os.path.join(E14, "01-探针报告.json")),
        (os.path.join(ROOT, "build", "gp14_readings.txt"), os.path.join(E14, "02-A级读数.md")),
        (os.path.join(ROOT, "build", "gp14_gates.txt"), os.path.join(E14, "03-八关卡读数.txt")),
        (os.path.join(ROOT, "build", "gp14_perturb.txt"), os.path.join(E14, "04-扰动矩阵.txt")),
        (os.path.join(ROOT, "build", "gp14_build.log"), os.path.join(E14, "05-构建日志.txt")),
        (os.path.join(ROOT, "build", "gp14_rs.log"), os.path.join(E14, "06-runServer日志.txt")),
        (PROBE_SRC, os.path.join(SCRIPTS, "GprProbe.java.txt")),
        (os.path.join(ROOT, "build", "gp14_edits.txt"), os.path.join(E14, "07-改动SHA.txt")),
        (os.path.join(ROOT, "run", "probe", "gp14", "error.txt"), os.path.join(E14, "08-探针error.txt")),
    ]
    for src, dst in pairs:
        if not os.path.exists(src):
            print("[skip] %s 不存在" % os.path.relpath(src, ROOT))
            continue
        rows.append(cp(src, dst))
    for f in ("apply_edits.py", "install_probe.py", "readings.py", "gates.py", "perturb.py", "peek.py"):
        src = os.path.join(ROOT, "probe", "gpu", f)
        if os.path.exists(src):
            rows.append(cp(src, os.path.join(SCRIPTS, "probe-gpu", f)))

    # ② 删探针 + 开关（源码已归档）
    if os.path.exists(PROBE_SRC):
        os.remove(PROBE_SRC)
        print("[gp14] deleted", os.path.relpath(PROBE_SRC, ROOT))
    if os.path.isdir(PROBE_DIR) and not os.listdir(PROBE_DIR):
        os.rmdir(PROBE_DIR)
        print("[gp14] removed empty dir probe/")
    if os.path.exists(SWITCH):
        os.remove(SWITCH)
        print("[gp14] deleted", os.path.relpath(SWITCH, ROOT))

    # ③ server.properties 逐字节复原
    if os.path.exists(PROPS_BAK):
        b = open(PROPS_BAK, "rb").read()
        open(PROPS, "wb").write(b)
        print("[gp14] server.properties restored sha=%s" % sha(PROPS))

    L = ["# 第十四轮证据归档", "", "| 文件 | 大小 | SHA256 |", "|---|---|---|"]
    for p, n, h in rows:
        L.append("| `%s` | %d B | `%s` |" % (p, n, h))
    open(os.path.join(E14, "00-归档清单.md"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(L) + "\n")
    print("[gp14] archived %d files -> %s" % (len(rows), os.path.relpath(E14, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
