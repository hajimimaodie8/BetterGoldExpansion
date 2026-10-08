# -*- coding: utf-8 -*-
"""bgfix6 扰动矩阵用：造一份「有残留 forceload」的 chunks.dat（**只写到 %TEMP%，绝不碰 run\\**）。

结构（与 SavedDataStorage 的包装一致）：根 compound -> `data` compound -> `Forced` = long[1] = [0]。
字节是手写的 NBT（big-endian），再用 gzip 压缩 —— 与 `check_forced_chunks.py` 的 read_nbt 对得上。
用法: python make-dirty-chunks.py <输出路径>
"""
import gzip
import struct
import sys
from pathlib import Path

out = Path(sys.argv[1])

# inner compound: Forced = long[1] { 0 }
forced = b"\x0c" + struct.pack(">H", len("Forced")) + b"Forced" \
    + struct.pack(">i", 1) + struct.pack(">q", 0)
inner = b"\x0a" + struct.pack(">H", len("data")) + b"data" + forced + b"\x00"
root = b"\x0a" + struct.pack(">H", 0) + inner + b"\x00"

out.write_bytes(gzip.compress(root, mtime=0))
print(f"[make-dirty-chunks] 写出 {out}（Forced = [0]；gzip {out.stat().st_size} B）")
