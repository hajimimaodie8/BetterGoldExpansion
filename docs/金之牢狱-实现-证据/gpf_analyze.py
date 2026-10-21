# -*- coding: utf-8 -*-
"""第五轮 A 级读数（离线复算）——从 runServer 探针的 dump 里算：

  ① 10 个种子的序列指纹 / 件数 / 模板种类 / 落单口 / 池命中（第 2、3 步）
  ② 真实生成的 3 个群系里「结构内部地形格数」（第 5 步：修前/修后同一份脚本各跑一次）
  ③ 实体（item frame）/ 方块实体（spawner / chest）逐件核对（第 1 步）
  ④ 出入口顶部 vs 上方地形（第 4 步）

用法： python gpf_analyze.py --dir <dump 目录> [--tag 修前|修后]
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
           'minecraft:lava', 'minecraft:blackstone', 'minecraft:polished_blackstone'}


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

    # ---------------- ① 10 个种子
    sp = os.path.join(d, 'seeds.json')
    if os.path.exists(sp):
        sd = json.load(open(sp, encoding='utf-8'))
        runs = sd['runs']
        fps = [tuple(r['fingerprint']) for r in runs]
        distinct = len(set(fps))
        pieces = [len(r['pieces']) for r in runs]
        tpls = [len(set(r['fingerprint'])) for r in runs]
        orphans = [len(r['orphans']) for r in runs]
        hits = collections.Counter()
        for r in runs:
            for k, v in r['poolHits'].items():
                hits[k] += v
        print('-- 10 个种子（同一份配置）')
        print('   %-10s %-6s %-6s %-6s %-8s %s' % ('seed', '件数', '模板', '落单口', '指纹去重', '指纹'))
        seen = set()
        for r in runs:
            fp = tuple(r['fingerprint'])
            print('   %-10d %-6d %-6d %-6d %-8s %s' % (r['seed'], len(r['pieces']),
                                                       len(set(fp)), len(r['orphans']),
                                                       'NEW' if fp not in seen else 'DUP',
                                                       '>'.join(fp)))
            seen.add(fp)
        print('   序列指纹不同取值 = %d / %d（要求 >= 5）' % (distinct, len(runs)))
        print('   件数范围 = %d..%d；模板种类范围 = %d..%d；落单口合计 = %d'
              % (min(pieces), max(pieces), min(tpls), max(tpls), sum(orphans)))
        print('   池命中合计 = %s（要求不是某一个池 100%%）' % dict(hits))
        res['seeds'] = {'runs': len(runs), 'distinctFingerprints': distinct,
                        'pieceRange': [min(pieces), max(pieces)],
                        'templateKindRange': [min(tpls), max(tpls)],
                        'orphans': sum(orphans), 'poolHits': dict(hits),
                        'fingerprints': ['>'.join(f) for f in fps]}

    # ---------------- ②③④ 真实生成
    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        print('(no meta.json)')
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
        # 结构内部（件 bbox 内）里出现的「不属于任何模板调色板」的方块 = 自然地形/晚期 feature
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
        # 刷怪笼/箱子/实体
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
        print('   #%d %-18s 件=%d 自然地形格=%d（地形类 %d） spawner %d/%d 带 money_gremlin；'
              'chest %d/%d 带 LootTable；item_frame %d（chaos_coin %d）'
              % (i, m['biome'], len(m['pieces']), sum(foreign.values()), foreign_natural,
                 sp_ok, nsp, ch_ok, nch, len(frames), len(coin)))
        if foreign:
            print('      非模板方块 top: %s' % dict(foreign.most_common(8)))
        for e in ex:
            print('      exit#%d bbox=%s topY=%s 地表(WORLD_SURFACE-1)=%s 上方 8 格全空柱=%s/%s '
                  '上方最高非空气=%s 第一段空=%s'
                  % (e['pieceIndex'], e['bbox'], e['topY'], e['terrainSurfaceY'],
                     e.get('columnsClearAboveTop'), e.get('columns'),
                     e.get('maxSolidAbove'), e.get('clearFrom')))
        real.append({'biome': m['biome'], 'pieces': len(m['pieces']),
                     'foreign': sum(foreign.values()), 'foreignNatural': foreign_natural,
                     'foreignTop': dict(foreign.most_common(8)),
                     'spawner': [sp_ok, nsp], 'chest': [ch_ok, nch],
                     'frames': len(frames), 'framesCoin': len(coin),
                     'exits': ex})
    res['real'] = real
    if a.json:
        open(a.json, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
        print('   -> %s' % a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
