# -*- coding: utf-8 -*-
"""收尾：把探针证据搬进 docs、删探针临时物、复原 server.properties 并自证。"""
import hashlib
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
EV = os.path.join(ROOT, 'docs', '金之牢狱-第八轮-证据')
os.makedirs(EV, exist_ok=True)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


# 1) 证据：报告 + 源码 + 日志
src_report = os.path.join(ROOT, r'run\probe\gpj\report.json')
shutil.copyfile(src_report, os.path.join(EV, '10-A级-report.json'))
shutil.copyfile(os.path.join(ROOT, r'src\main\java\com\hjmmd_8\bettergold\probe\GpjProbe.java'),
                os.path.join(EV, 'GpjProbe.java.txt'))
for log, dst in ((r'build\gpj_server.log', '11-runServer-第1次.log'),
                 (r'build\gpj_server2.log', '12-runServer-第2次.log')):
    p = os.path.join(ROOT, log)
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(EV, dst))
# 2) 删探针：源码目录 + 探针世界 + run/probe
probe_src = os.path.join(ROOT, r'src\main\java\com\hjmmd_8\bettergold\probe')
if os.path.isdir(probe_src):
    shutil.rmtree(probe_src)
for rel in (r'run\probe', r'run\gpj_probe'):
    p = os.path.join(ROOT, rel)
    if os.path.isdir(p):
        shutil.rmtree(p)
# 3) 复原 server.properties
P = os.path.join(ROOT, r'run\server.properties')
BAK = P + '.gpj.bak'
if os.path.exists(BAK):
    shutil.copyfile(BAK, P)
print('server.properties sha =', sha(P))
print('probe src exists =', os.path.isdir(probe_src))
print('run/probe exists =', os.path.isdir(os.path.join(ROOT, r'run\probe')))
print('run/gpj_probe exists =', os.path.isdir(os.path.join(ROOT, r'run\gpj_probe')))
print('saves:', sorted(os.listdir(os.path.join(ROOT, 'run', 'saves'))))
d = json.load(open(os.path.join(EV, '10-A级-report.json'), encoding='utf-8'))
print('report keys:', list(d))
