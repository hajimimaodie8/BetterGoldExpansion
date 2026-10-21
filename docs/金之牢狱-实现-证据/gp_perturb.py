# -*- coding: utf-8 -*-
"""金之牢狱关卡扰动矩阵（[bgp-*] 的「能红」自证）。

每个用例：备份字节 + SHA256 -> 施加扰动 -> 跑关卡 -> 逐字节复原 -> 复查 SHA256。
判读三列：exit / hit_expected / restored（见 docs\\构建与跑测注意事项.md §六/§七）。
用法：
  "<bundled python>" gp_perturb.py
"""
import gzip
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
VAL = os.path.join(ROOT, 'tools', 'asset-generator', 'validate_golden_prison.py')
STRUCT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'structure', 'golden_prison')
LOOT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'loot_table', 'chests',
                    'golden_prison.json')
POOL = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'worldgen', 'template_pool',
                    'golden_prison', 'room.json')
POOL_DIR = os.path.dirname(POOL)
LANE = os.path.join(POOL_DIR, 'lane.json')
START = os.path.join(POOL_DIR, 'start.json')
SSET = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'worldgen', 'structure_set',
                    'golden_prison.json')


# ---------------------------------------------------------------- NBT 读写（独立实现）
class Rd:
    def __init__(self, d):
        self.d = d
        self.p = 0

    def take(self, n):
        b = self.d[self.p:self.p + n]
        self.p += n
        if len(b) != n:
            raise EOFError('eof')
        return b

    def u1(self):
        return self.take(1)[0]

    def u2(self):
        return struct.unpack('>H', self.take(2))[0]

    def i4(self):
        return struct.unpack('>i', self.take(4))[0]

    def i8(self):
        return struct.unpack('>q', self.take(8))[0]

    def s(self):
        return self.take(self.u2()).decode('utf-8')


def read_payload(r, t):
    if t == 1:
        return struct.unpack('>b', r.take(1))[0]
    if t == 2:
        return struct.unpack('>h', r.take(2))[0]
    if t == 3:
        return r.i4()
    if t == 4:
        return r.i8()
    if t == 5:
        return struct.unpack('>f', r.take(4))[0]
    if t == 6:
        return struct.unpack('>d', r.take(8))[0]
    if t == 7:
        return r.take(r.i4())
    if t == 8:
        return r.s()
    if t == 9:
        it = r.u1()
        n = r.i4()
        return [] if it == 0 else [read_payload(r, it) for _ in range(n)]
    if t == 10:
        out = {}
        while True:
            tt = r.u1()
            if tt == 0:
                return out
            k = r.s()
            out[k] = read_payload(r, tt)
    if t == 11:
        n = r.i4()
        return list(struct.unpack('>%di' % n, r.take(4 * n)))
    if t == 12:
        n = r.i4()
        return list(struct.unpack('>%dq' % n, r.take(8 * n)))
    raise ValueError(t)


def load_nbt(path):
    raw = open(path, 'rb').read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    r = Rd(raw)
    assert r.u1() == 10
    r.s()
    return read_payload(r, 10)


def enc_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def infer(v):
    if isinstance(v, bool):
        return 1, (1 if v else 0)
    if isinstance(v, int):
        return 3, v
    if isinstance(v, float):
        return 6, v
    if isinstance(v, str):
        return 8, v
    if isinstance(v, bytes):
        return 7, v
    if isinstance(v, list):
        if not v:
            return 9, (3, [])
        et = None
        for it in v:
            t, _ = infer(it)
            if et is None:
                et = t
        return 9, (et, v)
    if isinstance(v, dict):
        return 10, v
    raise TypeError(type(v))


def write_tag(buf, t, name, val):
    buf += bytes([t]) + enc_str(name)
    write_payload(buf, t, val)


def write_payload(buf, t, val):
    if t == 1:
        buf += struct.pack('>b', val)
    elif t == 2:
        buf += struct.pack('>h', val)
    elif t == 3:
        buf += struct.pack('>i', val)
    elif t == 4:
        buf += struct.pack('>q', val)
    elif t == 5:
        buf += struct.pack('>f', val)
    elif t == 6:
        buf += struct.pack('>d', val)
    elif t == 7:
        buf += struct.pack('>i', len(val)) + val
    elif t == 8:
        buf += enc_str(val)
    elif t == 9:
        et, items = val
        buf += bytes([et]) + struct.pack('>i', len(items))
        for it in items:
            write_payload(buf, et, it)
    elif t == 10:
        for k, v in val.items():
            tt, vv = infer(v)
            write_tag(buf, tt, k, vv)
        buf += b'\x00'
    elif t == 11:
        buf += struct.pack('>i', len(val)) + struct.pack('>%di' % len(val), *val)
    elif t == 12:
        buf += struct.pack('>i', len(val)) + struct.pack('>%dq' % len(val), *val)
    else:
        raise ValueError(t)


def save_nbt(path, root):
    buf = bytearray()
    write_tag(buf, 10, '', root)
    open(path, 'wb').write(gzip.compress(bytes(buf), 9, mtime=0))


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


# ---------------------------------------------------------------- 扰动
def flip_orientation(root):
    """把宝藏房南口的 south_up 改成 north_up（方向反了）。"""
    n = 0
    for b in root['blocks']:
        be = b.get('nbt') or {}
        if be.get('id') == 'minecraft:jigsaw' and be.get('name') == 'room':
            pal = root['palette'][b['state']]
            if pal.get('Properties', {}).get('orientation') == 'south_up':
                pal['Properties']['orientation'] = 'north_up'
                n += 1
    return n


def shift_jigsaw(root):
    """把 cell_small_a 的北口 jigsaw 沿 z 平移 1 格（口位错一格）。"""
    n = 0
    for b in root['blocks']:
        be = b.get('nbt') or {}
        if be.get('id') == 'minecraft:jigsaw' and b['pos'][2] == 0 and b['pos'][1] == 1:
            b['pos'][2] += 1
            n += 1
            break
    return n


def drop_block(root):
    n0 = len(root['blocks'])
    for i, b in enumerate(root['blocks']):
        if b['pos'] == [1, 0, 1]:
            del root['blocks'][i]
            break
    return n0 - len(root['blocks'])


def move_mirror_block(root):
    """把镜像件的某个方块换掉（破坏镜像逐格一致性）。"""
    n = 0
    idx = None
    for i, e in enumerate(root['palette']):
        if e['Name'] == 'bettergold:gold_bricks':
            idx = i
            break
    if idx is None:
        return 0
    for b in root['blocks']:
        if b['pos'] == [13, 1, 5]:
            b['state'] = idx
            n += 1
            break
    return n


def loot_weight(text):
    d = json.loads(text)
    d['pools'][0]['entries'][0]['weight'] = 99
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def pool_missing(text):
    d = json.loads(text)
    d['elements'][0]['element']['location'] = 'bettergold:golden_prison/does_not_exist'
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def pool_fallback_empty(text):
    """把 lane 的 fallback 改成 empty ⇒ 深度 7 不再长出出入口（[bgp-connect] 必须红）。"""
    d = json.loads(text)
    d['fallback'] = 'minecraft:empty'
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def strip_air(root):
    """P7 = P0 复现：把这个件里的空气条目全删掉（修前那种「模板不含空气」的样子）。"""
    n0 = len(root['blocks'])
    root['blocks'] = [b for b in root['blocks']
                      if root['palette'][b['state']]['Name'] != 'minecraft:air']
    return n0 - len(root['blocks'])


def plug_mouth_cell(root):
    """P8：把口平面 3x3 的中间一格填成实心（门洞从 3x3 退化成 1~2 格）。"""
    idx = None
    for i, e in enumerate(root['palette']):
        if e['Name'] not in ('minecraft:air', 'minecraft:jigsaw', 'minecraft:chest',
                             'minecraft:structure_void'):
            idx = i
            break
    if idx is None:
        return 0
    for b in root['blocks']:
        if b['pos'] == [7, 2, 0]:
            b['state'] = idx
            return 1
    return 0


def only_whitespace(text):
    return '\n\n' + text.replace('{', '{\n', 1) + '\n\n'


def _treasure_element(weight=1):
    return {
        'weight': weight,
        'element': {
            'element_type': 'minecraft:single_pool_element',
            'location': 'bettergold:golden_prison/treasure',
            'processors': 'minecraft:empty',
            'projection': 'rigid',
        },
    }


def lane_add_treasure(text):
    """P10：把 treasure 加进 lane.json 的 elements ⇒ 必须红在 [bgp-treasure-unique-noref]。"""
    d = json.loads(text)
    d['elements'].append(_treasure_element())
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def lane_fallback_start(text):
    """P11：给 lane.json 加 fallback=start ⇒ 必须红在 [bgp-treasure-unique-fallback]。"""
    d = json.loads(text)
    d['fallback'] = 'bettergold:golden_prison/start'
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def start_add_treasure(text):
    """P12：把 start.json 再塞一份 treasure ⇒ 必须红在 [bgp-treasure-unique-start]。"""
    d = json.loads(text)
    d['elements'].append(_treasure_element(weight=2))
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def sset_spacing_32(text):
    """P13：把 spacing 改回旧值 32 ⇒ 必须红在 [bgp-rate-fortress]。"""
    d = json.loads(text)
    d['placement']['spacing'] = 32
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def sset_spread_triangular(text):
    """P14：把 spread_type 改成 triangular ⇒ 必须红在 [bgp-rate-fortress]。"""
    d = json.loads(text)
    d['placement']['spread_type'] = 'triangular'
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


# ---------------------------------------------------------------- 第五轮新增
def strip_entities(root):
    """P15：把 treasure 的实体段清空（= 作者三图「展示框没放」的回归）。"""
    n = len(root.get('entities') or [])
    root['entities'] = []
    return n


def strip_spawn_data(root):
    """P16：把第一个刷怪笼的 SpawnData 删掉（= 「刷怪笼的金钱妖没了」）。"""
    for b in root['blocks']:
        be = b.get('nbt') or {}
        if be.get('id') == 'minecraft:mob_spawner' and 'SpawnData' in be:
            be.pop('SpawnData')
            return 1
    return 0


def cut_shaft(root):
    """P17：把 exit 的上升段切掉（只留门楼 8 层）—— [bgp-shaft] 必须红。"""
    n0 = len(root['blocks'])
    root['blocks'] = [b for b in root['blocks'] if b['pos'][1] < 8]
    return n0 - len(root['blocks'])


def room_fallback_empty(text):
    """P18：room 的 fallback 改成 empty ⇒ 深度到顶没有出口，[bgp-pool-reach] 必须红。"""
    d = json.loads(text)
    d['fallback'] = 'minecraft:empty'
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def room_fertile_weight_1(text):
    """P19：丰饶权重 6 → 1 ⇒ [bgp-pool-reach] 的权重记账必须红。"""
    d = json.loads(text)
    for e in d['elements']:
        if (e['element']['location'] or '').endswith('_fertile'):
            e['weight'] = 1
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def exit_target_room(root):
    """P20：把 exit 的口 target 改回 room ⇒ [bgp-pool-reach] 必须红。"""
    for b in root['blocks']:
        be = b.get('nbt') or {}
        if be.get('id') == 'minecraft:jigsaw':
            be['target'] = 'room'
            be['pool'] = 'bettergold:golden_prison/room'
            return 1
    return 0


def run_val():
    r = subprocess.run([sys.executable, VAL], capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')


CASES = []


def nbt_case(name, fname, mut, needle):
    CASES.append((name, os.path.join(STRUCT, fname), 'nbt', mut, needle))


def text_case(name, path, mut, needle):
    CASES.append((name, path, 'text', mut, needle))


nbt_case('P1-orientation-flip', 'treasure.nbt', flip_orientation, 'orientation')
nbt_case('P2-jigsaw-shift-1', 'cell_small_a.nbt', shift_jigsaw, '不在唯一的外侧面上')
nbt_case('P3-drop-one-block', 'cell_medium_a.nbt', drop_block, '方块数')
nbt_case('P4-mirror-cell-mismatch', 'cell_small_mirror.nbt', move_mirror_block, '镜像')
text_case('P5-loot-weight', LOOT, loot_weight, '权重和')
text_case('P6-pool-missing-template', POOL, pool_missing, '不存在的模板')
text_case('C1-loot-only-whitespace', LOOT, only_whitespace, '')
text_case('C2-validator-comment-only', VAL,
          lambda t: t.replace('# -*- coding: utf-8 -*-',
                              '# -*- coding: utf-8 -*-\n# (perturb: comment only, must stay green)', 1),
          '')
# ---- 阶段 B 新增：空气档必须「能红」（P0 的真值 + 3x3 门洞 + 拼接连通）
nbt_case('P7-strip-all-air (= P0)', 'cell_small_a.nbt', strip_air, 'bgp-air')
nbt_case('P8-plug-one-mouth-cell', 'cell_small_a.nbt', plug_mouth_cell, '口平面 3x3x1')
text_case('P9-lane-fallback-empty', POOL.replace('room.json', 'lane.json'),
          pool_fallback_empty, 'bgp-connect')
# ---- 第三轮新增：宝藏房「结构唯一性」断言必须能红（P10/P11/P12 各打一条）
text_case('P10-treasure-second-pool', LANE, lane_add_treasure, 'bgp-treasure-unique-noref')
text_case('P11-lane-fallback-start', LANE, lane_fallback_start, 'bgp-treasure-unique-fallback')
text_case('P12-start-second-treasure', START, start_add_treasure, 'bgp-treasure-unique-start')
# ---- 第三轮追加：生成率 == 下界要塞（P13/P14 打 [bgp-rate-fortress]）
text_case('P13-spacing-back-to-32', SSET, sset_spacing_32, 'bgp-rate-fortress')
text_case('P14-spread-type-triangular', SSET, sset_spread_triangular, 'bgp-rate-fortress')
# ---- 第五轮新增：实体/BE 导出（P15/P16）、出入口上升段（P17）、随机化的池（P18/P19/P20）
nbt_case('P15-drop-entities', 'treasure.nbt', strip_entities, 'bgp-entity')
nbt_case('P16-drop-spawn-data', 'treasure.nbt', strip_spawn_data, 'bgp-be')
nbt_case('P17-cut-exit-shaft', 'exit.nbt', cut_shaft, 'bgp-shaft')
text_case('P18-room-fallback-empty', POOL, room_fallback_empty, 'bgp-pool-reach')
text_case('P19-fertile-weight-1', POOL, room_fertile_weight_1, 'bgp-pool-reach')
nbt_case('P20-exit-target-room', 'exit.nbt', exit_target_room, 'bgp-pool-reach')
text_case('C3-room-only-whitespace', POOL, only_whitespace, '')


def main():
    print('== 金之牢狱关卡扰动矩阵 ==')
    hdr = '%-28s %-6s %-13s %-6s' % ('case', 'exit', 'hit_expected', 'restored')
    print(hdr)
    rows = []
    base_exit, base_out = run_val()
    print('%-28s %-6d %-13s %-6s' % ('P0-baseline(no change)', base_exit, 'n/a', 'n/a'))
    bad = 0
    for name, path, kind, mut, needle in CASES:
        before = open(path, 'rb').read()
        h0 = hashlib.sha256(before).hexdigest()
        try:
            if kind == 'nbt':
                root = load_nbt(path)
                n = mut(root)
                applied = n > 0 or name.startswith('P3')
                save_nbt(path, root)
            else:
                txt = before.decode('utf-8')
                new = mut(txt)
                applied = new != txt
                open(path, 'w', encoding='utf-8', newline='\n').write(new)
        finally:
            pass
        code, out = run_val()
        hit = (needle in out) if needle else (code == 0)
        hit_s = 'YES' if hit else 'NO'
        open(path, 'wb').write(before)
        h1 = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        restored = 'YES' if h0 == h1 else 'NO'
        print('%-28s %-6d %-13s %-6s  (mut_applied=%s)' % (name, code, hit_s, restored, applied))
        rows.append((name, code, hit_s, restored, applied, h0))
        if not (hit and restored and applied):
            bad += 1
    print('\n== 汇总 ==')
    print('baseline exit=%d, cases=%d, 不合格=%d' % (base_exit, len(CASES), bad))
    if base_exit != 0:
        print('baseline 不是 0 -> 扰动矩阵无效')
        return 2
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
