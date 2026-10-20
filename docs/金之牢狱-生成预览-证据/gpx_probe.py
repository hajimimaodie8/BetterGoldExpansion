# -*- coding: utf-8 -*-
"""一键跑金之牢狱预览探针（阶段 B / 可复现）。

做 7 件事（无论成败都复原）：
  1) 断言没有别的 java 跑测进程（run\\ 是独占资源；gradle daemon 不算）；
  2) `run\\server.properties` 用 .bak **字节备份**（已有且一致就复用）；
  3) 改 level-name / level-seed / max-tick-time / difficulty（其余逐行不动）；
  4) 把 `脚本副本\\GpPreviewProbe.java.txt` 复制进 `src\\...\\probe\\GpPreviewProbe.java`；
  5) 建开关 `run\\probe\\gpx\\PROBE_ON.flag`，跑 `gradlew runServer`（日志进 `build\\`）；
  6) **无论成败**：按 .bak 字节复原 server.properties（复查 SHA256）、删探针 java + flag；
  7) 把 `run\\probe\\gpx\\*.tsv|*.json` 拷到 `--out` 目录，然后删 `run\\probe\\gpx`。

用法：
  py -3 docs\\金之牢狱-生成预览-证据\\gpx_probe.py --seed 20261020 --world gp_preview_gpb --out "...\\_raw"
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
EVID = ROOT / 'docs' / '金之牢狱-生成预览-证据'
PROBE_SRC = EVID / '脚本副本' / 'GpPreviewProbe.java.txt'
PROBE_JAVA_DIR = ROOT / 'src' / 'main' / 'java' / 'com' / 'hjmmd_8' / 'bettergold' / 'probe'
PROBE_DST = PROBE_JAVA_DIR / 'GpPreviewProbe.java'
PROBE_DIR = PROBE_DST.parent
PROBE_OUT = RUN / 'probe' / 'gpx'
FLAG = PROBE_OUT / 'PROBE_ON.flag'
SP = RUN / 'server.properties'
SP_BAK = RUN / 'server.properties.gpx.bak'


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def foreign_java():
    """返回「像 Minecraft 跑测」的 java 进程命令行（Gradle 守护进程/worker 不算）。

    ⚠ 本仓的 gradle daemon 常年是 java.exe：不能只看「有没有 java」。
    """
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
        print('[gpx] 查进程失败（%s），按「没有 java」处理' % e)
    return out


def patch_props(seed, world):
    """按行替换 4 个键，其余字节不动。"""
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
    for k, v in want.items():
        if k not in seen:
            raise SystemExit('[gpx] server.properties 里没有键 %r' % k)
    new = b'\n'.join(out)
    SP.write_bytes(new)
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--world', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--timeout', type=int, default=1500)
    ap.add_argument('--planes', default='', help='x,z —— 强制剖面坐标（修前/修后同视角）')
    ap.add_argument('--reuse', action='store_true', help='世界目录已存在时吃已生成的区块')
    a = ap.parse_args()
    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out

    if foreign_java():
        for c in foreign_java():
            print('[gpx] 在跑的 java: %s' % c[:160])
        print('[gpx] 有 java 跑测进程，run\\ 不是独占的 —— 拒绝启动')
        return 2
    if not a.world.startswith('gp_preview_gp'):
        print('[gpx] 世界名必须以 gp_preview_gp 开头（绝不碰作者的存档）')
        return 2
    if '新的世界' in a.world:
        print('[gpx] 世界名里不许出现作者存档名')
        return 2
    if not PROBE_SRC.exists():
        print('[gpx] 缺探针源码 %s' % PROBE_SRC)
        return 2

    # 1) 备份（已有且与当前一致就复用；否则当前字节即基线）
    cur = SP.read_bytes()
    if SP_BAK.exists() and sha(SP_BAK.read_bytes()) == sha(cur):
        print('[gpx] server.properties.bak 已存在且与当前一致（SHA %s…）' % sha(cur)[:16])
    else:
        SP_BAK.write_bytes(cur)
        print('[gpx] 备份 server.properties -> %s（SHA %s…）' % (SP_BAK.name, sha(cur)[:16]))
    base = SP_BAK.read_bytes()

    # 2) 世界目录（新世界；同名目录必须不是作者存档）
    wdir = RUN / a.world
    if wdir.exists() and not a.reuse:
        print('[gpx] 世界目录 %s 已存在 —— 为免读到旧地形，请换一个 --world 名（或 --reuse）' % wdir)
        return 2

    # 3) 探针源码 + 开关
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    PROBE_DST.write_bytes(PROBE_SRC.read_bytes())
    PROBE_OUT.mkdir(parents=True, exist_ok=True)
    for f in PROBE_OUT.glob('*'):
        if f.name != 'PROBE_ON.flag':
            f.unlink()
    if a.planes:
        (PROBE_OUT / 'PLANES.txt').write_bytes(a.planes.encode('ascii'))
        print('[gpx] 强制剖面 x,z = %s' % a.planes)
    FLAG.write_bytes(b'1\n')
    print('[gpx] 探针 -> %s ; flag=%s' % (PROBE_DST, FLAG))

    ok = False
    try:
        patch_props(a.seed, a.world)
        print('[gpx] server.properties: level-name=%s level-seed=%d max-tick-time=-1' % (a.world, a.seed))
        log = ROOT / 'build' / ('gpx_server_%s.out.txt' % a.world)
        t0 = time.time()
        with open(log, 'wb') as f:
            p = subprocess.run(['.\\gradlew.bat', '--console=plain', 'runServer'],
                               cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT,
                               timeout=a.timeout)
        print('[gpx] gradlew runServer exit=%d  用时 %.0f s  日志 %s' % (p.returncode, time.time() - t0, log))
        ok = True
    except subprocess.TimeoutExpired:
        print('[gpx] runServer 超时（%d s）' % a.timeout)
    finally:
        # 4) 复原（字节 + SHA256）
        SP.write_bytes(base)
        got = sha(SP.read_bytes())
        same = got == sha(base)
        print('[gpx] server.properties 复原 %s（SHA %s…）' % ('OK' if same else '失败', got[:16]))
        # 5) 删探针 java（只删这一个文件 + 空目录，绝不递归）
        if PROBE_DST.exists():
            PROBE_DST.unlink()
        try:
            PROBE_DIR.rmdir()
            print('[gpx] 删空目录 %s' % PROBE_DIR)
        except OSError:
            print('[gpx] probe/ 里还有别的文件，未删目录')
        # 6) 拷 dump
        out.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in sorted(PROBE_OUT.glob('*')):
            if f.name == 'PROBE_ON.flag':
                f.unlink()
                continue
            shutil.copyfile(f, out / f.name)
            f.unlink()
            n += 1
        print('[gpx] dump %d 个文件 -> %s' % (n, out))
        try:
            PROBE_OUT.rmdir()
            (RUN / 'probe').rmdir()
            print('[gpx] run\\probe 已删净')
        except OSError:
            print('[gpx] run\\probe 非空，保留')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
