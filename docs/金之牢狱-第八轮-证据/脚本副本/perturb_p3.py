# -*- coding: utf-8 -*-
"""P3 单跑：临时造出「玄武岩那一套」文件 ⇒ [bgp-worldgen-single] 必须红，然后删掉复原。"""
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
PY = r'C:\Users\Lenovo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
F = r'src\main\resources\data\bettergold\worldgen\structure_set\golden_prison_basalt.json'
import os

path = os.path.join(ROOT, F)
assert not os.path.exists(path), 'file already exists'
open(path, 'wb').write(b'{"structures": [], "placement": {}}\n')
try:
    r = subprocess.run([PY, os.path.join(ROOT, r'tools\asset-generator\validate_golden_prison.py')],
                       cwd=ROOT, capture_output=True)
    txt = (r.stdout or b'').decode('utf-8', 'replace') + (r.stderr or b'').decode('utf-8', 'replace')
    hit = '[bgp-worldgen-single]' in txt
    print('| P3 玄武岩 set 复活 | exit=%d | hit=%s |' % (r.returncode, hit))
    ok = r.returncode != 0 and hit
finally:
    os.remove(path)
print('复原（文件已删除）:', not os.path.exists(path), '| PASS' if ok and not os.path.exists(path) else '| FAIL')
