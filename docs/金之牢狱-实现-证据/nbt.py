# -*- coding: utf-8 -*-
"""最小 NBT / 区域文件(.mca) 解析器 —— 手写实现，无第三方依赖。

类型码见 NBT 规范（1..12）。区域文件格式：8 KiB 头（4096 偏移 + 4096 时间戳），
每区块 4 字节长度 + 1 字节压缩方式（1 gzip / 2 zlib / 3 none / 4 lz4）。
"""
import gzip
import io
import struct
import zlib

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


class Reader:
    def __init__(self, data):
        self.d = data
        self.p = 0

    def take(self, n):
        b = self.d[self.p:self.p + n]
        if len(b) != n:
            raise EOFError('unexpected end of NBT buffer')
        self.p += n
        return b

    def u1(self):
        return self.take(1)[0]

    def i1(self):
        return struct.unpack('>b', self.take(1))[0]

    def u2(self):
        return struct.unpack('>H', self.take(2))[0]

    def i2(self):
        return struct.unpack('>h', self.take(2))[0]

    def i4(self):
        return struct.unpack('>i', self.take(4))[0]

    def i8(self):
        return struct.unpack('>q', self.take(8))[0]

    def f4(self):
        return struct.unpack('>f', self.take(4))[0]

    def f8(self):
        return struct.unpack('>d', self.take(8))[0]

    def string(self):
        n = self.u2()
        return self.take(n).decode('utf-8', 'replace')


def read_payload(r, t):
    if t == TAG_BYTE:
        return r.i1()
    if t == TAG_SHORT:
        return r.i2()
    if t == TAG_INT:
        return r.i4()
    if t == TAG_LONG:
        return r.i8()
    if t == TAG_FLOAT:
        return r.f4()
    if t == TAG_DOUBLE:
        return r.f8()
    if t == TAG_BYTE_ARRAY:
        return r.take(r.i4())
    if t == TAG_STRING:
        return r.string()
    if t == TAG_LIST:
        it = r.u1()
        n = r.i4()
        if it == TAG_END:
            return []
        return [read_payload(r, it) for _ in range(n)]
    if t == TAG_COMPOUND:
        out = {}
        while True:
            tt = r.u1()
            if tt == TAG_END:
                return out
            name = r.string()
            out[name] = read_payload(r, tt)
    if t == TAG_INT_ARRAY:
        n = r.i4()
        return list(struct.unpack('>%di' % n, r.take(4 * n)))
    if t == TAG_LONG_ARRAY:
        n = r.i4()
        return list(struct.unpack('>%dq' % n, r.take(8 * n)))
    raise ValueError('unknown tag type %r' % t)


def parse(data, offset=0):
    """返回 (root_name, root_payload)。data 可为原始未压缩 NBT。"""
    r = Reader(data)
    r.p = offset
    t = r.u1()
    if t != TAG_COMPOUND:
        raise ValueError('root tag is not compound: %r' % t)
    name = r.string()
    return name, read_payload(r, TAG_COMPOUND)


def parse_auto(data):
    """按魔数自动识别 gzip / zlib / 原始 NBT。"""
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    elif data[:1] == b'\x78':
        try:
            data = zlib.decompress(data)
        except zlib.error:
            pass
    return parse(data)


def parse_region(path):
    """遍历区域文件，产出 (chunk_x, chunk_z, root_dict, compression)。"""
    raw = open(path, 'rb').read()
    if len(raw) < 8192:
        return
    for i in range(1024):
        off = (raw[i * 4] << 16) | (raw[i * 4 + 1] << 8) | raw[i * 4 + 2]
        cnt = raw[i * 4 + 3]
        if off == 0 or cnt == 0:
            continue
        start = off * 4096
        if start + 5 > len(raw):
            continue
        length = struct.unpack('>I', raw[start:start + 4])[0]
        comp = raw[start + 4]
        payload = raw[start + 5:start + 4 + length]
        if comp == 1:
            payload = gzip.decompress(payload)
        elif comp == 2:
            payload = zlib.decompress(payload)
        elif comp == 3:
            pass
        elif comp == 4:
            raise ValueError('LZ4 region chunk not supported: %s' % path)
        else:
            raise ValueError('unknown compression %r in %s' % (comp, path))
        _, root = parse(payload)
        yield (i & 31, i >> 5, root, comp)


def bits_for(n):
    b = max(1, (n - 1).bit_length())
    return max(4, b)


def unpack_indices(longs, bits, count):
    """1.16+ 非跨长边打包：每个 long 放 64//bits 个索引，低位在前。"""
    per = 64 // bits
    mask = (1 << bits) - 1
    out = []
    for v in longs:
        v &= (1 << 64) - 1
        for _ in range(per):
            out.append(v & mask)
            v >>= bits
            if len(out) >= count:
                return out
    return out[:count]


def section_blocks(section):
    """返回 {(x,y,z): (name, props)}，局部坐标 0..15。"""
    bs = section.get('block_states')
    if not bs:
        return {}
    palette = bs.get('palette') or []
    data = bs.get('data')
    names = [(p.get('Name'), p.get('Properties') or {}) for p in palette]
    out = {}
    if not data:
        if not names:
            return out
        nm, pr = names[0]
        if nm == 'minecraft:air':
            return out
        for y in range(16):
            for z in range(16):
                for x in range(16):
                    out[(x, y, z)] = (nm, pr)
        return out
    bits = bits_for(len(palette))
    idx = unpack_indices(data, bits, 4096)
    for y in range(16):
        for z in range(16):
            for x in range(16):
                i = idx[(y * 16 + z) * 16 + x]
                if i >= len(names):
                    continue
                nm, pr = names[i]
                if nm == 'minecraft:air':
                    continue
                out[(x, y, z)] = (nm, pr)
    return out
