# -*- coding: utf-8 -*-
"""跑测夹具：备份 / 改 / 逐字节复原 `run\\server.properties`（Python bytes，绝不走 PS 文本编码）。

用法：
  python probe/gpj/run_fixture.py patch     # 备份 + 改 level-name / level-seed / level-type
  python probe/gpj/run_fixture.py restore   # 逐字节复原 + SHA256 自证
  python probe/gpj/run_fixture.py verify    # 只核对当前 SHA
"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
P = os.path.join(ROOT, r'run\server.properties')
BAK = P + '.gpj.bak'
BASE_SHA = 'A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4'
LEVEL = 'gpj_probe'
SEED = '20261022'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


def set_kv(txt, k, v):
    lines = txt.split('\n')
    out = []
    hit = False
    for line in lines:
        if line.startswith(k + '='):
            out.append('%s=%s' % (k, v))
            hit = True
        else:
            out.append(line)
    if not hit:
        out.append('%s=%s' % (k, v))
    return '\n'.join(out)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    if cmd == 'patch':
        if not os.path.exists(BAK):
            shutil.copyfile(P, BAK)
        bak_sha = sha(BAK)
        if bak_sha != BASE_SHA:
            print('[fixture] NG 备份 SHA=%s != 基线 %s' % (bak_sha, BASE_SHA))
            return 1
        txt = open(BAK, 'rb').read().decode('utf-8')
        txt = set_kv(txt, 'level-name', LEVEL)
        txt = set_kv(txt, 'level-seed', SEED)
        open(P, 'wb').write(txt.encode('utf-8'))
        print('[fixture] patched level-name=%s level-seed=%s' % (LEVEL, SEED))
        print('[fixture] now sha=%s' % sha(P))
        return 0
    if cmd == 'restore':
        if not os.path.exists(BAK):
            print('[fixture] NG 没有备份')
            return 1
        shutil.copyfile(BAK, P)
        got = sha(P)
        ok = got == BASE_SHA
        print('[fixture] restored sha=%s %s' % (got, 'OK' if ok else 'MISMATCH'))
        return 0 if ok else 1
    print('[fixture] current sha=%s %s' % (sha(P), 'OK' if sha(P) == BASE_SHA else 'DIFF'))
    print('[fixture] backup sha=%s' % (sha(BAK) if os.path.exists(BAK) else '(none)'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
