# -*- coding: utf-8 -*-
"""从 run/probe/gpr/report.json（改后）生成验收读数表，写 build/gpr_report.txt。

跑法（工作区自带 python）：
  <python> probe\\gpr\\gpr_report.py
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
AFTER = os.path.join(ROOT, 'docs', '金之牢狱-第十二轮-证据', '02-改后-探针报告.json')
BEFORE = os.path.join(ROOT, 'docs', '金之牢狱-第十二轮-证据', '01-改前-探针报告.json')
OUT = os.path.join(ROOT, 'build', 'gpr_report.txt')

L = []


def w(s=''):
    L.append(s)
    print(s)


def kind(tpl):
    if tpl == 'treasure':
        return 'start'
    if tpl == 'lane':
        return 'lane'
    if tpl == 'exit':
        return 'exit'
    return 'room'


def load(p):
    d = json.load(open(p, encoding='utf-8'))
    return d['A']['runs']['runs'], {m['size']: m['runs']['runs'] for m in d['M']}


after, after_m = load(AFTER)
before, before_m = load(BEFORE)

w('# 金之牢狱 第十二轮（gpr）验收读数 —— 出入口的父件类型')
w('')
w('数据 = run/probe/gpr/report.json（探针 GprProbe，`Structure#generate` 真拼件，不生成区块）')
w('12 座/配置 = 6 个种子 × 2 个区块坐标 (40,40) / (0,0)')
w('')

# ---------------------------------------------------------------- 1 改动前后总表
w('## 1 改动前后总表（A = 注册表里的真实结构）')
w('')
w('| 配置 | size | 结构数 | 有出入口的结构 | 出入口总数 | 父件类型分布 | 落单口 | 被 max_distance 裁掉的件 | 最远件(格) | 件数区间 |')
w('|---|---|---|---|---|---|---|---|---|---|')
for tag, runs in (('改前', before), ('改后', after)):
    ex = sum(r['exitCount'] for r in runs)
    withx = sum(1 for r in runs if r['exitCount'] > 0)
    pk = Counter()
    for r in runs:
        for k, v in r['parentKindCounts'].items():
            pk[k] += v
    orphan = sum(r['orphanCount'] for r in runs)
    culled = sum(r['culledWouldBe'] for r in runs)
    reach = max(r['maxReach'] for r in runs)
    pieces = [r['pieces'] for r in runs]
    size = 5 if tag == '改前' else 4
    w('| %s | %d | %d | **%d/%d** | **%d** | `%s` | %d | %d | %d | %d..%d |'
      % (tag, size, len(runs), withx, len(runs), ex, dict(pk), orphan, culled, reach,
         min(pieces), max(pieces)))
w('')
w('## 2 尺寸矩阵（同一批种子，只换 size；改后的池与 socket）')
w('')
w('| size | 结构数 | 有出入口 | 出入口总数 | 父件类型分布 | lane 父件 | 落单口 | 被裁件 | 最远件 | 件数区间 |')
w('|---|---|---|---|---|---|---|---|---|---|')
for size in sorted(after_m):
    runs = after_m[size]
    ex = sum(r['exitCount'] for r in runs)
    withx = sum(1 for r in runs if r['exitCount'] > 0)
    pk = Counter()
    for r in runs:
        for k, v in r['parentKindCounts'].items():
            pk[k] += v
    orphan = sum(r['orphanCount'] for r in runs)
    culled = sum(r['culledWouldBe'] for r in runs)
    reach = max(r['maxReach'] for r in runs)
    pieces = [r['pieces'] for r in runs]
    w('| **%d** | %d | %d | %d | `%s` | **%d** | %d | %d | %d | %d..%d |'
      % (size, len(runs), withx, ex, dict(pk), pk.get('lane', 0), orphan, culled, reach,
         min(pieces), max(pieces)))
w('')
w('> size=4 = 本轮选值：唯一 `被裁件 = 0` 的一档，落单口 37（改前 34）；size=5 落单口 75、被裁 6；')
w('> size=6 落单口 63、被裁 10（三连四面道前缀已经吃掉 max_distance=116 的预算）。')
w('')

# ---------------------------------------------------------------- 3 逐口
w('## 3 逐口 parentKind 表（改后 = size 4，12 座，63 口）')
w('')
w('| # | 种子 | 区块 | 出入口件 | 深度 | 父件模板 | **父件类型** | 父件深度 |')
w('|---|---|---|---|---|---|---|---|')
i = 0
for r in after:
    for e in r['exits']:
        i += 1
        w('| %d | %s | %s | #%d | %d | `%s` | **%s** | %d |'
          % (i, r['seed'], r['cp'], e['piece'], e['depth'], e['parentTpl'],
             e['parentKind'], e['parentDepth']))
w('')
pk = Counter()
for r in after:
    for e in r['exits']:
        pk[e['parentKind']] += 1
w('合计：`%s` ⇒ **parentKind == lane 的口 = %d**' % (dict(pk), pk.get('lane', 0)))
w('')

# ---------------------------------------------------------------- 4 逐座
w('## 4 逐座读数（改后）')
w('')
w('| 种子 | 区块 | 件数 | 宝藏房 | 四面道 | 出入口 | 父件模板 | 落单口 | 最远件 | 最深层 |')
w('|---|---|---|---|---|---|---|---|---|---|')
for r in after:
    parents = Counter()
    for e in r['exits']:
        parents[e['parentTpl']] += 1
    tail = max(int(k) for k in r['depthKinds'])
    w('| %s | %s | %d | %d | %d | %d | %s | %d | %d | %d |'
      % (r['seed'], r['cp'], r['pieces'], r['treasure'], r['crosses'], r['exitCount'],
         ', '.join('%s×%d' % (k, v) for k, v in sorted(parents.items())) or '-',
         r['orphanCount'], r['maxReach'], tail))
w('')

# ---------------------------------------------------------------- 5 深度序列
w('## 5 深度 → 件类型序列（改前 / 改后 对照，前 3 座）')
w('')
for tag, runs in (('改前 size=5', before), ('改后 size=4', after)):
    w('### %s' % tag)
    w('')
    for r in runs[:3]:
        w('`seed %s / cp %s`（%d 件）' % (r['seed'], r['cp'], r['pieces']))
        w('')
        for dep in sorted(r['depthKinds'], key=int):
            kinds = r['depthKinds'][dep]
            mark = ''
            if all(kind(t) in ('room',) for t in kinds):
                mark = ' ← 全是房间'
            elif any(t == 'lane' for t in kinds) and all(t == 'lane' for t in kinds):
                mark = ' ← 全是过道'
            if dep == str(max(int(k) for k in r['depthKinds'])) and 'exit' in kinds:
                mark += ' **（链尾 = 出入口）**'
            w('- d%s：`%s`%s' % (dep, ', '.join('%s×%d' % (k, v) for k, v in sorted(kinds.items())), mark))
        w('')
w('')

# ---------------------------------------------------------------- 6 落单口成分
w('## 6 落单口成分（改后）')
w('')
c = Counter()
cd = Counter()
for r in after:
    for o in r['orphans']:
        c[(kind(o['tpl']), o['target'])] += 1
        cd[(o['depth'], o['tpl'], o['target'])] += 1
w('| 件类型 | 口 target | 个数 |')
w('|---|---|---|')
for k, v in sorted(c.items(), key=lambda kv: -kv[1]):
    w('| %s | %s | %d |' % (k[0], k[1], v))
w('')
w('按深度：' + ', '.join('d%d:%s→%s×%d' % (k[0], k[1], k[2], v)
                     for k, v in sorted(cd.items())[:12]))
w('')

open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print('\n[gpr-report] wrote %s' % OUT)
