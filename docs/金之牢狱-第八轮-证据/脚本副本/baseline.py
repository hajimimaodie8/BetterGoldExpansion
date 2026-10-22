# -*- coding: utf-8 -*-
"""第八轮：改动前基线 SHA256 留档（只读扫描 + 写一个清单文件）。

用法：  python probe/gpj/baseline.py snapshot   # 写 <证据>/00-baseline-sha256.tsv
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
EVID = os.path.join(ROOT, 'docs', '金之牢狱-第八轮-证据')
TARGETS = [
    'docs/金之牢狱-实现-证据/gp_build.py',
    'docs/金之牢狱-实现-证据/pieces_stage1.json',
    'docs/金之牢狱-实现-证据/pieces_stage2.json',
    'docs/金之牢狱-实现-证据/nbt_manifest.json',
    'tools/asset-generator/validate_golden_prison.py',
    'src/main/java/com/hjmmd_8/bettergold/entity/MoneyGremlin.java',
    'src/main/resources/assets/bettergold/lang/zh_cn.json',
    'src/main/resources/assets/bettergold/lang/en_us.json',
    'src/main/resources/assets/bettergold/sounds.json',
    'src/main/resources/data/bettergold/worldgen/structure/golden_prison.json',
    'src/main/resources/data/bettergold/worldgen/structure/golden_prison_basalt.json',
    'src/main/resources/data/bettergold/worldgen/structure_set/golden_prison.json',
    'src/main/resources/data/bettergold/worldgen/structure_set/golden_prison_basalt.json',
    'src/main/resources/data/bettergold/tags/worldgen/biome/golden_prison/no_basalt.json',
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''):
            h.update(b)
    return h.hexdigest()


def walk(rel):
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    if os.path.isfile(p):
        return [(rel, os.path.getsize(p), sha(p))]
    out = []
    for dp, _dn, fns in os.walk(p):
        for fn in sorted(fns):
            fp = os.path.join(dp, fn)
            r = os.path.relpath(fp, ROOT).replace(os.sep, '/')
            out.append((r, os.path.getsize(fp), sha(fp)))
    return sorted(out)


rows = []
for t in TARGETS:
    rows += walk(t)
for rel in ('src/main/resources/data/bettergold/structure/golden_prison',
            'src/main/resources/data/bettergold/worldgen/template_pool/golden_prison',
            'docs/金之牢狱-蓝图'):
    rows += walk(rel)

os.makedirs(EVID, exist_ok=True)
out = os.path.join(EVID, '00-baseline-sha256.tsv')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 金之牢狱 第八轮（2026-10-22）改动前基线\n')
    f.write('# 每行：相对路径 <TAB> 字节 <TAB> SHA256；缺失文件记 missing\n')
    for rel, size, h in rows:
        f.write('%s\t%d\t%s\n' % (rel, size, h))
    for t in TARGETS:
        p = os.path.join(ROOT, t.replace('/', os.sep))
        if not os.path.exists(p):
            f.write('%s\tmissing\t-\n' % t)
print('wrote %s  rows=%d' % (out, len(rows)))
