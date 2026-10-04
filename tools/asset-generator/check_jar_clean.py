# -*- coding: utf-8 -*-
"""收尾核对：产物 jar 名 / jar 内是否有 *Probe* 路径 / class 里是否含 halt 字节。"""
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
LIBS = REPO / "build" / "libs"

jars = sorted(LIBS.glob("*.jar"))
print("build/libs jars:")
for j in jars:
    print(f"  {j.name}  ({j.stat().st_size} bytes)")

# ⚠ bg-16（1.6）：**jar 名必须从 gradle.properties 的 mod_version 现算**，不许写死 ——
#   写死 1.5.0 时，1.6.0 这一轮里这个关卡会去检查一个**过期的旧 jar**（而且照样全绿），
#   于是"收尾核对"检查的根本不是这一轮的产物（旧 jar 里当然没有新探针）。
_props = (REPO / "gradle.properties").read_text(encoding="utf-8")
_m = re.search(r"^mod_version\s*=\s*(\S+)\s*$", _props, re.MULTILINE)
_version = _m.group(1) if _m else "0.0.0"
target = LIBS / f"bettergold-{_version}.jar"
print(f"\n产物 bettergold-{_version}.jar（来自 gradle.properties 的 mod_version）存在 = {target.is_file()}")
if len(jars) > 1:
    print(f"  ⚠ build/libs 里有 {len(jars)} 个 jar（旧版本的 jar 会留在这里）——"
          f"只核对上面这一个；跑 `gradlew clean` 可在干净树里复核")

if target.is_file():
    with zipfile.ZipFile(target) as z:
        names = z.namelist()
        probe_paths = [n for n in names if "Probe" in n or "probe" in n.lower()]
        print(f"jar 内 *Probe* 路径 = {len(probe_paths)} {probe_paths[:5]}")
        halt_classes = []
        for n in names:
            if n.endswith(".class"):
                data = z.read(n)
                # 常量池里的 "halt" 会以 UTF8 常量出现；直接找字节序列
                if b"halt" in data:
                    halt_classes.append(n)
        print(f"jar 内含 'halt' 字节的 class = {len(halt_classes)} {halt_classes[:5]}")
        probe_str = [n for n in names if n.endswith(".class") and b"BG-PROBE" in z.read(n)]
        print(f"jar 内含 'BG-PROBE' 常量的 class = {len(probe_str)} {probe_str[:5]}")
        print(f"jar 内文件总数 = {len(names)}")
