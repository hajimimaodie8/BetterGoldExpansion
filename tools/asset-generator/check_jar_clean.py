# -*- coding: utf-8 -*-
"""收尾核对：产物 jar 名 / jar 内是否有 *Probe* 路径 / class 里是否含 halt 字节。"""
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

target = LIBS / "bettergold-1.5.0.jar"
print(f"\n产物 bettergold-1.5.0.jar 存在 = {target.is_file()}")

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
