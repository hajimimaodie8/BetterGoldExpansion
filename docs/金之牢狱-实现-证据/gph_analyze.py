# -*- coding: utf-8 -*-
"""金之牢狱 第六轮 A 级读数（离线复算）——从 runServer 探针（GphProbe）的 dump 里算：

  ① 10 个种子各拼一座（两套结构各跑一遍）：序列指纹 / 件数 / 模板种类 / 落单口 / 池命中 /
     宝藏房件数 / **丰饶件比例**（③ 的验收：10 个种子里出现过至少一个 fertile 件的座数）
  ② 真实生成的 3 个群系（basalt_deltas / crimson_forest / soul_sand_valley）里
     **件 bbox 内不属于任何模板调色板的方块**（= 地形/feature 长进结构里的量，② 的验收）
  ③ 实体（item frame）/ 方块实体（spawner / chest）
  ④ 出入口：井口环顶 topY / airFromY（岩石之上的第一格空气）/ deltaNeeded / outcrop（① 的验收）

用法： python gph_analyze.py --dir <dump 目录> [--tag 名字] [--json 输出.json]
"""
import argparse
import collections
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'docs', '金之牢狱-实现-证据'))
import nbt  # noqa: E402

STRUCT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'structure', 'golden_prison')
NATURAL = {'minecraft:basalt', 'minecraft:blackstone', 'minecraft:magma_block', 'minecraft:netherrack',
           'minecraft:soul_sand', 'minecraft:soul_soil', 'minecraft:gravel', 'minecraft:glowstone',
           'minecraft:lava', 'minecraft:blackstone', 'minecraft:polished_blackstone',
           'minecraft:nether_wart_block', 'minecraft:warped_wart_block', 'minecraft:crimson_stem',
           'minecraft:warped_stem', 'minecraft:weeping_vines', 'minecraft:twisting_vines',
           'minecraft:shroomlight', 'minecraft:crimson_nylium', 'minecraft:warped_nylium',
           'minecraft:brown_mushroom', 'minecraft:red_mushroom', 'minecraft:nether_sprouts',
           'minecraft:crimson_roots', 'minecraft:warped_roots', 'minecraft:soul_fire_',
           'minecraft:basalt', 'minecraft:bedrock'}


def template_palettes():
    """每个模板允许出现的方块 id（作者件自己的调色板 + 我们的 jigsaw）。"""
    out = {}
    for fn in os.listdir(STRUCT):
        if not fn.endswith('.nbt'):
            continue
        _, root = nbt.parse_auto(open(os.path.join(STRUCT, fn), 'rb').read())
        out[fn[:-4]] = {p['Name'] for p in root['palette']}
    return out


def load_blocks(path):
    out = []
    for line in open(path, encoding='utf-8'):
        a = line.rstrip('\n').split(',')
        if len(a) < 4:
            continue
        out.append((int(a[0]), int(a[1]), int(a[2]), a[3]))
    return out


def inside(b, x, y, z):
    return b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[2] <= z <= b[5]


def seed_stats(runs, label):
    runs = [r for r in runs if r.get('fingerprint')]
    if not runs:
        print('-- %s：没有有效 run（全部 valid=false）' % label)
        return {'label': label, 'runs': 0}
    fps = [tuple(r['fingerprint']) for r in runs]
    distinct = len(set(fps))
    pieces = [len(r['pieces']) for r in runs]
    tpls = [len(set(r['fingerprint'])) for r in runs]
    orphans = [len(r['orphans']) for r in runs]
    treasures = [int(r.get('treasurePieces') or 0) for r in runs]
    fert = [sum(1 for t in r['fingerprint'] if t.endswith('_fertile')) for r in runs]
    rooms = [sum(1 for t in r['fingerprint'] if t not in ('treasure', 'lane', 'exit')) for r in runs]
    hits = collections.Counter()
    for r in runs:
        for k, v in r['poolHits'].items():
            hits[k] += v
    print('-- %s：10 个种子（同一份配置）' % label)
    print('   %-10s %-6s %-6s %-6s %-8s %-6s %-6s %-6s %s'
          % ('seed', '件数', '模板', '落单口', '指纹去重', '宝藏房', 'room', 'fertile', '指纹'))
    seen = set()
    for r in runs:
        fp = tuple(r['fingerprint'])
        print('   %-10d %-6d %-6d %-6d %-8s %-6d %-6d %-6d %s'
              % (r['seed'], len(r['pieces']), len(set(fp)), len(r['orphans']),
                 'NEW' if fp not in seen else 'DUP', int(r.get('treasurePieces') or 0),
                 sum(1 for t in fp if t not in ('treasure', 'lane', 'exit')),
                 sum(1 for t in fp if t.endswith('_fertile')), '>'.join(fp)))
        seen.add(fp)
    with_fert = sum(1 for f in fert if f > 0)
    print('   序列指纹不同取值 = %d / %d（参考：>=5）' % (distinct, len(runs)))
    print('   件数范围 = %d..%d；模板种类范围 = %d..%d；落单口合计 = %d；宝藏房合计 = %d（每座必须 1）'
          % (min(pieces), max(pieces), min(tpls), max(tpls), sum(orphans), sum(treasures)))
    print('   池命中合计 = %s' % dict(hits))
    print('   丰饶：含至少 1 个 fertile 件的座数 = %d / %d（%.0f%%）；fertile 件合计 = %d / room 件合计 = %d（%.1f%%）'
          % (with_fert, len(runs), 100.0 * with_fert / max(1, len(runs)),
             sum(fert), sum(rooms), 100.0 * sum(fert) / max(1, sum(rooms))))
    return {'label': label, 'runs': len(runs), 'distinctFingerprints': distinct,
            'pieceRange': [min(pieces), max(pieces)],
            'templateKindRange': [min(tpls), max(tpls)],
            'orphans': sum(orphans), 'treasurePieces': sum(treasures),
            'treasurePerRun': treasures,
            'poolHits': dict(hits),
            'fertileRuns': with_fert,
            'fertilePieces': sum(fert), 'roomPieces': sum(rooms),
            'fertilePieceRatio': (sum(fert) / sum(rooms)) if sum(rooms) else None,
            'fingerprints': ['>'.join(f) for f in fps]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--tag', default='')
    ap.add_argument('--json', default='')
    a = ap.parse_args()
    d = a.dir
    tag = a.tag or os.path.basename(d.rstrip('\\/'))
    res = {'tag': tag, 'dir': d}
    print('== [%s] %s ==' % (tag, d))

    sp = os.path.join(d, 'seeds.json')
    if os.path.exists(sp):
        sd = json.load(open(sp, encoding='utf-8'))
        res['world'] = {'worldName': sd.get('worldName'), 'seed': sd.get('seed')}
        if sd.get('runs'):
            res['seeds_main'] = seed_stats(sd['runs'], 'golden_prison（主结构，非玄武岩群系）')
        for k in sd:
            if k.startswith('runs_'):
                res['seeds_' + k] = seed_stats(sd[k], k[len('runs_'):])
        res['structureNames'] = [k for k in sd if k.startswith('runs')]

    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        print('(no meta.json)')
        if a.json:
            open(a.json, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    metas = json.load(open(mp, encoding='utf-8'))
    pals = template_palettes()
    allowed = set()
    for s in pals.values():
        allowed |= s
    print('-- 真实生成 %d 座（模板调色板并集 %d 种方块）' % (len(metas), len(allowed)))
    real = []
    for i, m in enumerate(metas):
        blocks = load_blocks(os.path.join(d, 'blocks_%d.tsv' % i))
        boxes = [(p['tpl'], p['bbox']) for p in m['pieces']]
        foreign = collections.Counter()
        foreign_natural = 0
        for (x, y, z, nm) in blocks:
            if nm in allowed:
                continue
            for tpl, b in boxes:
                if inside(b, x, y, z):
                    foreign[nm] += 1
                    if nm in NATURAL:
                        foreign_natural += 1
                    break
        bes = m.get('blockEntities') or []
        nsp = sum(1 for b in bes if b['id'] == 'minecraft:mob_spawner')
        nch = sum(1 for b in bes if b['id'] == 'minecraft:chest')
        sp_ok = sum(1 for b in bes if b['id'] == 'minecraft:mob_spawner'
                    and 'bettergold:money_gremlin' in (b.get('spawnData') or ''))
        ch_ok = sum(1 for b in bes if b['id'] == 'minecraft:chest'
                    and b.get('lootTable') == 'bettergold:chests/golden_prison')
        ents = m.get('entities') or []
        frames = [e for e in ents if e['id'] == 'minecraft:glow_item_frame']
        coin = [e for e in frames if e.get('item') == 'bettergold:chaos_coin']
        ex = m.get('exits') or []
        print('   #%d %-18s %-26s 件=%d 宝藏房=%s 落单口=%s（口 %s/配对 %s）异类方块=%d（地形类 %d） '
              'spawner %d/%d；chest %d/%d；item_frame %d（chaos_coin %d）'
              % (i, m['biome'], m.get('structure'), len(m['pieces']),
                 m.get('treasurePieces'), len(m.get('orphans') or []), m.get('ports'),
                 m.get('paired'), sum(foreign.values()), foreign_natural,
                 sp_ok, nsp, ch_ok, nch, len(frames), len(coin)))
        if foreign:
            print('      异类方块 top: %s' % dict(foreign.most_common(8)))
        for e in ex:
            print('      exit#%d bbox=%s topY=%s airFromY=%s（最好列 %s / 岩石顶 %s）firstAirRunY=%s '
                  'deltaNeeded=%s outcrop=%s 环顶上方 8 格全空 %s/%s'
                  % (e['pieceIndex'], e['bbox'], e['topY'], e.get('airFromY'),
                     e.get('airFromBestY'), e.get('maxNaturalTop'), e.get('firstAirRunY'),
                     e.get('deltaNeededFromTop'),
                     e.get('outcrop'), e.get('columnsClearAboveRim8'), e.get('columns')))
            cols = e.get('cols') or []
            if cols:
                print('        逐列空气段（环顶以上）：%s'
                      % ' '.join('%s:%s' % ((c['x'], c['z']), c.get('runsAboveRim'))
                                 for c in cols))
        real.append({'structure': m.get('structure'), 'biome': m['biome'],
                     'pieces': len(m['pieces']), 'treasurePieces': m.get('treasurePieces'),
                     'orphans': len(m.get('orphans') or []), 'ports': m.get('ports'),
                     'paired': m.get('paired'),
                     'foreign': sum(foreign.values()), 'foreignNatural': foreign_natural,
                     'foreignTop': dict(foreign.most_common(8)),
                     'spawner': [sp_ok, nsp], 'chest': [ch_ok, nch],
                     'frames': len(frames), 'framesCoin': len(coin),
                     'exits': ex})
    res['real'] = real
    if res.get('real'):
        oc = [e for m in real for e in m['exits'] if e.get('outcrop')]
        allx = [e for m in real for e in m['exits']]
        print('-- 出入口：%d 个，达标（airFromY <= topY）= %d 个' % (len(allx), len(oc)))
    if a.json:
        open(a.json, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
        print('   -> %s' % a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
