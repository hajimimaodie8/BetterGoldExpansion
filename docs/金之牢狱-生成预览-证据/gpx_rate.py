# -*- coding: utf-8 -*-
"""一键跑金之牢狱「生成率」探针（gpxr，可复现）。

做 6 件事（无论成败都复原）：
  1) 断言没有别的 java 跑测进程（run\\ 是独占资源；gradle daemon 不算）；
  2) `run\\server.properties` 用 .bak **字节备份**（已有且一致就复用）；
  3) 改 level-name / level-seed / max-tick-time / difficulty（其余逐行不动）；
  4) 把 `docs\\金之牢狱-实现-证据\\GpRateProbe.java.txt` 复制进 `src\\...\\probe\\`；
  5) 建开关 `run\\probe\\gpxr\\RATE_ON.flag`，跑 `gradlew runServer`（日志进 `build\\`）；
  6) **无论成败**：按 .bak 字节复原 server.properties（复查 SHA256）、删探针 java + flag、
     把 `run\\probe\\gpxr\\*` 拷到 `--out` 目录后删掉 probe 目录；**世界目录留给调用方删**。

用法：
  "<bundled python>" gpx_rate.py --seed 20261020 --world gp_rate_gp1 --out "...\\docs\\金之牢狱-实现-证据\\rate_gp1"
"""
import argparse
import hashlib
import json
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
PROBE_SRC = EVID / 'GpRateProbe.java.txt'
PROBE_JAVA_DIR = ROOT / 'src' / 'main' / 'java' / 'com' / 'hjmmd_8' / 'bettergold' / 'probe'
PROBE_DST = PROBE_JAVA_DIR / 'GpRateProbe.java'
PROBE_OUT = RUN / 'probe' / 'gpxr'
FLAG = PROBE_OUT / 'RATE_ON.flag'
SP = RUN / 'server.properties'
SP_BAK = RUN / 'server.properties.gpxr.bak'


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def foreign_java():
    """返回「像 Minecraft 跑测」的 java 进程命令行（Gradle 守护进程/worker 不算）。"""
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
        print('[gpxr] 查进程失败（%s），按「没有 java」处理' % e)
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
            raise SystemExit('[gpxr] server.properties 里没有键 %r' % k)
    new = b'\n'.join(out)
    SP.write_bytes(new)
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--world', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--timeout', type=int, default=1800)
    a = ap.parse_args()
    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out

    if foreign_java():
        for c in foreign_java():
            print('[gpxr] 在跑的 java: %s' % c[:160])
        print('[gpxr] 有 java 跑测进程，run\\ 不是独占的 —— 拒绝启动')
        return 2
    if not a.world.startswith('gp_rate_gp') or '新的世界' in a.world:
        print('[gpxr] 世界名必须以 gp_rate_gp 开头且不含作者存档名')
        return 2
    if not PROBE_SRC.exists():
        print('[gpxr] 缺探针源码 %s' % PROBE_SRC)
        return 2

    cur = SP.read_bytes()
    if SP_BAK.exists() and sha(SP_BAK.read_bytes()) == sha(cur):
        print('[gpxr] server.properties.bak 已存在且与当前一致（SHA %s…）' % sha(cur)[:16])
    else:
        SP_BAK.write_bytes(cur)
        print('[gpxr] 备份 server.properties -> %s（SHA %s…）' % (SP_BAK.name, sha(cur)[:16]))
    base = SP_BAK.read_bytes()

    wdir = RUN / a.world
    if wdir.exists():
        print('[gpxr] 世界目录 %s 已存在 —— 为免读到旧数据，请换一个 --world 名' % wdir)
        return 2

    PROBE_JAVA_DIR.mkdir(parents=True, exist_ok=True)
    PROBE_DST.write_bytes(PROBE_SRC.read_bytes())
    PROBE_OUT.mkdir(parents=True, exist_ok=True)
    for f in PROBE_OUT.glob('*'):
        if f.name != 'RATE_ON.flag':
            f.unlink()
    FLAG.write_bytes(b'1\n')
    print('[gpxr] 探针 -> %s ; flag=%s' % (PROBE_DST, FLAG))

    ok = False
    try:
        patch_props(a.seed, a.world)
        print('[gpxr] server.properties: level-name=%s level-seed=%d max-tick-time=-1' % (a.world, a.seed))
        log = ROOT / 'build' / ('gpxr_server_%s.out.txt' % a.world)
        t0 = time.time()
        with open(log, 'wb') as f:
            p = subprocess.run(['.\\gradlew.bat', '--console=plain', 'runServer'],
                               cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT,
                               timeout=a.timeout)
        print('[gpxr] gradlew runServer exit=%d  用时 %.0f s  日志 %s' % (p.returncode, time.time() - t0, log))
        ok = True
    except subprocess.TimeoutExpired:
        print('[gpxr] runServer 超时（%d s）' % a.timeout)
    finally:
        SP.write_bytes(base)
        got = sha(SP.read_bytes())
        print('[gpxr] server.properties 复原 %s（SHA %s…）'
              % ('OK' if got == sha(base) else '失败', got[:16]))
        if PROBE_DST.exists():
            PROBE_DST.unlink()
        try:
            PROBE_JAVA_DIR.rmdir()
            print('[gpxr] 删空目录 %s' % PROBE_JAVA_DIR)
        except OSError:
            print('[gpxr] probe/ 里还有别的文件，未删目录')
        out.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in sorted(PROBE_OUT.glob('*')):
            if f.name == 'RATE_ON.flag':
                f.unlink()
                continue
            shutil.copyfile(f, out / f.name)
            f.unlink()
            n += 1
        print('[gpxr] dump %d 个文件 -> %s' % (n, out))
        try:
            PROBE_OUT.rmdir()
            (RUN / 'probe').rmdir()
            print('[gpxr] run\\probe 已删净')
        except OSError:
            print('[gpxr] run\\probe 非空，保留')

    meta_path = out / 'meta.json'
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        print('[gpxr] world=%s seed=%s complete=%s radius=%s'
              % (meta.get('worldName'), meta.get('seed'), meta.get('complete'), meta.get('radiusBlocks')))
        for row in meta.get('structures') or []:
            print('[gpxr]   %-28s count=%d calls=%d nulls=%d elapsed=%dms complete=%s'
                  % (row.get('id'), row.get('count'), row.get('calls'), row.get('nullResults'),
                     row.get('elapsedMs'), row.get('complete')))
            if not row.get('complete'):
                print('[gpxr]   ⚠ %s 未完成（超时）—— 不许当绿' % row.get('id'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
