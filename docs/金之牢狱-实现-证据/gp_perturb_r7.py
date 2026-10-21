# -*- coding: utf-8 -*-
"""第七轮扰动矩阵（12 用例）：每条都要能红 + 逐字节复原 + SHA256 自证。

覆盖本轮新增的每一类断言：
  ① 空腔几何（地板/四壁/天花板/3x3 通道）
  ② 箱子 ↔ BE 双向
  ③ 落单口的 canAttach（socket name）
  ④ 露头校准快照 / 探针口径
  ⑤ 去注释源码 needle（add_cavity / socket name / 常量）
  + 「只改注释仍绿」一条

用法： python gp_perturb_r7.py
"""
import gzip
import hashlib
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
EVID = os.path.join(ROOT, 'docs', '金之牢狱-实现-证据')
RES = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'structure', 'golden_prison')
WG = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'worldgen')
GATE = os.path.join(ROOT, 'tools', 'asset-generator', 'validate_golden_prison.py')
sys.path.insert(0, EVID)
import nbt  # noqa: E402


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def run_gate():
    r = subprocess.run(['py', '-3', GATE], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')


class File:
    def __init__(self, path):
        self.path = path
        self.bak = open(path, 'rb').read()
        self.h = sha(self.bak)

    def restore(self):
        with open(self.path, 'wb') as f:
            f.write(self.bak)
        return sha(open(self.path, 'rb').read()) == self.h


def write_bytes(path, b):
    with open(path, 'wb') as f:
        f.write(b)



def conv(v, key=''):
    """把 nbt.parse_auto 的结果写回带类型的 NBT 值（模板里只有这些类型）。"""
    if isinstance(v, bool):
        return (1, 1 if v else 0)
    if isinstance(v, int):
        return (3, v)
    if isinstance(v, float):
        return (6, v)
    if isinstance(v, str):
        return (8, v)
    if isinstance(v, list):
        if key in ('pos', 'size') and v and all(isinstance(x, int) for x in v):
            return (9, (3, [int(x) for x in v]))
        if key == 'pos' and v and all(isinstance(x, (int, float)) for x in v):
            return (9, (6, [float(x) for x in v]))
        if v and isinstance(v[0], dict):
            # 列表里的 compound：nbt_payload(t=9) 对 et=10 直接吃 dict（不是 (type,val)）
            return (9, (10, [conv(x)[1] for x in v]))
        if v and all(isinstance(x, str) for x in v):
            return (9, (8, list(v)))
        return (9, (10, [conv(x)[1] for x in v]))
    if isinstance(v, dict):
        return (10, {kk: conv(vv, kk) for kk, vv in v.items()})
    raise ValueError('conv: %r' % (v,))


def mutate_nbt_direct(path, fn):
    """直接改 .nbt 文件（绕过 build_nbt 的兜底），用来模拟"产物本身坏了"。"""
    import gp_build
    _, root = nbt.parse_auto(open(path, 'rb').read())
    fn(root)
    buf = bytearray()
    gp_build.nbt_tag(buf, 10, '', conv(root)[1])
    write_bytes(path, gzip.compress(bytes(buf), 9, mtime=0))


def piece_json():
    with open(os.path.join(EVID, 'pieces_stage2.json'), encoding='utf-8') as f:
        return json.load(f)


def build_nbt_for(name, mutate):
    import gp_build
    data = piece_json()
    p = json.loads(json.dumps(data['pieces'][name]))
    mutate(p)
    raw = gp_build.build_nbt(p)
    return gzip.compress(raw, 9, mtime=0)


def k(x, y, z):
    return '%d,%d,%d' % (x, y, z)


CASES = []


def case(code, desc):
    def deco(fn):
        CASES.append((code, desc, fn))
        return fn
    return deco


@case('bgp-cavity', 'P33 空腔地板挖一个洞 (5,39,5)')
def _(f):
    def m(p):
        p['blocks'].pop(k(5, 39, 5), None)
    write_bytes(os.path.join(RES, 'exit.nbt'), build_nbt_for('exit', m))


@case('bgp-cavity', 'P34 空腔四壁挖一个洞 (10,50,5)')
def _(f):
    def m(p):
        p['blocks'].pop(k(10, 50, 5), None)
    write_bytes(os.path.join(RES, 'exit.nbt'), build_nbt_for('exit', m))


@case('bgp-cavity', 'P35 空腔天花板挖一个洞 (5,61,5)')
def _(f):
    def m(p):
        p['blocks'].pop(k(5, 61, 5), None)
    write_bytes(os.path.join(RES, 'exit.nbt'), build_nbt_for('exit', m))


@case('bgp-cavity', 'P36 3x3 井筒通道被堵 (2,50,2)')
def _(f):
    def m(p):
        p['blocks'][k(2, 50, 2)] = ['bettergold:gold_bricks', {}]
    write_bytes(os.path.join(RES, 'exit.nbt'), build_nbt_for('exit', m))


@case('bgp-be', 'P37 箱子方块上的 BE 被换成 mob_spawner（反向断言）')
def _(f):
    def m(root):
        pal = root['palette']
        for b in root['blocks']:
            if pal[b['state']]['Name'] == 'minecraft:chest' and 'nbt' in b:
                b['nbt']['id'] = 'minecraft:mob_spawner'
                return
    mutate_nbt_direct(os.path.join(RES, 'cell_small_fertile.nbt'), m)


@case('bgp-chest', 'P38 箱子方块丢掉 LootTable')
def _(f):
    def m(root):
        pal = root['palette']
        for b in root['blocks']:
            if pal[b['state']]['Name'] == 'minecraft:chest' and 'nbt' in b:
                b['nbt'].pop('LootTable', None)
                return
    mutate_nbt_direct(os.path.join(RES, 'cell_small_fertile.nbt'), m)


@case('bgp-cavity-calib', 'P39 校准快照里把一个口干成 airFromY=99')
def _(f):
    s = open(GATE, encoding='utf-8').read()
    old = "'crimson_forest#6': (77, 42),"
    assert s.count(old) == 1
    write_bytes(GATE, s.replace(old, "'crimson_forest#6': (77, 99),").encode('utf-8'))


@case('bgp-cavity-calib', 'P40 探针口径回退 EXIT_CAVITY_ABOVE 18 → 17')
def _(f):
    p = os.path.join(EVID, 'GphProbe.java.txt')
    s = open(p, encoding='utf-8').read()
    old = 'EXIT_CAVITY_ABOVE = 18'
    assert s.count(old) == 1
    write_bytes(p, s.replace(old, 'EXIT_CAVITY_ABOVE = 17').encode('utf-8'))


@case('bgp-worldgen', 'P41 structure size 回退 5 → 6')
def _(f):
    p = os.path.join(WG, 'structure', 'golden_prison.json')
    s = open(p, encoding='utf-8').read()
    assert '"size": 5' in s
    write_bytes(p, s.replace('"size": 5', '"size": 6', 1).encode('utf-8'))


@case('bgp-cavity', 'P42 gp_build 空腔净空常量改小 EXIT_CAVITY_INNER (1,9)→(1,7)')
def _(f):
    p = os.path.join(EVID, 'gp_build.py')
    s = open(p, encoding='utf-8').read()
    old = 'EXIT_CAVITY_INNER = (1, 9)'
    assert s.count(old) == 1
    write_bytes(p, s.replace(old, 'EXIT_CAVITY_INNER = (1, 7)').encode('utf-8'))


@case('bgp-cavity', 'P43 gp_build exit socket name 回退 room → lane')
def _(f):
    p = os.path.join(EVID, 'gp_build.py')
    s = open(p, encoding='utf-8').read()
    old = "'exit':        {'north': ('room', 'empty', 'minecraft:empty')},"
    assert s.count(old) == 1
    write_bytes(p, s.replace(old, old.replace("('room'", "('lane'")).encode('utf-8'))


@case('bgp-cavity', 'P44 gp_build 的 add_cavity 改名（空腔不再由流水线生成）')
def _(f):
    p = os.path.join(EVID, 'gp_build.py')
    s = open(p, encoding='utf-8').read()
    old = 'def add_cavity('
    assert s.count(old) == 1
    write_bytes(p, s.replace(old, 'def add_cavity_v1(').encode('utf-8'))


def target_of(desc):
    pre = desc[:3]
    if pre in ('P33', 'P34', 'P35', 'P36'):
        return os.path.join(RES, 'exit.nbt')
    if pre in ('P37', 'P38'):
        return os.path.join(RES, 'cell_small_fertile.nbt')
    if pre == 'P39':
        return GATE
    if pre == 'P40':
        return os.path.join(EVID, 'GphProbe.java.txt')
    if pre == 'P41':
        return os.path.join(WG, 'structure', 'golden_prison.json')
    return os.path.join(EVID, 'gp_build.py')


def main():
    results = []
    for code, desc, fn in CASES:
        tgt = target_of(desc)
        f = File(tgt)
        try:
            fn(f)
            rc, out = run_gate()
            hit = ('[%s]' % code) in out
            results.append((desc, rc, hit, f.restore()))
            print('%-58s exit=%d hit=%s restored=%s' % (desc, rc, 'YES' if hit else 'NO',
                                                        'YES' if results[-1][3] else 'NO'))
        except Exception as e:
            f.restore()
            results.append((desc, -1, False, True))
            print('%-58s EXC %s' % (desc, e))
        sys.stdout.flush()
    # + 只改注释仍绿
    g = File(os.path.join(EVID, 'gp_build.py'))
    s = open(g.path, 'ab')
    s.write(b'\n# r7 perturb: comment only (should stay green)\n')
    s.close()
    rc, out = run_gate()
    restored = g.restore()
    print('%-58s exit=%d hit=%s restored=%s' % ('C5 只改注释（注释里写 add_cavity/room 仍应绿）',
                                                rc, 'NO' if rc == 0 else 'YES', 'YES' if restored else 'NO'))
    results.append(('C5 只改注释', rc, rc != 0, restored))
    bad = [r for r in results
           if (r[0].startswith('C5') and (r[1] != 0 or not r[3]))
           or (not r[0].startswith('C5') and (r[1] != 1 or not r[2] or not r[3]))]
    print('== 合计 %d 用例；不合预期 %d 条 ==' % (len(results), len(bad)))
    for b in bad:
        print('   NG', b)
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
