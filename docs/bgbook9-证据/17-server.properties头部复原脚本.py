# -*- coding: utf-8 -*-
"""bg-book §九：把 `run/server.properties` 逐字节复原（专用服务器会重写头部时间戳那一行）。

口径（`mcmod_experience` `ex\\05`）：目标哈希是唯一判据；先把已知的原始时间戳行放回去，
不中就在一个时间窗里**穷举那一行**，直到哈希等于目标（不中则如实记账）。

Run: python build\\bgbook9-restore-props.py
"""
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
P = os.path.join(REPO, "run", "server.properties")
TARGET = "a2229937ba8ab7428bc959e87a784890500d6d7061b10fa8302758e46a01d3c4"
ORIG_LINE = b"#Mon Oct 05 17:40:32 CST 2026"
raw = io.open(P, "rb").read()
cur = raw.split(b"\n")[1] if raw.count(b"\n") else b""
print("current header line:", cur)
print("current sha256     :", hashlib.sha256(raw).hexdigest())
print("target  sha256     :", TARGET)

if hashlib.sha256(raw).hexdigest() == TARGET:
    print("ALREADY-OK")
    sys.exit(0)

new = raw.replace(cur, ORIG_LINE + b"\r", 1)
h = hashlib.sha256(new).hexdigest()
print("after restoring the known original timestamp line:", h, "OK" if h == TARGET else "**MISMATCH**")
if h != TARGET:
    # 穷举：同一天 ±1 天、09:00~23:59 的每一分钟
    pat = re.compile(rb"^#\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} CST 2026$")
    if not pat.match(cur):
        raise SystemExit("SETUP-FAIL: 头部那一行不是预期形状：%r" % cur)
    days = [b"Sun", b"Mon", b"Tue", b"Wed", b"Thu", b"Fri", b"Sat"]
    months = [b"Jan", b"Feb", b"Mar", b"Apr", b"May", b"Jun",
              b"Jul", b"Aug", b"Sep", b"Oct", b"Nov", b"Dec"]
    found = None
    for mo in (b"Oct", b"Sep", b"Nov"):
        for d in range(1, 32):
            for hh in range(0, 24):
                for mm in range(0, 60):
                    for ss in range(0, 60, 7):
                        for wd in days:
                            cand = b"#%s %s %02d %02d:%02d:%02d CST 2026" % (wd, mo, d, hh, mm, ss)
                            trial = raw.replace(cur, cand, 1)
                            if hashlib.sha256(trial).hexdigest() == TARGET:
                                found = cand
                                break
                        if found:
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        if found:
            break
    if not found:
        raise SystemExit("EXHAUST-FAIL: 穷举没找到能还原目标哈希的时间戳行（如实记账）")
    new, h = raw.replace(cur, found, 1), TARGET
    print("exhaustive rescue found:", found)

io.open(P, "wb").write(new)
print("restored sha256    :", hashlib.sha256(io.open(P, "rb").read()).hexdigest())
