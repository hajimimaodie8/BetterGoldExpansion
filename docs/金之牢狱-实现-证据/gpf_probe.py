# -*- coding: utf-8 -*-
"""一键跑「金之牢狱 第五轮」A 级探针（GpFinalProbe）。

与 gpx_probe.py 同一套纪律（run\\ 独占 / 字节备份复原 / 探针跑完整块删除），差异只有：
  探针源码 = docs\\金之牢狱-实现-证据\\GpFinalProbe.java.txt
  dump 目录 = run\\probe\\gpf  →  --out（默认 docs\\金之牢狱-实现-证据\\gpf）

用法：
  python docs\\金之牢狱-实现-证据\\gpf_probe.py --seed 20261020 --world gp_final_gp1 --out docs\\金之牢狱-实现-证据\\gpf
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'run'
EVID = ROOT / 'docs' / '金之牢狱-实现-证据'
PROBE_SRC = EVID / 'GpFinalProbe.java.txt'
PROBE_JAVA_DIR = ROOT / 'src' / 'main' / 'java' / 'com' / 'hjmmd_8' / 'bettergold' / 'probe'
PROBE_DST = PROBE_JAVA_DIR / 'GpFinalProbe.java'
PROBE_OUT = RUN / 'probe' / 'gpf'
FLAG = PROBE_OUT / 'PROBE_ON.flag'
SP = RUN / 'server.properties'
SP_BAK = RUN / 'server.properties.gpf.bak'


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def foreign_java():
    out = []
    try:
        r = subprocess.run(['wmic', 'process', 'where', "name='java.exe'",
                            'get', 'CommandLine', '/format:list'],
                           capture_output=True, text=True, errors='replace')
        for ln in (r.stdout or '').splitlines():
            ln = ln.strip()
            if not ln.startswith('CommandLine='):
                continue
            cmd = ln[len('CommandLine='):].strip()
            if not cmd:
                continue
            low = cmd.lower()
            if 'gradledaemon' in low or 'gradleworker' in low or 'kotlin-daemon' in low:
                continue
            out.append(cmd)
    except Exception as e:
        print('[gpf] 查进程失败（%s），按「没有 java」处理' % e)
    return out


def patch_props(seed, world):
    raw = SP.read_bytes()
    lines = raw.split(b'\n')
    want = {b'level-name': world.encode(), b'level-seed': str(seed).encode(),
            b'max-tick-time': b'-1', b'difficulty': b'peaceful'}
    seen = set()
    out = []
    for ln in lines:
        k, sep, _ = ln.partition(b'=')
        if sep and k in want:
            out.append(k + b'=' + want[k])
            seen.add(k)
        else:
            out.append(ln)
    for k in want:
        if k not in seen:
            raise SystemExit('[gpf] server.properties 里没有键 %r' % k)
    SP.write_bytes(b'\n'.join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--world', required=True)
    ap.add_argument('--out', default='docs/金之牢狱-实现-证据/gpf')
    ap.add_argument('--timeout', type=int, default=1800)
    a = ap.parse_args()
    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out

    for c in foreign_java():
        print('[gpf] 在跑的 java: %s' % c[:160])
        print('[gpf] 有 java 跑测进程，run\\ 不是独占的 —— 拒绝启动')
        return 2
    if not a.world.startswith('gp_final_gp'):
        print('[gpf] 世界名必须以 gp_final_gp 开头（绝不碰作者的存档）')
        return 2
    if '新的世界' in a.world:
        print('[gpf] 世界名里不许出现作者存档名')
        return 2
    if not PROBE_SRC.exists():
        print('[gpf] 缺探针源码 %s' % PROBE_SRC)
        return 2

    cur = SP.read_bytes()
    if SP_BAK.exists() and sha(SP_BAK.read_bytes()) == sha(cur):
        print('[gpf] server.properties.bak 已存在且与当前一致（SHA %s…）' % sha(cur)[:16])
    else:
        SP_BAK.write_bytes(cur)
        print('[gpf] 备份 server.properties -> %s（SHA %s…）' % (SP_BAK.name, sha(cur)[:16]))
    base = SP_BAK.read_bytes()

    wdir = RUN / a.world
    if wdir.exists():
        print('[gpf] 世界目录 %s 已存在 —— 换一个 --world 名' % wdir)
        return 2

    PROBE_JAVA_DIR.mkdir(parents=True, exist_ok=True)
    PROBE_DST.write_bytes(PROBE_SRC.read_bytes())
    PROBE_OUT.mkdir(parents=True, exist_ok=True)
    for f in PROBE_OUT.glob('*'):
        if f.name != 'PROBE_ON.flag':
            f.unlink()
    FLAG.write_bytes(b'1\n')
    print('[gpf] 探针 -> %s ; flag=%s' % (PROBE_DST, FLAG))

    ok = False
    try:
        patch_props(a.seed, a.world)
        print('[gpf] server.properties: level-name=%s level-seed=%d max-tick-time=-1' % (a.world, a.seed))
        log = ROOT / 'build' / ('gpf_server_%s.out.txt' % a.world)
        t0 = time.time()
        with open(log, 'wb') as f:
            p = subprocess.run(['.\\gradlew.bat', '--console=plain', 'runServer'],
                               cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT,
                               timeout=a.timeout)
        print('[gpf] gradlew runServer exit=%d  用时 %.0f s  日志 %s' % (p.returncode, time.time() - t0, log))
        ok = True
    except subprocess.TimeoutExpired:
        print('[gpf] runServer 超时（%d s）' % a.timeout)
    finally:
        SP.write_bytes(base)
        got = sha(SP.read_bytes())
        print('[gpf] server.properties 复原 %s（SHA %s…）' % ('OK' if got == sha(base) else '失败', got[:16]))
        if PROBE_DST.exists():
            PROBE_DST.unlink()
        try:
            PROBE_JAVA_DIR.rmdir()
            print('[gpf] 删空目录 %s' % PROBE_JAVA_DIR)
        except OSError:
            print('[gpf] probe/ 里还有别的文件，未删目录')
        out.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in sorted(PROBE_OUT.glob('*')):
            if f.name == 'PROBE_ON.flag':
                f.unlink()
                continue
            shutil.copyfile(f, out / f.name)
            f.unlink()
            n += 1
        print('[gpf] dump %d 个文件 -> %s' % (n, out))
        try:
            PROBE_OUT.rmdir()
            (RUN / 'probe').rmdir()
            print('[gpf] run\\probe 已删净')
        except OSError:
            print('[gpf] run\\probe 非空，保留')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
