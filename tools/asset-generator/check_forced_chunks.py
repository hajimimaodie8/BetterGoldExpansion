# -*- coding: utf-8 -*-
"""核对 forceload：打印 run/world/data/chunks.dat 的 data 段键与 Forced 长度。

用法: python check_forced_chunks.py [<chunks.dat 路径>]
"""
import gzip
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "run" / "world" / "data" / "chunks.dat"


def read_nbt(data, pos=0):
    tag = data[pos]
    pos += 1
    if tag == 0:
        return None, pos
    nlen = struct.unpack(">H", data[pos:pos + 2])[0]
    pos += 2
    name = data[pos:pos + nlen].decode("utf-8", "replace")
    pos += nlen
    if tag == 1:
        return (name, struct.unpack(">b", data[pos:pos + 1])[0]), pos + 1
    if tag == 2:
        return (name, struct.unpack(">h", data[pos:pos + 2])[0]), pos + 2
    if tag == 3:
        return (name, struct.unpack(">i", data[pos:pos + 4])[0]), pos + 4
    if tag == 4:
        return (name, struct.unpack(">q", data[pos:pos + 8])[0]), pos + 8
    if tag == 5:
        return (name, struct.unpack(">f", data[pos:pos + 4])[0]), pos + 4
    if tag == 6:
        return (name, struct.unpack(">d", data[pos:pos + 8])[0]), pos + 8
    if tag == 7:
        ln = struct.unpack(">i", data[pos:pos + 4])[0]
        return (name, list(data[pos + 4:pos + 4 + ln])), pos + 4 + ln
    if tag == 8:
        ln = struct.unpack(">H", data[pos:pos + 2])[0]
        return (name, data[pos + 2:pos + 2 + ln].decode("utf-8", "replace")), pos + 2 + ln
    if tag == 9:
        et = data[pos]
        ln = struct.unpack(">i", data[pos + 1:pos + 5])[0]
        pos += 5
        items = []
        for _ in range(ln):
            v, pos = read_payload(data, pos, et)
            items.append(v)
        return (name, items), pos
    if tag == 10:
        out = {}
        while True:
            if data[pos] == 0:
                pos += 1
                break
            (k, v), pos = read_nbt(data, pos)
            out[k] = v
        return (name, out), pos
    if tag == 11:
        ln = struct.unpack(">i", data[pos:pos + 4])[0]
        return (name, list(struct.unpack(">" + "i" * ln, data[pos + 4:pos + 4 + 4 * ln]))), pos + 4 + 4 * ln
    if tag == 12:
        ln = struct.unpack(">i", data[pos:pos + 4])[0]
        return (name, list(struct.unpack(">" + "q" * ln, data[pos + 4:pos + 4 + 8 * ln]))), pos + 4 + 8 * ln
    raise ValueError(f"unsupported tag {tag} at {pos}")


def read_payload(data, pos, tag):
    if tag == 3:
        return struct.unpack(">i", data[pos:pos + 4])[0], pos + 4
    if tag == 4:
        return struct.unpack(">q", data[pos:pos + 8])[0], pos + 8
    if tag == 10:
        out = {}
        while True:
            if data[pos] == 0:
                pos += 1
                break
            (k, v), pos = read_nbt(data, pos)
            out[k] = v
        return out, pos
    if tag == 8:
        ln = struct.unpack(">H", data[pos:pos + 2])[0]
        return data[pos + 2:pos + 2 + ln].decode("utf-8", "replace"), pos + 2 + ln
    raise ValueError(f"unsupported list element tag {tag}")


raw = gzip.decompress(PATH.read_bytes())
(_, root), _ = read_nbt(raw, 0)
inner = root.get("data", {})
print("chunks.dat top-level keys =", list(root.keys()))
print("chunks.dat data keys      =", list(inner.keys()))
forced = inner.get("Forced")
print("data.Forced               =", forced)
print("data.Forced length        =", 0 if forced is None else len(forced))
print("chunks.dat 侧 forceload 为 0 =", forced is None or len(forced) == 0)
