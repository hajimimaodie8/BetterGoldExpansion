# -*- coding: utf-8 -*-
"""最小 NBT 读取器（gzip + big-endian），只为读出金之牢狱模板里的 jigsaw 块。

不写世界、不改文件；输出每个模板的 jigsaw 块：pos / name / pool / target / joint / facing。
用法: py -3 probe/gpr/nbt_dump.py [模板目录]
"""
import gzip
import json
import os
import struct
import sys

TAG = {
    1: "byte", 2: "short", 3: "int", 4: "long", 5: "float", 6: "double",
    7: "byteArray", 8: "string", 9: "list", 10: "compound", 11: "intArray", 12: "longArray",
}


class R:
    def __init__(self, buf):
        self.b = buf
        self.i = 0

    def take(self, n):
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def u1(self):
        return self.take(1)[0]

    def i2(self):
        return struct.unpack(">h", self.take(2))[0]

    def u2(self):
        return struct.unpack(">H", self.take(2))[0]

    def i4(self):
        return struct.unpack(">i", self.take(4))[0]

    def i8(self):
        return struct.unpack(">q", self.take(8))[0]

    def f4(self):
        return struct.unpack(">f", self.take(4))[0]

    def f8(self):
        return struct.unpack(">d", self.take(8))[0]

    def s(self):
        n = self.u2()
        return self.take(n).decode("utf-8", "replace")


def payload(r, t):
    if t == 1:
        return r.u1()
    if t == 2:
        return r.i2()
    if t == 3:
        return r.i4()
    if t == 4:
        return r.i8()
    if t == 5:
        return r.f4()
    if t == 6:
        return r.f8()
    if t == 7:
        n = r.i4()
        return list(r.take(n))
    if t == 8:
        return r.s()
    if t == 9:
        et = r.u1()
        n = r.i4()
        return [payload(r, et) for _ in range(n)]
    if t == 10:
        out = {}
        while True:
            tt = r.u1()
            if tt == 0:
                return out
            nm = r.s()
            out[nm] = payload(r, tt)
    if t == 11:
        n = r.i4()
        return [r.i4() for _ in range(n)]
    if t == 12:
        n = r.i4()
        return [r.i8() for _ in range(n)]
    raise ValueError("bad tag %d at %d" % (t, r.i))


def read_nbt(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    r = R(raw)
    t = r.u1()
    if t != 10:
        raise ValueError("root not compound")
    r.s()  # root name
    return payload(r, 10)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else \
        r"src\main\resources\data\bettergold\structure\golden_prison"
    rows = {}
    for fn in sorted(os.listdir(base)):
        if not fn.endswith(".nbt"):
            continue
        root = read_nbt(os.path.join(base, fn))
        blocks = root.get("blocks", [])
        js = []
        for b in blocks:
            if b.get("nbt", {}).get("id") != "minecraft:jigsaw":
                continue
            n = b["nbt"]
            js.append({
                "pos": b.get("pos"),
                "name": n.get("name"),
                "pool": n.get("pool"),
                "target": n.get("target"),
                "joint": n.get("joint"),
                "facing": n.get("facing"),
                "final_state": b.get("state"),
            })
        js.sort(key=lambda d: (d["pos"][1], d["pos"][0], d["pos"][2]))
        rows[fn[:-4]] = {"size": root.get("size"), "jigsaws": js}
    print(json.dumps(rows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
