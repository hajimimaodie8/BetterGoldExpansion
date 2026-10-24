# -*- coding: utf-8 -*-
"""bgbig 收尾核对：把关键读数写成证据文件（不修改任何产物）。"""
import hashlib
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "bgbig-证据", "08-收尾核对.txt")
DOC = os.path.join(ROOT, "docs", "1.7-混沌金与崩乱合金-需求立档.md")
ZH = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang", "zh_cn.json")
EN = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang", "en_us.json")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def lines(p):
    return io.open(p, encoding="utf-8").read().count("\n") + 1


def main():
    out = []
    out.append("bgbig 收尾核对（2026-10-24）")
    out.append("")
    out.append("server.properties SHA256 = " + sha(os.path.join(ROOT, "run", "server.properties")))
    out.append("build.gradle SHA256        = " + sha(os.path.join(ROOT, "build.gradle")))
    out.append("jar SHA256                 = " + sha(os.path.join(ROOT, "build", "libs",
                                                                    "bettergold-1.7.0.jar")))
    out.append("zh_cn.json SHA256          = " + sha(ZH) + "  keys=" + str(len(json.load(
        io.open(ZH, encoding="utf-8")))))
    out.append("en_us.json SHA256          = " + sha(EN) + "  keys=" + str(len(json.load(
        io.open(EN, encoding="utf-8")))))
    out.append("docs/1.7-* 行数            = " + str(lines(DOC)))
    out.append("run/saves 目录             = " + repr(os.listdir(os.path.join(ROOT, "run", "saves"))))
    out.append("run 下 bgbig* 残留         = " + repr([f for f in os.listdir(os.path.join(ROOT, "run"))
                                                    if "bgbig" in f.lower()]))
    probe = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe")
    out.append("src probe 目录             = " + repr(os.listdir(probe) if os.path.isdir(probe) else []))
    # 进程
    ps = subprocess.run(["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | "
                         "ForEach-Object { $_.CommandLine }"],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    hits = [l for l in (ps.stdout or "").splitlines()
            if any(k in l.lower() for k in ("runserver", "runclient", "devlaunch"))]
    out.append("java run 进程              = " + str(len(hits)))
    # diff 统计
    d = subprocess.check_output(["git", "diff", "--numstat"], cwd=ROOT, text=True,
                                encoding="utf-8", errors="replace")
    add = dele = 0
    doc_add = doc_del = 0
    for line in d.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].isdigit():
            add += int(parts[0])
            dele += int(parts[1])
            if parts[2].startswith('"docs/') or parts[2].startswith("docs/"):
                doc_add += int(parts[0])
                doc_del += int(parts[1])
    out.append("git diff 合计              = +%d / -%d" % (add, dele))
    out.append("docs/ 的删除行             = %d（文档侧只追加）" % doc_del)
    out.append("")
    out.append("八关卡 / 扰动 / D 键数见同目录 06-八关卡.txt、04-扰动矩阵.txt、"
               "zh-json-替换证据/。")
    text = "\n".join(out) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
