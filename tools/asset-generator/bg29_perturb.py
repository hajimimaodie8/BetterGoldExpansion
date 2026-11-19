# -*- coding: utf-8 -*-
"""bg29 扰动脚本：每个用例 = 改一处 → 跑 validate_metal_data.py → 期望 exit 1
→ **逐字节复原** → SHA256 自证。收尾必须全部复原（最后再做一次全量校验）。"""
import hashlib
import json
import pathlib
import subprocess
import sys

PY = r'C:\Users\Lenovo\AppData\Local\Python\bin\python.exe'
REPO = pathlib.Path('.')
VAL = REPO / 'tools' / 'asset-generator' / 'validate_metal_data.py'

RING_TYPE = REPO / 'src/main/java/com/hjmmd_8/bettergold/material/RingType.java'
RING_ITEMS = REPO / 'src/main/java/com/hjmmd_8/bettergold/material/RingItems.java'
RECIPE = REPO / 'src/main/resources/data/bettergold/recipe/ring_frost_water_bucket.json'
OGG = REPO / 'src/main/resources/assets/bettergold/sounds/thunder_ring.ogg'
TAG = REPO / 'src/main/resources/data/curios/tags/item/ring.json'


def drop_one_tag_value(b):
    obj = json.loads(b.decode('utf-8'))
    obj['values'] = [v for v in obj['values'] if v != 'bettergold:chaosalloy_ring']
    return (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


CASES = [
    ('P1 烈火转化类型 on_fire→magic', RING_TYPE,
     lambda b: b.replace(b'DamageTypes.ON_FIRE', b'DamageTypes.MAGIC', 1), False),
    ('P2 混源耐久 64→65', RING_ITEMS,
     lambda b: b.replace(b'durability(64)', b'durability(65)', 1), False),
    ('P3 冰霜配方戒指换成烈火', RECIPE,
     lambda b: b.replace(b'bettergold:frostgold_ring', b'bettergold:flamegold_ring', 1), False),
    ('P4 音效 ogg 改 1 字节', OGG,
     lambda b: b[:600] + bytes([b[600] ^ 0xFF]) + b[601:], False),
    ('P5 Curios 标签少一枚', TAG, drop_one_tag_value, False),
    ('P6 只加注释（应保持绿）', RING_TYPE,
     lambda b: b.replace(b'public enum RingType {',
                         b'// bg29 perturb: comment only\npublic enum RingType {', 1), True),
]


def run_validator():
    return subprocess.run([PY, str(VAL)], capture_output=True).returncode


results = []
error = None
try:
    for name, path, mutate, expect_green in CASES:
        before = path.read_bytes()
        sha_before = hashlib.sha256(before).hexdigest()
        after = mutate(before)
        if after == before:
            raise AssertionError(name + '：扰动没生效')
        path.write_bytes(after)
        try:
            code = run_validator()
        finally:
            path.write_bytes(before)
        sha_restored = hashlib.sha256(path.read_bytes()).hexdigest()
        restored_ok = sha_restored == sha_before
        hit = (code == 0) if expect_green else (code == 1)
        results.append((name, code, 'PASS' if (hit and restored_ok) else 'FAIL',
                        sha_before[:16], sha_restored[:16], restored_ok, hit))
except BaseException as exc:      # noqa: BLE001
    error = repr(exc)

print('name\texit\tverdict\tsha_before16\tsha_restore16\tbyte_identical\texpected_hit')
for r in results:
    print('\t'.join(str(x) for x in r))
bad = [r[0] for r in results if not (r[5] and r[6])]
print('CASES=%d HITS=%d' % (len(results), len(results) - len(bad)))
print('RESTORE_ALL_IDENTICAL=%s' % (not bad))
if error:
    print('ERROR=%s' % error)
final = run_validator()
print('FINAL_VALIDATOR_EXIT=%d（必须 0）' % final)
sys.exit(0 if (not bad and error is None and final == 0) else 1)
