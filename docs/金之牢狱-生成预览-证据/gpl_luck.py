# -*- coding: utf-8 -*-
"""金之牢狱战利品「幸运 0 vs 3」回归（runServer 一次性探针的跑测壳）。

与 `gpx_probe.py` 同一套纪律（run\\ 独占、`server.properties` 字节备份/复原、探针跑完整块删除），
只是把探针换成 `脚本副本\\GpLuckProbe.java.txt`，跑完从日志里读 `[gpl]` 两行。

用法：
  py -3 docs\\金之牢狱-生成预览-证据\\gpl_luck.py
"""
import hashlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import gpx_probe as G  # noqa: E402  （复用 foreign_java / patch_props / 路径常量）

EVID = G.EVID
NAME = 'GpLuckProbe'
SRC = EVID / '脚本副本' / (NAME + '.java.txt')
DST = G.PROBE_JAVA_DIR / (NAME + '.java')
WORLD = 'gp_luck_probe'
SEED = 20261020


def main():
    if G.foreign_java():
        print('[gpl] 有 java 跑测进程在跑 —— 拒绝启动')
        return 2
    cur = G.SP.read_bytes()
    if G.SP_BAK.exists() and G.sha(G.SP_BAK.read_bytes()) == G.sha(cur):
        print('[gpl] server.properties.bak 已存在且一致（SHA %s…）' % G.sha(cur)[:16])
    else:
        G.SP_BAK.write_bytes(cur)
    base = G.SP_BAK.read_bytes()
    wdir = G.RUN / WORLD
    if wdir.exists():
        print('[gpl] 世界目录已存在，换名或手工删：%s' % wdir)
        return 2
    G.PROBE_JAVA_DIR.mkdir(parents=True, exist_ok=True)
    DST.write_bytes(SRC.read_bytes())
    G.PROBE_OUT.mkdir(parents=True, exist_ok=True)
    for f in G.PROBE_OUT.glob('*'):
        if f.name != 'PROBE_ON.flag':
            f.unlink()
    G.FLAG.write_bytes(b'1\n')
    log = G.ROOT / 'build' / ('gpl_server_%s.out.txt' % WORLD)
    try:
        G.patch_props(SEED, WORLD)
        t0 = time.time()
        with open(log, 'wb') as f:
            p = subprocess.run(['.\\gradlew.bat', '--console=plain', 'runServer'],
                               cwd=str(G.ROOT), stdout=f, stderr=subprocess.STDOUT, timeout=1500)
        print('[gpl] gradlew runServer exit=%d  用时 %.0f s' % (p.returncode, time.time() - t0))
    except subprocess.TimeoutExpired:
        print('[gpl] runServer 超时')
    finally:
        G.SP.write_bytes(base)
        print('[gpl] server.properties 复原 %s（SHA %s…）'
              % ('OK' if G.sha(G.SP.read_bytes()) == G.sha(base) else '失败',
                 G.sha(G.SP.read_bytes())[:16]))
        if DST.exists():
            DST.unlink()
        try:
            G.PROBE_JAVA_DIR.rmdir()
            print('[gpl] 删空目录 %s' % G.PROBE_JAVA_DIR)
        except OSError:
            print('[gpl] probe/ 里还有别的文件')
        if G.FLAG.exists():
            G.FLAG.unlink()
        try:
            G.PROBE_OUT.rmdir()
            (G.RUN / 'probe').rmdir()
            print('[gpl] run\\probe 已删净')
        except OSError:
            print('[gpl] run\\probe 非空')
        if wdir.exists():
            shutil.rmtree(wdir)
            print('[gpl] 探针世界 %s 已删' % wdir)
    # 读数
    t = log.read_bytes().decode('utf-8', errors='replace') if log.exists() else ''
    lines = [l for l in t.splitlines() if '[gpl]' in l]
    for l in lines:
        print(l)
    return 0 if any('PASS' in l for l in lines) else 1


if __name__ == '__main__':
    sys.exit(main())
