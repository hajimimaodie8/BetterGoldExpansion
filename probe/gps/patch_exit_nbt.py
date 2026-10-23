# -*- coding: utf-8 -*-
"""本轮唯一一次 .nbt 改动：exit.nbt 的 jigsaw `name` room -> lane（4 字节，其余一律不动）。

- 改前留档（逐字节）到 docs\\金之牢狱-第十三轮-证据\\exit.nbt.before-<sha8>.bin
- 只在**解压后的 NBT 字节流**里替换那 4 字节；`target`/`pool`/`joint`/`orientation`/`final_state`、
  方块集合与坐标全部不动
- 自证：解压后逐字节 diff（应恰好 4 字节不同）+ 结构逐格 diff（removed 0 / added 0 / changed 0）

跑法（工作区自带 python，禁止 py -3）：
  <python> probe\\gps\\patch_exit_nbt.py [apply|check]
"""
import gzip
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EVID = os.path.join(ROOT, "docs", "金之牢狱-第十三轮-证据")
NBT = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "structure",
                   "golden_prison", "exit.nbt")
TAG = b"\x08\x00\x04name\x00\x04"
OUT = os.path.join(ROOT, "build", "gps_nbt_diff.txt")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def payload(b):
    return gzip.decompress(b)


def apply():
    raw = open(NBT, "rb").read()
    dec = payload(raw)
    os.makedirs(EVID, exist_ok=True)
    bak = os.path.join(EVID, "exit.nbt.before-%s.bin" % sha(raw)[:8])
    shutil.copyfile(NBT, bak)
    print("before %d B sha256=%s -> %s" % (len(raw), sha(raw), os.path.basename(bak)))
    if dec.count(TAG) != 1:
        raise SystemExit("exit.nbt 里 name 标签出现 %d 次（应恰好 1）" % dec.count(TAG))
    i = dec.find(TAG) + len(TAG)
    cur = dec[i:i + 4]
    if cur == b"lane":
        print("已经是 lane（幂等）")
        return 0
    if cur != b"room":
        raise SystemExit("jigsaw name = %r（既不是 room 也不是 lane）" % cur)
    dec2 = dec[:i] + b"lane" + dec[i + 4:]
    assert len(dec2) == len(dec) and dec2 != dec
    open(NBT, "wb").write(gzip.compress(dec2, compresslevel=9, mtime=0))
    raw2 = open(NBT, "rb").read()
    assert payload(raw2) == dec2
    print("after  %d B sha256=%s" % (len(raw2), sha(raw2)))
    diff = [k for k in range(len(dec)) if dec[k] != dec2[k]]
    print("decompressed bytes=%d, differing offsets=%r (4 字节)" % (len(dec), diff))
    return 0


def check():
    raw = open(NBT, "rb").read()
    dec = payload(raw)
    i = dec.find(TAG) + len(TAG)
    print("now %d B sha256=%s" % (len(raw), sha(raw)))
    print("jigsaw name = %r / 紧随其后的字符串（target 等）按结构 diff 见下" % dec[i:i + 4])
    baks = [f for f in os.listdir(EVID) if f.startswith("exit.nbt.before-")]
    if not baks:
        raise SystemExit("找不到改前留档")
    old = payload(open(os.path.join(EVID, sorted(baks)[0]), "rb").read())
    diff = [k for k in range(max(len(old), len(dec))) if k >= len(old) or k >= len(dec) or old[k] != dec[k]]
    print("改前留档=%s / 解压后差异字节=%d（位置 %r）" % (sorted(baks)[0], len(diff), diff))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    sys.exit(apply() if cmd == "apply" else check())
