# -*- coding: utf-8 -*-
"""`run/server.properties` 的**头部时间戳穷举抢救**（口径见 docs/1.6-规格.md §18.6 第 6 条）。

服务器每次启动都会把第 2 行重写成 `#<Day> <Mon> <DD> <HH:MM:SS> CST <YYYY>`；其余字节不动。
所以"逐字节复原"= 以外面的目标 SHA256 为准，穷举那一行的时间戳。
"""
import hashlib
import io
import sys
from datetime import datetime, timedelta

sys.stdout.reconfigure(errors="replace")
PATH = r"E:\mc\mcmod\bettergold-template-1.21.1\run\server.properties"
TARGET = "A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4"

raw = io.open(PATH, "rb").read()
lines = raw.split(b"\r\n")
assert lines[0] == b"#Minecraft server properties", lines[0]
rest = b"\r\n".join(lines[2:])                      # 第 3 行起（含行尾）
print("current header:", lines[1])
print("rest bytes:", len(rest))

start = datetime(2026, 9, 25, 0, 0, 0)
end = datetime(2026, 10, 8, 23, 59, 59)
cur = start
hits = []
while cur <= end:
    header = cur.strftime("#%a %b %d %H:%M:%S CST %Y").encode("ascii")
    blob = b"#Minecraft server properties\r\n" + header + b"\r\n" + rest
    if hashlib.sha256(blob).hexdigest().upper() == TARGET:
        hits.append((header, blob))
        break
    cur += timedelta(seconds=1)
if hits:
    header, blob = hits[0]
    io.open(PATH, "wb").write(blob)
    print("RESTORED header =", header.decode())
    print("new sha =", hashlib.sha256(io.open(PATH, "rb").read()).hexdigest().upper())
else:
    print("NOT FOUND in 2026-09-25 .. 2026-10-08 (restore 失败，需要更宽的范围或别的差异)")
    sys.exit(1)
