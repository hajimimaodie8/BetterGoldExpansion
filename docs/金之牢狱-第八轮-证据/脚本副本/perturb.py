# -*- coding: utf-8 -*-
"""第八轮扰动矩阵：7 个用例（6 红 + 1 只改注释仍绿），每个用例单独跑对应关卡，逐字节复原 + SHA256。

用法： python probe/gpj/perturb.py
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
PY = r'C:\Users\Lenovo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
VG = os.path.join(ROOT, r'tools\asset-generator\validate_golden_prison.py')
VM = os.path.join(ROOT, r'tools\asset-generator\validate_metal_data.py')


def p(rel):
    return os.path.join(ROOT, rel)


def sha(rel):
    return hashlib.sha256(open(p(rel), 'rb').read()).hexdigest().upper()


def run(gate, tag):
    r = subprocess.run([PY, gate], cwd=ROOT, capture_output=True)
    txt = (r.stdout or b'').decode('utf-8', 'replace') + (r.stderr or b'').decode('utf-8', 'replace')
    hit = tag in txt
    return r.returncode, hit, [l for l in txt.split('\n') if tag in l][:1]


def case(label, rel, mutate, gate, tag, expect_fail=True):
    before = sha(rel)
    saved = open(p(rel), 'rb').read()
    try:
        mutate()
        rc, hit, line = run(gate, tag)
    finally:
        open(p(rel), 'wb').write(saved)
    after = sha(rel)
    ok = (rc != 0 and hit) if expect_fail else (rc == 0)
    print('| %s | `%s` | %s | exit=%d | hit=%s | 复原 SHA %s | %s |'
          % (label, rel, '改' if expect_fail else '只加注释', rc, hit,
             'OK' if before == after else 'MISMATCH', 'PASS' if ok and before == after else 'FAIL'))
    return ok and before == after


def write(rel, data):
    open(p(rel), 'wb').write(data)


results = []

# P1 ① 空位计数掉 1（关卡期望值）
def m1():
    t = open(p(r'tools\asset-generator\validate_golden_prison.py'), 'rb').read().decode('utf-8')
    t = t.replace("'cross_a': 1480", "'cross_a': 1479", 1)
    write(r'tools\asset-generator\validate_golden_prison.py', t.encode('utf-8'))


results.append(case('P1 空位计数-1', r'tools\asset-generator\validate_golden_prison.py', m1, VG, '[bgp-void]'))


# P2 ③ biomes 退回 is_nether
def m2():
    f = r'src\main\resources\data\bettergold\worldgen\structure\golden_prison.json'
    t = open(p(f), 'rb').read().decode('utf-8')
    t = t.replace('"#bettergold:golden_prison/no_basalt"', '"#minecraft:is_nether"', 1)
    write(f, t.encode('utf-8'))


results.append(case('P2 biomes 退回 is_nether', r'src\main\resources\data\bettergold\worldgen\structure\golden_prison.json',
                    m2, VG, '[bgp-worldgen]'))


# P3 ③ 玄武岩那一套文件回来
def m3():
    f = r'src\main\resources\data\bettergold\worldgen\structure_set\golden_prison_basalt.json'
    write(f, b'{"structures": [], "placement": {}}\n')


results.append(case('P3 玄武岩 set 复活',
                    r'src\main\resources\data\bettergold\worldgen\structure_set\golden_prison_basalt.json',
                    m3, VG, '[bgp-worldgen-single]'))


# P4 ④ 槽 2 池少一个样式
def m4():
    f = r'src\main\resources\data\bettergold\worldgen\template_pool\golden_prison\cross_slot_2.json'
    d = json.load(open(p(f), encoding='utf-8'))
    d['elements'] = [e for e in d['elements'] if 'cross_slot_2_b' not in str(e)]
    write(f, (json.dumps(d, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


results.append(case('P4 槽 2 池少一个样式',
                    r'src\main\resources\data\bettergold\worldgen\template_pool\golden_prison\cross_slot_2.json',
                    m4, VG, '[bgp-cross3]'))


# P5 ⑤ 删掉受伤音效文件
OGG = r'src\main\resources\assets\bettergold\sounds\money_gremlin_hurt.ogg'
_bak = None


def m5():
    global _bak
    _bak = open(p(OGG), 'rb').read()
    os.remove(p(OGG))


def case_del(label, rel, mutate, gate, tag):
    mutate()
    try:
        rc, hit, line = run(gate, tag)
    finally:
        open(p(rel), 'wb').write(_bak)
    after_exists = os.path.exists(p(rel))
    ok = rc != 0 and hit and after_exists
    print('| %s | `%s` | 删 | exit=%d | hit=%s | 复原 %s | %s |'
          % (label, rel, rc, hit, 'OK' if after_exists else 'MISSING', 'PASS' if ok else 'FAIL'))
    return ok


results.append(case_del('P5 删受伤音效', OGG, m5, VM, '[bgsnd-ogg]'))


# P6 ⑤ 僵尸音效回来
def m6():
    f = r'src\main\java\com\hjmmd_8\bettergold\entity\MoneyGremlin.java'
    t = open(p(f), 'rb').read().decode('utf-8')
    t = t.replace('return com.hjmmd_8.bettergold.registry.AllSounds.MONEY_GREMLIN_AMBIENT.get();',
                  'return SoundEvents.ZOMBIE_AMBIENT;', 1)
    write(f, t.encode('utf-8'))


results.append(case('P6 僵尸音效回来', r'src\main\java\com\hjmmd_8\bettergold\entity\MoneyGremlin.java',
                    m6, VM, '[bgsnd-zombie]'))


# P7 只改注释 ⇒ 仍然全绿（正向 needle 跑在去注释源码上）
def m7():
    f = r'docs\金之牢狱-实现-证据\gp_build.py'
    t = open(p(f), 'rb').read().decode('utf-8')
    write(f, ('# 第八轮扰动用例 C7：只加注释，必须仍然全绿\n' + t).encode('utf-8'))


results.append(case('P7 只加注释（应保持绿）', r'docs\金之牢狱-实现-证据\gp_build.py', m7, VG,
                    '[bgp-ok]', expect_fail=False))

print('\n矩阵结果：%d/%d PASS' % (sum(1 for r in results if r), len(results)))
