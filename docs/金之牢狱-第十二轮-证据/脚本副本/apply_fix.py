# -*- coding: utf-8 -*-
"""第十二轮（金之牢狱小修）：三处数据改动，一律 bytes 读写 + 改前留档 + SHA256 自证。

1) exit.nbt：jigsaw 的 `name` **room → lane**（4 字节 → 4 字节，纯字节替换，长度不变）
   依据：`JigsawBlock.canAttach` = 「父口 target == 子件 name」⇒ name=room 时出入口**只能**贴在
   target=room 的口上，而全仓只有 lane.nbt 的 target 是 room ⇒ 出入口 100% 挂在过道后面。
   改成 lane 后只能贴 target=lane 的口（= 牢房/四面道）⇒ "房间 → 出入口" 成为唯一收尾方式。
2) room.json 的 fallback：exit → minecraft:empty（过道的口不再给出口）。
3) structure/golden_prison.json 的 size：5 → 4（偶数 ⇒ 链尾那件是房间；4 而不是 6：三连四面道
   前缀已经吃掉距离预算，size=6 实测 10 件被 max_distance=116 裁掉）。

跑法：
  <python> probe\\gpr\\apply_fix.py apply      # 改
  <python> probe\\gpr\\apply_fix.py revert     # 逐字节复原（从 .orig 副本）
  <python> probe\\gpr\\apply_fix.py check      # 只打印 SHA256
"""
import gzip
import hashlib
import json
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EVID = os.path.join(ROOT, "docs", "金之牢狱-第十二轮-证据")
NBT = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "structure",
                   "golden_prison", "exit.nbt")
ROOM = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                    "template_pool", "golden_prison", "room.json")
STRUCT = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "worldgen",
                      "structure", "golden_prison.json")

BEFORE = {}   # rel -> sha256(before)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def save_orig(path, tag):
    """把**改前**的字节原样留档到 docs 证据目录（只增不改；同名只留最早那份）。"""
    os.makedirs(EVID, exist_ok=True)
    name = os.path.basename(path)
    cand = [f for f in os.listdir(EVID) if f.startswith(name + '.before-')]
    if cand:
        dst = os.path.join(EVID, sorted(cand)[0])
    else:
        dst = os.path.join(EVID, name + '.before-' + tag + '.bin')
        shutil.copyfile(path, dst)
    b = open(path, "rb").read()
    BEFORE[name] = sha(b)
    print('  before %-24s %6d B  sha256=%s' % (name, len(b), sha(b)))
    return dst


def patch_nbt():
    b = open(NBT, "rb").read()
    dec = gzip.decompress(b)
    tag = b'\x08\x00\x04name\x00\x04'
    j = dec.find(tag)
    if j < 0:
        raise SystemExit('exit.nbt 里找不到 jigsaw 的 name 字段')
    cur = dec[j + len(tag):j + len(tag) + 4]
    if cur == b'lane':
        print('  exit.nbt 已经是 name=lane（幂等跳过）')
        return
    if cur != b'room':
        raise SystemExit('exit.nbt 的 jigsaw name = %r（既不是 room 也不是 lane）' % cur)
    save_orig(NBT, sha(b)[:8])
    dec2 = dec[:j + len(tag)] + b'lane' + dec[j + len(tag) + 4:]
    assert len(dec2) == len(dec)
    open(NBT, 'wb').write(gzip.compress(dec2, compresslevel=9, mtime=0))
    after = open(NBT, 'rb').read()
    print('  after  %-24s %6d B  sha256=%s' % (os.path.basename(NBT), len(after), sha(after)))
    assert gzip.decompress(after) == dec2


def _tok(v):
    return ('"%s"' % v) if isinstance(v, str) else str(v)


def patch_json(path, key, old, new):
    b = open(path, 'rb').read()
    save_orig(path, sha(b)[:8])
    s = b.decode('utf-8')
    d = json.loads(s)
    assert d.get(key) == old, '%s.%s = %r != %r' % (os.path.basename(path), key, d.get(key), old)
    pat = '"%s": %s' % (key, _tok(old))
    rep = '"%s": %s' % (key, _tok(new))
    assert s.count(pat) == 1, '模式 %r 在 %s 里出现 %d 次' % (pat, os.path.basename(path), s.count(pat))
    s2 = s.replace(pat, rep, 1)
    d2 = json.loads(s2)
    assert d2.get(key) == new
    open(path, 'wb').write(s2.encode('utf-8'))
    after = open(path, 'rb').read()
    print('  after  %-24s %6d B  sha256=%s' % (os.path.basename(path), len(after), sha(after)))


def revert():
    for src in (NBT, ROOM, STRUCT):
        name = os.path.basename(src)
        tag = BEFORE.get(name)
        if tag is None:
            # 从现场反推：找 docs 里同名的 .before-*.bin（只有一个）
            cand = [f for f in os.listdir(EVID) if f.startswith(name + '.before-')] \
                if os.path.isdir(EVID) else []
            if not cand:
                raise SystemExit('找不到 %s 的改前留档' % name)
            src_bak = os.path.join(EVID, cand[0])
        else:
            src_bak = os.path.join(EVID, name + '.before-' + tag + '.bin')
        shutil.copyfile(src_bak, src)
        b = open(src, 'rb').read()
        print('  revert %-24s sha256=%s' % (name, sha(b)))


def check():
    for src in (NBT, ROOM, STRUCT):
        b = open(src, 'rb').read()
        print('  now    %-24s %6d B  sha256=%s' % (os.path.basename(src), len(b), sha(b)))
    dec = gzip.decompress(open(NBT, 'rb').read())
    i = dec.find(b'\x08\x00\x04name\x00\x04')
    print('  exit.nbt jigsaw name =', dec[i + 9:i + 13])
    print('  room.json fallback   =', json.load(open(ROOM, encoding='utf-8'))['fallback'])
    print('  structure size       =', json.load(open(STRUCT, encoding='utf-8'))['size'])
    print('  max_distance         =',
          json.load(open(STRUCT, encoding='utf-8'))['max_distance_from_center'])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'check':
        check()
        return 0
    if cmd == 'revert':
        revert()
        return 0
    if cmd == 'apply':
        print('[apply] exit.nbt jigsaw name room -> lane')
        patch_nbt()
        print('[apply] room.json fallback exit -> minecraft:empty')
        patch_json(ROOM, 'fallback', 'bettergold:golden_prison/exit', 'minecraft:empty')
        print('[apply] structure size 5 -> 4')
        patch_json(STRUCT, 'size', 5, 4)
        check()
        return 0
    raise SystemExit('用法: apply_fix.py [apply|revert|check]')


if __name__ == '__main__':
    sys.exit(main())
