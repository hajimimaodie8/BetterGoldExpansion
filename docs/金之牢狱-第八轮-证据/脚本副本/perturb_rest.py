# -*- coding: utf-8 -*-
"""P4~P7 单跑（P3 已单独跑过；P1/P2 已在 perturb.py 里 PASS）。"""
import hashlib
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
PY = r'C:\Users\Lenovo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
VG = os.path.join(ROOT, r'tools\asset-generator\validate_golden_prison.py')
VM = os.path.join(ROOT, r'tools\asset-generator\validate_metal_data.py')


def P(rel):
    return os.path.join(ROOT, rel)


def sha(rel):
    return hashlib.sha256(open(P(rel), 'rb').read()).hexdigest().upper()


def run(gate, tag):
    r = subprocess.run([PY, gate], cwd=ROOT, capture_output=True)
    txt = (r.stdout or b'').decode('utf-8', 'replace') + (r.stderr or b'').decode('utf-8', 'replace')
    return r.returncode, (tag in txt)


def report(label, rel, rc, hit, restored, expect_fail=True):
    ok = (rc != 0 and hit) if expect_fail else (rc == 0)
    print('| %s | `%s` | exit=%d | hit=%s | 复原 %s | %s |'
          % (label, rel, rc, hit, 'OK' if restored else 'MISMATCH', 'PASS' if ok and restored else 'FAIL'))
    return ok and restored


res = []
# P4 槽 2 池少一个样式
rel = r'src\main\resources\data\bettergold\worldgen\template_pool\golden_prison\cross_slot_2.json'
before = sha(rel)
raw = open(P(rel), 'rb').read()
d = json.loads(raw.decode('utf-8'))
d['elements'] = [e for e in d['elements'] if 'cross_slot_2_b' not in str(e)]
open(P(rel), 'wb').write((json.dumps(d, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
rc, hit = run(VG, '[bgp-cross3]')
open(P(rel), 'wb').write(raw)
res.append(report('P4 槽 2 池少一个样式', rel, rc, hit, sha(rel) == before))

# P5 删受伤音效 ogg
rel = r'src\main\resources\assets\bettergold\sounds\money_gremlin_hurt.ogg'
before = sha(rel)
raw = open(P(rel), 'rb').read()
os.remove(P(rel))
rc, hit = run(VM, '[bgsnd-ogg]')
open(P(rel), 'wb').write(raw)
res.append(report('P5 删受伤音效', rel, rc, hit, sha(rel) == before))

# P6 僵尸音效回来
rel = r'src\main\java\com\hjmmd_8\bettergold\entity\MoneyGremlin.java'
before = sha(rel)
raw = open(P(rel), 'rb').read()
t = raw.decode('utf-8').replace(
    'return com.hjmmd_8.bettergold.registry.AllSounds.MONEY_GREMLIN_AMBIENT.get();',
    'return SoundEvents.ZOMBIE_AMBIENT;', 1)
open(P(rel), 'wb').write(t.encode('utf-8'))
rc, hit = run(VM, '[bgsnd-zombie]')
open(P(rel), 'wb').write(raw)
res.append(report('P6 僵尸音效回来', rel, rc, hit, sha(rel) == before))

# P7 只加注释 ⇒ 仍然全绿
rel = r'docs\金之牢狱-实现-证据\gp_build.py'
before = sha(rel)
raw = open(P(rel), 'rb').read()
open(P(rel), 'wb').write(('# 第八轮扰动用例 C7：只加注释，必须仍然全绿\n'.encode('utf-8') + raw))
r = subprocess.run([PY, VG], cwd=ROOT, capture_output=True)
txt = (r.stdout or b'').decode('utf-8', 'replace') + (r.stderr or b'').decode('utf-8', 'replace')
hit = '[bgp-ok]' in txt
open(P(rel), 'wb').write(raw)
res.append(report('P7 只加注释（应保持绿）', rel, r.returncode, hit, sha(rel) == before, expect_fail=False))

print('\nP4~P7：%d/4 PASS' % sum(1 for x in res if x))
