# -*- coding: utf-8 -*-
"""第十三轮 A 方案：证据留档（探针删前）+ 列清单。只复制，不改源文件。"""
import json
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EVID = os.path.join(ROOT, "docs", "金之牢狱-第十三轮-证据")
RUN = os.path.join(ROOT, "run")
os.makedirs(os.path.join(EVID, "脚本副本"), exist_ok=True)

COPY = [
    (os.path.join(RUN, "probe", "gps", "report.json"), "02-改后-探针报告.json"),
    (os.path.join(ROOT, "build", "gps_readings2.txt"), "03b-逐口parentKind表-A方案.txt"),
    (os.path.join(ROOT, "build", "gps_nbt_diff.out"), "08-exit.nbt逐格diff.txt"),
    (os.path.join(ROOT, "build", "gps_perturb2.txt"), "05-扰动矩阵-A方案.txt"),
    (os.path.join(ROOT, "build", "gps-build3.log"), "06-构建日志-探针.txt"),
    (os.path.join(ROOT, "build", "gps-run3.log"), "07-runServer日志-A方案.txt"),
    (os.path.join(ROOT, "build", "gps-run2.log"), "07a-runServer日志-lane-fb-room（0出口）.txt"),
    (os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe",
                  "GprProbe.java"), "脚本副本/GprProbe.java.txt"),
]
for s, d in COPY:
    if not os.path.exists(s):
        print("MISSING %s" % s)
        continue
    dst = os.path.join(EVID, d)
    shutil.copyfile(s, dst)
    print("copied %-46s -> %s" % (os.path.basename(s), d))

for f in sorted(os.listdir(os.path.join(ROOT, "probe", "gps"))):
    if f.endswith(".py") or f.endswith(".txt"):
        shutil.copyfile(os.path.join(ROOT, "probe", "gps", f), os.path.join(EVID, "脚本副本", f))

d = json.load(open(os.path.join(RUN, "probe", "gps", "report.json"), encoding="utf-8"))
print("forcedChunksBefore=%r after=%r unchanged=%r"
      % (d["forcedChunksBefore"], d["forcedChunksAfter"], d["forcedChunksUnchanged"]))
