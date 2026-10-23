# -*- coding: utf-8 -*-
"""收尾①：A 级证据留档（探针删前）——只复制，不改任何源文件。"""
import json
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EVID = os.path.join(ROOT, "docs", "金之牢狱-第十三轮-证据")
RUN = os.path.join(ROOT, "run")
SRC12 = os.path.join(ROOT, "docs", "金之牢狱-第十二轮-证据")
os.makedirs(os.path.join(EVID, "脚本副本"), exist_ok=True)

COPY = [
    (os.path.join(RUN, "probe", "gps", "report.json"), "02-改后-探针报告.json"),
    (os.path.join(SRC12, "01-改前-探针报告.json"), "01-改前-探针报告.json"),
    (os.path.join(ROOT, "build", "gps_readings.txt"), "03-逐口parentKind表.txt"),
    (os.path.join(ROOT, "build", "gps-build.log"), "06-构建日志.txt"),
    (os.path.join(ROOT, "build", "gps-run.log"), "07-runServer日志.txt"),
    (os.path.join(ROOT, "build", "gps_sim_scan.txt"), "脚本副本/sim_scan.out.txt"),
    (os.path.join(ROOT, "build", "gps_sim_depth.txt"), "脚本副本/sim_depth.out.txt"),
    (os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe",
                  "GprProbe.java"), "脚本副本/GprProbe.java.txt"),
]
for s, d in COPY:
    if not os.path.exists(s):
        print("MISSING %s" % s)
        continue
    dst = os.path.join(EVID, d)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(s, dst)
    print("copied %-42s -> %s (%d B)" % (os.path.basename(s), d, os.path.getsize(dst)))

# 脚本副本：本轮 probe/gps 下的全部 .py
for f in sorted(os.listdir(os.path.join(ROOT, "probe", "gps"))):
    if f.endswith(".py") or f.endswith(".txt"):
        shutil.copyfile(os.path.join(ROOT, "probe", "gps", f), os.path.join(EVID, "脚本副本", f))
        print("copied script %s" % f)

d = json.load(open(os.path.join(RUN, "probe", "gps", "report.json"), encoding="utf-8"))
print("forcedChunksBefore=%r forcedChunksAfter=%r unchanged=%r"
      % (d["forcedChunksBefore"], d["forcedChunksAfter"], d["forcedChunksUnchanged"]))
