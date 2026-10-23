import json
import sys

sys.stdout.reconfigure(errors="replace")
p = r'run\probe\gpr\report.json'
d = json.load(open(p, encoding='utf-8'))
print('probe', d.get('probe'), 'forcedUnchanged', d.get('forcedChunksUnchanged'))


def show(tag, m):
    print('==== %s size=%s structs=%s valid=%s withExit=%s exits=%s parentKinds=%s orphans=%s culled=%s maxReach=%s'
          % (tag, m.get('size'), m.get('structures'), m.get('valid'), m.get('structuresWithExit'),
             m.get('totalExits'), m.get('parentKindCounts'), m.get('totalOrphans'),
             m.get('culledWouldBe'), m.get('maxReach')))
    for r in m['runs']:
        if not r.get('valid'):
            print('   seed %s cp %s INVALID' % (r['seed'], r['cp']))
            continue
        ex = r['exitCount']
        parents = r['parentTplCounts']
        print('   seed %-9s cp %-6s pieces=%-3d cross=%-2d exits=%-2d parents=%s orphans=%-2d reach=%-3d tail=%s'
              % (r['seed'], r['cp'], r['pieces'], r['crosses'], ex, parents, r['orphanCount'],
                 r['maxReach'], r['tailKind']))


A = d['A']['runs']
show('A', A)
MS = {}
for mm in d['M']:
    MS[mm['size']] = mm['runs']
    show('M', mm['runs'])

# 深度 → 件类型序列：挑一座
print('\n==== depth->kind (A, first two runs)')
for r in A['runs'][:2]:
    print('seed %s cp %s' % (r['seed'], r['cp']))
    for dep in sorted(r['depthKinds'], key=int):
        print('   d%-2s %s' % (dep, r['depthKinds'][dep]))

print('\n==== orphan target/pool 分布')
from collections import Counter

for tag, runs in (('A', A['runs']), ('size4', MS[4]['runs']), ('size6', MS[6]['runs'])):
    c = Counter()
    cd = Counter()
    for r in runs:
        for o in r['orphans']:
            c[(o['tpl'], o['pool'], o['target'])] += 1
            cd[(o['depth'], o['pool'], o['target'])] += 1
    print('--', tag, 'orphan total', sum(c.values()))
    for k, v in sorted(c.items(), key=lambda kv: -kv[1]):
        print('   piece/pool/target', k, v)
    print('   -- by depth/pool/target')
    for k, v in sorted(cd.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        print('   ', k, v)

print('\n==== exit 逐口 (A, first run)')
for e in A['runs'][0]['exits']:
    print('  ', e)

print('\n==== size4 depth->kind (first run)')
for dep in sorted(MS[4]['runs'][0]['depthKinds'], key=int):
    print('   d%-2s %s' % (dep, MS[4]['runs'][0]['depthKinds'][dep]))

