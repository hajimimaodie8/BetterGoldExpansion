# -*- coding: utf-8 -*-
"""第十二轮扰动矩阵：把 [bgp-exit-parent] 的每条判据都弄红一次，并证明"只改空白仍绿"。

每个用例：改字节 → 跑关卡 → 记 exit 与命中的 [bgp-exit-parent] 文案 → **逐字节复原** → SHA256 自证。
跑法（工作区自带 python，禁用 py -3）：
  <python> probe\\gpr\\gpr_perturb.py [--only P1,P2]
输出 build\\gpr_perturb.txt
"""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PY = sys.executable
GATE = os.path.join(ROOT, 'tools', 'asset-generator', 'validate_golden_prison.py')
OUT = os.path.join(ROOT, 'build', 'gpr_perturb.txt')

NBT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'structure',
                   'golden_prison', 'exit.nbt')
ROOM = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'worldgen',
                    'template_pool', 'golden_prison', 'room.json')
LANE = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'worldgen',
                    'template_pool', 'golden_prison', 'lane.json')
STRUCT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'worldgen',
                      'structure', 'golden_prison.json')

FILES = (NBT, ROOM, LANE, STRUCT)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_gate():
    p = subprocess.run([PY, GATE], cwd=ROOT, capture_output=True)
    out = (p.stdout or b'').decode('utf-8', 'replace') + (p.stderr or b'').decode('utf-8', 'replace')
    hits = [l.strip() for l in out.splitlines() if '[bgp-exit-parent]' in l or '[bgp] NG' in l]
    okline = [l.strip() for l in out.splitlines() if l.strip().startswith('[bgp-ok]')]
    failline = [l.strip() for l in out.splitlines() if l.strip().startswith('[bgp-fail]')]
    return p.returncode, hits, okline, failline


def sub_bytes(path, pairs):
    b = open(path, 'rb').read()
    for old, new in pairs:
        if b.count(old) != 1:
            raise SystemExit('%s: 模式 %r 出现 %d 次（应为 1）'
                             % (os.path.basename(path), old, b.count(old)))
        b = b.replace(old, new, 1)
    open(path, 'wb').write(b)
    return b


def nbt_room():
    """把 exit.nbt 的 jigsaw name 改回 room（重压缩）。"""
    b = open(NBT, 'rb').read()
    dec = gzip.decompress(b)
    tag = b'\x08\x00\x04name\x00\x04'
    i = dec.find(tag)
    assert dec[i + len(tag):i + len(tag) + 4] == b'lane'
    dec2 = dec[:i + len(tag)] + b'room' + dec[i + len(tag) + 4:]
    open(NBT, 'wb').write(gzip.compress(dec2, compresslevel=9, mtime=0))


CASES = []


def case(pid, desc, fn, want_red, want_problem_kw=None):
    CASES.append((pid, desc, fn, want_red, want_problem_kw))


def _room_fb_exit():
    sub_bytes(ROOM, [(b'"fallback": "minecraft:empty"', b'"fallback": "bettergold:golden_prison/exit"')])


def _lane_fb_room():
    sub_bytes(LANE, [(b'"fallback": "bettergold:golden_prison/exit"',
                      b'"fallback": "bettergold:golden_prison/room"')])


def _exit_name_room():
    nbt_room()


def _size_5():
    sub_bytes(STRUCT, [(b'"size": 4', b'"size": 5')])


def _size_odd_7():
    sub_bytes(STRUCT, [(b'"size": 4', b'"size": 7')])


def _whitespace_only_room():
    sub_bytes(ROOM, [(b'"fallback": "minecraft:empty"', b'"fallback" :  "minecraft:empty"')])


def _newline_only_lane():
    b = open(LANE, 'rb').read()
    open(LANE, 'wb').write(b + b'\n')


case('P1', 'room.json 的 fallback: empty → exit（= 回退到第七~十一轮口径）',
     _room_fb_exit, True, '过道仍可能接出入口')
case('P2', 'lane.json 的 fallback: exit → room（= 房间不再收口）',
     _lane_fb_room, True, '必须是')
case('P3', 'exit.nbt 的口 name: lane → room（= 回退到第七轮）',
     _exit_name_room, True, '必须是 lane')
case('P4', 'structure 的 size: 4 → 5（奇数 ⇒ 链尾是过道）',
     _size_5, True, '不是偶数')
case('P5', 'structure 的 size: 4 → 7（偶数但越界）',
     _size_odd_7, True, '越界')
case('P6', '只改空白（room.json 的冒号两侧多空格）⇒ 必须仍绿',
     _whitespace_only_room, False, None)
case('P7', '只加一个换行（lane.json 末尾）⇒ 必须仍绿',
     _newline_only_lane, False, None)


def main():
    only = None
    if len(sys.argv) > 2 and sys.argv[1] == '--only':
        only = set(sys.argv[2].split(','))
    base = {p: open(p, 'rb').read() for p in FILES}
    base_sha = {p: sha(v) for p, v in base.items()}
    L = []
    L.append('# 第十二轮 扰动矩阵（[bgp-exit-parent]）')
    L.append('')
    L.append('| 用例 | 改动 | 期望 | 实测 exit | 命中文案 | 复原 SHA256 |')
    L.append('|---|---|---|---|---|---|')
    bad = 0
    for pid, desc, fn, want_red, kw in CASES:
        if only and pid not in only:
            continue
        fn()
        rc, hits, okline, failline = run_gate()
        hit = ''
        for h in hits:
            if h.startswith('[bgp] NG') and (kw is None or kw in h):
                hit = h
                break
        red = (rc != 0)
        good = (red == want_red) and (not want_red or hit)
        for p in FILES:
            open(p, 'wb').write(base[p])
        same = all(sha(open(p, 'rb').read()) == base_sha[p] for p in FILES)
        if not same or not good:
            bad += 1
        L.append('| %s | %s | %s | **%d** | `%s` | %s |'
                 % (pid, desc, '红' if want_red else '绿', rc,
                    (hit or (okline[0] if okline else (failline[0] if failline else '-')))[:150],
                    'OK' if same else '**MISMATCH**'))
        print('%s exit=%d want=%s hit=%s restore=%s' % (pid, rc, 'red' if want_red else 'green',
                                                        bool(hit), 'OK' if same else 'BAD'))
    L.append('')
    L.append('复原后 SHA256（应与改前逐字节相同）：')
    L.append('')
    for p in FILES:
        L.append('- `%s` = `%s`' % (os.path.relpath(p, ROOT), base_sha[p]))
    L.append('')
    L.append('结论：%d 个用例，失败 %d 个。' % (len([c for c in CASES if not only or c[0] in only]), bad))
    text = '\n'.join(L) + '\n'
    open(OUT, 'w', encoding='utf-8', newline='\n').write(text)
    print('\n[gpr-perturb] wrote %s (bad=%d)' % (OUT, bad))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
