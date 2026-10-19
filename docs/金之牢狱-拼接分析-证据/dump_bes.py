# -*- coding: utf-8 -*-
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt

BASE = r'E:\mc\mcmod\bettergold-template-1.21.1\docs\金之牢狱-素材清单\金之牢狱'
OUT = os.path.dirname(os.path.abspath(__file__))


def dump(obj):
    """把 NBT 值转成可 JSON 的纯 Python 对象（bytes -> hex 摘要）。"""
    if isinstance(obj, bytes):
        return {'__bytes_len__': len(obj), 'hex_head': obj[:32].hex()}
    if isinstance(obj, list):
        return [dump(v) for v in obj]
    if isinstance(obj, dict):
        return {k: dump(v) for k, v in obj.items()}
    return obj


def main():
    bes = []
    for fn in sorted(os.listdir(os.path.join(BASE, 'region'))):
        if not fn.endswith('.mca'):
            continue
        for cx, cz, root, comp in nbt.parse_region(os.path.join(BASE, 'region', fn)):
            for be in (root.get('block_entities') or []):
                be = dict(be)
                be['__chunk__'] = [cx, cz]
                be['__region__'] = fn
                bes.append(be)
    print('total block entities', len(bes))
    ids = {}
    for be in bes:
        ids[be.get('id')] = ids.get(be.get('id'), 0) + 1
    print(json.dumps(ids, indent=1))
    with open(os.path.join(OUT, 'block_entities.json'), 'w', encoding='utf-8') as f:
        json.dump(dump(bes), f, ensure_ascii=False, indent=1)

    print('\n== structure blocks ==')
    for be in bes:
        if be.get('id') == 'minecraft:structure_block':
            print(json.dumps(dump(be), ensure_ascii=False))
    print('\n== chests / barrels ==')
    for be in bes:
        if be.get('id') in ('minecraft:chest', 'minecraft:barrel', 'minecraft:trapped_chest'):
            slim = {k: v for k, v in be.items() if k not in ('__chunk__',)}
            print(json.dumps(dump(slim), ensure_ascii=False)[:1200])
    print('\n== spawners ==')
    for be in bes:
        if be.get('id') == 'minecraft:mob_spawner':
            sd = be.get('SpawnData') or {}
            print(be.get('x'), be.get('y'), be.get('z'), json.dumps(dump(sd), ensure_ascii=False)[:300])
    print('\n== other BE ids ==')
    for be in bes:
        if be.get('id') not in ('minecraft:structure_block', 'minecraft:chest', 'minecraft:barrel',
                                'minecraft:mob_spawner', 'minecraft:trapped_chest'):
            print(be.get('id'), be.get('x'), be.get('y'), be.get('z'))


if __name__ == '__main__':
    main()
